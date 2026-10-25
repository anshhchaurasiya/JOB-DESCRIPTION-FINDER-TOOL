import sqlite3
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.settings import SQLITE_DB_PATH, RAW_DATA_DIR
from src.models import JobRecord, ExtractedJD

class StorageManager:
    def __init__(self, db_path=SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes SQLite tables for raw jobs covering all 34 columns and extractions."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    id TEXT,
                    site TEXT,
                    job_url TEXT,
                    job_url_direct TEXT,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    date_posted TEXT,
                    job_type TEXT,
                    salary_source TEXT,
                    interval TEXT,
                    min_amount REAL,
                    max_amount REAL,
                    currency TEXT,
                    is_remote INTEGER,
                    job_level TEXT,
                    job_function TEXT,
                    listing_type TEXT,
                    emails TEXT,
                    description TEXT,
                    company_industry TEXT,
                    company_url TEXT,
                    company_logo TEXT,
                    company_url_direct TEXT,
                    company_addresses TEXT,
                    company_num_employees TEXT,
                    company_revenue TEXT,
                    company_description TEXT,
                    skills TEXT,
                    experience_range TEXT,
                    company_rating REAL,
                    company_reviews_count INTEGER,
                    vacancy_count INTEGER,
                    work_from_home_type TEXT,
                    collection_timestamp TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS extractions (
                    job_id TEXT PRIMARY KEY,
                    extraction_status TEXT,
                    schema_version TEXT,
                    extracted_data TEXT,
                    updated_at TEXT,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
                )
            """)
            conn.commit()

    def save_jobs(self, jobs: List[JobRecord]) -> int:
        """Saves scraped job records into SQLite, ignoring duplicates by job_id."""
        saved_count = 0
        with self._get_connection() as conn:
            for job in jobs:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO jobs (
                            job_id, id, site, job_url, job_url_direct, title, company, location, 
                            date_posted, job_type, salary_source, interval, min_amount, max_amount, 
                            currency, is_remote, job_level, job_function, listing_type, emails, 
                            description, company_industry, company_url, company_logo, company_url_direct, 
                            company_addresses, company_num_employees, company_revenue, company_description, 
                            skills, experience_range, company_rating, company_reviews_count, vacancy_count, 
                            work_from_home_type, collection_timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job.job_id, job.id, job.site, job.job_url, job.job_url_direct, job.title, job.company, job.location,
                        job.date_posted, job.job_type, job.salary_source, job.interval, job.min_amount, job.max_amount,
                        job.currency, int(job.is_remote) if job.is_remote is not None else None, job.job_level, job.job_function,
                        job.listing_type, job.emails, job.description, job.company_industry, job.company_url, job.company_logo,
                        job.company_url_direct, job.company_addresses, job.company_num_employees, job.company_revenue,
                        job.company_description, job.skills, job.experience_range, job.company_rating, job.company_reviews_count,
                        job.vacancy_count, job.work_from_home_type, job.collection_timestamp
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving job {job.job_id}: {e}")
            conn.commit()
        
        # Export snapshots to CSV and clean JSON
        self.export_raw_files(jobs)
        return saved_count

    def export_raw_files(self, jobs: List[JobRecord]):
        """Exports raw dataset snapshots to CSV and clean JSON with unescaped URLs."""
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM jobs ORDER BY collection_timestamp DESC", conn)
        
        # Export CSV directly
        df.to_csv(RAW_DATA_DIR / "jobs.csv", index=False)
        
            # Export all database records to JSON
        dicts = (
            df.astype(object)
            .where(pd.notna(df), None)
            .to_dict(orient="records")
    )

        with open(RAW_DATA_DIR / "jobs.json", "w", encoding="utf-8") as f:
            json.dump(dicts, f, indent=2, ensure_ascii=False)
        
        # # Export JSON directly with ensure_ascii=False for clean URLs
        # dicts = [job.model_dump() for job in jobs]
        # with open(RAW_DATA_DIR / "jobs.json", "w", encoding="utf-8") as f:
        #     json.dump(dicts, f, indent=2, ensure_ascii=False)

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def save_extraction(self, extracted: ExtractedJD):
        """Saves or updates LLM extraction results."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO extractions (
                    job_id, extraction_status, schema_version, extracted_data, updated_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                extracted.job_id,
                extracted.extraction_status,
                extracted.schema_version,
                extracted.model_dump_json(),
                datetime.utcnow().isoformat()
            ))
            conn.commit()

    def get_extraction(self, job_id: str) -> Optional[ExtractedJD]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT extracted_data FROM extractions WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row and row["extracted_data"]:
                data = json.loads(row["extracted_data"])
                return ExtractedJD(**data)
        return None