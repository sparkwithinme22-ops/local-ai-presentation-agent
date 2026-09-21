from __future__ import annotations

import streamlit as st

from agent.config import Settings
from agent.ollama_client import OllamaError
from presentation_service import generate_presentation


st.set_page_config(page_title="Local AI Presentation Agent", page_icon="📊", layout="centered")

st.title("Local AI Presentation Agent")
st.caption("Create an editable university presentation using your local Ollama model.")

settings = Settings.from_environment()

with st.sidebar:
    st.subheader("Current setup")
    st.text(f"Model: {settings.ollama_model}")
    st.text("Runs locally with Ollama")

prompt = st.text_area(
    "What presentation would you like?",
    placeholder="Create a presentation explaining quantum computing to first-year university students.",
    height=150,
)

source_information = st.text_area(
    "Information or data to use (optional)",
    placeholder=(
        "Paste your facts and numbers here. Example:\n"
        "Production output: 2021 = 120 units, 2022 = 145, 2023 = 171. "
        "Source: Internal production report."
    ),
    height=130,
    help="Charts are created only from numeric data you provide here or in the request.",
)

left, right = st.columns(2)
with left:
    slide_count = st.number_input("Number of slides", min_value=3, max_value=30, value=5)
with right:
    audience = st.text_input("Audience", placeholder="First-year university students")

if st.button("Generate presentation", type="primary", use_container_width=True):
    if not prompt.strip():
        st.warning("Enter a presentation request first.")
    else:
        try:
            with st.status("Creating your presentation...", expanded=True) as status:
                st.write(f"Asking {settings.ollama_model} to create the slide plan...")
                generated = generate_presentation(
                    prompt,
                    slide_count=int(slide_count),
                    audience=audience,
                    source_information=source_information,
                    settings=settings,
                )
                st.write("Generating the PowerPoint file...")
                st.write("Checking the finished presentation...")

                if generated.validation.valid:
                    status.update(label="Presentation ready", state="complete")
                else:
                    status.update(label="Presentation needs attention", state="error")

            if generated.validation.valid:
                st.success(
                    f"Created {len(generated.plan.slides)} slides: {generated.plan.title}"
                )
                if generated.validation.issues:
                    with st.expander("Validation warnings"):
                        for issue in generated.validation.issues:
                            st.warning(f"Slide {issue.slide}: {issue.message}")

                with generated.output_path.open("rb") as presentation_file:
                    st.download_button(
                        "Download PowerPoint",
                        data=presentation_file.read(),
                        file_name=generated.output_path.name,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True,
                    )
            else:
                st.error("The file was created, but it failed validation and is not ready to download.")
                for issue in generated.validation.issues:
                    st.error(f"Slide {issue.slide}: {issue.message}")
        except OllamaError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Presentation generation failed: {exc}")
