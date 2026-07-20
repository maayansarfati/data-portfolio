import pandas as pd

from analysis import analyze_drinks_break_momentum


def test_basic_analysis_counts_matches():
    momentum = pd.DataFrame(
        {
            "match_id": [1] * 16,
            "minute": list(range(1, 17)),
            "value": [0, 0, 0, 0, 0, 0, 0, 0, 100, 100, 100, 100, 100, 100, 100, 100],
        }
    )

    events = pd.DataFrame(
        {
            "match_id": [1],
            "minute": [8],
            "event_type": ["drinks_break"],
        }
    )

    result = analyze_drinks_break_momentum(momentum, events, threshold=30, n_simulations=10)
    assert len(result) == 1
    assert result.iloc[0]["match_id"] == 1
    assert result.iloc[0]["break_change_minutes"] == 1
