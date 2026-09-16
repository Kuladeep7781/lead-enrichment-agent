# Lead Enrichment Agent

A Python-based autonomous lead enrichment pipeline that crawls a company's public website and uses a local LLM to extract structured company intelligence.

## Features

- Accepts company domains as input.
- Uses Playwright for browser-based website crawling.
- Discovers relevant company pages such as About, Team, Company, Contact, Pricing, Leadership, and Founders pages.
- Handles JavaScript-rendered websites.
- Cleans HTML before sending content to the LLM.
- Uses Ollama with the Qwen 2.5 3B local model for structured extraction.
- Uses Pydantic for schema validation.
- Extracts public email addresses and LinkedIn URLs.
- Extracts company overview, target audience, leadership/team members, and confidence score.
- Handles failed pages, 404 responses, access blocks, timeouts, and missing content.
- Continues processing other companies when one company fails.

## Project Structure

```text
lead-enrichment-agent/
│
├── main.py
├── scraper.py
├── llm_extractor.py
├── models.py
├── requirements.txt
├── output.json
│
├── test_scrape.py
├── test_supabase.py
└── test_vapi.py