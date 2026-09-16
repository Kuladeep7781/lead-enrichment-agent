import argparse
import json
from typing import Any

from llm_extractor import extract_company_data
from scraper import scrape_company


DEFAULT_DOMAINS = [
    "postman.com",
    "supabase.com",
    "vapi.ai",
]

PRIORITY_KEYWORDS = [
    "/about",
    "/team",
    "/company",
    "/leadership",
    "/founders",
    "/contact",
    "/pricing",
]

MAX_CHARS_PER_PAGE = 4000
MAX_TOTAL_CONTEXT_CHARS = 18000


def build_llm_context(
    scraped_pages: list[dict[str, Any]],
) -> str:
    """
    Build focused, page-aware context for the LLM.

    The homepage and company-information pages are prioritized.
    Each page is labeled with its source URL so the LLM can
    understand where the information came from.
    """

    successful_pages = [
        page
        for page in scraped_pages
        if page.get("text")
    ]

    if not successful_pages:
        return ""

    priority_pages = []
    other_pages = []

    for index, page in enumerate(successful_pages):
        url = page.get("url", "").lower()

        # Always prioritize the first successfully scraped page,
        # which is the homepage.
        if index == 0:
            priority_pages.append(page)
            continue

        if any(
            keyword in url
            for keyword in PRIORITY_KEYWORDS
        ):
            priority_pages.append(page)
        else:
            other_pages.append(page)

    # Use priority pages first.
    selected_pages = priority_pages + other_pages

    context_parts = []
    total_characters = 0

    for page in selected_pages:
        if total_characters >= MAX_TOTAL_CONTEXT_CHARS:
            break

        url = page.get("url", "")
        text = page.get("text", "").strip()

        if not text:
            continue

        remaining_characters = (
            MAX_TOTAL_CONTEXT_CHARS
            - total_characters
        )

        page_text = text[
            :min(
                MAX_CHARS_PER_PAGE,
                remaining_characters,
            )
        ]

        if not page_text:
            continue

        context_parts.append(
            f"SOURCE PAGE: {url}\n"
            f"{page_text}"
        )

        total_characters += len(page_text)

    return "\n\n".join(context_parts)


def process_company(
    domain: str,
) -> dict[str, Any]:
    """
    Scrape and extract intelligence for one company.

    Errors for one company are captured so the pipeline
    can continue processing the remaining companies.
    """

    print("\n" + "=" * 60)
    print("PROCESSING:", domain)
    print("=" * 60)

    try:
        # ---------------------------------------------------------
        # 1. Scrape the company's public website.
        # ---------------------------------------------------------
        scraped_pages = scrape_company(domain)

        print(
            "Pages scraped:",
            len(scraped_pages),
        )

        # ---------------------------------------------------------
        # 2. Build focused LLM context.
        # ---------------------------------------------------------
        company_text = build_llm_context(
            scraped_pages
        )

        if not company_text:
            return {
                "domain": domain,
                "status": "failed",
                "error": (
                    "No usable website text was extracted."
                ),
            }

        print(
            "LLM context characters:",
            len(company_text),
        )

        # ---------------------------------------------------------
        # 3. Extract structured company intelligence.
        # ---------------------------------------------------------
        company_data = extract_company_data(
            company_text
        )

        # ---------------------------------------------------------
        # 4. Convert the Pydantic model into JSON data.
        # ---------------------------------------------------------
        return {
            "domain": domain,
            "status": "success",
            **company_data.model_dump(),
        }

    except Exception as error:
        # ---------------------------------------------------------
        # If this company fails, return the error and allow the
        # pipeline to continue with the next company.
        # ---------------------------------------------------------
        print(
            "ERROR:",
            str(error),
        )

        return {
            "domain": domain,
            "status": "failed",
            "error": str(error),
        }


def run_pipeline(
    domains: list[str],
) -> list[dict[str, Any]]:
    """Process all company domains independently."""

    results = []

    for domain in domains:
        result = process_company(domain)
        results.append(result)

    return results


def save_results(
    results: list[dict[str, Any]],
    filename: str = "output.json",
) -> None:
    """Save final company intelligence to a JSON file."""

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )


def parse_arguments() -> argparse.Namespace:
    """
    Parse optional company domains from the command line.

    If no domains are provided, the three assignment test
    domains are used.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Lead enrichment agent for company domains."
        )
    )

    parser.add_argument(
        "domains",
        nargs="*",
        help=(
            "Company domains to process. "
            "If omitted, the assignment test domains "
            "are used."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Run the complete company intelligence pipeline."""

    print("=" * 60)
    print("LEAD ENRICHMENT AGENT")
    print("=" * 60)

    args = parse_arguments()

    domains = (
        args.domains
        if args.domains
        else DEFAULT_DOMAINS
    )

    print("\nDomains to process:")

    for domain in domains:
        print("-", domain)

    results = run_pipeline(domains)

    save_results(results)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    print("\nResults saved to output.json")

    for result in results:
        print(
            f"\n{result['domain']}: "
            f"{result['status']}"
        )


if __name__ == "__main__":
    main()
