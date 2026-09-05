"""
Deterministic matching + scoring engine.

Per spec #12/#13, the LLM is never asked "give this resume a score" - all
scoring math happens here, in plain Python, using:
  1. normalized keyword matching (exact / substring / token overlap)
  2. semantic similarity (sentence-transformers embeddings, lazily loaded)
  3. verified candidate data (skills/verification_status)

Every weight lives in app.core.config so it's centralized, not scattered.
"""
import re
from difflib import SequenceMatcher
from functools import lru_cache

from app.core.config import settings

_STOPWORDS = {"a", "an", "the", "and", "or", "with", "for", "of", "in", "on", "to", "using"}


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s+#.]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@lru_cache
def _get_embedder():
    """Loaded lazily and cached - the model is ~80MB and we don't want to pay
    that cost on every request, only the first time it's actually needed."""
    if settings.ENV.lower() == "production":
        return None
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


def semantic_similarity(a: str, b: str) -> float:
    """Cosine similarity via sentence-transformers when available, otherwise
    a lexical fallback (SequenceMatcher on normalized token sets) so matching
    never hard-fails if the embedding model can't load."""
    embedder = _get_embedder()
    if embedder is not None:
        import numpy as np
        vectors = embedder.encode([a, b], normalize_embeddings=True)
        return float(np.dot(vectors[0], vectors[1]))
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def token_overlap_score(requirement: str, candidate_text: str) -> float:
    req_tokens = {t for t in normalize(requirement).split() if t not in _STOPWORDS}
    if not req_tokens:
        return 0.0
    candidate_norm = normalize(candidate_text)
    hits = sum(1 for t in req_tokens if t in candidate_norm)
    return hits / len(req_tokens)


MATCH_THRESHOLD = 0.82   # >= this -> MATCHED
PARTIAL_THRESHOLD = 0.55  # >= this -> PARTIAL, else MISSING


def classify_requirement_match(requirement_label: str, candidate_skill_labels: list[str], resume_text: str) -> tuple[str, float]:
    """Returns (status, similarity_score). Checks exact/substring match against
    verified candidate skills first (cheap + precise), then falls back to
    semantic similarity against the full resume text."""
    norm_req = normalize(requirement_label)

    # 1. exact / substring match against candidate's own skill list
    for skill in candidate_skill_labels:
        norm_skill = normalize(skill)
        if norm_req == norm_skill:
            return "MATCHED", 1.0
        if norm_req in norm_skill or norm_skill in norm_req:
            return "MATCHED", 0.95

    # 2. semantic similarity against the skill list (catches synonyms/rephrasing)
    best_skill_score = 0.0
    for skill in candidate_skill_labels:
        score = semantic_similarity(requirement_label, skill)
        best_skill_score = max(best_skill_score, score)

    # 3. token overlap against the full resume body (catches "Built RESTful
    #    services using Spring Boot" matching a requirement of "REST API development")
    overlap_score = token_overlap_score(requirement_label, resume_text)
    body_semantic_score = semantic_similarity(requirement_label, resume_text[:2000]) if resume_text else 0.0

    final_score = max(best_skill_score, overlap_score, body_semantic_score * 0.9)

    if final_score >= MATCH_THRESHOLD:
        return "MATCHED", final_score
    if final_score >= PARTIAL_THRESHOLD:
        return "PARTIAL", final_score
    return "MISSING", final_score


def compute_ats_components(
    required_match_ratio: float,
    preferred_match_ratio: float,
    keyword_coverage_ratio: float,
    experience_relevance_ratio: float,
    project_relevance_ratio: float,
    section_completeness_ratio: float,
    formatting_ratio: float,
    education_alignment_ratio: float,
) -> dict:
    """Each *_ratio is 0..1. Returns component scores (0-100) plus the
    weighted final ATS score, using centrally configured weights."""
    components = {
        "required_skills": round(required_match_ratio * 100),
        "preferred_skills": round(preferred_match_ratio * 100),
        "keywords": round(keyword_coverage_ratio * 100),
        "experience_relevance": round(experience_relevance_ratio * 100),
        "project_relevance": round(project_relevance_ratio * 100),
        "section_completeness": round(section_completeness_ratio * 100),
        "formatting": round(formatting_ratio * 100),
        "education_alignment": round(education_alignment_ratio * 100),
    }
    final = (
        required_match_ratio * settings.ATS_WEIGHT_REQUIRED_SKILLS
        + preferred_match_ratio * settings.ATS_WEIGHT_PREFERRED_SKILLS
        + keyword_coverage_ratio * settings.ATS_WEIGHT_KEYWORDS
        + experience_relevance_ratio * settings.ATS_WEIGHT_EXPERIENCE
        + project_relevance_ratio * settings.ATS_WEIGHT_PROJECTS
        + section_completeness_ratio * settings.ATS_WEIGHT_SECTION_COMPLETENESS
        + formatting_ratio * settings.ATS_WEIGHT_FORMATTING
        + education_alignment_ratio * settings.ATS_WEIGHT_EDUCATION
    )
    components["final_score"] = round(final * 100)
    return components


def compute_job_match_score(required_match_ratio: float, preferred_match_ratio: float, experience_relevance_ratio: float) -> int:
    """Job Match answers 'how well does this candidate fit THIS job' - weighted
    more heavily toward required skills than the general ATS score is."""
    score = required_match_ratio * 0.6 + preferred_match_ratio * 0.15 + experience_relevance_ratio * 0.25
    return round(score * 100)


def compute_section_completeness(profile_dict: dict) -> dict:
    """Returns 0-100 per section, used both for the radar chart and the
    'section_completeness' ATS component."""
    def score_list(items, min_expected=1):
        if not items:
            return 0
        return min(100, round(100 * min(len(items), min_expected * 3) / (min_expected * 3)))

    personal = profile_dict.get("personal_information", {}) or {}
    summary_score = 100 if (profile_dict.get("summary") or personal.get("summary")) else 0

    return {
        "summary": summary_score,
        "skills": score_list(profile_dict.get("skills", []), min_expected=5),
        "experience": score_list(profile_dict.get("experience", []), min_expected=2),
        "projects": score_list(profile_dict.get("projects", []), min_expected=1),
        "education": score_list(profile_dict.get("education", []), min_expected=1),
        "achievements": score_list(profile_dict.get("achievements", []), min_expected=1),
    }


def compute_formatting_score(resume_text: str) -> float:
    """Lightweight, deterministic heuristics for ATS formatting risk - not a
    layout parser, just cheap red flags (excessive special characters, no
    detectable section headers, extremely short content)."""
    if not resume_text:
        return 0.0
    length_ok = 1.0 if len(resume_text) > 400 else len(resume_text) / 400
    weird_char_ratio = len(re.findall(r"[^\x00-\x7F]", resume_text)) / max(len(resume_text), 1)
    weird_penalty = max(0.0, 1.0 - weird_char_ratio * 5)
    has_common_sections = any(
        kw in resume_text.lower() for kw in ["experience", "education", "skills"]
    )
    section_bonus = 1.0 if has_common_sections else 0.6
    return min(1.0, length_ok * 0.4 + weird_penalty * 0.3 + section_bonus * 0.3)
