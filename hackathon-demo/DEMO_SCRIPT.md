# Journal-club demo script

A YouTube recording under 3 minutes. The spoken section is about two and a half minutes at a calm pace.

Record only after `NEBIUS_API_KEY` is set in the shell. Do not show the key on screen. Do not read a clinical recommendation from the model. The input is a synthetic fixture.

## Before you record

1. Export the key in the terminal you will use: `export NEBIUS_API_KEY="..."`
2. Start the app: `streamlit run hackathon-demo/app.py`
3. Open `http://localhost:8501`
4. Confirm the sidebar says the key is set, and that the model is `nvidia/nemotron-3-super-120b-a12b`
5. Confirm the study box contains the split-mouth fixture and the blue source note says it is synthetic
6. Run the appraisal once off camera. If the brief invents a citation, a sample size, or a treatment recommendation, say that on camera. That failure is part of an honest demo.

## Shot list

| Time | Picture | Action |
|---|---|---|
| 0:00 | Title card: "Journal club. Can we trust this result?" | Start the spoken script |
| 0:15 | `research-critic/SKILL.md` open at Phase 0 | Scroll two screens, then leave it |
| 0:35 | App sidebar, key status "set", model id visible | Do not open `.env` |
| 0:50 | Study text and the source note | Leave the fixture as loaded |
| 1:15 | Click **Run appraisal** | Cut the silent wait if the model is slow |
| 1:30 | Brief, sections 1 to 4 | Scroll slowly |
| 2:15 | Section "What this single text cannot decide" | Read the limitation, not a treatment line |
| 2:35 | `hackathon-demo/README.md` environment table | End on the setup, then stop |

## Spoken script

<!-- spoken:start -->
This is a journal club, not a treatment plan. One study is on the screen. The question is whether we can trust the result.

The appraisal rules already live in this repository. The file is research-critic. This demo loads that file and sends it to an NVIDIA Nemotron model through Nebius Token Factory. The skill file stays as it is. The sidebar names Nemotron 3 Super and the us-central1 host. Preview builds the request with no call. Only the live button spends credits.

The text in the box is a synthetic fixture. It is not a published trial. Twenty-eight patients. A split-mouth design. Two recession defects each. The write-up counts fifty-six sites as if they were independent. It uses an unpaired t-test. It says technique A is superior because mean root coverage was 82 percent versus 71 percent, with p equal to 0.04.

The source line stays on screen. It says the full paper was not provided. I run the appraisal.

The brief has to extract the question before it judges. If a method is missing, it says not reported. It names the bias tool for a within-person trial. Every finding has to come from this text.

The useful point for the room: the sites are paired, and the test treats them as independent. A small p-value does not fix that. The last section says what this excerpt cannot decide. It does not tell a dentist to change a flap design.

To run it, put your Nebius API key in the environment. The README lists the base URL and the Nemotron model id. Then start the app. Read the paper yourself before you use any line of the output.
<!-- spoken:end -->

## If the live output goes off the rails

Say this, then stop:

"The wrapper asked for findings only from the fixture. This sentence is not in the fixture, so I would not use it. That is why a person still reads the paper."

Do not invent a correction from memory. Cut to the README.
