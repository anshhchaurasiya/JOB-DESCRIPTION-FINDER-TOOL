from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from src.storage import StorageManager
from config.settings import SQLITE_DB_PATH

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



database_manager = StorageManager(db_path=SQLITE_DB_PATH)


@app.get("/api/jobs")
def get_jobs():
    conn=database_manager._get_connection()
    cursor = conn.cursor()
    
    # Adjust 'jobs' if your table has a different name
    cursor.execute("SELECT * FROM jobs ORDER BY collection_timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    jobs_list = [dict(row) for row in rows]
    return jobs_list