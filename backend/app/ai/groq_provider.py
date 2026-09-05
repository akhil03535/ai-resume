import json
import logging
import re

import groq
from groq import Groq
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.common.exceptions import AIProviderError
from app.ai.base import AIProvider
from app.ai.schemas import AnalyzedJobDescription, BulletImprovement, ParsedResume

logger = logging.getLogger("resumeai.ai")

# Every prompt repeats these ground rules. This is the single most important
# instruction in the whole AI layer (spec #2, #34): never fabricate facts.
ANTI_FABRICATION_RULE = (
    "You must use ONLY the facts explicitly present in the provided text. "
    "Never invent skills, employers, job titles, dates, metrics, certifications, "
    "or achievements. If a field is not present in the source text, leave it null "
    "or omit it - do not guess or generalize. Distinguish clearly between what is "
    "known and what is unknown."
)


def _classify_groq_error(exc: Exception, model: str) -> tuple[str, str, str]:
    """Classifies a Groq SDK exception into (code, log_tag, user_message).

    `code` is a machine-readable category returned in the API's error JSON
    (error.code) so the frontend/developer can distinguish failure types
    without parsing prose - this is what item #4 asks for: MISSING_API_KEY,
    INVALID_API_KEY, etc. as actual response codes, not just log text.

    `user_message` stays deliberately generic/safe for anything that could
    hint at infrastructure details; only the missing-key case gets a more
    specific (but still secret-free) message, since that's an admin
    configuration problem, not a transient failure the user should "just
    retry".
    """
    status_code = getattr(exc, "status_code", None)
    body = getattr(exc, "body", None)
    log_ctx = f"model={model!r} status_code={status_code} body={body}"
    retry_msg = "The AI service is temporarily unavailable. Please try again."

    if not settings.GROQ_API_KEY:
        return ("ai_missing_api_key", f"[A - MISSING API KEY] GROQ_API_KEY is empty. {log_ctx}",
                "The AI service is not configured (missing GROQ_API_KEY). Please contact your administrator.")
    if isinstance(exc, groq.AuthenticationError):
        return ("ai_invalid_api_key", f"[B - INVALID API KEY / 401] Groq rejected the API key as invalid or expired. {log_ctx}", retry_msg)
    if isinstance(exc, groq.PermissionDeniedError):
        return ("ai_forbidden", f"[C - FORBIDDEN / 403] Key is valid but lacks permission for this model/action. {log_ctx}", retry_msg)
    if isinstance(exc, groq.RateLimitError):
        return ("ai_rate_limited", f"[D - RATE LIMIT / 429] Groq account or model rate limit exceeded. {log_ctx}",
                "The AI service is receiving too many requests right now. Please try again in a moment.")
    if isinstance(exc, groq.NotFoundError):
        return ("ai_invalid_model", f"[G - INVALID MODEL / 404] AI_MODEL={model!r} was not found on Groq - check for typos or a retired model name. {log_ctx}", retry_msg)
    if isinstance(exc, groq.APITimeoutError):
        return ("ai_timeout", f"[F - TIMEOUT] Request to Groq timed out. {log_ctx}",
                "The AI service took too long to respond. Please try again.")
    if isinstance(exc, groq.APIConnectionError):
        return ("ai_network_error", f"[E - NETWORK FAILURE] Could not reach Groq's API (DNS/TLS/connection refused/egress blocked). {log_ctx}", retry_msg)
    if isinstance(exc, groq.BadRequestError):
        return ("ai_bad_request", f"[J - BAD REQUEST / 400] Groq rejected the request shape (check response_format/model support for JSON mode). {log_ctx}", retry_msg)
    if isinstance(exc, groq.InternalServerError):
        return ("ai_provider_error", f"[J - GROQ INTERNAL ERROR / 5xx] Groq's own service returned a server error. {log_ctx}", retry_msg)
    if isinstance(exc, groq.APIStatusError):
        return ("ai_provider_error", f"[J - UNKNOWN PROVIDER ERROR] Unclassified Groq API status error. {log_ctx}", retry_msg)
    return ("ai_unknown_error", f"[J - UNKNOWN PROVIDER ERROR] {type(exc).__name__}: {exc} | {log_ctx}", retry_msg)


class GroqProvider(AIProvider):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning(
                "GROQ_API_KEY is empty. Every AI call will fail immediately. "
                "Set a real key in backend/.env (see .env.example)."
            )
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.AI_MODEL

    def _chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=settings.AI_TEMPERATURE,
                # NOTE: "json_object" mode works but is, per the Groq SDK's
                # own docs, "an older method... json_schema is recommended
                # for models that support it." Not switched to json_schema
                # here deliberately: this couldn't be tested against the
                # real API in this environment (no network access to Groq),
                # and an untested response_format change risks introducing
                # a new, harder-to-diagnose failure mode. See README for
                # this as a documented follow-up recommendation.
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw = response.choices[0].message.content
            return self._parse_json_defensively(raw)
        except AIProviderError:
            raise
        except Exception as exc:
            code, log_line, user_message = _classify_groq_error(exc, self.model)
            logger.error(log_line)
            raise AIProviderError(user_message, code=code)

    @staticmethod
    def _parse_json_defensively(raw: str | None) -> dict:
        """Groq's json_object mode is usually reliable, but we never trust a
        vendor's output blindly (spec #5/#34). Handles: empty responses,
        markdown code-fence wrapping (```json ... ```), leading/trailing
        prose the model sometimes adds despite instructions, and plain
        malformed JSON - all surfaced as a clean AIProviderError rather than
        an unhandled crash."""
        if not raw or not raw.strip():
            logger.error("[AI FAILURE: H - MALFORMED RESPONSE] Groq returned an empty response body.")
            raise AIProviderError("The AI service returned an empty response. Please try again.", code="ai_bad_response")

        text = raw.strip()

        # Strip ```json ... ``` or ``` ... ``` fences if present.
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Last resort: extract the first {...} block in case the model added
        # commentary before/after the JSON despite instructions not to.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        logger.error("[AI FAILURE: H - MALFORMED RESPONSE] Groq returned JSON that could not be recovered: %r", raw[:500])
        raise AIProviderError("The AI service returned an unexpected response. Please try again.", code="ai_bad_response")

    @retry(stop=stop_after_attempt(settings.AI_MAX_RETRIES), wait=wait_fixed(1), reraise=True)
    def parse_resume(self, raw_text: str) -> ParsedResume:
        system = (
            f"You are a resume parsing engine. {ANTI_FABRICATION_RULE} "
            "Return a single JSON object matching this schema exactly: "
            "{personal_information: {full_name, email, phone, location, headline, summary}, "
            "education: [{institution, degree, field_of_study, start_date, end_date, gpa}], "
            "experience: [{company, title, location, start_date, end_date, is_current, bullets, technologies}], "
            "projects: [{name, description, bullets, technologies, url}], "
            "skills: [string], "
            "certifications: [{name, issuer, issue_date}], "
            "achievements: [{title, description}], "
            "links: [{label, url}]}"
        )
        data = self._chat_json(system, raw_text)
        try:
            return ParsedResume.model_validate(data)
        except ValidationError as exc:
            logger.error("[AI FAILURE: I - PYDANTIC VALIDATION FAILURE] Resume parse output did not match ParsedResume schema: %s", exc)
            raise AIProviderError("Couldn't reliably parse this resume. Please review the extracted fields manually.", code="ai_schema_error")

    @retry(stop=stop_after_attempt(settings.AI_MAX_RETRIES), wait=wait_fixed(1), reraise=True)
    def analyze_job_description(self, raw_text: str) -> AnalyzedJobDescription:
        system = (
            "You are a job description analysis engine. Extract structured requirements. "
            "Classify each requirement's importance as 'required' or 'preferred' based on the "
            "language used (e.g. 'must have' vs 'nice to have'). Separate skills, technologies, "
            "and general keywords. Return a single JSON object matching this schema exactly: "
            "{role_title, domain, experience_requirement, education_requirement, "
            "responsibilities: [string], "
            "requirements: [{label, type: 'skill'|'technology'|'keyword', importance: 'required'|'preferred'}]}"
        )
        data = self._chat_json(system, raw_text)
        try:
            return AnalyzedJobDescription.model_validate(data)
        except ValidationError as exc:
            logger.error("[AI FAILURE: I - PYDANTIC VALIDATION FAILURE] JD analysis output did not match AnalyzedJobDescription schema: %s", exc)
            raise AIProviderError("Couldn't reliably analyze this job description. Please try again.", code="ai_schema_error")

    @retry(stop=stop_after_attempt(settings.AI_MAX_RETRIES), wait=wait_fixed(1), reraise=True)
    def improve_bullet(self, bullet_text: str, mode: str, context: str | None = None) -> BulletImprovement:
        mode_instructions = {
            "improve": "Improve clarity and professional tone.",
            "concise": "Make it significantly more concise while keeping all facts.",
            "ats_friendly": "Rewrite using strong action verbs and standard ATS-parseable phrasing.",
            "technical": "Sharpen technical wording and terminology precision.",
            "impact": "Emphasize the impact and outcome, but ONLY using numbers/results already stated.",
        }
        instruction = mode_instructions.get(mode, mode_instructions["improve"])
        system = (
            f"You rewrite a single resume bullet point. {instruction} "
            f"{ANTI_FABRICATION_RULE} Do not add metrics, percentages, or outcomes that were not "
            "already present in the original text. Return JSON: {improved_text, notes}."
        )
        user = f"Original bullet: {bullet_text}"
        if context:
            user += f"\nRelevant job context: {context}"
        data = self._chat_json(system, user)
        try:
            return BulletImprovement.model_validate(data)
        except ValidationError as exc:
            logger.error("[AI FAILURE: I - PYDANTIC VALIDATION FAILURE] Bullet improvement output did not match BulletImprovement schema: %s", exc)
            raise AIProviderError("Couldn't improve this bullet right now. Please try again.", code="ai_schema_error")

    @retry(stop=stop_after_attempt(settings.AI_MAX_RETRIES), wait=wait_fixed(1), reraise=True)
    def generate_summary(self, profile_facts: dict, jd_context: dict) -> str:
        system = (
            f"You write a 2-4 sentence professional resume summary. {ANTI_FABRICATION_RULE} "
            "Use only the facts given in 'profile_facts'. Prioritize aspects relevant to 'jd_context' "
            "but do not claim experience with anything not listed in profile_facts. "
            "Return JSON: {summary: string}."
        )
        user = json.dumps({"profile_facts": profile_facts, "jd_context": jd_context})
        data = self._chat_json(system, user)
        return data.get("summary", "").strip()
