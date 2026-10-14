import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import PROCESSED_DATA_DIR
from src.storage import StorageManager
from src.models import CandidateProfile, ExtractedJD, CandidateGapAnalysis

class MarketAggregator:
    def __init__(self, storage_manager: Optional[StorageManager] = None):
        self.storage = storage_manager or StorageManager()
        self.candidate = CandidateProfile()

    def generate_market_report(self) -> Dict[str, Any]:
        """
        Aggregates deduplicated job extractions, computes skill demand percentages,
        analyzes salaries, calculates candidate gaps, and exports artifacts.
        """
        raw_jobs = self.storage.get_all_jobs()
        total_collected = len(raw_jobs)
        
        analyzed_jobs: List[ExtractedJD] = []
        failed_count = 0

        for job in raw_jobs:
            extraction = self.storage.get_extraction(job["job_id"])
            if extraction and extraction.extraction_status == "success":
                analyzed_jobs.append(extraction)
            else:
                failed_count += 1

        total_analyzed = len(analyzed_jobs)
        if total_analyzed == 0:
            print("[!] No successfully analyzed jobs available for aggregation.")
            return {"total_collected": total_collected, "total_analyzed": 0}

        # --- 1. Skill Frequency & Demand Aggregation ---
        skill_counts: Dict[str, int] = {}
        framework_counts: Dict[str, int] = {}
        vector_db_counts: Dict[str, int] = {}
        llm_framework_counts: Dict[str, int] = {}

        for jd in analyzed_jobs:
            # Combine skills for general frequency
            all_job_skills = set(
                jd.technical_skills + 
                jd.programming_languages + 
                jd.backend_frameworks + 
                jd.frontend_frameworks + 
                jd.ai_ml_frameworks + 
                jd.llm_frameworks + 
                jd.vector_databases + 
                jd.cloud_platforms + 
                jd.devops_tools + 
                jd.databases +
                jd.required_skills
            )
            for skill in all_job_skills:
                norm_skill = skill.strip().title()
                skill_counts[norm_skill] = skill_counts.get(norm_skill, 0) + 1

            for fw in jd.backend_frameworks + jd.frontend_frameworks + jd.ai_ml_frameworks:
                norm_fw = fw.strip().title()
                framework_counts[norm_fw] = framework_counts.get(norm_fw, 0) + 1

            for llm_fw in jd.llm_frameworks:
                norm_llm = llm_fw.strip().title()
                llm_framework_counts[norm_llm] = llm_framework_counts.get(norm_llm, 0) + 1

            for vdb in jd.vector_databases:
                norm_vdb = vdb.strip().title()
                vector_db_counts[norm_vdb] = vector_db_counts.get(norm_vdb, 0) + 1

        # Calculate percentages (Denominator = total_analyzed)
        def compute_percentages(counts: Dict[str, int]) -> List[Dict[str, Any]]:
            items = []
            for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                percentage = round((count / total_analyzed) * 100, 2)
                items.append({"skill": name, "count": count, "demand_percentage": percentage})
            return items

        top_skills = compute_percentages(skill_counts)[:15]
        top_frameworks = compute_percentages(framework_counts)
        top_llm_frameworks = compute_percentages(llm_framework_counts)
        top_vector_dbs = compute_percentages(vector_db_counts)

        # --- 2. Candidate Gap Analysis ---
        gap_analyses: List[Dict[str, Any]] = []
        baseline_lower = [s.lower() for s in self.candidate.baseline_skills]

        for jd in analyzed_jobs:
            req_skills = [s.strip() for s in jd.required_skills + jd.programming_languages + jd.backend_frameworks]
            pref_skills = [s.strip() for s in jd.preferred_skills + jd.llm_frameworks + jd.vector_databases]

            matched = [s for s in req_skills if s.lower() in baseline_lower or any(b in s.lower() for b in baseline_lower)]
            high_gaps = [s for s in req_skills if s.lower() not in baseline_lower and not any(b in s.lower() for b in baseline_lower)]
            sec_gaps = [s for s in pref_skills if s.lower() not in baseline_lower]

            coverage = round((len(matched) / max(len(req_skills), 1)) * 100, 2)

            gap_analyses.append({
                "job_id": jd.job_id,
                "matched_skills": matched,
                "high_priority_gaps": high_gaps,
                "secondary_gaps": sec_gaps,
                "coverage_score": coverage
            })

        # --- 3. Salary Analysis ---
        salaries = [jd.salary_min for jd in analyzed_jobs if jd.salary_min is not None]
        avg_salary = round(sum(salaries) / len(salaries), 2) if salaries else None

        # --- 4. Export CSV & JSON Artifacts ---
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Export analyses json
        analyses_data = [jd.model_dump() for jd in analyzed_jobs]
        with open(PROCESSED_DATA_DIR / "analyses.json", "w", encoding="utf-8") as f:
            json.dump(analyses_data, f, indent=2)

        # Export skill demand CSV
        df_skills = pd.DataFrame(top_skills)
        df_skills.to_csv(PROCESSED_DATA_DIR / "skill_demand.csv", index=False)

        # Export salary summary CSV
        df_salary = pd.DataFrame([{"analyzed_jobs_with_salary": len(salaries), "average_salary_min": avg_salary}])
        df_salary.to_csv(PROCESSED_DATA_DIR / "salary_summary.csv", index=False)

        # --- 5. Generate Markdown Report ---
        report_content = f"""# Market Intelligence Report: Full-Stack AI Engineer (10+ LPA Target)

## 📊 Executive Summary
- **Total Jobs Collected:** {total_collected}
- **Successfully Analyzed:** {total_analyzed}
- **Extraction Failures / Skipped:** {failed_count}
- **Target Candidate:** {self.candidate.name}
- **Target Role Categories:** {', '.join(self.candidate.target_roles)}

---

## 🔥 Top Technical Skills Demanded (Sample Size: {total_analyzed})
| Skill / Technology | Mentions | Demand Frequency (%) |
| :--- | :--- | :--- |
"""
        for item in top_skills[:10]:
            report_content += f"| {item['skill']} | {item['count']} | {item['demand_percentage']}% |\n"

        report_content += f"""
---

## 🤖 LLM & Generative AI Framework Demand
| Framework | Mentions | Demand Frequency (%) |
| :--- | :--- | :--- |
"""
        for item in top_llm_frameworks:
            report_content += f"| {item['skill']} | {item['count']} | {item['demand_percentage']}% |\n"

        report_content += f"""
---

## 🗄️ Vector Databases & Retrieval Technologies
| Vector Database | Mentions | Demand Frequency (%) |
| :--- | :--- | :--- |
"""
        for item in top_vector_dbs:
            report_content += f"| {item['skill']} | {item['count']} | {item['demand_percentage']}% |\n"

        report_content += f"""
---

## 🎯 Candidate Skill Gap Analysis (Rakesh Baseline vs. Market)
- **Baseline Profile:** {', '.join(self.candidate.baseline_skills)}
- **Average Skill Coverage Score:** {round(sum(g['coverage_score'] for g in gap_analyses) / max(len(gap_analyses), 1), 2)}%

### Top High-Priority Gaps to Close for 10+ LPA Roles:
"""
        all_high_gaps = [gaps for g in gap_analyses for gaps in g["high_priority_gaps"]]
        gap_freq = pd.Series(all_high_gaps).value_counts().head(5) if all_high_gaps else []
        for gap, count in gap_freq.items():
            report_content += f"- **{gap}** (Requested in {count} analyzed listings)\n"

        report_content += f"""
---
*Report generated automatically by JD Analysis Tool.*
"""

        with open(PROCESSED_DATA_DIR / "market_report.md", "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"[+] Market report and CSV/JSON artifacts successfully generated in {PROCESSED_DATA_DIR}")
        return {
            "total_collected": total_collected,
            "total_analyzed": total_analyzed,
            "top_skills": top_skills,
            "top_llm_frameworks": top_llm_frameworks,
            "top_vector_dbs": top_vector_dbs
        }