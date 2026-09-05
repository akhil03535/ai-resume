from app.analysis import scoring


def test_normalize_strips_punctuation_and_case():
    # apostrophes and punctuation become whitespace, then collapse
    assert scoring.normalize("REST API's!!") == "rest api s"
    assert scoring.normalize("  C++   Developer  ") == "c++ developer"


def test_exact_skill_match_returns_matched():
    status, score = scoring.classify_requirement_match("Kafka", ["Kafka", "Java"], "some resume text")
    assert status == "MATCHED"
    assert score == 1.0


def test_missing_skill_with_no_overlap_returns_missing():
    status, score = scoring.classify_requirement_match(
        "Kubernetes", ["Java", "Spring Boot", "MySQL"], "Built REST services with Spring Boot and MySQL."
    )
    assert status == "MISSING"


def test_production_matching_uses_lexical_fallback_without_loading_embedder(monkeypatch):
    monkeypatch.setattr(scoring.settings, "ENV", "production")
    scoring._get_embedder.cache_clear()

    def fail_heavy_import(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise AssertionError("SentenceTransformer must not load in production")
        return original_import(name, *args, **kwargs)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fail_heavy_import)

    try:
        assert scoring.semantic_similarity("Python API", "Python API") == 1.0
    finally:
        scoring._get_embedder.cache_clear()


def test_related_phrase_can_partially_or_fully_match():
    status, score = scoring.classify_requirement_match(
        "REST API development",
        ["Spring Boot", "Java"],
        "Built RESTful services and APIs using Spring Boot for a banking platform.",
    )
    assert status in ("MATCHED", "PARTIAL")


def test_ats_components_weighted_sum_is_consistent():
    components = scoring.compute_ats_components(
        required_match_ratio=1.0,
        preferred_match_ratio=1.0,
        keyword_coverage_ratio=1.0,
        experience_relevance_ratio=1.0,
        project_relevance_ratio=1.0,
        section_completeness_ratio=1.0,
        formatting_ratio=1.0,
        education_alignment_ratio=1.0,
    )
    assert components["final_score"] == 100


def test_ats_score_zero_when_everything_missing():
    components = scoring.compute_ats_components(0, 0, 0, 0, 0, 0, 0, 0)
    assert components["final_score"] == 0
