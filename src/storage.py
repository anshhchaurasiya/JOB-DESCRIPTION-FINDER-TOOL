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
        """Initializes SQLite tables for raw jobs and extractions."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    job_url TEXT,
                    source TEXT,
                    raw_description TEXT,
                    date_posted TEXT,
                    salary_string TEXT,
                    employment_type TEXT,
                    experience_requirements TEXT,
                    collection_timestamp TEXT,
                    source_job_id TEXT
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
                            job_id, title, company, location, job_url, source, 
                            raw_description, date_posted, salary_string, 
                            employment_type, experience_requirements, 
                            collection_timestamp, source_job_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job.job_id, job.title, job.company, job.location, job.job_url, job.source,
                        job.raw_description, job.date_posted, job.salary_string,
                        job.employment_type, job.experience_requirements,
                        job.collection_timestamp, job.source_job_id
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving job {job.job_id}: {e}")
            conn.commit()
        
        # Also export raw dataset snapshot to CSV
        self.export_raw_csv()
        return saved_count

    def export_raw_csv(self):
        """Exports all raw jobs to data/raw/jobs.csv"""
        with self._get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM jobs", conn)
        df.to_csv(RAW_DATA_DIR / "jobs.csv", index=False)
        df.to_json(RAW_DATA_DIR / "jobs.json", orient="records", indent=2)

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