import json
import urllib.error
import urllib.request
from datetime import date

import anvil.secrets
import anvil.server


OPENAI_URL = "https://api.openai.com/v1/responses"
MODEL = "gpt-6.1-sol"
MAX_PROMPT_CHARS = 4000
MAX_CODE_CHARS = 40000
MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_MESSAGE_CHARS = 4000
MAX_DAILY_REQUESTS = 12

LANGUAGES = {
  "Python", "JavaScript", "TypeScript", "HTML + CSS", "Java", "C#", "C++",
  "Go", "PHP", "Ruby", "SQL", "Bash", "Rust", "Kotlin", "Swift",
}
PROJECT_TYPES = {
  "Website", "Mobile app concept", "Online store", "Portfolio", "Blog",
  "Dashboard", "REST API", "Automation tool", "Chatbot", "Learning project", "Game",
}

INSTRUCTIONS = """You are Vrokal AI, a helpful conversational assistant. Answer general questions naturally and clearly, explain ideas in simple language, and help users think through projects. You are also a coding partner.

Use the selected language and project type when the user requests code. Write a concrete first implementation rather than a generic scaffold or a list of TODOs. Make sensible assumptions when details are missing and mention them briefly in assistant_message. For games, implement the described gameplay and include appropriate controls, movement, collisions, scoring, and a start/end/restart flow. For an HTML + CSS browser game, return a complete, self-contained HTML file with its CSS and JavaScript included. Include short setup or dependency notes in assistant_message when needed. Do not claim the code was run or tested.

For ordinary questions or conversation, answer in assistant_message and return an empty string for code so the existing editor content is preserved. When the user asks to create or change code, return the full code in code, not a patch. Use the latest code supplied in the request as the starting point for code changes. Never invent code just to fill the code field. Do not claim to browse the web or take actions unless a tool actually did that."""

OUTPUT_SCHEMA = {
  "type": "object",
  "properties": {
    "assistant_message": {"type": "string"},
    "code": {"type": "string"},
  },
  "required": ["assistant_message", "code"],
  "additionalProperties": False,
}


def _failure(message):
  return {"ok": False, "message": message}


def _collect_output_text(response_data):
  pieces = []
  for output_item in response_data.get("output", []):
    if output_item.get("type") != "message" or output_item.get("role") != "assistant":
      continue
    for content_item in output_item.get("content", []):
      if content_item.get("type") == "output_text":
        pieces.append(content_item.get("text", ""))
  return "".join(pieces)


@anvil.server.callable
def generate_project_code(language, project_type, prompt, history=None, current_code=""):
  if language not in LANGUAGES or project_type not in PROJECT_TYPES:
    return _failure("Choose a language and project type from the menus.")
  if not isinstance(prompt, str) or not prompt.strip():
    return _failure("Write a short description of what you want to build.")
  if len(prompt) > MAX_PROMPT_CHARS:
    return _failure("Please keep each message under 4,000 characters.")
  if not isinstance(current_code, str) or len(current_code) > MAX_CODE_CHARS:
    return _failure("The current code is too long to revise in one request. Start a new chat or shorten it.")

  if history is None:
    history = []
  if not isinstance(history, list) or len(history) > MAX_HISTORY_MESSAGES:
    return _failure("This conversation is too long to continue. Start a new chat and try again.")

  clean_history = []
  total_history_chars = 0
  for message in history:
    if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
      return _failure("The conversation history could not be read. Start a new chat and try again.")
    content = message.get("content")
    if not isinstance(content, str) or len(content) > MAX_HISTORY_MESSAGE_CHARS:
      return _failure("A chat message is too long to continue. Start a new chat and try again.")
    total_history_chars += len(content)
    if total_history_chars > 24000:
      return _failure("This conversation is too long to continue. Start a new chat and try again.")
    clean_history.append({"role": message["role"], "content": content})

  try:
    api_key = anvil.secrets.get_secret("OPENAI_API_KEY")
  except anvil.secrets.SecretError:
    return _failure("Vrokal AI is not connected yet. Add OPENAI_API_KEY in the app's App Secrets, then try again.")

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

  request_text = "Selected language: {}\nProject type: {}\nLatest user request:\n{}".format(
    language, project_type, prompt.strip()
  )
  if current_code.strip():
    request_text += "\n\nLatest code from the editor (revise this full version):\n{}".format(current_code)

  input_messages = clean_history + [{"role": "user", "content": request_text}]
  payload = {
    "model": MODEL,
    "instructions": INSTRUCTIONS,
    "input": input_messages,
    "max_output_tokens": 6000,
    "store": False,
    "text": {
      "format": {
        "type": "json_schema",
        "name": "vrokal_code_result",
        "strict": True,
        "schema": OUTPUT_SCHEMA,
      }
    },
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
    with urllib.request.urlopen(request, timeout=90) as response:
      response_data = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as error:
    if error.code in (401, 403):
      return _failure("OpenAI rejected the API key. Check OPENAI_API_KEY in App Secrets.")
    if error.code == 429:
      return _failure("The AI service is at its usage limit. Check the OpenAI API account or try again later.")
    if error.code >= 500:
      return _failure("The AI service is temporarily unavailable. Please try again shortly.")
    return _failure("The AI service rejected this request. Check model access or shorten your description.")
  except urllib.error.URLError:
    return _failure("Vrokal could not reach the AI service. Check your connection and try again.")
  except TimeoutError:
    return _failure("Vrokal AI took too long to respond. Please try again with a shorter request.")
  except json.JSONDecodeError:
    return _failure("The AI service returned an unreadable response. Please try again.")

  if response_data.get("status") != "completed":
    return _failure("The code response was interrupted. Please try a shorter description.")

  output_text = _collect_output_text(response_data)
  if not output_text:
    return _failure("Vrokal AI did not return code this time. Please revise your request and try again.")
  try:
    result = json.loads(output_text)
  except json.JSONDecodeError:
    return _failure("Vrokal AI returned a response that could not be read. Please try again.")

  if not isinstance(result, dict):
    return _failure("Vrokal AI returned an incomplete result. Please try again.")
  assistant_message = result.get("assistant_message")
  code = result.get("code")
  if not isinstance(assistant_message, str) or not isinstance(code, str):
    return _failure("Vrokal AI returned an incomplete result. Please try again.")

  return {"ok": True, "assistant_message": assistant_message, "code": code}
