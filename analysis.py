import random
from typing import List, Tuple

import numpy as np
import pandas as pd


def analyze_drinks_break_momentum(
    momentum: pd.DataFrame,
    events: pd.DataFrame,
    threshold: float = 30.0,
    n_simulations: int = 1000,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Analyze whether drinks breaks coincide with momentum shifts.

    Parameters
    ----------
    momentum : pd.DataFrame
        Must include columns match_id, minute, value.
    events : pd.DataFrame
        Must include columns match_id, minute, event_type.
    threshold : float
        Minimum absolute delta needed to mark a momentum change.
    n_simulations : int
        Number of random simulations for the baseline comparison.
    random_seed : int
        Seed for the random baseline simulations.
    """
    required_momentum = {"match_id", "minute", "value"}
    required_events = {"match_id", "minute", "event_type"}

    missing_momentum = required_momentum.difference(momentum.columns)
    missing_events = required_events.difference(events.columns)
    if missing_momentum:
        raise ValueError(f"momentum is missing columns: {sorted(missing_momentum)}")
    if missing_events:
        raise ValueError(f"events is missing columns: {sorted(missing_events)}")

    momentum = momentum.copy()
    events = events.copy()

    momentum["minute"] = pd.to_numeric(momentum["minute"], errors="coerce")
    momentum["value"] = pd.to_numeric(momentum["value"], errors="coerce")
    events["minute"] = pd.to_numeric(events["minute"], errors="coerce")

    momentum = momentum.dropna(subset=["match_id", "minute", "value"]).copy()
    events = events.dropna(subset=["match_id", "minute", "event_type"]).copy()

    candidate_minutes = list(range(6, 41)) + list(range(51, 86))
    match_ids = sorted(momentum["match_id"].dropna().astype(int).unique())

    rows: List[dict] = []
    rng = random.Random(random_seed)

    for match_id in match_ids:
        match_momentum = momentum[momentum["match_id"] == match_id].sort_values("minute")
        match_events = events[events["match_id"] == match_id]

        match_break_minutes = set(
            match_events.loc[
                match_events["event_type"].astype(str).str.lower() == "drinks_break",
                "minute",
            ].astype(int).tolist()
        )

        change_minutes: List[int] = []
        for minute in candidate_minutes:
            before_window = match_momentum[match_momentum["minute"].between(minute - 5, minute - 1)]
            after_window = match_momentum[match_momentum["minute"].between(minute + 1, minute + 5)]

            if len(before_window) < 5 or len(after_window) < 5:
                continue

            before_mean = before_window["value"].mean()
            after_mean = after_window["value"].mean()
            delta = abs(after_mean - before_mean)

            if delta >= threshold:
                change_minutes.append(int(minute))

        break_change_count = sum(1 for minute in change_minutes if minute in match_break_minutes)

        if not change_minutes:
            baseline_counts = [0] * n_simulations
        else:
            baseline_counts = []
            for _ in range(n_simulations):
                sampled_minutes = [
                    rng.choice(candidate_minutes)
                    for _ in range(len(change_minutes))
                ]
                baseline_counts.append(
                    sum(1 for minute in sampled_minutes if minute in match_break_minutes)
                )

        random_mean = float(np.mean(baseline_counts)) if baseline_counts else 0.0
        random_std = float(np.std(baseline_counts)) if baseline_counts else 0.0
        p_value = (
            (sum(1 for count in baseline_counts if count >= break_change_count) + 1)
            / (len(baseline_counts) + 1)
            if baseline_counts
            else 1.0
        )

        rows.append(
            {
                "match_id": int(match_id),
                "total_change_minutes": len(change_minutes),
                "break_change_minutes": break_change_count,
                "break_change_rate": break_change_count / len(change_minutes) if change_minutes else np.nan,
                "change_minutes": change_minutes,
                "break_minutes": sorted(match_break_minutes),
                "random_mean_breaks": random_mean,
                "random_std_breaks": random_std,
                "p_value": p_value,
            }
        )

    summary = pd.DataFrame(rows).sort_values("match_id").reset_index(drop=True)
    return summary


if __name__ == "__main__":
    momentum = pd.read_csv("world_cup_momentum_dataset.csv")
    events = pd.read_csv("world_cup_match_events.csv")

    summary = analyze_drinks_break_momentum(momentum, events, threshold=30.0, n_simulations=500)
    summary.to_csv("drinks_break_momentum_summary.csv", index=False)
    print(summary.head())
    print(f"\nRows analyzed: {len(summary)}")
    print(f"Average break-change rate: {summary['break_change_rate'].mean():.3f}")
    print(f"Fraction of matches with at least one break-change: {(summary['break_change_minutes'] > 0).mean():.3f}")
