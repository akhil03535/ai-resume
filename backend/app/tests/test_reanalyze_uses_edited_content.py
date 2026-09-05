import uuid

from app.users.models import User
from app.profiles.models import CandidateProfile
from app.profiles.service import add_candidate_skill
from app.profiles.models import SkillSource, SkillVerificationStatus
from app.jobs.models import JobDescription, JobRequirement, RequirementType, RequirementImportance
from app.resumes.models import GeneratedResume
from app.analysis.scoring import normalize
from app.analysis import service as analysis_service


def _seed(db_session):
    user = User(id=uuid.uuid4(), email="editor@example.com", hashed_password="x", full_name="Editor Test")
    db_session.add(user)
    db_session.flush()
    profile = CandidateProfile(id=uuid.uuid4(), user_id=user.id, summary="Backend engineer.")
    db_session.add(profile)
    db_session.flush()

    # Candidate profile only has Java - Kubernetes is nowhere in the profile.
    add_candidate_skill(db_session, profile, "Java", source=SkillSource.MANUAL, verification_status=SkillVerificationStatus.VERIFIED)
    db_session.flush()

    jd = JobDescription(
        id=uuid.uuid4(), user_id=user.id, title="Platform Engineer",
        raw_text="Looking for a Platform Engineer with Java and Kubernetes experience.",
        is_analyzed=True,
    )
    db_session.add(jd)
    db_session.flush()
    for label, rtype in [("Java", "SKILL"), ("Kubernetes", "SKILL")]:
        db_session.add(JobRequirement(
            job_description_id=jd.id, label=label, normalized_label=normalize(label),
            requirement_type=RequirementType(rtype), importance=RequirementImportance.REQUIRED,
        ))
    db_session.flush()

    generated = GeneratedResume(
        id=uuid.uuid4(), user_id=user.id, job_description_id=jd.id,
        version_name="v1",
        content={
            "personal_information": {"full_name": "Editor Test"},
            "summary": "Backend engineer.",
            "skills": ["Java"],  # Kubernetes not yet on the document
            "technical_exposure": [],
            "experience": [], "projects": [], "education": [],
            "certifications": [], "achievements": [], "links": [],
        },
    )
    db_session.add(generated)
    db_session.flush()
    return user, profile, jd, generated


def test_reanalyze_scores_edited_resume_content_not_stale_profile(db_session):
    """Reproduces the exact architectural bug flagged: re-analyzing a
    generated resume must score what's actually in GeneratedResume.content
    (which the editor mutates) - not silently re-derive from the candidate
    profile, which doesn't change when the user edits the resume document."""
    user, profile, jd, generated = _seed(db_session)

    # Before edit: Kubernetes is MISSING because it's not on the document
    # (even though this has nothing to do with the profile, which never
    # had Kubernetes either - both sides agree here, so we need a case
    # where they'd disagree to prove content is actually being read).
    analysis_before = analysis_service.run_analysis(
        db_session, user.id, jd.id, generated_resume_id=generated.id
    )
    kube_match = next(m for m in analysis_before.skill_matches if m.skill_label == "Kubernetes")
    assert kube_match.status == "MISSING"

    # Simulate the user editing the resume in the Editor: they add Kubernetes
    # to the document's skills list (e.g. after verifying it) WITHOUT this
    # ever touching the candidate_skills table / profile at all.
    generated.content = {**generated.content, "skills": ["Java", "Kubernetes"]}
    db_session.flush()

    analysis_after = analysis_service.run_analysis(
        db_session, user.id, jd.id, generated_resume_id=generated.id
    )
    kube_match_after = next(m for m in analysis_after.skill_matches if m.skill_label == "Kubernetes")

    # If this bug were still present, run_analysis would have silently
    # rebuilt from profile_to_dict(profile) - which still has no Kubernetes
    # anywhere - and this would incorrectly still read MISSING.
    assert kube_match_after.status == "MATCHED"
    assert analysis_after.ats_score > analysis_before.ats_score
