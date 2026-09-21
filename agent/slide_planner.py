from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Optional

from pydantic import ValidationError

from .models import PresentationSpec
from .ollama_client import OllamaClient, OllamaError


SYSTEM_PROMPT = """You are a university presentation planner.
Return only JSON matching the supplied schema. Write concise, natural slide copy.
Do not fabricate statistics, sources, quotations, or current facts. When no research
has been provided, explain stable concepts without unsupported numbers.

The presentation uses a formal Knowledge Foundation university design system.
Choose slide types based on communication needs, not decoration. The first slide
must be type 'title'. Reserve the final slide exclusively for type 'closing', with
a short thank-you title in the presentation language and an optional subtitle.
Never place recommendations, findings, charts, bullets, or other substantive
content on the closing slide. When the topic benefits from a conclusion, place a
separate conclusion content slide immediately before the closing slide. For short
decks, combine earlier material so the final closing slide is still preserved.
The final slide must use exactly this structure:
{"type": "closing", "title": "Thank you", "subtitle": "Questions and discussion"}
Use 'agenda' only when it improves navigation. Use 'section' sparingly. Use
'quote' only when the user supplied a real quotation; otherwise do not use it.

Use a 'chart' slide when the user provides useful numeric data. Supported chart
types are bar, column, line, pie, and doughnut. Copy the user's labels, values,
units, and source note accurately. Never invent, estimate, complete, extrapolate,
or alter chart values. If the request contains no numeric data, do not create a
chart and do not fabricate illustrative numbers. Pie and doughnut charts must
contain exactly one series. Other chart types may contain up to four series.

For content slides, provide 2-5 concise bullets. Each bullet should express one
specific idea and normally stay below 18 words. Avoid marketing language, vague
claims, em dashes, semicolons, arrow characters, and repetitive three-part slogans.
Slide titles should directly name the subject. Do not include formatting instructions."""


def requested_slide_count(request: str) -> Optional[int]:
    match = re.search(r"\b(\d{1,2})\s*[- ]?slides?\b", request, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _is_thank_you_title(title: object) -> bool:
    if not isinstance(title, str):
        return False
    normalized = re.sub(r"[^a-z]+", " ", title.casefold()).strip()
    return normalized in {
        "thank you",
        "thanks",
        "danke",
        "vielen dank",
        "merci",
        "gracias",
    }


class SlidePlanner:
    def __init__(self, client: OllamaClient) -> None:
        self.client = client

    def create_plan(self, request: str, *, slide_count: Optional[int] = None) -> PresentationSpec:
        count = slide_count if slide_count is not None else requested_slide_count(request)
        count_instruction = (
            f"Create exactly {count} slides in total, including title and closing slides."
            if count
            else "Choose a concise slide count between 5 and 10, including title and closing slides."
        )
        user_prompt = f"""User request:
{request.strip()}

{count_instruction}
Create a coherent presentation for the audience stated or implied by the request.
The closing slide title should be appropriate for the request language."""

        schema = deepcopy(PresentationSpec.model_json_schema())
        if count is not None:
            slides_schema = schema["properties"]["slides"]
            slides_schema["minItems"] = count
            slides_schema["maxItems"] = count

        last_error: Optional[Exception] = None
        for attempt in range(3):
            current_prompt = user_prompt
            if attempt > 0:
                retry_requirements = [
                    "The previous plan was invalid. Return a corrected plan.",
                    "The first slide must be type 'title'.",
                    "The final slide must be type 'closing' and contain no bullets, chart, or quote.",
                    "Use the exact final slide title 'Thank you'.",
                    "Keep all recommendations and conclusions on slides before the closing slide.",
                ]
                if count is not None:
                    retry_requirements.append(
                        f"Return exactly {count} slide objects. Count them before responding."
                    )
                current_prompt += "\n\n" + "\n".join(retry_requirements)

            raw = self.client.chat_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=current_prompt,
                schema=schema,
            )
            try:
                plan_data = json.loads(raw)
                slides = plan_data.get("slides") if isinstance(plan_data, dict) else None
                if not isinstance(slides, list) or len(slides) < 2:
                    raise ValueError("the plan must contain at least two slides")
                if not isinstance(slides[0], dict) or slides[0].get("type") != "title":
                    raise ValueError("the first slide must use type 'title'")
                if not isinstance(slides[-1], dict) or slides[-1].get("type") != "closing":
                    raise ValueError("the final slide must use type 'closing'")
                if not _is_thank_you_title(slides[-1].get("title")):
                    raise ValueError("the final slide title must be 'Thank you'")
                plan = PresentationSpec.model_validate(plan_data)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    continue
                raise OllamaError(
                    f"The model returned invalid presentation data after retrying: {exc}"
                ) from exc

            if count is None or len(plan.slides) == count:
                return plan

        raise OllamaError(f"The model could not create a valid slide structure: {last_error}")
