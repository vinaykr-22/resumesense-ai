from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any


# ──────────────────────────────────────────────
# Existing Auth Schemas (V1) — DO NOT REMOVE
# ──────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# ──────────────────────────────────────────────
# V2 Response Schemas
# ──────────────────────────────────────────────

class ATSScoreBreakdown(BaseModel):
    """Breakdown of ATS compatibility score."""
    keyword_score: float = 0.0
    section_completeness: float = 0.0
    bullet_strength: float = 0.0
    formatting_score: float = 0.0


class RewrittenBullet(BaseModel):
    """A weak bullet point paired with its improved rewrite."""
    original: str
    rewritten: str
    improvement_reason: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Full V2 analysis result stored under result:{resume_id} in Redis."""
    resume_id: str
    ats_score: float = 0.0
    ats_breakdown: ATSScoreBreakdown = ATSScoreBreakdown()
    weak_bullets: List[str] = []
    rewritten_bullets: List[RewrittenBullet] = []
    extracted_skills: List[str] = []
    job_match_data: Dict[str, Any] = {}
    learning_path: Dict[str, Any] = {}


class JobMatchResponse(BaseModel):
    """Response for job matching endpoint."""
    resume_id: str
    matches: List[Dict[str, Any]] = []
    total: int = 0
    generated_at: Optional[str] = None


class LearningPathResponse(BaseModel):
    """Recommended learning resources based on skill gaps."""
    resume_id: str
    target_role: Optional[str] = None
    courses: List[Dict[str, Any]] = []
    certifications: List[str] = []
    estimated_duration_weeks: Optional[int] = None


class ResumeUploadResponse(BaseModel):
    """Response returned after uploading a resume."""
    resume_id: str
    job_id: str
    filename: str
    char_count: int
    version: int = 2
    status: str = "processing"
    message: str = "Resume received. Analysis starting..."


class ResumeStatusResponse(BaseModel):
    """Response for resume processing status queries."""
    status: str
    stage_label: Optional[str] = None
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
