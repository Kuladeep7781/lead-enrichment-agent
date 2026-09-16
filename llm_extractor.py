import json
import re
from typing import Any

import requests

from models import CompanyData, TeamMember


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"
OLLAMA_TIMEOUT_SECONDS = 300


def extract_contact_points(text: str) -> list[str]:
    """Extract public email addresses directly from website text."""

    email_pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    emails = re.findall(email_pattern, text)

    return list(dict.fromkeys(emails))


def clean_llm_response(response_text: str) -> str:
    """Remove common Markdown code fences from an LLM response."""

    cleaned = response_text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    return cleaned.strip()


def parse_json_response(response_text: str) -> dict[str, Any]:
    """Parse a JSON object returned by the LLM."""

    cleaned = clean_llm_response(response_text)

    try:
        result = json.loads(cleaned)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "LLM response did not contain a valid JSON object."
        )

    try:
        result = json.loads(
            cleaned[start:end + 1]
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "LLM response contained invalid JSON."
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            "LLM output was not a JSON object."
        )

    return result


def split_into_sentences(text: str) -> list[str]:
    """Split text into simple sentences."""

    normalized = " ".join(text.split()).strip()

    if not normalized:
        return []

    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            normalized,
        )
        if sentence.strip()
    ]


def clean_prose_text(text: str) -> str:
    """Remove common Markdown formatting from prose."""

    if not isinstance(text, str):
        return ""

    text = text.strip()

    # Markdown headings.
    text = re.sub(
        r"#{1,6}\s*",
        "",
        text,
    )

    # Bold / italic.
    text = re.sub(
        r"\*\*([^*]+)\*\*",
        r"\1",
        text,
    )

    text = re.sub(
        r"__([^_]+)__",
        r"\1",
        text,
    )

    text = re.sub(
        r"\*([^*]+)\*",
        r"\1",
        text,
    )

    # Inline code.
    text = re.sub(
        r"`([^`]+)`",
        r"\1",
        text,
    )

    # Markdown links.
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text,
    )

    # Bullet prefixes.
    text = re.sub(
        r"(^|\s)[\-•]\s+",
        r"\1",
        text,
    )

    # Numbered list prefixes.
    text = re.sub(
        r"(^|\s)\d+\.\s+",
        r"\1",
        text,
    )

    return " ".join(text.split()).strip()


def remove_llm_commentary(text: str) -> str:
    """Remove obvious LLM summary commentary."""

    sentences = split_into_sentences(text)

    if not sentences:
        return ""

    commentary_patterns = [
        r"^here(?:'s| is) (?:a|an) .*summary",
        r"^here(?:'s| is) (?:a|an) .*overview",
        r"^this (?:is|provides) (?:a|an) .*summary",
        r"^the following (?:is|provides)",
        r"^key (?:features|benefits|points)",
        r"^in summary",
        r"^overall,",
        r"^note that",
        r"^as (?:a )?summary",
    ]

    result = []

    for sentence in sentences:
        lowered = sentence.lower().strip()

        if any(
            re.search(pattern, lowered)
            for pattern in commentary_patterns
        ):
            continue

        result.append(sentence)

    return " ".join(result).strip()


def clean_overview_text(text: str) -> str:
    """Clean an LLM-generated company overview."""

    text = clean_prose_text(text)

    prefixes = [
        "here's a summary of",
        "here is a summary of",
        "here's an overview of",
        "here is an overview of",
        "summary:",
        "overview:",
    ]

    lowered = text.lower()

    for prefix in prefixes:
        if lowered.startswith(prefix):
            text = text[len(prefix):].strip()
            text = text.lstrip(":.- ")
            break

    return remove_llm_commentary(text)


def format_two_sentence_overview(overview: str) -> str:
    """Return a concise overview containing exactly two sentences."""

    text = clean_overview_text(overview)

    if not text:
        return (
            "The company provides products or services described "
            "in the supplied website content. The retrieved pages "
            "did not provide enough additional information for a "
            "more specific summary."
        )

    sentences = split_into_sentences(text)

    if len(sentences) >= 2:
        return (
            sentences[0].rstrip(".!?").strip()
            + ". "
            + sentences[1].rstrip(".!?").strip()
            + "."
        )

    sentence = text.rstrip(".!?").strip()

    # Try a natural comma/semicolon split.
    positions = [
        match.start()
        for match in re.finditer(
            r"[,;]",
            sentence,
        )
    ]

    if positions:
        midpoint = len(sentence) // 2
        position = min(
            positions,
            key=lambda value: abs(value - midpoint),
        )

        first = sentence[:position].strip()
        second = sentence[position + 1:].strip()

        if first and second:
            return f"{first}. {second}."

    words = sentence.split()

    if len(words) >= 8:
        midpoint = len(words) // 2

        first = " ".join(words[:midpoint])
        second = " ".join(words[midpoint:])

        return f"{first}. {second}."

    return (
        sentence
        + ". The supplied website content contains limited "
        + "additional information."
    )


def clean_target_audience(text: str) -> str:
    """Clean and shorten the target audience field."""

    text = clean_prose_text(text)
    text = remove_llm_commentary(text)

    if not text:
        return (
            "The supplied website content did not clearly identify "
            "the company's primary target audience."
        )

    sentences = split_into_sentences(text)

    if not sentences:
        return (
            "The supplied website content did not clearly identify "
            "the company's primary target audience."
        )

    # Keep only the first two useful sentences.
    selected = sentences[:2]

    cleaned = " ".join(
        sentence.rstrip(".!?").strip()
        for sentence in selected
    )

    # Fix a common small-model punctuation problem.
    cleaned = re.sub(
        r"\s+(It|They|These|This|For|The)\s+",
        r". \1 ",
        cleaned,
        count=1,
    )

    cleaned = cleaned.strip(" .")

    return cleaned + "."


def build_extraction_prompt(website_context: str) -> str:
    """Build a grounded extraction prompt for Ollama."""

    return f"""
You extract structured company intelligence from public company
website pages.

Use ONLY the supplied website content.
Do not use outside knowledge.
Do not guess.
Do not invent missing information.

SOURCE PAGE labels identify the pages from which the information
was retrieved.

COMPANY OVERVIEW:
Write exactly TWO concise normal sentences explaining what the
company does.

TARGET AUDIENCE:
Write ONE or TWO concise normal sentences describing the actual
customers or users of the company's products or services.

Do not describe employees, job candidates, investors, or partners
as customers.

LEADERSHIP:
Extract key company leaders or team members ONLY when the supplied
website content clearly identifies them as company employees,
founders, cofounders, executives, or team members.

Prioritize evidence from:
- /team
- /leadership
- /founders
- /company
- /about

Do NOT treat the following as company leadership:
- investors
- investment firms
- venture capital firms
- angel funds
- partner companies
- customers
- podcast guests
- event speakers
- article authors
- people mentioned only in unrelated content

A leadership name should be the person's actual name, not a company,
fund, or organization.

If leadership cannot be established clearly, return an empty list.

LINKEDIN:
Only return a LinkedIn URL when the exact URL appears in the
supplied website content and is clearly associated with that person.

Never construct a LinkedIn URL from a person's name.

EMAIL:
Only return an email address when the exact address appears in the
supplied website content.

Never invent contact addresses.

CONFIDENCE:
Return a value from 0.0 to 1.0 reflecting how complete and directly
supported the extracted information is.

Do not automatically return 1.0.

OUTPUT:
Return ONLY one JSON object containing:
company_overview
target_audience
contact_points
leadership
confidence_score

Do not return Markdown.
Do not return explanations.
Do not return comments.

WEBSITE CONTENT:

{website_context}
""".strip()


def call_ollama(prompt: str) -> str:
    """Send the extraction request to the local Ollama model."""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "format": CompanyData.model_json_schema(),
            "stream": False,
        },
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    response_data = response.json()

    generated_text = response_data.get(
        "response",
        "",
    )

    if not generated_text:
        raise ValueError(
            "Ollama returned an empty response."
        )

    return generated_text


def normalize_contact_points(
    emails: list[str],
) -> list[str]:
    """Normalize and deduplicate email addresses."""

    normalized = []

    for email in emails:
        value = email.strip().lower()

        if value and value not in normalized:
            normalized.append(value)

    return normalized


def normalize_linkedin_url(
    value: Any,
) -> str | None:
    """Accept only LinkedIn URLs returned by the LLM."""

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value.startswith(
        "https://www.linkedin.com/"
    ):
        return None

    return value


def looks_like_organization_name(
    name: str,
) -> bool:
    """Reject obvious company, fund, and organization names."""

    lowered = name.lower()

    blocked_terms = [
        "fund",
        "ventures",
        "capital",
        "partners",
        "investment",
        "company",
        "technologies",
        "technology",
        "labs",
        "angel",
        "inc.",
        "llc",
        "ltd.",
    ]

    return any(
        term in lowered
        for term in blocked_terms
    )


def normalize_leadership(
    leadership_data: Any,
) -> list[TeamMember]:
    """Validate and filter leadership records."""

    if not isinstance(
        leadership_data,
        list,
    ):
        return []

    leadership = []

    for member in leadership_data:

        if not isinstance(
            member,
            dict,
        ):
            continue

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

        # A single first name is not sufficiently reliable.
        if len(name.split()) < 2:
            continue

        if looks_like_organization_name(name):
            continue

        lowered_role = role.lower()

        # Reject obvious non-leadership contexts.
        blocked_roles = [
            "angel fund",
            "venture",
            "investor",
            "investment",
            "partner",
            "customer",
            "podcast",
            "speaker",
            "author",
        ]

        if any(
            term in lowered_role
            for term in blocked_roles
        ):
            continue

        linkedin_url = normalize_linkedin_url(
            member.get(
                "linkedin_url"
            )
        )

        try:
            person = TeamMember(
                name=name,
                role=role,
                linkedin_url=linkedin_url,
            )
        except Exception:
            continue

        if any(
            existing.name.lower() == person.name.lower()
            for existing in leadership
        ):
            continue

        leadership.append(person)

    return leadership


def calculate_confidence(
    company_overview: str,
    target_audience: str,
    contact_points: list[str],
    leadership: list[TeamMember],
) -> float:
    """
    Calculate a conservative confidence score from the extracted
    evidence and completeness of the result.
    """

    score = 0.0

    if len(company_overview.split()) >= 12:
        score += 0.35

    if len(target_audience.split()) >= 5:
        score += 0.30

    if contact_points:
        score += 0.15

    if leadership:
        score += 0.20

    # Do not claim perfect confidence from a small local model.
    return round(
        min(score, 0.90),
        2,
    )


def extract_company_data(
    company_text: str,
) -> CompanyData:
    """Extract and validate structured company intelligence."""

    if not company_text.strip():
        raise ValueError(
            "No website content was provided to the LLM extractor."
        )

    # ---------------------------------------------------------
    # 1. Extract emails deterministically.
    # ---------------------------------------------------------
    contact_points = normalize_contact_points(
        extract_contact_points(company_text)
    )

    # ---------------------------------------------------------
    # 2. Build grounded prompt.
    # ---------------------------------------------------------
    prompt = build_extraction_prompt(
        company_text
    )

    # ---------------------------------------------------------
    # 3. Call local Ollama model.
    # ---------------------------------------------------------
    raw_response = call_ollama(
        prompt
    )

    # ---------------------------------------------------------
    # 4. Parse JSON.
    # ---------------------------------------------------------
    data = parse_json_response(
        raw_response
    )

    # ---------------------------------------------------------
    # 5. Extract raw fields.
    # ---------------------------------------------------------
    overview = str(
        data.get(
            "company_overview",
            "",
        )
    ).strip()

    target_audience = str(
        data.get(
            "target_audience",
            "",
        )
    ).strip()

    leadership = normalize_leadership(
        data.get(
            "leadership",
            [],
        )
    )

    # ---------------------------------------------------------
    # 6. Clean final prose.
    # ---------------------------------------------------------
    overview = format_two_sentence_overview(
        overview
    )

    target_audience = clean_target_audience(
        target_audience
    )

    # ---------------------------------------------------------
    # 7. Calculate confidence.
    # ---------------------------------------------------------
    confidence_score = calculate_confidence(
        company_overview=overview,
        target_audience=target_audience,
        contact_points=contact_points,
        leadership=leadership,
    )

    # ---------------------------------------------------------
    # 8. Final Pydantic validation.
    # ---------------------------------------------------------
    return CompanyData(
        company_overview=overview,
        target_audience=target_audience,
        contact_points=contact_points,
        leadership=leadership,
        confidence_score=confidence_score,
    )
