from ._anvil_designer import Form1Template
from anvil import *
import anvil.server
import anvil.media


class Form1(Form1Template):
  def __init__(self, **properties):
    super().__init__(**properties)
    self.language_dropdown.items = [
      "Python", "JavaScript", "TypeScript", "HTML + CSS", "Java", "C#", "C++",
      "Go", "PHP", "Ruby", "SQL", "Bash", "Rust", "Kotlin", "Swift",
    ]
    self.language_dropdown.selected_value = "Python"
    self.project_type_dropdown.items = [
      "Website", "Mobile app concept", "Online store", "Portfolio", "Blog",
      "Dashboard", "REST API", "Automation tool", "Chatbot", "Learning project", "Game",
    ]
    self.project_type_dropdown.selected_value = "Game"
    self.code_output.text = ""
    self.conversation_history = []
    self.active_generation_task_id = None
    self.generation_offset = 0
    self.pending_generation_prompt = None
    self.exiting_wizard_slide = None
    self.chat_messages = [{
      "speaker": "Vrokal AI",
      "content": "Describe the app, website, game, or tool you want. Vrokal AI will write the code in the selected language.",
    }]
    self.chat_history_panel.items = self.chat_messages
    self.generator_status.text = "Describe what you want to build."
    self.current_wizard_step = 1
    self._set_wizard_step(1)

  def _set_wizard_step(self, step):
    step_slides = [self.language_step, self.project_step, self.details_step]
    step_markers = [
      self.step_marker_language,
      self.step_marker_project,
      self.step_marker_details,
    ]
    previous_step = self.current_wizard_step
    self.current_wizard_step = max(1, min(3, step))
    moving_forward = self.current_wizard_step > previous_step
    direction = "forward" if moving_forward else "back"

    if self.exiting_wizard_slide is not None:
      self.exiting_wizard_slide.classes["is-exiting-forward"] = False
      self.exiting_wizard_slide.classes["is-exiting-back"] = False
      self.exiting_wizard_slide = None

    for slide in step_slides:
      slide.classes["is-entering-forward"] = False
      slide.classes["is-entering-back"] = False

    if self.current_wizard_step != previous_step:
      old_slide = step_slides[previous_step - 1]
      old_slide.classes["is-active"] = False
      old_slide.classes["is-exiting-{}".format(direction)] = True
      self.exiting_wizard_slide = old_slide
      self.slide_transition_timer.interval = 0.28

    for index, slide in enumerate(step_slides, start=1):
      slide.classes["is-active"] = index == self.current_wizard_step

    if self.current_wizard_step != previous_step:
      step_slides[self.current_wizard_step - 1].classes[
        "is-entering-{}".format(direction)
      ] = True

    for index, marker in enumerate(step_markers, start=1):
      marker.classes["is-active"] = index == self.current_wizard_step
      marker.classes["is-complete"] = index < self.current_wizard_step

    self.wizard_back_control.classes["is-hidden"] = self.current_wizard_step == 1
    self.wizard_next_control.classes["is-hidden"] = self.current_wizard_step == 3

  @handle("generate_button", "click")
  def generate_button_click(self, **event_args):
    language = self.language_dropdown.selected_value or "Python"
    project_type = self.project_type_dropdown.selected_value or "Game"
    project = (self.project_prompt.text or "").strip()

    if not project:
      self.generator_status.text = "Type a message or a question for Vrokal AI."
      return

    if len(project) > 4000:
      self.generator_status.text = "Please keep each message under 4,000 characters."
      return

    self.generate_button.enabled = False
    self.generate_button.text = "Starting code…"
    self.generator_status.text = "Starting your first code draft…"
    self.active_generation_task_id = None
    try:
      result = anvil.server.call(
        "start_project_code_generation",
        language,
        project_type,
        project,
        self.conversation_history[-4:],
        (self.code_output.text or "").strip(),
      )

      if not result.get("ok"):
        message = result.get("message", "The request could not be completed. Please try again.")
        self.chat_messages.append({"speaker": "Vrokal AI", "content": message})
        self.chat_history_panel.items = self.chat_messages
        self.generator_status.text = message
        return

      self.active_generation_task_id = result["task_id"]
      self.generation_offset = 0
      self.pending_generation_prompt = project
      self.code_output.text = ""
      self.chat_messages.append({"speaker": "You", "content": project})
      self.chat_history_panel.items = self.chat_messages
      self.project_prompt.text = ""
      self.new_chat_button.enabled = False
      self.generate_button.text = "Writing code…"
      self.generator_status.text = "Vrokal AI is writing your code…"
      self.thinking_timer.interval = 0.7
    finally:
      if self.active_generation_task_id is None:
        self.thinking_timer.interval = 0
        self.generate_button.enabled = True
        self.generate_button.text = "Generate code"

  @handle("wizard_next_button", "click")
  def wizard_next_button_click(self, **event_args):
    self._set_wizard_step(self.current_wizard_step + 1)
    if self.current_wizard_step == 3:
      self.generator_status.text = "Describe your idea and Vrokal AI will write a tailored first version."

  @handle("wizard_back_button", "click")
  def wizard_back_button_click(self, **event_args):
    self._set_wizard_step(self.current_wizard_step - 1)

  @handle("slide_transition_timer", "tick")
  def slide_transition_timer_tick(self, **event_args):
    if self.exiting_wizard_slide is not None:
      self.exiting_wizard_slide.classes["is-exiting-forward"] = False
      self.exiting_wizard_slide.classes["is-exiting-back"] = False
      self.exiting_wizard_slide = None
    self.slide_transition_timer.interval = 0

  @handle("thinking_timer", "tick")
  def thinking_timer_tick(self, **event_args):
    task_id = self.active_generation_task_id
    if not task_id:
      self.thinking_timer.interval = 0
      return

    poll_succeeded = False
    try:
      progress = anvil.server.call(
        "get_project_code_progress",
        task_id,
        self.generation_offset,
      )
      poll_succeeded = True
    finally:
      if not poll_succeeded:
        self._finish_generation("The progress check failed. Please start a new request.")

    new_code = progress.get("code_delta", "")
    if new_code:
      self.code_output.text = (self.code_output.text or "") + new_code
      self.generation_offset = progress.get("next_offset", self.generation_offset + len(new_code))
      self.generator_status.text = "Code is arriving…"

    if not progress.get("ok"):
      message = progress.get("message", "The request could not be completed. Please try again.")
      self.chat_messages.append({"speaker": "Vrokal AI", "content": message})
      self.chat_history_panel.items = self.chat_messages
      self._finish_generation(message)
      return

    if progress.get("done"):
      if progress.get("ok"):
        self.conversation_history.append({
          "role": "user",
          "content": self.pending_generation_prompt or "",
        })
        self.conversation_history = self.conversation_history[-4:]
        self._finish_generation("Code ready. Ask for a change to keep improving it.")

  def _finish_generation(self, status):
    self.active_generation_task_id = None
    self.pending_generation_prompt = None
    self.thinking_timer.interval = 0
    self.generate_button.enabled = True
    self.generate_button.text = "Generate code"
    self.new_chat_button.enabled = True
    self.generator_status.text = status

  @handle("new_chat_button", "click")
  def new_chat_button_click(self, **event_args):
    self.conversation_history = []
    self.active_generation_task_id = None
    self.generation_offset = 0
    self.pending_generation_prompt = None
    self.thinking_timer.interval = 0
    self.generate_button.enabled = True
    self.generate_button.text = "Generate code"
    self.new_chat_button.enabled = True
    self.chat_messages = [{
      "speaker": "Vrokal AI",
      "content": "Describe the app, website, game, or tool you want. Vrokal AI will write the code in the selected language.",
    }]
    self.chat_history_panel.items = self.chat_messages
    self.code_output.text = ""
    self.project_prompt.text = ""
    self._set_wizard_step(1)
    self.generator_status.text = "New chat started. Describe your next idea."

  @handle("save_response_button", "click")
  def save_response_button_click(self, **event_args):
    code = (self.code_output.text or "").strip()
    if len(self.chat_messages) <= 1 and not code:
      self.generator_status.text = "Generate a response before saving."
      return

    sections = []
    for message in self.chat_messages[1:]:
      sections.append("{}:\n{}".format(message["speaker"], message["content"]))
    if code:
      sections.append("GENERATED CODE:\n\n{}".format(code))

    content = "\n\n---\n\n".join(sections)
    download = BlobMedia(
      "text/markdown",
      content.encode("utf-8"),
      name="vrokal_ai_project.md",
    )
    anvil.media.download(download)
    self.generator_status.text = "Downloaded the conversation and code as a Markdown file."
