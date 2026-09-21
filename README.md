# Local AI Presentation Agent

A local presentation generator that asks Ollama for a structured slide plan and
turns that plan into an editable PowerPoint presentation with the
visual system reconstructed from the supplied PDF template.

## Requirements

- Python 3.9+
- Ollama running locally
- An installed Ollama model (development default: `qwen3.5:9b`)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

Browser interface:

```bash
streamlit run app.py
```

Streamlit will print a local URL and normally open it in your browser. Enter a
request, choose the audience and slide count, then download the generated
PowerPoint from the page. Paste factual information or numeric data into the
optional information field when you want the agent to create charts.

Command-line interface:

Interactive mode:

```bash
python main.py
```

Or pass the request directly:

```bash
python main.py "Create a 5-slide presentation explaining quantum computing to first-year university students."
```

The generated `.pptx` is saved in `output/`. The model name and Ollama host are
read from environment variables; application code does not hard-code a model.

## Test

```bash
pytest
```

## Current scope

The application supports title, agenda, content, section, quote, editable chart,
and closing slides. Supported native chart types are bar, column, line, pie, and
doughnut. Charts are created only from numeric information supplied by the user;
the planner is instructed not to invent values. The application validates the
structured model response and checks the resulting PowerPoint package for basic
layout and content problems. Web research, automatic citations, and iterative
slide repair are not yet included.
