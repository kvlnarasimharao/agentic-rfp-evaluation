# Demonstration

Public application: https://rfp-evaluation-kvlnarasimharao.streamlit.app/

## Successful completed run

1. Open the Sample run tab and keep Live Gemini evaluation selected.
2. Review the four-supplier leaderboard. Apex Systems ranks first with absolute score 85.0 and PPI 94.4445.
3. Expand any supplier to see criterion scores, justification, supporting evidence, benchmark, gap, relative percentage, and weight.
4. Use Download complete result as JSON to export the full run. The same saved result is in [data/live_run.json](../data/live_run.json).

![Completed four-supplier leaderboard](screenshots/leaderboard.jpg)

## Validation example

1. In Sample run, choose Validation example.
2. The example contains a Security and Compliance score below zero for BrightPath Tech. Validation clips it to zero before scoring.
3. Run details displays the warning: BrightPath Tech: criterion 4 score clipped to range.
4. The validation example ranks NexaWorks first. Its complete result is in [data/sample_run.json](../data/sample_run.json).

The completed Gemini run also shows a malformed risks-field warning for BrightPath Tech. The response validator replaced that field with an empty list while retaining valid criterion scores.

## Criteria

The Criteria tab shows the active SQLite rubric and weights. The five active weights total 100%.

![Active evaluation criteria](screenshots/criteria.jpg)

## Verification

The public application responded successfully, and its hosted Sample run page displayed the completed leaderboard, scorecards, warning, and JSON download. Streamlit's application test harness loaded all four tabs without exceptions and displayed the validation warning after switching examples. All four automated tests pass with the test command in README.md.
