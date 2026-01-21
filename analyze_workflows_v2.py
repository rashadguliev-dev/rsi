import os
import re

def main():
    # Define keywords for each category
    categories = {
        "Scraping": ["scrape", "crawl", "extract", "parse"],
        "Shopify": ["shopify", "ecommerce", "store", "product", "inventory"],
        "Social": ["instagram", "tiktok", "twitter", "facebook", "youtube", "social"],
        "Telegram": ["telegram", "channel", "group", "bot"],
        "WhatsApp": ["whatsapp", "rapiwa", "twilio", "message"],
        "CRM": ["crm", "hubspot", "zoho", "pipedrive", "sheet", "airtable", "google sheets"],
        "AI": ["gpt", "openai", "ai", "llm", "claude", "gemini", "analysis"],
        "Routing": ["router", "switch", "classify", "category", "filter"],
        "Human": ["human", "escalat", "approv", "manual"]
    }

    # Walk through the directory
    root_dir = "n8n_templates/n8n-workflow-all-templates"

    results = {k: [] for k in categories.keys()}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if not filename.endswith(".json"):
                continue

            full_path = os.path.join(dirpath, filename)
            lower_name = filename.lower()

            for cat, keywords in categories.items():
                if any(k in lower_name for k in keywords):
                    results[cat].append(full_path)

    # Print results
    for cat, paths in results.items():
        print(f"--- {cat} ({len(paths)}) ---")
        for p in paths[:30]: # Limit output
            print(p)
        print("\n")

if __name__ == "__main__":
    main()
