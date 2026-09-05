"""
Templates are metadata + a shared Jinja2 renderer, not one-off hardcoded
generators per resume (spec #19). Each slug maps to a CSS variant applied
over the same semantic HTML structure, keeping every template ATS-safe
(single column reading order, no text-in-images, no tables for layout).
"""

TEMPLATES = {
    "ats_classic": {
        "name": "ATS Classic",
        "description": "Single-column, minimal, recruiter-friendly. Maximum ATS compatibility.",
        "css_variant": "classic",
        "is_ats_safe": True,
    },
    "modern_professional": {
        "name": "Modern Professional",
        "description": "Clean modern layout with restrained styling and professional typography.",
        "css_variant": "modern",
        "is_ats_safe": True,
    },
    "software_engineer": {
        "name": "Software Engineer",
        "description": "Technical focus with skills and projects emphasized, compact layout.",
        "css_variant": "technical",
        "is_ats_safe": True,
    },
}


def get_template(slug: str) -> dict:
    return TEMPLATES.get(slug, TEMPLATES["ats_classic"])


def list_templates() -> list[dict]:
    return [{"slug": slug, **meta} for slug, meta in TEMPLATES.items()]
