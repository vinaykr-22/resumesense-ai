"""
V2 Schema Tests
================
Validates that V2 Pydantic models work correctly with both
minimal and full data, and that V1 data is backward-compatible.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.schemas import (
    ATSScoreBreakdown,
    RewrittenBullet,
    AnalysisResponse,
    JobMatchResponse,
    LearningPathResponse,
    ResumeUploadResponse,
    ResumeStatusResponse,
)


# ── ATSScoreBreakdown ──────────────────────────

class TestATSScoreBreakdown:
    def test_defaults(self):
        b = ATSScoreBreakdown()
        assert b.keyword_score == 0.0
        assert b.section_completeness == 0.0
        assert b.bullet_strength == 0.0
        assert b.formatting_score == 0.0

    def test_full_data(self):
        b = ATSScoreBreakdown(
            keyword_score=85.5,
            section_completeness=90.0,
            bullet_strength=72.3,
            formatting_score=95.0,
        )
        assert b.keyword_score == 85.5


# ── RewrittenBullet ────────────────────────────

class TestRewrittenBullet:
    def test_minimal(self):
        rb = RewrittenBullet(original="Did stuff", rewritten="Led cross-functional initiative")
        assert rb.improvement_reason is None

    def test_full(self):
        rb = RewrittenBullet(
            original="Did stuff",
            rewritten="Led cross-functional initiative resulting in 20% efficiency gain",
            improvement_reason="Added quantifiable impact",
        )
        assert rb.improvement_reason == "Added quantifiable impact"


# ── AnalysisResponse ───────────────────────────

class TestAnalysisResponse:
    def test_minimal(self):
        """V1 result data (no V2 fields) should parse with defaults."""
        ar = AnalysisResponse(resume_id="res_abc123")
        assert ar.ats_score == 0.0
        assert ar.ats_breakdown.keyword_score == 0.0
        assert ar.weak_bullets == []
        assert ar.rewritten_bullets == []
        assert ar.extracted_skills == []
        assert ar.job_match_data == {}
        assert ar.learning_path == {}

    def test_full_data(self):
        ar = AnalysisResponse(
            resume_id="res_abc123",
            ats_score=78.5,
            ats_breakdown=ATSScoreBreakdown(keyword_score=80.0),
            weak_bullets=["Did stuff"],
            rewritten_bullets=[
                RewrittenBullet(original="Did stuff", rewritten="Achieved 20% gain")
            ],
            extracted_skills=["Python", "FastAPI"],
            job_match_data={"top_match": "Software Engineer"},
            learning_path={"courses": ["Advanced Python"]},
        )
        assert ar.ats_score == 78.5
        assert len(ar.rewritten_bullets) == 1
        assert ar.extracted_skills == ["Python", "FastAPI"]

    def test_backward_compat_v1_result(self):
        """Simulate parsing a V1 result dict that lacks V2 analysis_data fields."""
        v1_data = {"resume_id": "res_old123"}
        ar = AnalysisResponse(**v1_data)
        assert ar.ats_score == 0.0
        assert ar.extracted_skills == []


# ── JobMatchResponse ───────────────────────────

class TestJobMatchResponse:
    def test_defaults(self):
        jm = JobMatchResponse(resume_id="res_abc")
        assert jm.matches == []
        assert jm.total == 0
        assert jm.generated_at is None


# ── LearningPathResponse ──────────────────────

class TestLearningPathResponse:
    def test_defaults(self):
        lp = LearningPathResponse(resume_id="res_abc")
        assert lp.courses == []
        assert lp.certifications == []
        assert lp.estimated_duration_weeks is None


# ── ResumeUploadResponse ──────────────────────

class TestResumeUploadResponse:
    def test_v2_upload(self):
        r = ResumeUploadResponse(
            resume_id="res_abc",
            job_id="res_abc",
            filename="test.pdf",
            char_count=5000,
        )
        assert r.version == 2
        assert r.status == "processing"


# ── ResumeStatusResponse ─────────────────────

class TestResumeStatusResponse:
    def test_completed(self):
        s = ResumeStatusResponse(
            status="completed",
            stage_label="Processing complete",
            progress=100,
            result={"resume_id": "res_abc", "skills": {}},
        )
        assert s.error is None

    def test_failed(self):
        s = ResumeStatusResponse(status="failed", error="Timeout")
        assert s.progress == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
