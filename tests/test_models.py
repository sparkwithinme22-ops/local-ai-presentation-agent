import pytest
from pydantic import ValidationError

from agent.models import PresentationSpec


def test_valid_plan() -> None:
    plan = PresentationSpec.model_validate(
        {
            "title": "Quantum Computing",
            "audience": "First-year university students",
            "slides": [
                {"type": "title", "title": "Quantum Computing", "subtitle": "An introduction"},
                {"type": "content", "title": "Qubits", "bullets": ["A qubit stores quantum information"]},
                {"type": "closing", "title": "Thank you"},
            ],
        }
    )
    assert len(plan.slides) == 3


def test_plan_requires_closing_slide() -> None:
    with pytest.raises(ValidationError):
        PresentationSpec.model_validate(
            {
                "title": "Quantum Computing",
                "audience": "Students",
                "slides": [
                    {"type": "title", "title": "Quantum Computing"},
                    {"type": "content", "title": "Qubits", "bullets": ["One point"]},
                ],
            }
        )


def test_valid_chart_slide() -> None:
    plan = PresentationSpec.model_validate(
        {
            "title": "Production",
            "audience": "Managers",
            "slides": [
                {"type": "title", "title": "Production"},
                {
                    "type": "chart",
                    "title": "Annual output",
                    "chart": {
                        "type": "column",
                        "categories": ["2022", "2023", "2024"],
                        "series": [{"name": "Units", "values": [120, 145, 171]}],
                        "value_axis_title": "Units",
                        "source_note": "Internal production report",
                    },
                },
                {"type": "closing", "title": "Thank you"},
            ],
        }
    )
    assert plan.slides[1].chart is not None


def test_chart_rejects_mismatched_value_count() -> None:
    with pytest.raises(ValidationError):
        PresentationSpec.model_validate(
            {
                "title": "Production",
                "audience": "Managers",
                "slides": [
                    {"type": "title", "title": "Production"},
                    {
                        "type": "chart",
                        "title": "Annual output",
                        "chart": {
                            "type": "bar",
                            "categories": ["2023", "2024"],
                            "series": [{"name": "Units", "values": [145]}],
                        },
                    },
                    {"type": "closing", "title": "Thank you"},
                ],
            }
        )


def test_closing_slide_rejects_hidden_content() -> None:
    with pytest.raises(ValidationError):
        PresentationSpec.model_validate(
            {
                "title": "Energy assessment",
                "audience": "Engineers",
                "slides": [
                    {"type": "title", "title": "Energy assessment"},
                    {"type": "content", "title": "Conclusion", "bullets": ["Reduce idle load"]},
                    {
                        "type": "closing",
                        "title": "Thank you",
                        "bullets": ["This content would be hidden by the closing layout"],
                    },
                ],
            }
        )
