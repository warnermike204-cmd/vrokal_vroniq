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
    self.chat_messages = [{
      "speaker": "Vrokal AI",
      "content": "Describe the app, website, game, or tool you want. Vrokal AI will write the code in the selected language.",
    }]
    self.chat_history_panel.items = self.chat_messages
    self.generator_status.text = "Describe what you want to build."

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
    self.generate_button.text = "Vrokal AI is thinking…"
    self.generator_status.text = "Vrokal AI is thinking…"
    self.thinking_timer.interval = 5
    try:
      result = anvil.server.call(
        "generate_project_code",
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

      self.code_output.text = result["code"]
      self.conversation_history.append({"role": "user", "content": project})
      self.conversation_history = self.conversation_history[-4:]
      self.chat_messages.append({"speaker": "You", "content": project})
      self.chat_history_panel.items = self.chat_messages
      self.project_prompt.text = ""
      if result["code"]:
        self.generator_status.text = "Code generated."
      else:
        self.generator_status.text = "No code was returned. Try describing the project more simply."
    finally:
      self.thinking_timer.interval = 0
      self.generate_button.enabled = True
      self.generate_button.text = "Generate code"

  @handle("thinking_timer", "tick")
  def thinking_timer_tick(self, **event_args):
    self.thinking_timer.interval = 0
    if not self.generate_button.enabled:
      self.generate_button.text = "Still working…"
      self.generator_status.text = "Still generating. Your code will appear here when it is ready."

  @handle("new_chat_button", "click")
  def new_chat_button_click(self, **event_args):
    self.conversation_history = []
    self.chat_messages = [{
      "speaker": "Vrokal AI",
      "content": "Describe the app, website, game, or tool you want. Vrokal AI will write the code in the selected language.",
    }]
    self.chat_history_panel.items = self.chat_messages
    self.code_output.text = ""
    self.project_prompt.text = ""
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
