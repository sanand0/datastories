"""Extract questions from ChatGPT conversations.json into questions.txt."""

import json
from datetime import datetime

with open("conversations.json", "r") as file:
  data = json.load(file)


def get_question(conversation, start=200, end=100):
  # Get the first user message from the conversation
  question = conversation["title"] + ". "
  for mapping in conversation["mapping"].values():
    message = mapping["message"]
    if not message:
      continue
    if message.get("author", {}).get("role") == "user":
      for part in message["content"].get("parts", []):
        if isinstance(part, str):
          question += " " + part
        elif isinstance(part, dict) and "text" in part:
          question += " " + part["text"]
      # Stop after the first user message
      if len(question) > start + end:
        break
  # If the size is more than start + end, truncate it
  if len(question) > start + end:
    question = question[:start] + "..." + question[-end:]
  return question


with open("questions.txt", "w") as file:
  for conversation in data:
    date = datetime.fromtimestamp(conversation["create_time"]).strftime("%Y-%m-%d")
    question = get_question(conversation)
    file.write(
      date + "\t" + question.replace("\n", " ").replace("\r", " ").strip() + "\n"
    )
