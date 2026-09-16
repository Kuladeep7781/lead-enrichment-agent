# Lead Enrichment Agent

A Python-based autonomous lead enrichment pipeline that accepts company
domains, crawls their public websites, extracts relevant page content,
and uses a local LLM to produce structured company intelligence.

The project was built for the SoftwareBrio AI Engineer Intern take-home
assignment.

## Features

- Accepts one or more company domains from the command line.
- Uses Playwright with Chromium for browser-based website crawling.
- Discovers relevant company pages such as:
  - About
  - Company
  - Team
  - Leadership
  - Founders
  - Contact
  - Pricing
- Handles JavaScript-rendered pages through a headless browser.
- Removes scripts, styles, SVGs, navigation, footer, and other
  unnecessary HTML content before LLM processing.
- Limits the amount of website text sent to the LLM.
- Uses Ollama with `qwen2.5:3b` for local LLM extraction.
- Validates the structured result using Pydantic.
- Extracts public email addresses deterministically from website text.
- Handles failed pages and individual company failures without stopping
  the entire pipeline.
- Produces JSON output for each processed company.

## Project Structure

```text
lead-enrichment-agent/
├── main.py
├── scraper.py
├── llm_extractor.py
├── models.py
├── requirements.txt
├── README.md
├── output.json
└── .gitignore