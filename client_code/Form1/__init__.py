from ._anvil_designer import Form1Template
from anvil import *


class Form1(Form1Template):
  def __init__(self, **properties):
    super().__init__(**properties)
    self.language_dropdown.items = ["Python", "JavaScript", "HTML + CSS", "Java", "C#"]
    self.language_dropdown.selected_value = "Python"
    self.code_output.text = "Your starter code will appear here."

  @handle("generate_button", "click")
  def generate_button_click(self, **event_args):
    language = self.language_dropdown.selected_value or "Python"
    project = " ".join((self.project_prompt.text or "").split())[:240]

    if not project:
      self.generator_status.text = "Describe your app or website idea to generate a starter."
      return

    code = self._make_starter(language, project)
    self.code_output.text = code
    self.generator_status.text = "Starter template generated for {}. Copy it and build on the TODOs.".format(language)

  def _make_starter(self, language, project):
    if language == "Python":
      return "\n".join([
        "# Vrokal Python starter",
        "# Project idea: " + project,
        "",
        "def main():",
        '    print("Your Vrokal project is ready.")',
        "    # TODO: implement the main workflow for your project.",
        "",
        'if __name__ == "__main__":',
        "    main()",
      ])

    if language == "JavaScript":
      return "\n".join([
        "// Vrokal JavaScript starter",
        "// Project idea: " + project,
        "",
        'const appName = "Vrokal starter";',
        "",
        "function main() {",
        '  console.log(`${appName} is ready.`);',
        "  // TODO: implement the main workflow for your project.",
        "}",
        "",
        "main();",
      ])

    if language == "HTML + CSS":
      safe_project = project.replace("--", "—")
      return "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        "  <title>Vrokal starter</title>",
        "  <style>",
        "    body { font-family: system-ui, sans-serif; margin: 0; padding: 3rem; background: #f4f8fa; color: #172b36; }",
        "    main { max-width: 720px; margin: auto; padding: 2rem; border-radius: 1rem; background: white; }",
        "    a { color: #176b87; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <main>",
        "    <!-- Project idea: " + safe_project + " -->",
        "    <p>Vrokal project starter</p>",
        "    <h1>Bring your idea to life</h1>",
        "    <p>Replace this text with the core experience for your website.</p>",
        '    <a href="#start">Get started</a>',
        "  </main>",
        "</body>",
        "</html>",
      ])

    if language == "Java":
      return "\n".join([
        "// Vrokal Java starter",
        "// Project idea: " + project,
        "",
        "class Main {",
        "  public static void main(String[] args) {",
        '    System.out.println("Your Vrokal project is ready.");',
        "    // TODO: implement the main workflow for your project.",
        "  }",
        "}",
      ])

    safe_project = project.replace("*/", "* /")
    return "\n".join([
      "// Vrokal C# starter",
      "// Project idea: " + safe_project,
      "",
      "using System;",
      "",
      "class Program {",
      "  static void Main() {",
      '    Console.WriteLine("Your Vrokal project is ready.");',
      "    // TODO: implement the main workflow for your project.",
      "  }",
      "}",
    ])
