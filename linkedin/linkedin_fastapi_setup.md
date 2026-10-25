# JobBots FastAPI — n8n setup

## Install

1. Save `linkedin_fastapi.py` to:

   `D:\ird-projects\sahil_projects\my_jobbots_automation\linkedin\linkedin_fastapi.py`

2. Your existing `linkedin/services/` directory must contain the 10 Python services from `services.zip`. You do **not** need to overwrite working service files.

3. In PowerShell, from the JobBots root:

```powershell
cd D:\ird-projects\sahil_projects\my_jobbots_automation
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi uvicorn
$env:JOBBOTS_API_KEY = "REPLACE_WITH_A_LONG_RANDOM_SECRET"
python -m uvicorn linkedin.linkedin_fastapi:app --host 127.0.0.1 --port 8000 --workers 1
```

If you normally use CMD, activate with `.venv\Scripts\activate.bat` and set the key with `set JOBBOTS_API_KEY=...`.

- Interactive Swagger docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
- The API uses your activated virtualenv Python to start each worker subprocess.
- Your existing Chrome remote debugger must be running on `127.0.0.1:9222` and signed in to ChatGPT/LinkedIn for browser steps.
- Bind only to `127.0.0.1` for local n8n. If n8n runs in Docker, `127.0.0.1` inside the container is **not** your Windows host; use the appropriate host networking configuration (often `host.docker.internal`) and **protect the API with a secret and a firewall**. Do not expose this Selenium control API publicly.
- Start **one** Uvicorn worker only. The service coordinator uses a single-process concurrency lock.

## n8n HTTP Request node

**Method**: `POST`  
**URL**: `http://127.0.0.1:8000/api/v1/scraper` (replace the final route for each step)  
**Headers**: `Content-Type: application/json`, `X-API-Key: REPLACE_WITH_A_LONG_RANDOM_SECRET`  
**Body (JSON)**:

```json
{"date":"2026-10-19"}
```

For an n8n dynamically generated India date, use the expression `{{ $now.setZone('Asia/Kolkata').toFormat('yyyy-MM-dd') }}` as the date value. Note: `scraper` and `regex-grouping` can only run for the **machine's current local date**, because the existing scripts internally compute the date.

### API response (HTTP 202)

```json
{
  "job_id": "...",
  "service": "scraper",
  "date": "2026-10-19",
  "status": "queued",
  "company_folder": "job_profile/specific/company/2026-10-19",
  "log_endpoint": "/api/v1/jobs/.../logs"
}
```

This means **accepted**, not finished.

### Poll and continue

1. Save the `job_id` from the POST response.
2. Wait 15–30 seconds (n8n Wait node).
3. Send `GET http://127.0.0.1:8000/api/v1/jobs/<job_id>` with the same `X-API-Key` header.
4. If `status=running` or `queued`, repeat the Wait and GET.
5. If `status=completed`, trigger the **next** POST endpoint.
6. If `status=failed`, inspect `GET /api/v1/jobs/<job_id>/logs` and stop/retry after fixing the cause.

A single API process allows only one active service at a time. Starting another while a job is in progress returns HTTP `409` with the current job ID.

### Recommended ChatGPT-based sequence

```text
POST /api/v1/scraper
  -> poll GET /api/v1/jobs/{id} until completed
POST /api/v1/job-grouping
  -> poll until completed (THIS ONLY SUBMITS THE CHATGPT REQUEST)
  -> wait separately for ChatGPT to finish producing the ZIP
POST /api/v1/grouping-download
  -> poll until completed (imports dated JDs)
POST /api/v1/cv-generator
  -> poll until completed (THIS ONLY SUBMITS THE FOUR CV REQUESTS)
  -> wait separately for the four ChatGPT ZIPs to become available
POST /api/v1/cv-download
  -> poll until completed (imports dated CVs)
```

**Important:** ChatGPT processing is external and may take 30 minutes. A `completed` status on `job-grouping` or `cv-generator` does **not** mean the ZIPs are ready. `grouping-download` or `cv-download` will fail if the ZIP is not yet available; these steps can be retried later. When a service reports `completed`, that means its Python entry point returned successfully, not that every individual email or LinkedIn message was delivered. Inspect service logs for per-recipient outcomes.

### Alternative legacy regex path

`POST /api/v1/regex-grouping` -> poll -> `POST /api/v1/copy-grouped-jobs`. Avoid running this alternative against the same dated JD folders as the ChatGPT grouped files unless you intend to replace that content.

## Additional endpoints

- `GET /api/v1/services` — names and descriptions of 10 endpoints.
- `GET /api/v1/dates/2026-10-19` — date-based input/output directory presence.
- `GET /api/v1/jobs?date=2026-10-19` — recent jobs for the specified date.
- `GET /api/v1/jobs/{job_id}/logs?tail=100` — recent worker stdout/errors.

All except `/health` require the secret if `JOBBOTS_API_KEY` is configured.

## Sending email and LinkedIn outreach

The `email-sender`, `linkedin-connections` and `linkedin-messages` endpoints are disabled by default. If you intentionally want automated sending, **review the target recipients and messages first**, then start the API server with:

```powershell
$env:JOBBOTS_ALLOW_OUTREACH = "1"
```

The original `connection_req_msg_linkedin.py` contains a static `POSTED_BY_URLS` list and **does not** use the supplied date to select recipients. To enable that particular endpoint after reviewing the list:

```powershell
$env:JOBBOTS_ALLOW_STATIC_CONNECTIONS = "1"
```

A repeated request for the same service/date is deduplicated after success. To intentionally rerun, pass `{"date":"2026-10-19","force":true}`. **Do not use force casually for outreach**: an earlier task may have sent some messages before failing. The API does not automate login or verification screens.

## Date-based output folders

- Scraper JSON: `linkedin/output/scarp/YYYY-MM-DD.json`
- Legacy regex jobs: `linkedin/output/grouped_jobs/YYYY-MM-DD/`
- Grouped JD files, generated CVs: `job_profile/specific/company/YYYY-MM-DD/<role>/`
- Downloaded ZIPs: `job_profile/download_zip_files/`
- API job status and logs: `linkedin/output/fastapi_jobs/`

The API does not itself rename ZIP contents or overwrite files; it delegates these actions to your existing downloader services, which have their own validation/overwrite checks.
