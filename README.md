# JobBots Ubuntu ARM64 – clean Poetry environment

This is a lightweight **baseline** for the LinkedIn FastAPI and browser automation project, derived from the supplied `pyproject.toml`. It is not a verified full import audit for every script in the repository (the full repository was not supplied).

## Contents
- `pyproject.toml`: intended replacement for the existing project-root `pyproject.toml` (NOT `poetry.toml`).
- `reset_jobbots_venv_ubuntu.sh`: opt-in reset script; it verifies the exact project path, asks for `RESET`, backs up `poetry.lock` outside the project, deletes only this project's `.venv`, regenerates the lock, installs only core dependencies and validates imports.

## How to use
1. Stop `start_linkedin_fastapi.sh` / any running API using this `.venv`.
2. Back up the original `pyproject.toml` somewhere outside the repository.
3. Copy both files to `/home/ubuntu/ird-projects/my_jobbots_automation/`. The replacement file must be named exactly **pyproject.toml**.
4. Run:

```bash
cd ~/ird-projects/my_jobbots_automation
chmod +x reset_jobbots_venv_ubuntu.sh
./reset_jobbots_venv_ubuntu.sh
```

5. Check API on port 8010:

```bash
cd ~/ird-projects/my_jobbots_automation/linkedin/bat_file
./start_linkedin_fastapi.sh
# In another terminal:
curl -s http://127.0.0.1:8010/health
```

## Optional dependencies
If your specific LinkedIn scripts need GUI mouse/keyboard automation, run from project root:

```bash
poetry install --with desktop --no-root
```

For tests:

```bash
poetry install --with dev --no-root
```

System programs such as Chromium, Pandoc, Tesseract, or X display libraries require separate system installation when the corresponding scripts need them. They are not installed by Poetry.

**Removed from default dependency set:** torch, transformers, SageMaker, PySpark, Jupyter, notebook, Redshift, AWS data SDK, Azure DevOps, docx2pdf, CUDA and several other packages not demonstrated as needed for the LinkedIn API. If some other scripts import these, add only the necessary package after identifying it.

Poetry dependency groups still participate in resolution, but optional groups are not installed unless selected. The default dependency set contains no direct Torch/CUDA dependencies; third-party transitive packages depend on the resolver result, so check the lock for unexpected NVIDIA entries (`grep -i nvidia poetry.lock`).

Do not remove the separate Recruiter Email `.venv` or the `.env` configuration files.


# my_pyautomation
This project would be for ongoing researches on desktop/test/ui/rest automations

# Switch python versions
pyenv versions
PS D:\tge\2025\ird-projects\my_pyautomation\aws> pyenv versions
  3.10.11
* 3.12.9 (set by C:\Users\erirs\.pyenv\pyenv-win\version)

pyenv global 3.12.9

# debuger port
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chromedebug"

D:/ird-projects/sahil_projects/my_jobbots_automation/.venv/Scripts/activate.bat
