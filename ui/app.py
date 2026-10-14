import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

import streamlit as st
import pandas as pd
from config.settings import PROCESSED_DATA_DIR, RAW_DATA_DIR
from src.scraper import JobScraperService
from src.extractor import JDExtractorService
from src.aggregator import MarketAggregator
from src.models import CandidateProfile

st.set_page_config(
    page_title="AI Engineer JD Market Intelligence Tool",
    page_icon="🤖",
    layout="wide"
)

candidate = CandidateProfile()

# --- Sidebar Controls ---
st.sidebar.header("🔍 Search & Target Settings")
search_term = st.sidebar.text_input("Job Keyword", value="Full-Stack AI Engineer")
location = st.sidebar.text_input("Location", value="India")
results_limit = st.sidebar.slider("Jobs per Board Limit", 5, 50, 15)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Candidate Baseline (Rakesh)")
st.sidebar.write(f"**Target LPA:** {candidate.target_salary_lpa}+ LPA")
st.sidebar.write(f"**Core Skills:** {', '.join(candidate.baseline_skills)}")

run_button = st.sidebar.button("🚀 Run Full Pipeline (Scrape + Extract + Report)")

# --- Main Dashboard ---
st.title("🤖 Full-Stack AI Engineer JD Market Intelligence Dashboard")
st.markdown("Automated market intelligence tool helping target **10+ LPA** roles with evidence-based insights.")

if run_button:
    with st.spinner("Scraping job listings, running LLM extraction, and generating market intelligence..."):
        scraper = JobScraperService()
        jobs = scraper.fetch_jobs(search_term=search_term, location=location, results_wanted=results_limit)
        
        extractor = JDExtractorService()
        for job in jobs:
            extractor.extract_job(job)
            
        aggregator = MarketAggregator()
        aggregator.generate_market_report()
        st.success("Pipeline executed successfully!")

# --- Load Processed Artifacts if Available ---
report_md_path = PROCESSED_DATA_DIR / "market_report.md"
skills_csv_path = PROCESSED_DATA_DIR / "skill_demand.csv"
analyses_json_path = PROCESSED_DATA_DIR / "analyses.json"

col1, col2, col3 = st.columns(3)

raw_jobs_df = pd.read_csv(RAW_DATA_DIR / "jobs.csv") if (RAW_DATA_DIR / "jobs.csv").exists() else pd.DataFrame()
analyzed_df = pd.read_json(analyses_json_path) if analyses_json_path.exists() else pd.DataFrame()

col1.metric("Total Jobs Collected", len(raw_jobs_df))
col2.metric("Successfully Analyzed", len(analyzed_df) if not analyzed_df.empty else 0)
col3.metric("Target Salary", "10+ LPA")

st.markdown("---")

if skills_csv_path.exists():
    st.subheader("🔥 Top Demanded Technical Skills")
    df_skills = pd.read_csv(skills_csv_path)
    st.bar_chart(df_skills.set_index("skill")["demand_percentage"])
    st.dataframe(df_skills, width="stretch")

if report_md_path.exists():
    st.markdown("---")
    st.subheader("📋 Generated Market Intelligence Report")
    with open(report_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    st.markdown(md_text)

    st.download_button(
        label="📥 Download Markdown Report",
        data=md_text,
        file_name="market_report.md",
        mime="text/markdown"
    )