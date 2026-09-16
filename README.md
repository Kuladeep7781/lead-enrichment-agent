# Lead Enrichment Agent

A Python-based lead enrichment agent that crawls a company's public website and uses a local LLM to extract structured company intelligence.

The project was built as part of the SoftwareBrio AI Engineer Intern take-home assignment.

## What This Project Does

The agent accepts one or more company domains and:

1. Opens the company homepage using Playwright.
2. Discovers relevant pages such as About, Team, Company, Leadership, Founders, Contact, and Pricing.
3. Uses a headless Chromium browser to handle JavaScript-rendered websites.
4. Cleans the retrieved HTML and removes scripts, styles, SVGs, navigation, footers, and other unnecessary content.
5. Limits the amount of website text sent to the LLM to reduce unnecessary token usage.
6. Sends the cleaned website content to a local Ollama LLM.
7. Extracts structured company information using a Pydantic schema.
8. Handles common website errors without stopping the complete pipeline.
9. Saves the final results to `output.json`.

## Project Structure

```text
lead-enrichment-agent/
│
├── main.py
├── scraper.py
├── llm_extractor.py
├── models.py
├── requirements.txt
├── README.md
├── output.json
└── .gitignore