import time
import json
from typing import Optional
from google import genai
from google.genai import types
from config.settings import GEMINI_API_KEY, DEFAULT_MODEL_NAME
from src.models import JobRecord, ExtractedJD
from src.storage import StorageManager

class JDExtractorService:
    def __init__(self, storage_manager: Optional[StorageManager] = None):
        self.storage = storage_manager or StorageManager()
        if not GEMINI_API_KEY:
            print("[!] Warning: GEMINI_API_KEY is not set in environment or .env file.")
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

    def extract_job(self, job: JobRecord) -> Optional[ExtractedJD]:
        """
        Extracts structured requirements from raw job description using Gemini API with local Pydantic validation.
        """
        # 1. Check local cache first
        cached = self.storage.get_extraction(job.job_id)
        if cached and cached.extraction_status == "success":
            return cached

        if not self.client:
            print(f"[!] Cannot extract job {job.job_id}: Gemini API client not initialized.")
            return self._create_failed_extraction(job.job_id, "Missing GEMINI_API_KEY")

        if not job.raw_description or len(job.raw_description.strip()) < 20:
            print(f"[!] Job {job.job_id} has empty or insufficient description for extraction.")
            return self._create_failed_extraction(job.job_id, "Insufficient or empty job description")

        # Construct JSON schema template instructions for the prompt
        schema_example = ExtractedJD(job_id=job.job_id).model_dump_json(indent=2)

        prompt = f"""
You are an expert technical recruiter and AI systems architect analyzing job descriptions for a Full-Stack AI Engineer role targeting 10+ LPA.
Analyze the following Job Description carefully and output ONLY a valid JSON object matching this exact schema structure:

{schema_example}

CRITICAL EXTRACTION RULES:
1. Separate mandatory 'required_skills' from nice-to-have 'preferred_skills'.
2. Normalize technology aliases (e.g., Fast API -> FastAPI, Postgres -> PostgreSQL, LLM -> Large Language Model). Keep distinct tools separate (e.g., LangChain and LlamaIndex must remain separate).
3. Do NOT hallucinate technologies. If a tech is not explicitly mentioned or clearly implied by context, do not include it.
4. For every significant technology or requirement extracted, provide a short supporting excerpt from the text in the 'evidence' dictionary mapping (Key: technology name, Value: verbatim snippet).
5. Represent uncertainty honestly. Leave fields null or empty if data is unavailable. Do not fabricate salaries or experience.

JOB TITLE: {job.title}
COMPANY: {job.company}
LOCATION: {job.location}
RAW JOB DESCRIPTION:
{job.raw_description}
"""

        max_retries = 3
        backoff_factor = 2

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=DEFAULT_MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    )
                )

                response_text = response.text
                if response_text:
                    # Clean potential markdown block wrappers if present
                    cleaned_text = response_text.strip()
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:]
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3]
                    cleaned_text = cleaned_text.strip()

                    raw_dict = json.loads(cleaned_text)
                    raw_dict["job_id"] = job.job_id
                    raw_dict["extraction_status"] = "success"
                    raw_dict["schema_version"] = "1.0.0"

                    extracted = ExtractedJD(**raw_dict)
                    self.storage.save_extraction(extracted)
                    return extracted

            except Exception as e:
                print(f"[!] Extraction attempt {attempt + 1} failed for job {job.job_id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(backoff_factor ** attempt)
                else:
                    return self._create_failed_extraction(job.job_id, str(e))

        return self._create_failed_extraction(job.job_id, "Max retries exceeded")

    def _create_failed_extraction(self, job_id: str, reason: str) -> ExtractedJD:
            failed_obj = ExtractedJD(
                job_id=job_id,
                extraction_status="failed",
                extraction_error=reason,
                evidence=[]
            )
            self.storage.save_extraction(failed_obj)
            return failed_obj