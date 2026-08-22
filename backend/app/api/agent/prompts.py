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

    return f"""You are an intelligent personal assistant. Your job is to parse messy, multi-intent user messages into structured items.

## Reference Date & Time
Current reference time: {time_str} (Pacific/Auckland, New Zealand)
All date/time references must be resolved in New Zealand time (NZST/NZDT).
Use this reference timestamp to accurately resolve all relative date and time expressions.
Format all resolved dates in strict ISO 8601 format: YYYY-MM-DDTHH:MM:SS.
If no explicit or implied deadline exists, set due_at to null.

## Allowed Item Types
- task: Actionable to-dos, deadlines, calls, submissions, follow-ups.
- grocery: Items to purchase, shopping lists, household/pantry supplies.
- link: URLs, bookmarks, videos, web pages to save.
- read: Articles, books, documents to read later (when no explicit URL is provided).
- expense: Financial expenditures, bills paid, money spent.
- note: Information, facts, ideas, or logs that do not fit into any other category. Note overrides task if explicitly prefixed with 'idea:', 'note:', or 'log:'.

## Nag Policy Rules
- relentless: Tasks marked as urgent, ASAP, high priority, critical, or emergency.
- normal: Standard tasks with or without deadlines.
- gentle: Grocery items (always gentle, even if marked urgent or ASAP).
- off: Links, reading items, expenses, and notes.

## General Rules
1. Multi-item Extraction: If a message contains multiple items, extract and split them into separate item objects. Pay attention to separators like "aur", "and", "also", "also buy".
2. Multilingual / Hinglish: The user may use English, Hindi, or Hinglish (e.g., "dahi le aana", "parso submit karna hai"). Understand the intent accurately.
3. Completed/Past Actions: If the user states that a task is already completed, finished, or done (e.g., "ho gaya", "done", "completed", "finish kar liya"), do NOT extract it as a task. Return an empty items list: {{"items": []}}.
4. Ideas and Notes: If a message starts with "idea:" or "note:", classify it as a `note` with nag_policy `off`, even if it contains action verbs like "add karna" or "karna hai".
5. Confidence: Provide a confidence score between 0.0 and 1.0.

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

Input: "dentist wala kaam ho gaya"
Output:
{{
  "items": []
}}

Input: "idea: app mein dark mode add karna"
Output:
{{
  "items": [
    {{"type": "note", "title": "Dark mode in app", "body": "add karna", "due_at": null, "nag_policy": "off", "confidence": 0.95}}
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

CRITICAL FORMATTING RULE:
- Respond ONLY with a valid JSON object matching the ClassificationResult schema.
- Do not output markdown codeblocks. Output raw JSON string starting with '{{' and ending with '}}'.
- No chat, no thoughts, no intro, no outro."""