import json
import os
from datetime import datetime, timezone
from config import LOG_FILE

SESSION_SUMMARY_FILE = "logs/session_summary.jsonl"


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log.

    Writes a JSON object to logs/audit.jsonl with fields:
      - timestamp: ISO 8601 UTC datetime
      - tier: safety tier (safe, caution, refuse)
      - question: truncated to 300 chars
      - response_preview: first 200 chars of response
      - classification_reason: reason for tier assignment
      - response_length: full response length before truncation

    Prints a one-line summary to terminal for real-time visibility.
    """

    # Ensure logs/ directory exists
    logs_dir = os.path.dirname(LOG_FILE)
    if logs_dir:
        os.makedirs(logs_dir, exist_ok=True)

    # Create log entry with all required and additional fields
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    question_truncated = question[:300]
    response_preview = response[:200]
    response_length = len(response)

    log_entry = {
        "timestamp": timestamp,
        "tier": tier,
        "question": question_truncated,
        "response_preview": response_preview,
        "response_length": response_length,
    }

    try:
        # Append to audit log as a single JSON line
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Print one-line summary to terminal
        # Truncate question to 60-80 chars for readability
        question_preview = question[:70].replace("\n", " ")
        if len(question) > 70:
            question_preview += "..."
        print(
            f"[{timestamp}] {tier.upper()}: \"{question_preview}\" → logged ({response_length} chars)"
        )

    except Exception as e:
        # Log errors but don't crash the app
        print(f"Warning: Failed to log interaction: {e}")

    # After every 5 interactions, create a session summary
    _maybe_create_session_summary()


def _maybe_create_session_summary() -> None:
    """
    If the audit log now contains a multiple of 5 entries, create a session summary.

    Session summary includes:
    - timestamp of summary creation
    - total_interactions: total count of logged interactions
    - tier_distribution: count of safe/caution/refuse
    - recent_questions: last 3 questions asked
    """
    try:
        # Count entries in audit log
        if not os.path.exists(LOG_FILE):
            return

        with open(LOG_FILE, "r") as f:
            entries = [json.loads(line) for line in f if line.strip()]

        total_interactions = len(entries)

        # Only create summary if multiple of 5
        if total_interactions % 5 != 0:
            return

        # Count tiers
        tier_counts = {"safe": 0, "caution": 0, "refuse": 0}
        for entry in entries:
            tier = entry.get("tier", "unknown")
            if tier in tier_counts:
                tier_counts[tier] += 1

        # Get 3 most recent questions
        recent_questions = [
            entry.get("question", "")[:80] for entry in entries[-3:]
        ]
        recent_questions.reverse()  # Most recent first

        # Create summary entry
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "interaction_count": total_interactions,
            "tier_distribution": tier_counts,
            "recent_questions": recent_questions,
        }

        # Append to session summary file
        with open(SESSION_SUMMARY_FILE, "a") as f:
            f.write(json.dumps(summary) + "\n")

        # Print summary to terminal
        print(
            f"\n📊 SESSION SUMMARY (Interactions: {total_interactions}) "
            f"Safe: {tier_counts['safe']} | Caution: {tier_counts['caution']} | "
            f"Refuse: {tier_counts['refuse']}\n"
        )

    except Exception as e:
        # Silently fail on summary creation
        pass
