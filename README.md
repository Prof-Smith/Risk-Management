# Blackridge Comic Risk Lab v3

Changes:
- Replaces the jagged histogram with smoothed density curves, direct VaR/CVaR callouts, a focused x-axis, and a restrained tail highlight.
- Adds three expression variants for each fictional cast member: neutral, concerned, and decisive.
- Uses scene-specific expressions during synthetic exchanges.
- Reduces jumpiness by putting Monte Carlo and shock controls inside forms, caching simulation outputs, fixing chart sizes, preserving chart UI state, and disabling Plotly toolbars.
- Keeps the disclaimer gate, complete cast introduction, and no-decision ending.

## Portrait correction
The cast introduction now uses square, face-centered portrait crops generated from the expression sheet. The previous narrow source panels were being clipped by a global image-height rule, which produced neck and torso crops. The image rule now preserves each square portrait at a consistent aspect ratio in both the introduction and dialogue panels.
