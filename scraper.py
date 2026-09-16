import sys
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace",
    )


RELEVANT_KEYWORDS = [
    "about",
    "team",
    "company",
    "contact",
    "pricing",
    "leadership",
    "founder",
    "founders",
]


COMMON_PATHS = [
    "/about",
    "/team",
    "/company",
    "/leadership",
    "/founders",
    "/contact",
    "/pricing",
]


def discover_relevant_links(page):
    """Find useful same-domain links from the current page."""

    base_domain = urlparse(
        page.url
    ).netloc

    try:

        links = page.locator(
            "a"
        ).evaluate_all(
            """
            elements => elements.map(a => ({
                text: a.innerText,
                href: a.href
            }))
            """
        )

    except Exception:

        return []

    relevant_links = []

    for link in links:

        href = link.get(
            "href",
            "",
        )

        text = link.get(
            "text",
            "",
        ).strip().lower()

        if not href:
            continue

        parsed_url = urlparse(
            href
        )

        if parsed_url.netloc != base_domain:
            continue

        combined_text = (
            f"{text} {href.lower()}"
        )

        if any(
            keyword in combined_text
            for keyword in RELEVANT_KEYWORDS
        ):
            relevant_links.append(
                href
            )

    return list(
        dict.fromkeys(
            relevant_links
        )
    )


def build_common_urls(domain):
    """Build common company-information URLs as fallbacks."""

    parsed = urlparse(
        domain
    )

    base_url = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
    )

    return [
        base_url + path
        for path in COMMON_PATHS
    ]


def clean_html(html):
    """Convert HTML into clean text for LLM processing."""

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for element in soup(
        [
            "script",
            "style",
            "svg",
            "nav",
            "footer",
            "noscript",
        ]
    ):
        element.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True,
    )

    text = " ".join(
        text.split()
    )

    return text


def scrape_page(page, url):
    """
    Visit a page and return cleaned text.

    HTTP errors such as 404, 403, and 429 are
    recorded instead of being treated as valid pages.
    """

    try:

        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        if response is None:

            return {
                "url": url,
                "text": "",
                "error": "No HTTP response received.",
            }

        status = response.status

        if status == 404:

            return {
                "url": url,
                "text": "",
                "error": "HTTP 404 - Page not found.",
            }

        if status in [401, 403]:

            return {
                "url": url,
                "text": "",
                "error": (
                    f"HTTP {status} - "
                    "Access blocked or unauthorized."
                ),
            }

        if status == 429:

            return {
                "url": url,
                "text": "",
                "error": (
                    "HTTP 429 - Too many requests."
                ),
            }

        if status >= 500:

            return {
                "url": url,
                "text": "",
                "error": (
                    f"HTTP {status} - "
                    "Server error."
                ),
            }

        html = page.content()

        text = clean_html(
            html
        )

        if not text:

            return {
                "url": page.url,
                "text": "",
                "error": (
                    "No usable text found on page."
                ),
            }

        return {
            "url": page.url,
            "text": text,
            "error": None,
        }

    except Exception as error:

        return {
            "url": url,
            "text": "",
            "error": str(error),
        }


def scrape_company(domain):
    """Scrape a company's homepage and relevant subpages."""

    if not domain.startswith(
        (
            "http://",
            "https://",
        )
    ):
        domain = (
            "https://" + domain
        )

    results = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        try:

            homepage_result = scrape_page(
                page,
                domain,
            )

            results.append(
                homepage_result
            )

            # If the homepage itself failed,
            # do not attempt to discover links.
            if homepage_result["error"]:

                return results

            relevant_links = (
                discover_relevant_links(
                    page
                )
            )

            common_urls = (
                build_common_urls(
                    page.url
                )
            )

            candidate_urls = (
                relevant_links
                + common_urls
            )

            unique_urls = []

            for url in candidate_urls:

                if url not in unique_urls:

                    unique_urls.append(
                        url
                    )

            # Keep the crawl focused.
            unique_urls = unique_urls[:10]

            homepage_url = (
                homepage_result["url"]
            )

            for url in unique_urls:

                if (
                    url.rstrip("/")
                    == homepage_url.rstrip("/")
                ):
                    continue

                result = scrape_page(
                    page,
                    url,
                )

                # Keep successful pages.
                # Failed optional pages are ignored,
                # allowing the crawl to continue.
                if result["text"]:

                    results.append(
                        result
                    )

        except Exception as error:

            results.append(
                {
                    "url": domain,
                    "text": "",
                    "error": str(error),
                }
            )

        finally:

            browser.close()

    return results
