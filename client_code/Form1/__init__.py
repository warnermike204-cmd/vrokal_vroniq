from ._anvil_designer import Form1Template
from anvil import *


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
    self.project_type_dropdown.selected_value = "Website"
    self.code_output.text = "Your starter code will appear here."

  @handle("generate_button", "click")
  def generate_button_click(self, **event_args):
    language = self.language_dropdown.selected_value or "Python"
    project_type = self.project_type_dropdown.selected_value or "Website"
    project = " ".join((self.project_prompt.text or "").split())[:240]

    if not project:
      self.generator_status.text = "Describe your app or website idea to generate a starter."
      return

    code = self._make_starter(language, project_type, project)
    self.code_output.text = code
    self.generator_status.text = "{} starter created for your {} idea. Add your project features in the TODOs.".format(language, project_type.lower())

  def _make_starter(self, language, project_type, project):
    if language == "HTML + CSS":
      safe_project = project.replace("--", "—")
      safe_type = project_type.replace("--", "—")
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
        "    <!-- Project type: " + safe_type + " -->",
        "    <!-- Project idea: " + safe_project + " -->",
        "    <p>Vrokal project starter</p>",
        "    <h1>Bring your idea to life</h1>",
        "    <p>Replace this text with the core experience for your website.</p>",
        '    <a href="#start">Get started</a>',
        "  </main>",
        "</body>",
        "</html>",
      ])

    comment = {
      "Python": "#", "Ruby": "#", "Bash": "#", "SQL": "--",
    }.get(language, "//")
    if language == "PHP":
      safe_project = project.replace("?>", "? >")
      header = [
        "<?php",
        "// Vrokal PHP starter",
        "// Project type: " + project_type,
        "// Project idea: " + safe_project,
        "",
      ]
    elif language == "Bash":
      header = [
        "#!/usr/bin/env bash",
        "# Vrokal Bash starter",
        "# Project type: " + project_type,
        "# Project idea: " + project,
        "",
      ]
    else:
      header = [
        comment + " Vrokal " + language + " starter",
        comment + " Project type: " + project_type,
        comment + " Project idea: " + project,
        "",
      ]

    if language == "Python":
      body = [
        "def main():",
        '    print("Your Vrokal project is ready.")',
        "    # TODO: implement the main workflow for your project.",
        "",
        'if __name__ == "__main__":',
        "    main()",
      ]

    elif language == "JavaScript":
      body = [
        'const appName = "Vrokal starter";',
        "",
        "function main() {",
        '  console.log(`${appName} is ready.`);',
        "  // TODO: implement the main workflow for your project.",
        "}",
        "",
        "main();",
      ]

    elif language == "TypeScript":
      body = [
        'const appName: string = "Vrokal starter";',
        "",
        "function main(): void {",
        '  console.log(`${appName} is ready.`);',
        "  // TODO: implement the main workflow for your project.",
        "}",
        "",
        "main();",
      ]

    elif language == "Java":
      body = [
        "class Main {",
        "  public static void main(String[] args) {",
        '    System.out.println("Your Vrokal project is ready.");',
        "    // TODO: implement the main workflow for your project.",
        "  }",
        "}",
      ]

    elif language == "C#":
      body = [
        "using System;",
        "",
        "class Program {",
        "  static void Main() {",
        '    Console.WriteLine("Your Vrokal project is ready.");',
        "    // TODO: implement the main workflow for your project.",
        "  }",
        "}",
      ]

    elif language == "C++":
      body = [
        "#include <iostream>",
        "",
        "int main() {",
        '  std::cout << "Your Vrokal project is ready." << std::endl;',
        "  // TODO: implement the main workflow for your project.",
        "  return 0;",
        "}",
      ]

    elif language == "Go":
      body = [
        "package main",
        "",
        'import "fmt"',
        "",
        "func main() {",
        '  fmt.Println("Your Vrokal project is ready.")',
        "  // TODO: implement the main workflow for your project.",
        "}",
      ]

    elif language == "PHP":
      body = [
        "function main(): void {",
        '    echo "Your Vrokal project is ready." . PHP_EOL;',
        "    // TODO: implement the main workflow for your project.",
        "}",
        "",
        "main();",
      ]

    elif language == "Ruby":
      body = [
        "def main",
        '  puts "Your Vrokal project is ready."',
        "  # TODO: implement the main workflow for your project.",
        "end",
        "",
        "main",
      ]

    elif language == "SQL":
      body = [
        "CREATE TABLE project_items (",
        "  id INTEGER PRIMARY KEY,",
        "  name TEXT NOT NULL,",
        "  created_at TIMESTAMP",
        ");",
        "",
        "-- TODO: adapt the table fields to your project.",
        "SELECT id, name, created_at FROM project_items;",
      ]

    elif language == "Bash":
      body = [
        "set -euo pipefail",
        "",
        "main() {",
        '  echo "Your Vrokal project is ready."',
        "  # TODO: implement the main workflow for your project.",
        "}",
        "",
        'main "$@"',
      ]

    elif language == "Rust":
      body = [
        "fn main() {",
        '    println!("Your Vrokal project is ready.");',
        "    // TODO: implement the main workflow for your project.",
        "}",
      ]

    elif language == "Kotlin":
      body = [
        "fun main() {",
        '    println("Your Vrokal project is ready.")',
        "    // TODO: implement the main workflow for your project.",
        "}",
      ]

    else:  # Swift
      body = [
        'print("Your Vrokal project is ready.")',
        "// TODO: implement the main workflow for your project.",
      ]

    return "\n".join(header + body)
