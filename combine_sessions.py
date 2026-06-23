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

        # Extract root elements
        session_id = data.get("session_id")
        age = data.get("age", "")
        gender = data.get("gender", "")
        study_details = data.get("study_details", "")
        region = data.get("region", "")
        primary_language = data.get("primary_language", "")

        # Extend standard logs
        raw_all.extend(data.get("raw_events", []))
        para_all.extend(data.get("paragraph_events", []))
        interv_all.extend(data.get("intervention_log", []))

        # Core enrichment: Inject demographics line-by-line into the quiz dictionary mappings
        file_quiz_results = data.get("quiz_results", [])
        for q_row in file_quiz_results:
            q_row["age"] = age
            q_row["gender"] = gender
            q_row["study_details"] = study_details
            q_row["region"] = region
            q_row["primary_language"] = primary_language
        
        quiz_all.extend(file_quiz_results)

        print(f"Loaded {f}: session_id={session_id}, "
              f"{len(data.get('raw_events', []))} raw events, "
              f"{len(data.get('paragraph_events', []))} paragraph rows, "
              f"{len(data.get('intervention_log', []))} interventions")

    # Core fix: Expanded fallback array to safely register demographics columns
    fallback_cols = {
        "raw_events": ["session_id", "event_type", "paragraph_id", "timestamp", "scroll_y", "mouse_x", "mouse_y"],
        "paragraph_events": ["session_id", "paragraph_id", "dwell_time_s", "reread_count", "backtrack_count", "cursor_stops", "avg_mouse_speed", "reading_speed_wpm", "struggle_score", "struggle_type"],
        "quiz_results": ["session_id", "paragraph_id", "self_report_difficulty", "quiz_correct", "age", "gender", "study_details", "region", "primary_language"],
        "intervention_log": ["session_id", "paragraph_id", "struggle_type", "arm", "accepted", "follow_up_correct"]
    }

    # Save data frames safely with columns guaranteed and ordered cleanly
    pd.DataFrame(raw_all, columns=fallback_cols["raw_events"] if not raw_all else None).to_csv("raw_events.csv", index=False)
    pd.DataFrame(para_all, columns=fallback_cols["paragraph_events"] if not para_all else None).to_csv("paragraph_events.csv", index=False)
    
    # Process quiz results file saving pipeline 
    if quiz_all:
        # Converts list to a DataFrame and enforces standard order across columns
        quiz_df = pd.DataFrame(quiz_all)
        # Ensure fallback column parameters are completely satisfied 
        for col in fallback_cols["quiz_results"]:
            if col not in quiz_df.columns:
                quiz_df[col] = ""
        quiz_df = quiz_df[fallback_cols["quiz_results"]]
        quiz_df.to_csv("quiz_results.csv", index=False)
    else:
        pd.DataFrame(columns=fallback_cols["quiz_results"]).to_csv("quiz_results.csv", index=False)

    pd.DataFrame(interv_all, columns=fallback_cols["intervention_log"] if not interv_all else None).to_csv("intervention_log.csv", index=False)

    print("\n✅ Combined output successfully written to current directory:")
    print(f"  raw_events.csv        : {len(raw_all)} rows")
    print(f"  paragraph_events.csv  : {len(para_all)} rows")
    print(f"  quiz_results.csv      : {len(quiz_all)} rows")
    print(f"  intervention_log.csv  : {len(interv_all)} rows")

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "sessions"
    main(folder)
