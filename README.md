# Lead Enrichment Agent

A Python-based lead enrichment agent that crawls a company's public website and uses a local LLM to extract structured company intelligence.

This project was built as part of the SoftwareBrio AI Engineer Intern take-home assignment.

## What This Project Does

The agent accepts one or more company domains and:

1. Opens the company homepage using Playwright.
2. Discovers relevant pages such as About, Team, Company, Leadership, Founders, Contact, and Pricing.
3. Uses a headless Chromium browser to handle JavaScript-rendered websites.
4. Cleans the retrieved HTML by removing scripts, styles, SVGs, navigation, footers, and other unnecessary content.
5. Limits the amount of website text sent to the LLM.
6. Sends the cleaned website content to a local Ollama LLM.
7. Extracts structured company information using a Pydantic schema.
8. Validates the extracted information before saving it.
9. Handles common website errors without stopping the complete pipeline.
10. Saves the final results to `output.json`.

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
```

### File Description

- `main.py` - Runs the complete enrichment pipeline for one or more company domains.
- `scraper.py` - Uses Playwright and headless Chromium to crawl and clean public website content.
- `llm_extractor.py` - Sends cleaned website content to the local Ollama LLM and extracts structured information.
- `models.py` - Contains the Pydantic models used to validate structured company data.
- `requirements.txt` - Lists the Python dependencies required by the project.
- `output.json` - Contains the sample structured output for the assignment test domains.
- `.gitignore` - Prevents virtual environments, notebooks, temporary files, and other local files from being committed.

## Requirements

- Python 3.10 or newer
- Ollama
- Internet connection for crawling public company websites

Playwright installs and uses its own Chromium browser.

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Kuladeep7781/lead-enrichment-agent.git
cd lead-enrichment-agent
```

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Chromium

```bash
playwright install chromium
```

## Ollama Setup

This project uses Ollama as a local LLM, so no external LLM API key is required.

Make sure Ollama is installed and running on the local machine.

Pull the model used by the project:

```bash
ollama pull qwen2.5:3b
```

The application connects to the local Ollama service at:

```text
http://localhost:11434
```

The default model used by the application is:

```text
qwen2.5:3b
```

## Environment Variables

The current version of the project does not require an external API key or a `.env` file.

The LLM runs locally through Ollama, which avoids the need for an external LLM API key.

## Run the Agent

To run the assignment test domains:

```bash
python main.py postman.com supabase.com vapi.ai
```

The agent also accepts other company domains:

```bash
python main.py example.com
```

Multiple domains can be provided in the same command:

```bash
python main.py example.com anothercompany.com
```

Each company is processed independently so that an error with one website does not stop the complete pipeline.

## Output

The final structured results are saved to:

```text
output.json
```

The output contains structured company intelligence including:

- A concise company overview
- Target audience / Ideal Customer Profile (ICP)
- Generic public contact emails
- Leadership or team information when discoverable
- LinkedIn information when discoverable
- Confidence score between `0.0` and `1.0`

The repository includes sample output for the three assignment test domains:

```text
postman.com
supabase.com
vapi.ai
```

## Scraping and Website Processing

The scraper uses Playwright with a headless Chromium browser.

The process is:

1. Open the company homepage.
2. Wait for the page to load.
3. Discover relevant internal links.
4. Visit useful pages such as About, Team, Company, Leadership, Founders, Contact, and Pricing when available.
5. Remove unnecessary HTML elements such as scripts, styles, SVGs, navigation, footers, and other boilerplate.
6. Convert the remaining page content into clean text.
7. Limit the amount of text passed to the LLM.

This allows the pipeline to work with both normal websites and JavaScript-rendered websites.

## LLM and Structured Output

The cleaned website content is passed to a local Ollama LLM.

The LLM is instructed to extract only information supported by the provided website content and not to guess missing information.

The structured response follows the Pydantic schema defined in `models.py`.

The final response is validated using Pydantic before it is written to `output.json`.

## Error Handling

The scraper handles common website problems including:

- 404 pages
- 401/403 access errors
- 429 rate limiting
- Server errors
- Page timeouts
- Missing page content
- Empty page content
- Individual page failures

Errors are handled per page and per company so that one failed website does not terminate the complete pipeline.

## Test Domains

The assignment test domains are:

```text
postman.com
supabase.com
vapi.ai
```

Run all three with:

```bash
python main.py postman.com supabase.com vapi.ai
```

## End-to-End Flow

```text
Company Domain
      ↓
Playwright + Headless Chromium
      ↓
Homepage + Relevant Subpages
      ↓
Clean Website Text
      ↓
Local Ollama LLM
      ↓
Pydantic Structured Validation
      ↓
Structured Company Data
      ↓
output.json
```

## Local Execution Summary

After installing the dependencies, Playwright Chromium, and the Ollama model, the complete pipeline can be run with:

```bash
python main.py postman.com supabase.com vapi.ai
```

The results will be written to:

```text
output.json
```