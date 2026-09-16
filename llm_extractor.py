import json
import re

import requests

from models import CompanyData, TeamMember


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def extract_contact_points(text):
    """Extract public email addresses directly from website text."""

    email_pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    emails = re.findall(
        email_pattern,
        text,
    )

    return list(dict.fromkeys(emails))


def extract_linkedin_urls(text):
    """Extract LinkedIn profile URLs found in website text."""

    linkedin_pattern = (
        r"https?://(?:www\.)?linkedin\.com/in/"
        r"[A-Za-z0-9_-]+/?"
    )

    urls = re.findall(
        linkedin_pattern,
        text,
    )

    return list(dict.fromkeys(urls))


def count_sentences(text):
    """Count sentences using sentence-ending punctuation."""

    sentences = re.findall(
        r"[^.!?]+[.!?]",
        text.strip(),
    )

    return len(sentences)


def format_two_sentence_overview(text):
    """
    Convert text into exactly two sentences.

    If the LLM returns two or more sentences,
    keep the first two.

    If it returns one long sentence or text without
    punctuation, split the text approximately in half.
    """

    text = " ".join(
        text.strip().split()
    )

    if not text:
        return ""

    sentences = re.findall(
        r"[^.!?]+[.!?]",
        text,
    )

    if len(sentences) >= 2:
        return " ".join(
            sentence.strip()
            for sentence in sentences[:2]
        )

    body = text.rstrip(".!?").strip()

    words = body.split()

    if len(words) < 2:
        return body + "."

    midpoint = len(words) // 2

    first_part = " ".join(
        words[:midpoint]
    ).strip()

    second_part = " ".join(
        words[midpoint:]
    ).strip()

    if not first_part or not second_part:
        return body + "."

    return (
        first_part.rstrip(".!?")
        + ". "
        + second_part.rstrip(".!?")
        + "."
    )


def has_two_sentence_overview(text):
    """Check whether an overview contains exactly two sentences."""

    text = " ".join(
        text.strip().split()
    )

    if not text:
        return False

    sentences = re.findall(
        r"[^.!?]+[.!?]",
        text,
    )

    return len(sentences) == 2


def build_prompt(company_text):
    """Build the extraction prompt for the local LLM."""

    return f"""
You are a company research assistant.

Extract company intelligence ONLY from the website
content provided below.

IMPORTANT RULES:

1. Do not invent or guess information.
2. Use only information explicitly present in the
   website content.
3. If information is missing, use an empty string
   or empty list.
4. The company_overview MUST contain EXACTLY TWO
   sentences.
5. Keep the company_overview concise.
6. Identify the PRIMARY CUSTOMER target audience
   or ideal customer profile.
7. Do NOT describe employees, job candidates,
   investors, or partners as the target audience
   unless the website clearly identifies them as
   customers.
8. Identify key company leadership or team members
   when their names and roles are clearly stated.
9. Do not treat customers, investors, partners,
   podcast guests, article subjects, or unrelated
   people as company employees or leaders.
10. Do not create email addresses.
11. Do not create LinkedIn URLs.
12. Only use a LinkedIn URL when that exact URL is
    present in the website content.

SOURCE PAGE PRIORITY:

For leadership and company information, prioritize
information from pages whose URL contains:

- /team
- /leadership
- /founders
- /company
- /about

Information from these pages is more relevant for
identifying company employees and leadership.

Pages such as:

- /blog
- /articles
- /podcast
- /press
- /customers
- /investors

may mention other people. Do NOT automatically
consider those people company employees.

LEADERSHIP EXTRACTION:

For every person clearly identified as a company
leader or team member, return:

- name
- role
- LinkedIn URL only if explicitly present

Examples of useful leadership roles include:

- Founder
- Co-Founder
- CEO
- CTO
- CFO
- COO
- President
- Chief Executive Officer
- Chief Technology Officer
- Chief Financial Officer
- Chief Operating Officer
- Head of Engineering
- Head of Product
- Head of Sales
- VP Engineering
- VP Product
- VP Sales

If the website does not provide reliable leadership
information, return an empty leadership list.

Do not infer a person's role from their name.

CONFIDENCE SCORE:

- Must be between 0.0 and 1.0.
- 0.0 means very low confidence.
- 1.0 means very high confidence.
- Do not use a percentage.
- Do not use a 1-10 scale.

Return ONLY valid JSON with these fields:

{{
  "company_overview": "Sentence one. Sentence two.",
  "target_audience": "Primary customer target audience or ideal customer profile.",
  "contact_points": [],
  "leadership": [
    {{
      "name": "Person name",
      "role": "Person role",
      "linkedin_url": null
    }}
  ],
  "confidence_score": 0.0
}}

Remember:

company_overview = EXACTLY 2 sentences.

Website content:

{company_text}
"""


def call_ollama(prompt):
    """Send a prompt to the local Ollama model."""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "format": CompanyData.model_json_schema(),
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()["response"]


def normalize_confidence_score(value):
    """Convert common confidence formats to 0.0-1.0."""

    score = float(value)

    if 1.0 < score <= 10.0:
        score = score / 10.0

    elif 10.0 < score <= 100.0:
        score = score / 100.0

    return max(
        0.0,
        min(1.0, score),
    )


def extract_company_data(company_text):
    """
    Extract structured company intelligence.

    Emails and LinkedIn URLs are extracted with Python.

    Semantic fields are extracted by the LLM.
    """

    emails = extract_contact_points(
        company_text
    )

    linkedin_urls = extract_linkedin_urls(
        company_text
    )

    prompt = build_prompt(
        company_text
    )

    raw_output = call_ollama(
        prompt
    )

    data = json.loads(
        raw_output
    )

    data["confidence_score"] = (
        normalize_confidence_score(
            data.get(
                "confidence_score",
                0.0,
            )
        )
    )

    # Use deterministic email extraction.
    data["contact_points"] = emails

    # Clean and validate leadership data.
    leadership = []

    for member in data.get(
        "leadership",
        [],
    ):

        name = str(
            member.get(
                "name",
                "",
            )
        ).strip()

        role = str(
            member.get(
                "role",
                "",
            )
        ).strip()

        if not name or not role:
            continue

        leadership.append(
            TeamMember(
                name=name,
                role=role,
                linkedin_url=member.get(
                    "linkedin_url"
                ),
            )
        )

    data["leadership"] = leadership

    # Attach explicitly discovered LinkedIn URLs
    # when a leadership member does not already have one.
    if linkedin_urls:

        for index, url in enumerate(
            linkedin_urls
        ):

            if index < len(
                data["leadership"]
            ):

                member = data[
                    "leadership"
                ][index]

                if member.linkedin_url is None:
                    member.linkedin_url = url

    # Always normalize the overview.
    overview = data.get(
        "company_overview",
        "",
    ).strip()

    overview = format_two_sentence_overview(
        overview
    )

    data["company_overview"] = overview

    # Validate the final structured result.
    company_data = CompanyData.model_validate(
        data
    )

    if not has_two_sentence_overview(
        company_data.company_overview
    ):
        raise ValueError(
            "Company overview could not be "
            "converted into exactly two sentences."
        )

    return company_data