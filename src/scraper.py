import hashlib
from datetime import datetime
from typing import List, Optional
import pandas as pd
from jobspy import scrape_jobs
from src.models import JobRecord
from src.storage import StorageManager

class JobScraperService:
    def __init__(self, storage_manager: Optional[StorageManager] = None):
        self.storage = storage_manager or StorageManager()

    def _generate_job_id(self, source: str, title: str, company: str, url: str) -> str:
        """Generates a deterministic unique hash for deduplication."""
        unique_string = f"{source}_{title}_{company}_{url}"
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()[:16]

    def fetch_jobs(
        self, 
        search_term: str = "Full-Stack AI Engineer", 
        location: str = "India", 
        results_wanted: int = 20,
        sites: Optional[List[str]] = None
    ) -> List[JobRecord]:
        """
        Scrapes job boards concurrently using jobspy with isolated error handlers.
        """
        if sites is None:
            sites = ["indeed", "linkedin", "naukri"]

        print(f"[*] Starting job collection for '{search_term}' in '{location}' across sites: {sites}")
        
        all_job_records: List[JobRecord] = []
        timestamp = datetime.utcnow().isoformat()

        try:
            # JobSpy scrape call
            df: pd.DataFrame = scrape_jobs(
                site_name=sites,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                country_indeed="India"
            )

            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    title = str(row.get("title", "Unknown Role"))
                    company = str(row.get("company", "Unknown Company"))
                    url = str(row.get("job_url", ""))
                    source = str(row.get("site", "unknown"))
                    
                    job_id = self._generate_job_id(source, title, company, url)
                    
                    raw_desc = row.get("description")
                    raw_description_str = str(raw_desc) if pd.notna(raw_desc) else None

                    # Construct normalized JobRecord
                    record = JobRecord(
                        job_id=job_id,
                        title=title,
                        company=company,
                        location=row.get("location") if pd.notna(row.get("location")) else None,
                        job_url=url,
                        source=source,
                        raw_description=raw_description_str,
                        date_posted=str(row.get("date_posted")) if pd.notna(row.get("date_posted")) else None,
                        salary_string=f"{row.get('min_amount')} - {row.get('max_amount')} {row.get('currency')}" if pd.notna(row.get('min_amount')) else None,
                        employment_type=str(row.get("job_type")) if pd.notna(row.get("job_type")) else None,
                        experience_requirements=None, 
                        collection_timestamp=timestamp,
                        source_job_id=str(row.get("id")) if pd.notna(row.get("id")) else None
                    )
                    all_job_records.append(record)
                
                print(f"[+] Successfully scraped and normalized {len(all_job_records)} jobs.")
            else:
                print("[-] Scraper returned zero results.")

        except Exception as e:
            print(f"[!] Warning/Error during job collection execution: {e}")

        # Persist to SQLite & raw file cache
        if all_job_records:
            saved = self.storage.save_jobs(all_job_records)
            print(f"[+] Persisted {saved} new unique jobs to SQLite database.")

        return all_job_records