from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

class JobRecord(BaseModel):
    job_id: str
    id: Optional[str] = None
    site: Optional[str] = None
    job_url: Optional[str] = None
    job_url_direct: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    date_posted: Optional[str] = None
    job_type: Optional[str] = None
    salary_source: Optional[str] = None
    interval: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    is_remote: Optional[bool] = None
    job_level: Optional[str] = None
    job_function: Optional[str] = None
    listing_type: Optional[str] = None
    emails: Optional[str] = None
    description: Optional[str] = None
    company_industry: Optional[str] = None
    company_url: Optional[str] = None
    company_logo: Optional[str] = None
    company_url_direct: Optional[str] = None
    company_addresses: Optional[str] = None
    company_num_employees: Optional[str] = None
    company_revenue: Optional[str] = None
    company_description: Optional[str] = None
    skills: Optional[str] = None
    experience_range: Optional[str] = None
    company_rating: Optional[float] = None
    company_reviews_count: Optional[int] = None
    vacancy_count: Optional[int] = None
    work_from_home_type: Optional[str] = None
    collection_timestamp: str
    @property
    def raw_description(self) -> Optional[str]:
            """Backward-compatibility alias for description."""
            return self.description

class EvidenceItem(BaseModel):
    technology: str
    snippet: str

class ExtractedJD(BaseModel):
    job_id: str
    role_category: Optional[str] = Field(None, description="e.g., Full-Stack AI Engineer, GenAI Developer")
    technical_skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    backend_frameworks: List[str] = Field(default_factory=list)
    frontend_frameworks: List[str] = Field(default_factory=list)
    ai_ml_frameworks: List[str] = Field(default_factory=list)
    llm_frameworks: List[str] = Field(default_factory=list)
    vector_databases: List[str] = Field(default_factory=list)
    cloud_platforms: List[str] = Field(default_factory=list)
    devops_tools: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    
    minimum_experience_years: Optional[float] = None
    maximum_experience_years: Optional[float] = None
    
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    
    employment_type: Optional[str] = None
    education_requirements: Optional[str] = None
    job_location: Optional[str] = None
    remote_policy: Optional[str] = Field(None, description="Remote, Hybrid, On-site")
    
    evidence: List[EvidenceItem] = Field(default_factory=list)
    
    extraction_status: Literal["success", "failed", "partial"] = "success"
    extraction_error: Optional[str] = None
    schema_version: str = "1.0.0"

    @field_validator("employment_type", "job_location", "remote_policy", mode="before")
    @classmethod
    def convert_lists_to_string(cls, value: Any) -> Any:
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        return value

    @field_validator("evidence", mode="before")
    @classmethod
    def convert_evidence(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return [{"technology": str(k), "snippet": str(v)} for k, v in value.items()]
        elif isinstance(value, list):
            normalized = []
            for item in value:
                if isinstance(item, dict):
                    tech = item.get("technology") or item.get("tech") or "general"
                    snip = item.get("snippet") or item.get("text") or str(item)
                    normalized.append({"technology": str(tech), "snippet": str(snip)})
                elif isinstance(item, str):
                    normalized.append({"technology": "general", "snippet": item})
            return normalized
        return []

class CandidateProfile(BaseModel):
    name: str = "Rakesh"
    target_roles: List[str] = Field(default_factory=lambda: [
        "Full-Stack AI Engineer", 
        "Python AI Engineer", 
        "Generative AI Engineer", 
        "AI Application Developer"
    ])
    baseline_skills: List[str] = Field(default_factory=lambda: [
        "Python", 
        "Django", 
        "React", 
        "Data Structures and Algorithms",
        "SQL",
        "Git"
    ])
    target_salary_lpa: float = 10.0
    locations: List[str] = Field(default_factory=lambda: ["India", "Bengaluru", "Hyderabad", "Pune", "Remote"])

class CandidateGapAnalysis(BaseModel):
    job_id: str
    matched_skills: List[str] = Field(default_factory=list)
    high_priority_gaps: List[str] = Field(default_factory=list)
    secondary_gaps: List[str] = Field(default_factory=list)
    coverage_score: float = Field(0.0)