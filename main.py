from __future__ import annotations

import logging
import sys

from agent.config import Settings
from agent.ollama_client import OllamaError
from presentation_service import generate_presentation


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger("presentation-agent")


def main() -> int:
    settings = Settings.from_environment()
    request = " ".join(sys.argv[1:]).strip()
    if not request:
        request = input("What presentation would you like?\n> ").strip()
    if not request:
        print("Please provide a presentation request.", file=sys.stderr)
        return 2

    try:
        LOGGER.info("Planning presentation with Ollama model %s", settings.ollama_model)
        generated = generate_presentation(request, settings=settings)
        if not generated.validation.valid:
            LOGGER.error("Presentation validation failed: %s", generated.validation.as_dict())
            return 1

        LOGGER.info("Validated %d slides", len(generated.plan.slides))
        LOGGER.info("Presentation saved to %s", generated.output_path.resolve())
        if generated.validation.issues:
            LOGGER.warning(
                "Generated with %d non-blocking validation warning(s)",
                len(generated.validation.issues),
            )
        return 0
    except OllamaError as exc:
        LOGGER.error("%s", exc)
        return 1
    except Exception:
        LOGGER.exception("Presentation generation failed unexpectedly")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
