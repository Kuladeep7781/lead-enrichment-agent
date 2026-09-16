
import json

from scraper import scrape_company


domain = "supabase.com"

print("=" * 60)
print("SCRAPING:", domain)
print("=" * 60)

results = scrape_company(domain)

with open("supabase_scraped.json", "w", encoding="utf-8") as file:
    json.dump(results, file, ensure_ascii=False, indent=2)

print("\nPages scraped:", len(results))

for result in results:
    print("\nURL:", result["url"])

    if result["error"]:
        print("ERROR:", result["error"])
    else:
        print("Characters:", len(result["text"]))

print("\nSaved to supabase_scraped.json")
