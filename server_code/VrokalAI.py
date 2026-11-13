import json
import urllib.error
import urllib.request
from datetime import date

import anvil.secrets
import anvil.server


OPENAI_URL = "https://api.openai.com/v1/responses"
MODEL = "gpt-6-luna"
MAX_PROMPT_CHARS = 4000
MAX_CODE_CHARS = 40000
MAX_HISTORY_MESSAGES = 4
MAX_HISTORY_MESSAGE_CHARS = 4000
MAX_DAILY_REQUESTS = 12
MAX_OUTPUT_TOKENS = 1600
STREAM_TIMEOUT_SECONDS = 25

LANGUAGES = {
  "Python", "JavaScript", "TypeScript", "HTML + CSS", "Java", "C#", "C++",
  "Go", "PHP", "Ruby", "SQL", "Bash", "Rust", "Kotlin", "Swift",
}
PROJECT_TYPES = {
  "Website", "Mobile app concept", "Online store", "Portfolio", "Blog",
  "Dashboard", "REST API", "Automation tool", "Chatbot", "Learning project", "Game",
}

INSTRUCTIONS = """You are Vrokal AI, a code generator. Treat each user prompt as a request to create or revise software using the selected language and project type. Return the requested source code, not an explanation. If details are missing, make sensible assumptions and build a small, complete first version instead of asking questions. Keep the first draft focused on core features so it can be generated quickly. Avoid unrequested extras, long comments, lengthy explanations, and large sample datasets. Include every file essential to run a multi-file project; show filenames and separate each file clearly. For a single-file project, return the complete source without markdown fences. Never invent libraries. When revising, use the latest code supplied in the request. Never execute code or claim it was run, tested, or guaranteed to work."""


def _failure(message):
  return {"ok": False, "message": message}


def _clean_history(history):
  if history is None:
    history = []
  if not isinstance(history, list) or len(history) > MAX_HISTORY_MESSAGES:
    return None, "This conversation is too long to continue. Start a new chat and try again."

  clean_history = []
  total_history_chars = 0
  for message in history:
    if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
      return None, "The conversation history could not be read. Start a new chat and try again."
    content = message.get("content")
    if not isinstance(content, str) or len(content) > MAX_HISTORY_MESSAGE_CHARS:
      return None, "A chat message is too long to continue. Start a new chat and try again."
    total_history_chars += len(content)
    if total_history_chars > 24000:
      return None, "This conversation is too long to continue. Start a new chat and try again."
    clean_history.append({"role": message["role"], "content": content})
  return clean_history, None


def _set_task_failure(message):
  anvil.server.task_state.update({
    "ok": False,
    "done": True,
    "message": message,
  })


def _stream_code(request):
  code_parts = []
  code_length = 0
  completed = False

  with urllib.request.urlopen(request, timeout=STREAM_TIMEOUT_SECONDS) as response:
    for raw_line in response:
      if not raw_line.startswith(b"data:"):
        continue
      event_text = raw_line[5:].strip().decode("utf-8")
      if not event_text or event_text == "[DONE]":
        continue

      event = json.loads(event_text)
      event_type = event.get("type")

      if event_type == "response.output_text.delta":
        delta = event.get("delta", "")
        if isinstance(delta, str) and delta:
          code_parts.append(delta)
          code_length += len(delta)
          anvil.server.task_state["code"] = "".join(code_parts)
          if code_length > MAX_CODE_CHARS:
            return None, "This project is too large for one quick reply. Ask for one part at a time."

      elif event_type == "response.failed" or event_type == "error":
        return None, "The AI service could not finish this response. Please try again shortly."

      elif event_type == "response.incomplete":
        return None, "This project needs more code than fits in one quick reply. Ask for one feature at a time."

      elif event_type == "response.completed":
        response_data = event.get("response", {})
        if response_data.get("status") != "completed":
          return None, "This project needs more code than fits in one quick reply. Ask for one feature at a time."
        completed = True
        break

  code = "".join(code_parts)
  if not completed:
    return None, "The AI connection ended before the code was complete. Please try again."
  if not code.strip():
    return None, "Vrokal AI did not produce code. Describe the app, website, game, or feature you want, then try again."
  return code, None


@anvil.server.callable
def start_project_code_generation(language, project_type, prompt, history=None, current_code=""):
  if language not in LANGUAGES or project_type not in PROJECT_TYPES:
    return _failure("Choose a language and project type from the menus.")
  if not isinstance(prompt, str) or not prompt.strip():
    return _failure("Write a short description of what you want to build.")
  if len(prompt) > MAX_PROMPT_CHARS:
    return _failure("Please keep each message under 4,000 characters.")
  if not isinstance(current_code, str) or len(current_code) > MAX_CODE_CHARS:
    return _failure("The current code is too long to revise in one request. Start a new chat or shorten it.")

  clean_history, history_error = _clean_history(history)
  if history_error:
    return _failure(history_error)

  try:
    api_key = anvil.secrets.get_secret("OPENAI_API_KEY")
  except anvil.secrets.SecretError:
    api_key = None
  if not api_key:
    return _failure("Vrokal AI is not connected yet. Add OPENAI_API_KEY in the app's App Secrets, then try again.")

  today = date.today().isoformat()
  request_state = anvil.server.session.get("vrokal_ai_daily_requests", {})
  if not isinstance(request_state, dict) or request_state.get("day") != today:
    request_state = {"day": today, "count": 0}
  request_count = request_state.get("count", 0)
  if not isinstance(request_count, int):
    request_count = 0
  if request_count >= MAX_DAILY_REQUESTS:
    return _failure("This browser session has reached today's 12-request limit. Try again tomorrow.")
  anvil.server.session.set("vrokal_ai_daily_requests", {
    "day": today,
    "count": request_count + 1,
  })

  task = anvil.server.launch_background_task(
    "generate_project_code_task",
    language,
    project_type,
    prompt.strip(),
    clean_history,
    current_code.strip(),
  )
  task_id = task.get_id()
  anvil.server.session.set("vrokal_active_generation_task", task_id)
  return {"ok": True, "task_id": task_id}


@anvil.server.callable
def get_project_code_progress(task_id, offset=0):
  if not isinstance(task_id, str) or task_id != anvil.server.session.get("vrokal_active_generation_task"):
    return _failure("This code request is no longer active. Start a new chat and try again.")
  if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
    return _failure("The code progress request was invalid. Start a new chat and try again.")

  task = anvil.server.get_background_task(task_id)
  state = task.get_state()
  code = state.get("code", "")
  if not isinstance(code, str):
    code = ""
  code_delta = code[offset:]
  result = {
    "ok": state.get("ok", True),
    "done": state.get("done", False),
    "code_delta": code_delta,
    "next_offset": offset + len(code_delta),
    "message": state.get("message", ""),
  }

  if not result["done"] and not task.is_running():
    task_error = task.get_error()
    if task_error is not None:
      raise task_error
    return _failure("The code request stopped before finishing. Please try again.")
  return result


@anvil.server.background_task
def generate_project_code_task(language, project_type, prompt, history, current_code):
  anvil.server.task_state.update({
    "ok": True,
    "done": False,
    "code": "",
    "message": "",
  })

  try:
    api_key = anvil.secrets.get_secret("OPENAI_API_KEY")
  except anvil.secrets.SecretError:
    _set_task_failure("Vrokal AI is not connected yet. Add OPENAI_API_KEY in the app's App Secrets, then try again.")
    return
  if not api_key:
    _set_task_failure("Vrokal AI is not connected yet. Add OPENAI_API_KEY in the app's App Secrets, then try again.")
    return

  request_text = "Selected language: {}\nProject type: {}\nLatest user request:\n{}".format(
    language, project_type, prompt
  )
  if current_code:
    request_text += "\n\nLatest code from the editor (revise this full version):\n{}".format(current_code)

  payload = {
    "model": MODEL,
    "reasoning": {"effort": "none"},
    "instructions": INSTRUCTIONS,
    "input": history + [{"role": "user", "content": request_text}],
    "max_output_tokens": MAX_OUTPUT_TOKENS,
    "stream": True,
    "store": False,
  }
  request = urllib.request.Request(
    OPENAI_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={
      "Authorization": "Bearer {}".format(api_key),
      "Content-Type": "application/json",
    },
    method="POST",
  )

  try:
    code, error_message = _stream_code(request)
  except urllib.error.HTTPError as error:
    if error.code in (401, 403):
      error_message = "OpenAI rejected the API key. Check OPENAI_API_KEY in App Secrets."
    elif error.code == 429:
      error_message = "The AI service is at its usage limit. Check the OpenAI API account or try again later."
    elif error.code >= 500:
      error_message = "The AI service is temporarily unavailable. Please try again shortly."
    else:
      error_message = "The AI service rejected this request. Check model access or shorten your description."
    _set_task_failure(error_message)
    return
  except urllib.error.URLError:
    _set_task_failure("Vrokal could not reach the AI service. Check your connection and try again.")
    return
  except TimeoutError:
    _set_task_failure("Vrokal AI took too long to respond. Try a smaller request.")
    return
  except json.JSONDecodeError:
    _set_task_failure("The AI service returned an unreadable response. Please try again.")
    return

  if error_message:
    _set_task_failure(error_message)
    return

  anvil.server.task_state.update({
    "ok": True,
    "done": True,
    "code": code,
    "message": "Code generated.",
  })
