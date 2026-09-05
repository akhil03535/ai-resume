import os

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.templates.registry import get_template

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))


def render_resume_html(content: dict, template_slug: str) -> str:
    """content is the structured resume JSON: personal, summary, skills,
    experience, projects, education, certifications, achievements, links."""
    template_meta = get_template(template_slug)
    jinja_template = _env.get_template("resume.html.j2")
    return jinja_template.render(
        personal=content.get("personal_information", {}),
        summary=content.get("summary"),
        skills=content.get("skills", []),
        experience=content.get("experience", []),
        projects=content.get("projects", []),
        education=content.get("education", []),
        certifications=content.get("certifications", []),
        achievements=content.get("achievements", []),
        links=content.get("links", []),
        css_variant=template_meta["css_variant"],
    )


def render_resume_pdf(content: dict, template_slug: str) -> bytes:
    html_string = render_resume_html(content, template_slug)
    return HTML(string=html_string).write_pdf()
