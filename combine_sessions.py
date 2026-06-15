"""
Combine multiple session JSON files (downloaded from reading_app_v2.html)
into the same 4 CSV files produced by synthetic_data_generator.py:

  raw_events.csv
  paragraph_events.csv
  quiz_results.csv
  intervention_log.csv

Usage:
  1. Put all downloaded *.json session files into a folder, e.g. "sessions/"
  2. Run: python combine_sessions.py sessions/
  3. Output CSVs are written to the current directory.

These CSVs can be fed directly into analysis_validation.py (adjust the
script to read real data instead of synthetic data — the column names match).
"""

import sys
import json
import glob
import os
import pandas as pd

def main(folder):
    # Core fix: Check if the folder actually exists before scanning
    if not os.path.exists(folder):
        print(f"❌ Error: The folder '{folder}' does not exist.")
        print("Please create it and drop your participant JSON files inside.")
        return

    files = sorted(glob.glob(folder.rstrip("/") + "/*.json"))
    if not files:
        print(f"❌ No .json files found in folder: '{folder}'")
        return

    raw_all, para_all, quiz_all, interv_all = [], [], [], []

    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except json.JSONDecodeError:
                print(f"⚠️ Warning: Skipped corrupted file {f}")
                continue

        raw_all.extend(data.get("raw_events", []))
        para_all.extend(data.get("paragraph_events", []))
        quiz_all.extend(data.get("quiz_results", []))
        interv_all.extend(data.get("intervention_log", []))

        print(f"Loaded {f}: session_id={data.get('session_id')}, "
              f"{len(data.get('raw_events', []))} raw events, "
              f"{len(data.get('paragraph_events', []))} paragraph rows, "
              f"{len(data.get('intervention_log', []))} interventions")

    # Core fix: Define exact expected fallback columns to prevent downstream math crashes
    fallback_cols = {
        "raw_events": ["session_id", "event_type", "paragraph_id", "timestamp", "scroll_y", "mouse_x", "mouse_y"],
        "paragraph_events": ["session_id", "paragraph_id", "dwell_time_s", "reread_count", "backtrack_count", "cursor_stops", "avg_mouse_speed", "reading_speed_wpm", "struggle_score", "struggle_type"],
        "quiz_results": ["session_id", "paragraph_id", "self_report_difficulty", "quiz_correct"],
        "intervention_log": ["session_id", "paragraph_id", "struggle_type", "arm", "accepted", "follow_up_correct"]
    }

    # Save data frames safely with columns guaranteed
    pd.DataFrame(raw_all, columns=fallback_cols["raw_events"] if not raw_all else None).to_csv("raw_events.csv", index=False)
    pd.DataFrame(para_all, columns=fallback_cols["paragraph_events"] if not para_all else None).to_csv("paragraph_events.csv", index=False)
    pd.DataFrame(quiz_all, columns=fallback_cols["quiz_results"] if not quiz_all else None).to_csv("quiz_results.csv", index=False)
    pd.DataFrame(interv_all, columns=fallback_cols["intervention_log"] if not interv_all else None).to_csv("intervention_log.csv", index=False)

    print("\n✅ Combined output successfully written to current directory:")
    print(f"  raw_events.csv        : {len(raw_all)} rows")
    print(f"  paragraph_events.csv  : {len(para_all)} rows")
    print(f"  quiz_results.csv      : {len(quiz_all)} rows")
    print(f"  intervention_log.csv  : {len(interv_all)} rows")

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "sessions"
    main(folder)
