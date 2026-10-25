# Four ChatGPT Projects — Role CV Automation

Run from the Python project root with the new `chatgpt_cvs_generator.py`.

Each role now opens a **fresh chat inside its own ChatGPT Project**:

- aiengineer: https://chatgpt.com/g/g-p-6a7b6711b4748191a7dcb712ef99158c/project
- awsdataengineer: https://chatgpt.com/g/g-p-6ad4d3df646481919b57dc116e98be5b/project
- dataengineer: https://chatgpt.com/g/g-p-6ad4d3eb4e3881918beb94639237e5fb/project
- pythondeveloper: https://chatgpt.com/g/g-p-6ad4d3d115b88191a0927cd7080b617d/project

For each chat, Python builds and attaches the context ZIP containing the master
prompt, `md_irsad.md`, and the PDF/DOCX converters, followed by that role's
current JD TXT from the dated folder. It checks both attachment chips within
the composer and blocks Send if either one is missing. Then it sends the role
prompt, logs status and chat URL in `chatgpt_submission_results.json`, moves
to the next project immediately, and leaves the tabs open. It does not wait
for the output files or download/merge anything.

From the job automation project root:

```powershell
python -m linkedin.services.chatgpt_cvs_generator "job_profile\specific\company\2026-10-18" --dry-run
python -m linkedin.services.chatgpt_cvs_generator "job_profile\specific\company\2026-10-18"
```

Prior to launching, run Chrome with remote debugging enabled, sign in, and
ensure you have access to all four Projects. `--dry-run` stages but does not
send the requests. The script's project links and selectors cannot be live-
verified outside your signed-in browser; check them in dry-run first.

The standard output is one ZIP per role, with five generated documents under
`DATE/role/`; see Section 13 in `master_prompt.txt` for exact file names.

**Important:** The included historical `2026-09-29` JD set is only a sample.
For a new day, your daily JD scraper must create the date's four role folders.
The script never uploads an older JD instead of the selected day's JD.
