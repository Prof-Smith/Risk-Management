# Experienced Cases Upgrade

Replace `experience/live_case.py` and add `components/case_experience.py`.

This changes each case from a dashboard into a five-room experience:

1. Briefing
2. Evidence Room
3. Decision Desk
4. Shock Room
5. Board Defense

The workflow preserves the participant's initial action and confidence, introduces a controllable shock, calculates a decision boundary, and requires a defended final recommendation.

The current charts use deterministic synthetic data and the scaffold's illustrative risk engine. Replace those calculations with the validated course models and actual case evidence before instructional use.
