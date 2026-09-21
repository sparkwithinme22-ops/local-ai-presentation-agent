import json

from agent.slide_planner import SlidePlanner


def plan_json(slide_count: int) -> str:
    slides = [{"type": "title", "title": "Test"}]
    slides.extend(
        {"type": "content", "title": f"Slide {number}", "bullets": ["Point"]}
        for number in range(2, slide_count)
    )
    slides.append({"type": "closing", "title": "Thank you"})
    return json.dumps({"title": "Test", "audience": "Students", "slides": slides})


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0
        self.schemas = []

    def chat_json(self, **kwargs) -> str:
        self.calls += 1
        self.schemas.append(kwargs["schema"])
        return plan_json(6 if self.calls == 1 else 5)


def test_planner_retries_when_model_ignores_slide_count() -> None:
    client = FakeClient()
    plan = SlidePlanner(client).create_plan("Explain a topic", slide_count=5)

    assert len(plan.slides) == 5
    assert client.calls == 2
    assert client.schemas[0]["properties"]["slides"]["minItems"] == 5
    assert client.schemas[0]["properties"]["slides"]["maxItems"] == 5


class WrongEndpointsClient:
    def __init__(self) -> None:
        self.calls = 0

    def chat_json(self, **kwargs) -> str:
        self.calls += 1
        data = json.loads(plan_json(5))
        if self.calls == 1:
            data["slides"][0]["type"] = "content"
            data["slides"][0]["bullets"] = ["Incorrect model structure"]
            data["slides"][-1]["type"] = "content"
            data["slides"][-1]["bullets"] = ["Recommendations must not be discarded"]
        return json.dumps(data)


def test_planner_retries_invalid_endpoints_without_overwriting_content() -> None:
    client = WrongEndpointsClient()
    plan = SlidePlanner(client).create_plan("Explain a topic", slide_count=5)

    assert plan.slides[0].type.value == "title"
    assert plan.slides[-1].type.value == "closing"
    assert client.calls == 2


class WrongClosingTitleClient:
    def __init__(self) -> None:
        self.calls = 0

    def chat_json(self, **kwargs) -> str:
        self.calls += 1
        data = json.loads(plan_json(5))
        if self.calls < 3:
            data["slides"][-1]["title"] = "Recommended improvements"
        return json.dumps(data)


def test_planner_retries_until_final_slide_is_thank_you() -> None:
    client = WrongClosingTitleClient()
    plan = SlidePlanner(client).create_plan("Explain a topic", slide_count=5)

    assert plan.slides[-1].title == "Thank you"
    assert client.calls == 3
