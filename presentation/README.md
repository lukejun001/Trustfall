# Trustfall presentation

Open `Trustfall_Project_Story.pptx` in PowerPoint, Keynote, or Google Slides. The charts are native PowerPoint charts and can be edited directly.

To rebuild the deck with the latest database counts:

```bash
set -a; source .env.local; set +a
.venv-qwen/bin/python scripts/refresh_presentation_metrics.py
node scripts/generate_presentation.cjs
```

The refresh writes the ignored `trustfall-metrics.json` file and the generator creates a replacement `.pptx`. It does not modify source messages, labels, or model artifacts.

The deck distinguishes live operations metrics from the frozen 20-example training snapshot used for the initial Qwen LoRA result. This matters: labels may continue to arrive after a training run.

Photography is sourced from Unsplash and credited on the final slide. Before public commercial use, verify the current Unsplash license/attribution requirements for your intended use.
