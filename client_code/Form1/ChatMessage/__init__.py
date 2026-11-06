from ._anvil_designer import ChatMessageTemplate


class ChatMessage(ChatMessageTemplate):
  def __init__(self, **properties):
    super().__init__(**properties)
