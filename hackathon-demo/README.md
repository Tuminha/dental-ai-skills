# Dental journal club demo

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![UI](https://img.shields.io/badge/UI-Streamlit-red.svg)
![Track](https://img.shields.io/badge/Track-Best%20Apps%20and%20Agents-15365a.svg)

**A thin hackathon wrapper: one existing dental skill, Nebius Token Factory, one NVIDIA Nemotron model.**

[Setup](#setup) · [Environment](#environment-variables) · [Run](#run-locally) · [Video script](DEMO_SCRIPT.md)

</div>

Built for the Nebius x NVIDIA Global AI Hackathon 2026, Best Apps and Agents track. The organizer deadline used for this demo is Friday 30 October 2026, 19:00 CEST.

This folder loads the [`research-critic`](../research-critic/SKILL.md) protocol from disk and sends it to [Nebius Token Factory](https://docs.tokenfactory.nebius.com/api-reference/introduction). The default model is NVIDIA Nemotron 3 Super. The skill files in the repository are not modified.

The skills are markdown protocols. They were written for Claude and Codex hosts. They are not tied to one vendor API. This runner reads `SKILL.md` as text, adds a short demo adapter in the request, and leaves the skill file alone.

## What the demo does

- Loads `research-critic/SKILL.md`, including its frontmatter.
- Sends that file as the system prompt, plus a demo adapter that asks for a short journal-club brief.
- Appraises the text in the box. The box starts with the synthetic fixture [`fixtures/split-mouth-clustering.md`](../fixtures/split-mouth-clustering.md).
- Calls Token Factory's OpenAI-compatible chat completions endpoint.
- Shows the answer as it streams.

## What it does not do

- It does not rewrite a skill, fetch a paper, or search the web.
- It does not ship an API key.
- It does not turn one excerpt into a clinical recommendation.
- The fixture is synthetic. It is a regression prompt from this repository, not a published trial.
- Model output can be wrong. A dentist reads the source text before using any line of it.

The Expected Flags section of the fixture is an answer key. The runner sends the Prompt section only.

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r hackathon-demo/requirements.txt
cp hackathon-demo/.env.example hackathon-demo/.env
```

Create an API key in Nebius Token Factory. The steps are in the [Token Factory API introduction](https://docs.tokenfactory.nebius.com/api-reference/introduction). Put the key in `hackathon-demo/.env` or export it in the shell. `.env` is gitignored.

```bash
export NEBIUS_API_KEY="paste-your-key-here"
```

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `NEBIUS_API_KEY` | For a live run | empty | Bearer token. Token Factory's name for this value. |
| `NEBIUS_BASE_URL` | No | `https://api.tokenfactory.us-central1.nebius.com/v1/` | Regional OpenAI-compatible base URL. |
| `NEBIUS_MODEL` | No | `nvidia/nemotron-3-super-120b-a12b` | Model id. |
| `NEBIUS_MAX_TOKENS` | No | `1800` | Answer length cap. |
| `NEBIUS_TEMPERATURE` | No | `0.2` | Sampling temperature. |
| `NEBIUS_TIMEOUT_SECONDS` | No | `180` | HTTP timeout. |

The model and the regional host belong together. These pairs were read from the public [model catalog](https://tokenfactory.nebius.com/model-catalog.md) on 23 October 2026:

| Preset | Model id | Base URL |
|---|---|---|
| Nemotron 3 Super | `nvidia/nemotron-3-super-120b-a12b` | `https://api.tokenfactory.us-central1.nebius.com/v1/` |
| Nemotron 3 Nano | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | `https://api.tokenfactory.eu-north1.nebius.com/v1/` |
| Nemotron 3 Ultra | `nvidia/Nemotron-3-Ultra-550b-a55b` | `https://api.tokenfactory.us-central1.nebius.com/v1/` |

Super is the default. Nano is the smaller option if you want a cheaper run. Ultra is the large reasoning option. If a call says the model was not found, copy the current id from the catalog. Ids move.

On that catalog date, Super was listed at $0.30 per million input tokens and $0.90 per million output tokens. One brief, with the skill file in the prompt, is a small fraction of a dollar. Check the catalog before a long session. Prices change.

The same HTTP call with the OpenAI Python SDK looks like this:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.us-central1.nebius.com/v1/"),
    api_key=os.environ["NEBIUS_API_KEY"],
)
completion = client.chat.completions.create(
    model=os.environ.get("NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b"),
    messages=[{"role": "user", "content": "Hello"}],
)
print(completion.choices[0].message.content)
```

The demo runner uses the same endpoint with the Python standard library, so the repository smoke test does not need the SDK.

## Run locally

Preview the request without spending credits. This works before the key is set:

```bash
python3 hackathon-demo/journal_club_runner.py
```

Live call from the terminal, using the synthetic fixture:

```bash
python3 hackathon-demo/journal_club_runner.py --run
```

Paste your own text:

```bash
python3 hackathon-demo/journal_club_runner.py --run --text-file my-excerpt.txt
```

Streamlit UI. Start it from `hackathon-demo` so the local theme file is picked up:

```bash
cd hackathon-demo
streamlit run app.py
```

Open `http://localhost:8501`. **Preview request** shows the user message and confirms that the skill file is in the system prompt. **Run appraisal** calls Token Factory. The sidebar reports whether `NEBIUS_API_KEY` is set. It does not ask you to type the key into the page.

Offline checks, also run by `python3 scripts/smoke_test_repo.py`:

```bash
python3 hackathon-demo/journal_club_runner.py --self-check
```

## Video

The recording script is [DEMO_SCRIPT.md](DEMO_SCRIPT.md). It is a journal-club walkthrough under 3 minutes: load the fixture, show the source note, run the brief, and stop before any practice claim.

## Safety notes for the recording

- Say that the fixture is synthetic.
- If the model adds a citation or a treatment instruction that is not in the box, say so and discard that sentence.
- Keep the key off camera.
- The brief is study appraisal of supplied text. It is not a device, a guideline, or a body-of-evidence review. Body-of-evidence questions belong to `clinical-evidence-reviewer`, which is outside this demo so the model is not asked to recall a literature search.
