## Usage

### Prerequisites

- OBS
- Python 3

### Instructions

- Install the Python requirements: `python3 -m pip install -r requirements.txt`
  - Note that I probably _could_ use a virtual environment, OBS would then need to load Python from `venv/bin`, which I couldn't test while live-streaming.
- Install [LocalVocal](https://github.com/occ-ai/obs-localvocal)
- Add LocalVocal as a filter on your microphone. E.g. my setup looks like this:
  - ![image](https://github.com/AdamLearns/VocalStreamer/assets/60950402/7845078d-d475-4c97-934e-7a7190dbb434)
- Set up scripting in OBS
  - Go to **Tools** → **Scripts**
  - Under the **Python Settings** tab, choose the location to a version of Python that's compatible with OBS. There isn't very much information on how to find that version. I specified this on macOS: `/opt/homebrew/Cellar/python@3.11/3.11.7_1/Frameworks`.
  - On the **Scripts** tab, add the script from this repo.
- For now, the script has hard-coded parameters, e.g. for the name of scenes to switch to or the names of files, so you have to modify the script directly and then click the "Refresh" button on the **Scripts** tab.

### Adam-specific instructions

- Make a `password.txt` in the repo with the bot's server's password in it.

## Adam's Code Jam

This code was created in early 2024 for [Adam's Code Jam](https://jam.adamlearns.com/).
