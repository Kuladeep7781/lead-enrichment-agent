
import json

from scraper import scrape_company
from llm_extractor import extract_company_data


# Required test domains from the assignment.
COMPANY_DOMAINS = [
    "postman.com",
    "supabase.com",
    "vapi.ai",
]

def combine_scraped_text(scraped_pages):
    """Combine clean text from all successfully scraped pages."""

    return "\n\n".join(
        page["text"]
        for page in scraped_pages
        if page["text"]
    )


def process_company(domain):
    """
    Scrape and extract intelligence for one company.

    Errors for one company are captured so the pipeline can
    continue processing the remaining companies.
    """

    print("\n" + "=" * 60)
    print("PROCESSING:", domain)
    print("=" * 60)

    try:
        # -----------------------------------------------------
        # 1. Scrape the company's website.
        # -----------------------------------------------------

        scraped_pages = scrape_company(domain)

        print(
            "Pages scraped:",
            len(scraped_pages)
        )

        # -----------------------------------------------------
        # 2. Combine the cleaned page text.
        # -----------------------------------------------------

        company_text = combine_scraped_text(
            scraped_pages
        )

        if not company_text:
            return {
                "domain": domain,
                "status": "failed",
                "error": "No usable website text was extracted.",
            }

        print(
            "Characters extracted:",
            len(company_text)
        )

        # -----------------------------------------------------
        # 3. Extract structured company intelligence.
        # -----------------------------------------------------

        company_data = extract_company_data(
            company_text
        )

        # -----------------------------------------------------
        # 4. Convert the Pydantic model into JSON-compatible data.
        # -----------------------------------------------------

        result = {
            "domain": domain,
            "status": "success",
            **company_data.model_dump(),
        }

        return result

    except Exception as error:

        # -----------------------------------------------------
        # If anything fails for this company, return the error
        # instead of stopping the entire pipeline.
        # -----------------------------------------------------

        print(
            "ERROR:",
            str(error)
        )

        return {
            "domain": domain,
            "status": "failed",
            "error": str(error),
        }


def run_pipeline(domains):
    """Process all company domains."""

    results = []

    for domain in domains:

        result = process_company(domain)

        results.append(result)

    return results


def save_results(results, filename="output.json"):
    """Save final company intelligence to a JSON file."""

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main():
    """Run the complete company intelligence pipeline."""

    print("=" * 60)
    print("LEAD ENRICHMENT AGENT")
    print("=" * 60)

    results = run_pipeline(
        COMPANY_DOMAINS
    )

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
