from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from agent.config import Settings
from agent.models import PresentationSpec
from agent.ollama_client import OllamaClient
from agent.slide_planner import SlidePlanner
from presentation.generator import PresentationGenerator, safe_filename
from presentation.validator import ValidationResult, validate_presentation


@dataclass(frozen=True)
class GenerationResult:
    output_path: Path
    plan: PresentationSpec
    validation: ValidationResult


def build_request(
    prompt: str,
    *,
    slide_count: int | None = None,
    audience: str = "",
    source_information: str = "",
) -> str:
    parts = [prompt.strip()]
    if audience.strip():
        parts.append(f"The audience is {audience.strip()}.")
    if source_information.strip():
        parts.append(
            "Use the following user-provided information as the factual source. "
            "Preserve all numeric values and units exactly:\n"
            f"{source_information.strip()}"
        )
    return " ".join(part for part in parts if part)


def generate_presentation(
    prompt: str,
    *,
    slide_count: int | None = None,
    audience: str = "",
    source_information: str = "",
    settings: Settings | None = None,
) -> GenerationResult:
    if not prompt.strip():
        raise ValueError("A presentation request is required.")

    active_settings = settings or Settings.from_environment()
    client = OllamaClient(
        host=active_settings.ollama_host,
        model=active_settings.ollama_model,
        timeout_seconds=active_settings.ollama_timeout_seconds,
    )
    plan = SlidePlanner(client).create_plan(
        build_request(prompt, audience=audience, source_information=source_information),
        slide_count=slide_count,
    )

    active_settings.output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(plan.title).removesuffix(".pptx")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = active_settings.output_dir / f"{stem}-{timestamp}.pptx"

    PresentationGenerator().generate(plan, output_path)
    validation = validate_presentation(output_path, expected_slides=len(plan.slides))
    return GenerationResult(output_path=output_path, plan=plan, validation=validation)
