# Blackridge Sketch Story Lab

Website update with original editorial character sketches and context-specific expressions.

## Character system
Each of the eight roles has three local image assets:
- neutral
- concerned
- decisive

The app selects the expression based on the scene. The sketches are local assets, so no external image host is required.

## Risk visualization update
The Monte Carlo model uses a continuous credit-repricing channel plus jump-to-default loss. This avoids the artificial near-zero spike seen in earlier versions. The distribution chart trims only extreme plotting outliers, preserves the underlying VaR/CVaR calculations, uses a wider smoothing kernel, and highlights the stressed tail cleanly.

## Deployment
Copy the contents into the root of the GitHub repository and deploy `app.py` through Streamlit Community Cloud.
