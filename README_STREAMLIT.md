# Risk Management Decision Lab

This scaffold adds a Streamlit experiential layer beside the existing MkDocs course.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Integration

Copy the scaffold contents into the root of the existing `Risk-Management` repository. Keep the current `docs/`, `data/`, `mkdocs.yml`, and existing GitHub workflows. Review file conflicts before copying.

## Architecture

- `experience/`: the 50-minute facilitated journey
- `components/`: reusable interface elements
- `services/`: case loading, session, simulation, and reversal logic
- `cases/`: data-driven case definitions
- `tests/`: starter model and loader tests

The included quantitative model is explicitly illustrative. Replace it with the validated course model and actual case assumptions before instructional use.
