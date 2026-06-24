import json
import os
from datetime import datetime, timezone
from config import LOG_FILE


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
