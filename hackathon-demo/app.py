#!/usr/bin/env python3
"""Streamlit wrapper for one dental skill on Nebius Token Factory.

Run from the repository root:

    streamlit run hackathon-demo/app.py
"""

from __future__ import annotations

import streamlit as st

import journal_club_runner as runner


PRESETS = runner.MODEL_PRESETS
CUSTOM = "Custom model id"


def _preset_index(model: str) -> int:
    labels = list(PRESETS)
    for index, label in enumerate(labels):
        if PRESETS[label]["model"] == model:
            return index
    return len(labels)


def _selected_endpoint() -> tuple[str, str]:
    label = st.session_state.get("preset", list(PRESETS)[0])
    if label == CUSTOM:
        return (
            st.session_state.get("custom_model", "").strip(),
            st.session_state.get("custom_base_url", "").strip(),
        )
    preset = PRESETS[label]
    return preset["model"], preset["base_url"]


def _config_for_request() -> dict[str, object]:
    config = runner.runtime_config()
    model, base_url = _selected_endpoint()
    config["model"] = model
    config["base_url"] = base_url
    return config


def main() -> None:
    runner.load_local_env()
    st.set_page_config(page_title="Dental journal club demo", layout="wide")
    skill = runner.load_skill(runner.DEFAULT_SKILL)
    fixture_text = runner.default_fixture_text()

    st.markdown(
        """
        <div style="background:#15365a;color:#f7f0da;padding:16px 20px;border-radius:8px;">
          <div style="font-size:13px;letter-spacing:0.04em;">NEBIUS x NVIDIA HACKATHON 2026 · BEST APPS AND AGENTS</div>
          <div style="font-size:28px;font-weight:700;margin-top:4px;">Dental journal club</div>
          <div style="font-size:16px;margin-top:6px;">A demo wrapper around the research-critic skill. The brief is an appraisal of text you supply. It is not a clinical recommendation.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.caption(
        f"Loaded `{skill['name']}` {skill['protocol_version']} from `{skill['path']}` "
        f"({len(skill['text'])} characters). The skill file is not modified."
    )

    with st.sidebar:
        st.header("Token Factory")
        env_config = runner.runtime_config()
        labels = list(PRESETS) + [CUSTOM]
        st.selectbox(
            "Model preset",
            labels,
            index=min(_preset_index(str(env_config["model"])), len(labels) - 1),
            key="preset",
            help="Presets use model ids from the public Token Factory catalog checked on 23 Oct 2026.",
        )
        if st.session_state.get("preset") == CUSTOM:
            st.text_input("Model id", value=str(env_config["model"]), key="custom_model")
            st.text_input("Base URL", value=str(env_config["base_url"]), key="custom_base_url")
        model, base_url = _selected_endpoint()
        st.write(f"Model: `{model}`")
        st.write(f"Base URL: `{base_url}`")
        if env_config["api_key"]:
            st.success("NEBIUS_API_KEY is set in the environment.")
        else:
            st.warning("NEBIUS_API_KEY is not set. Preview still works. A live run needs the key.")
        st.caption("The key stays in the environment. This page has no key field and does not store one.")
        st.caption("Catalog: https://tokenfactory.nebius.com/model-catalog.md")

    if "study_text" not in st.session_state:
        st.session_state["study_text"] = fixture_text
    study_text = st.text_area(
        "Study text",
        height=220,
        key="study_text",
        help="The box starts with the synthetic split-mouth fixture. Paste other text if you want a different appraisal.",
    )
    source_note = runner.source_note_for(study_text)
    st.info(source_note)

    preview, run = st.columns(2)
    with preview:
        preview_clicked = st.button("Preview request", type="secondary")
    with run:
        run_clicked = st.button("Run appraisal", type="primary")

    if preview_clicked:
        try:
            messages = runner.build_messages(skill, study_text, source_note)
            st.session_state["preview"] = runner.dry_run_report(skill, messages, _config_for_request())
            st.session_state["error"] = ""
        except (runner.ConfigError, ValueError) as exc:
            st.session_state["preview"] = ""
            st.session_state["error"] = str(exc)

    if run_clicked:
        collected: list[str] = []
        try:
            messages = runner.build_messages(skill, study_text, source_note)
            config = _config_for_request()
            box = st.empty()
            for piece in runner.iter_chat_deltas(config, messages):
                collected.append(piece)
                box.markdown("".join(collected))
            brief = "".join(collected).strip()
            if not brief:
                raise runner.TokenFactoryError(
                    "Token Factory returned an empty answer. If the model id was retired, "
                    "pick another preset from the catalog."
                )
            st.session_state["brief"] = brief
            st.session_state["preview"] = ""
            st.session_state["error"] = ""
        except (runner.ConfigError, runner.TokenFactoryError, ValueError) as exc:
            st.session_state["brief"] = "".join(collected).strip()
            st.session_state["error"] = str(exc)

    error = st.session_state.get("error") or ""
    if error:
        st.error(error)
    preview_text = st.session_state.get("preview") or ""
    if preview_text:
        st.subheader("Request preview")
        st.code(preview_text)
    brief = st.session_state.get("brief") or ""
    if brief and not run_clicked:
        st.subheader("Journal-club brief")
        st.markdown(brief)
    if brief:
        st.download_button("Download brief", data=brief, file_name="journal-club-brief.md", mime="text/markdown")

    st.divider()
    st.caption(
        "Hackathon demo wrapper. It does not fetch papers, search the web, or change the skill files. "
        "A dentist reads the source text before using any line of the output."
    )


main()
