from datetime import datetime
from zoneinfo import ZoneInfo


def get_classification_prompt(text: str, current_time: datetime) -> str:
    """
        Takes raw user input and a reference timestamp,
        returns a formatted prompt for LLM classification.
    """ 
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=ZoneInfo("Pacific/Auckland"))

    time_str = current_time.strftime("%Y-%m-%d %H:%M %Z (%A)")
    # %Z = "NZST" ya "NZDT" — LLM ko timezone dikhega

    return f"""You are an intelligent personal assistant...

## Reference Date & Time
Current reference time: {time_str} (Pacific/Auckland, New Zealand)
All date/time references must be resolved in New Zealand time (NZST/NZDT).
Use this reference timestamp to accurately resolve all relative date and time expressions.(e.g., "tomorrow", "next Tuesday", "in 2 hours", "kal", "parso"). 
Format all resolved dates in strict ISO 8601 format: YYYY-MM-DDTHH:MM:SS. 
If no explicit or implied deadline exists, set due_at to null.

## Allowed Item Types
- task: Actionable to-dos, deadlines, calls, submissions, follow-ups.
- grocery: Items to purchase, shopping lists, household/pantry supplies.
- link: URLs, bookmarks, videos, web pages to save.
- read: Articles, books, documents to read later (when no explicit URL is provided).
- expense: Financial expenditures, bills paid, money spent.
- note: Information, facts, ideas, or logs that do not fit into any other category.

## Nag Policy Rules
- relentless: Tasks marked as urgent, ASAP, high priority, critical, or emergency.
- normal: Standard tasks with or without deadlines.
- gentle: Grocery items.
- off: Links, reading items, expenses, and notes.

## General Rules
1. Multi-item Extraction: If a message contains multiple items, extract and split them into separate item objects. Never combine distinct items into a single entry.
2. Multilingual / Hinglish: The user may use English, Hindi, or Hinglish (e.g., "dahi le aana", "parso submit karna hai"). Understand the intent accurately.
3. Confidence: Provide a confidence score between 0.0 and 1.0 reflecting classification certainty.

## Examples

Input: "call dentist tuesday 4pm"
Output:
{{
  "items": [
    {{
      "type": "task",
      "title": "Call dentist",
      "body": null,
      "due_at": "2025-08-19T16:00:00",
      "nag_policy": "normal",
      "confidence": 0.95
    }}
  ]
}}

Input: "milk, bread aur dahi le aana"
Output:
{{
  "items": [
    {{"type": "grocery", "title": "Milk", "body": null, "due_at": null, "nag_policy": "gentle", "confidence": 0.95}},
    {{"type": "grocery", "title": "Bread", "body": null, "due_at": null, "nag_policy": "gentle", "confidence": 0.95}},
    {{"type": "grocery", "title": "Dahi", "body": null, "due_at": null, "nag_policy": "gentle", "confidence": 0.95}}
  ]
}}

Input: "https://youtu.be/xyz save this for later"
Output:
{{
  "items": [
    {{"type": "link", "title": "https://youtu.be/xyz", "body": "save this for later", "due_at": null, "nag_policy": "off", "confidence": 0.98}}
  ]
}}

Input: "urgent: submit visa form tomorrow"
Output:
{{
  "items": [
    {{"type": "task", "title": "Submit visa form", "body": null, "due_at": "2025-08-16T00:00:00", "nag_policy": "relentless", "confidence": 0.95}}
  ]
}}

Input: "spent 40 on petrol"
Output:
{{
  "items": [
    {{"type": "expense", "title": "Petrol", "body": "40", "due_at": null, "nag_policy": "off", "confidence": 0.90}}
  ]
}}

## User Message to Classify:
{text}

Respond ONLY with a valid JSON object matching the ClassificationResult schema. Do not include markdown codeblocks, thinking process, or explanatory text."""