import argparse
from src.scraper import JobScraperService
from src.extractor import JDExtractorService
from src.aggregator import MarketAggregator

def main():
    parser = argparse.ArgumentParser(description="Automated JD Analysis Tool for Full-Stack AI Engineer Roles")
    parser.add_argument("--search", type=str, default="Full-Stack AI Engineer", help="Job search query keyword")
    parser.add_argument("--location", type=str, default="India", help="Location (e.g., India, Bengaluru, Remote)")
    parser.add_argument("--limit", type=int, default=15, help="Number of jobs wanted per site")
    parser.add_argument("--extract", action="store_true", help="Run LLM extraction on collected jobs")
    parser.add_argument("--report", action="store_true", help="Generate market intelligence report & exports")

    args = parser.parse_args()

    print(f"\n[🚀] Starting Job Analysis Pipeline...")
    print(f" -> Query: {args.search}")
    print(f" -> Location: {args.location}")
    print(f" -> Limit per board: {args.limit}\n")

    # 1. Scrape Jobs
    scraper = JobScraperService()
    jobs = scraper.fetch_jobs(search_term=args.search, location=args.location, results_wanted=args.limit)
    print(f"[+] Total jobs fetched/cached in DB: {len(jobs)}")

    # 2. Extract Structured Data via LLM if requested
    if args.extract and jobs:
        print(f"\n[🤖] Starting LLM Extraction for collected jobs...")
        extractor = JDExtractorService()
        for i, job in enumerate(jobs):
            print(f" [{i+1}/{len(jobs)}] Extracting: {job.title} at {job.company}...")
            extractor.extract_job(job)
        print(f"[+] Extraction pass completed.")

    # 3. Aggregate and Report if requested
    if args.report:
        print(f"\n[📊] Generating Market Intelligence Report & Artifacts...")
        aggregator = MarketAggregator()
        metrics = aggregator.generate_market_report()
        print(f"[+] Successfully generated market intelligence report!")
        print(f" -> Successfully Analyzed Jobs: {metrics.get('total_analyzed', 0)}")

    print("\n[✨] Pipeline execution completed successfully!\n")

if __name__ == "__main__":
    main()