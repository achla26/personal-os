# Evaluation Results - Personal OS Classifier

## 2026-08-19 — Baseline Run (Prompt v1)
- **Score:** 12/20 (60%)
- **Failures:** `link_save`, `expense_petrol`, `link_with_comment`, `hindi_expense`, `read_article`, `note_idea`, `multi_urgent_grocery`, `negative_done`
- **Notes:** Hit sequential speed issues (took 4 mins) and YAML boolean interpretation bugs (`off` became `False`).

## 2026-08-19 — Async Parallel + Retry Run (Prompt v2)
- **Score:** 16/20 (80%)
- **Failures:** `hinglish_date`, `note_idea`, `long_paragraph`, `multi_urgent_grocery`
- **Notes:** Hit Groq 429 Rate Limits due to parallel batching. Fixed by moving to sequential run with 1.5s delay and automatic backoff on 429.

## 2026-08-19 — Strict Rules & formatting (Prompt v3) - CURRENT
- **Score:** 18/20 (90%) ✅
- **Failures:** `date_next_week`, `link_with_comment`
- **Notes:** Great improvements! Handles negative cases like "done/completed" flawlessly, splits complex items correctly, and categorizes notes/ideas with action verbs perfectly.