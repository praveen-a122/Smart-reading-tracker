"""
Validation analysis on synthetic SRT data.

RQ1: Does struggle_score correlate with self-report difficulty and quiz performance?
RQ2: Which intervention arm works best, and does it depend on struggle_type
     (the novelty / intervention-matching contribution)?

Run after synthetic_data_generator.py:
  python analysis_validation.py
"""

import pandas as pd
from scipy import stats

para_df = pd.read_csv("paragraph_events.csv")
quiz_df = pd.read_csv("quiz_results.csv")
interv_df = pd.read_csv("intervention_log.csv")

df = para_df.merge(quiz_df, on=["session_id", "paragraph_id"])

print("=" * 60)
print("RQ1: Struggle score vs self-report difficulty / quiz score")
print("=" * 60)

corr_self, p_self = stats.spearmanr(df.struggle_score, df.self_report_difficulty)
print(f"struggle_score vs self_report_difficulty : r={corr_self:.3f}, p={p_self:.4g}")

corr_quiz, p_quiz = stats.pointbiserialr(df.quiz_correct, df.struggle_score)
print(f"struggle_score vs quiz_correct (higher struggle -> wrong) : "
      f"r={corr_quiz:.3f}, p={p_quiz:.4g}")

# Also check: does struggle_score separate the TRUE easy vs hard paragraphs?
group_easy = df[df.self_report_difficulty <= 2].struggle_score
group_hard = df[df.self_report_difficulty > 2].struggle_score
t_stat, p_t = stats.ttest_ind(group_hard, group_easy)
print(f"\nMean struggle_score | easy paragraphs : {group_easy.mean():.3f}")
print(f"Mean struggle_score | hard paragraphs : {group_hard.mean():.3f}")
print(f"t-test hard vs easy: t={t_stat:.2f}, p={p_t:.4g}")

print()
print("=" * 60)
print("RQ2: Intervention arm effectiveness, by struggle type (NOVELTY)")
print("=" * 60)

# overall accuracy by arm
overall = interv_df.groupby("arm")["follow_up_correct"].mean().sort_values(ascending=False)
print("\nFollow-up accuracy by arm (overall):")
print(overall.round(3))

# accuracy by arm WITHIN each struggle type -- this is the key novelty table
print("\nFollow-up accuracy by arm, split by struggle_type:")
pivot = interv_df.pivot_table(
    index="struggle_type", columns="arm", values="follow_up_correct", aggfunc="mean"
)
print(pivot.round(3))

print("\nBest-performing arm per struggle type:")
print(pivot.idxmax(axis=1))

# acceptance rate by arm
print("\nAcceptance rate by arm:")
print(interv_df.groupby("arm")["accepted"].mean().round(3))
