from presentation_service import build_request


def test_build_request_adds_audience_without_duplicating_slide_count() -> None:
    request = build_request(
        "Explain quantum computing.",
        slide_count=7,
        audience="First-year university students",
    )

    assert "Explain quantum computing." in request
    assert "exactly 7 slides" not in request
    assert "First-year university students" in request


def test_build_request_includes_user_data_verbatim() -> None:
    request = build_request(
        "Create a production report.",
        source_information="2022: 120 units; 2023: 145 units",
    )
    assert "2022: 120 units; 2023: 145 units" in request
    assert "Preserve all numeric values and units exactly" in request
