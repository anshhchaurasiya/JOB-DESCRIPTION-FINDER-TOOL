import hashlib
from datetime import datetime
from typing import List, Optional, Any
from zoneinfo import ZoneInfo  # <--- Added Any here
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

    def _safe_val(self, val: Any, target_type: type = str) -> Any:
        """Converts Pandas NaN or missing values to None, casting appropriately."""
        if pd.isna(val):
            return None
        try:
            if target_type == float:
                return float(val)
            elif target_type == int:
                return int(val)
            elif target_type == bool:
                return bool(val)
            return str(val)
        except Exception:
            return None

    def fetch_jobs(
        self, 
        search_term: str = "Full-Stack AI Engineer", 
        location: str = "India", 
        results_wanted: int = 20,
        sites: Optional[List[str]] = None,
        hours_old: int = 48,
    ) -> List[JobRecord]:
        """
        Scrapes job boards concurrently using jobspy with isolated error handlers,
        capturing all 34 columns with plain text descriptions.
        """
        if sites is None:
            sites = ["indeed", "linkedin", "naukri"]

        print(f"[*] Starting job collection for '{search_term}' in '{location}' across sites: {sites}")
        
        all_job_records: List[JobRecord] = []
        timestamp = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()

        try:
            df: pd.DataFrame = scrape_jobs(
                site_name=sites,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                country_indeed="India",
                description_format="markdown",
                fetch_description=True,
                hours_old=hours_old
            )

            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    title = self._safe_val(row.get("title"), str) or "Unknown Role"
                    company = self._safe_val(row.get("company"), str) or "Unknown Company"
                    url = self._safe_val(row.get("job_url"), str) or ""
                    source = self._safe_val(row.get("site"), str) or "unknown"
                    
                    job_id = self._generate_job_id(source, title, company, url)

                    record = JobRecord(
                        job_id=job_id,
                        id=self._safe_val(row.get("id")),
                        site=source,
                        job_url=url,
                        job_url_direct=self._safe_val(row.get("job_url_direct")),
                        title=title,
                        company=company,
                        location=self._safe_val(row.get("location")),
                        date_posted=self._safe_val(row.get("date_posted")),
                        job_type=self._safe_val(row.get("job_type")),
                        salary_source=self._safe_val(row.get("salary_source")),
                        interval=self._safe_val(row.get("interval")),
                        min_amount=self._safe_val(row.get("min_amount"), float),
                        max_amount=self._safe_val(row.get("max_amount"), float),
                        currency=self._safe_val(row.get("currency")),
                        is_remote=self._safe_val(row.get("is_remote"), bool),
                        job_level=self._safe_val(row.get("job_level")),
                        job_function=self._safe_val(row.get("job_function")),
                        listing_type=self._safe_val(row.get("listing_type")),
                        emails=self._safe_val(row.get("emails")),
                        description=self._safe_val(row.get("description")),
                        company_industry=self._safe_val(row.get("company_industry")),
                        company_url=self._safe_val(row.get("company_url")),
                        company_logo=self._safe_val(row.get("company_logo")),
                        company_url_direct=self._safe_val(row.get("company_url_direct")),
                        company_addresses=self._safe_val(row.get("company_addresses")),
                        company_num_employees=self._safe_val(row.get("company_num_employees")),
                        company_revenue=self._safe_val(row.get("company_revenue")),
                        company_description=self._safe_val(row.get("company_description")),
                        skills=self._safe_val(row.get("skills")),
                        experience_range=self._safe_val(row.get("experience_range")),
                        company_rating=self._safe_val(row.get("company_rating"), float),
                        company_reviews_count=self._safe_val(row.get("company_reviews_count"), int),
                        vacancy_count=self._safe_val(row.get("vacancy_count"), int),
                        work_from_home_type=self._safe_val(row.get("work_from_home_type")),
                        collection_timestamp=timestamp
                    )
                    all_job_records.append(record)
                
                print(f"[+] Successfully scraped and normalized {len(all_job_records)} jobs.")
            else:
                print("[-] Scraper returned zero results.")

        except Exception as e:
            print(f"[!] Warning/Error during job collection execution: {e}")

        if all_job_records:
            saved = self.storage.save_jobs(all_job_records)
            print(f"[+] Persisted {saved} new unique jobs to SQLite database.")

        return all_job_records