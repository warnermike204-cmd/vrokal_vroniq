from ._anvil_designer import Form1Template
from anvil import *
import anvil.server


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
      "content": "Hi! Ask me a question, talk through an idea, or tell me what code you want to build. For a game, you can describe the controls, goal, enemies, and scoring.",
    }]
    self.chat_history_panel.items = self.chat_messages
    self.generator_status.text = "Ask a question or describe something you want to make."

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
    try:
      result = anvil.server.call(
        "generate_project_code",
        language,
        project_type,
        project,
        self.conversation_history[-8:],
        (self.code_output.text or "").strip(),
      )

      if not result.get("ok"):
        message = result.get("message", "The request could not be completed. Please try again.")
        self.chat_messages.append({"speaker": "Vrokal AI", "content": message})
        self.chat_history_panel.items = self.chat_messages
        self.generator_status.text = message
        return

      assistant_message = result["assistant_message"]
      if result["code"]:
        self.code_output.text = result["code"]
      self.conversation_history.extend([
        {"role": "user", "content": project},
        {"role": "assistant", "content": assistant_message},
      ])
      self.conversation_history = self.conversation_history[-8:]
      self.chat_messages.extend([
        {"speaker": "You", "content": project},
        {"speaker": "Vrokal AI", "content": assistant_message},
      ])
      self.chat_history_panel.items = self.chat_messages
      self.project_prompt.text = ""
      if result["code"]:
        self.generator_status.text = "Your code is ready. Ask Vrokal AI a question or request another change."
      else:
        self.generator_status.text = "Vrokal AI replied. You can keep chatting or ask it to write code."
    finally:
      self.generate_button.enabled = True
      self.generate_button.text = "Ask Vrokal AI"

  @handle("new_chat_button", "click")
  def new_chat_button_click(self, **event_args):
    self.conversation_history = []
    self.chat_messages = [{
      "speaker": "Vrokal AI",
      "content": "Hi! Ask me a question, talk through an idea, or tell me what code you want to build. For a game, you can describe the controls, goal, enemies, and scoring.",
    }]
    self.chat_history_panel.items = self.chat_messages
    self.code_output.text = ""
    self.project_prompt.text = ""
    self.generator_status.text = "New chat started. Describe your next idea."
