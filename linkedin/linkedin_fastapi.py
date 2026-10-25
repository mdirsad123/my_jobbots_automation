"""JobBots synchronous FastAPI endpoints for n8n (no JSON body required).

Install as: <project_root>/linkedin/linkedin_fastapi.py
Run: python -m uvicorn linkedin.linkedin_fastapi:app --host 127.0.0.1 --port 8000

POST /api/v1/scraper (and the nine other service endpoints) takes NO BODY.
The current Windows host date is selected when the request begins. Each POST
starts its original service in an isolated subprocess, blocks the HTTP response
until it exits, then reports success/failure and relevant output locations.

For an INTENTIONAL rerun of a completed job, use POST /api/v1/scraper?force=true.
The default skips services already marked completed for the current date.

IMPORTANT: For job-grouping and cv-generator, finishing means only that the
ChatGPT prompts were SUBMITTED. It does not mean ChatGPT generated the ZIP.
Call the matching download step when output is ready, not immediately.

Long requests: raise the n8n HTTP Request timeout enough for Selenium/scraper.
Any proxy or network gateway between n8n and FastAPI can impose its own limit.
Logs and job IDs are still recorded under linkedin/output/fastapi_jobs.

Keep only one Uvicorn worker. If exposing outside localhost, configure
JOBBOTS_API_KEY and send X-API-Key in n8n. Outreach stays disabled by default.
"""
from __future__ import annotations

import ctypes
import hmac
import json
import os
import re
import subprocess
import time
import sys
import threading
import traceback
import uuid
from datetime import date as Date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel

# This file belongs in <root>/linkedin/linkedin_fastapi.py.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LINKEDIN_DIR = PROJECT_ROOT / "linkedin"
JOB_STATE_DIR = LINKEDIN_DIR / "output" / "fastapi_jobs"
COMPANY_ROOT = PROJECT_ROOT / "job_profile" / "specific" / "company"
GROUPED_ROOT = LINKEDIN_DIR / "output" / "grouped_jobs"
SCRAP_ROOT = LINKEDIN_DIR / "output" / "scarp"  # Original scraper spelling
DOWNLOAD_ROOT = PROJECT_ROOT / "job_profile" / "download_zip_files"

ROLE_NAMES = ("aiengineer", "awsdataengineer", "dataengineer", "pythondeveloper")

# Registry: service aliases and descriptions, for interactive OpenAPI docs.
SERVICES: dict[str, dict[str, Any]] = {
    "scraper": {"module": "scraper_service", "about": "Scrape LinkedIn feed to dated JSON", "current_date_only": True},
    "job-grouping": {"module": "chatgpt_job_grouping", "about": "Submit JSON and master prompt to ChatGPT; no ZIP download"},
    "grouping-download": {"module": "chatgpt_job_grouping_zip_downloader", "about": "Download/import dated grouped-JD ZIP"},
    "cv-generator": {"module": "chatgpt_cvs_generator", "about": "Submit four role-specific JD prompts; no CV download"},
    "cv-download": {"module": "chatgpt_cv_zip_downloader", "about": "Download/import CV ZIPs only for today's eligible role folders"},
    "regex-grouping": {"module": "find_similar_jobs", "about": "Legacy title-regex grouping (not the ChatGPT route)", "current_date_only": True},
    "copy-grouped-jobs": {"module": "copy_group_role_specific_data", "about": "Copy legacy regex-grouped files into dated company folders"},
    "email-sender": {"module": "manual_email_sender", "about": "Send emails from dated role folders", "outreach": True},
    "linkedin-connections": {"module": "connection_req_msg_linkedin", "about": "Send connection requests from static POSTED_BY_URLS; not date-scoped", "outreach": True, "unscoped": True},
    "linkedin-messages": {"module": "direct_msg_linkedin_hr", "about": "Send role-based LinkedIn messages", "outreach": True},
}

app = FastAPI(
    title="JobBots LinkedIn Service API",
    version="2.0.0",
    description=(
        "Each POST takes no JSON body, automatically selects today's Windows local date, "
        "and waits for its service to finish before returning HTTP 200. "
        "Use ?force=true only for intentional reruns. "
        "ChatGPT submission completion is not the same as ZIP generation completion."
    ),
)
_START_LOCK = threading.Lock()


class DateRequest(BaseModel):
    """Internal queue options only. Clients no longer supply a request body."""
    date: str
    force: bool = False


def today_date() -> str:
    """Use the same local system date as the existing scraper and role scripts."""
    return datetime.now().date().isoformat()


def checked_date(value: str) -> str:
    if not isinstance(value, str) or len(value) != 10:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD")
    try:
        parsed = Date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="date must be a valid YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD")
    return value


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _state_path(job_id: str) -> Path:
    return JOB_STATE_DIR / f"{job_id}.json"


def _log_path(job_id: str) -> Path:
    return JOB_STATE_DIR / f"{job_id}.log"


def _atomic_save(record: dict) -> None:
    JOB_STATE_DIR.mkdir(parents=True, exist_ok=True)
    output = _state_path(record["job_id"])
    temp = JOB_STATE_DIR / f".{record['job_id']}-{uuid.uuid4().hex}.tmp"
    temp.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(output)


def _load_job(job_id: str) -> dict:
    try:
        uuid.UUID(job_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=404, detail="Unknown job ID") from exc
    path = _state_path(job_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=500, detail="Unable to read job state") from exc


def _pid_alive(pid: int | None) -> bool:
    if not pid or pid < 1:
        return False
    if os.name == "nt":
        # Windows: do not call os.kill(pid, 0) because its meaning differs.
        kernel = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _refresh_orphan(record: dict) -> dict:
    if record["status"] not in {"queued", "running"}:
        return record
    pid = record.get("pid")
    if pid and not _pid_alive(pid):
        # The worker exited without persisting a terminal state.
        record["status"] = "failed"
        record["finished_at"] = utc_now()
        record["error"] = "Worker process exited unexpectedly; inspect the job log"
        _atomic_save(record)
    return record


def _all_jobs() -> list[dict]:
    if not JOB_STATE_DIR.exists():
        return []
    results = []
    for path in JOB_STATE_DIR.glob("*.json"):
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(obj, dict) and obj.get("job_id"):
                results.append(_refresh_orphan(obj))
        except (ValueError, OSError):
            continue
    return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)


def _output_info(day: str) -> dict:
    daily = COMPANY_ROOT / day
    result = {
        "date": day,
        "scraped_json": str((SCRAP_ROOT / f"{day}.json").relative_to(PROJECT_ROOT)),
        "scraped_json_exists": (SCRAP_ROOT / f"{day}.json").is_file(),
        "legacy_group_folder": str((GROUPED_ROOT / day).relative_to(PROJECT_ROOT)),
        "legacy_group_folder_exists": (GROUPED_ROOT / day).is_dir(),
        "company_folder": str(daily.relative_to(PROJECT_ROOT)),
        "company_folder_exists": daily.is_dir(),
        "role_folders": {name: (daily / name).is_dir() for name in ROLE_NAMES},
        "download_folder": str(DOWNLOAD_ROOT.relative_to(PROJECT_ROOT)),
    }
    return result


def _authorize(request: Request, x_api_key: str | None = Header(None, alias="X-API-Key")) -> None:
    token = os.getenv("JOBBOTS_API_KEY", "").strip()
    if token:
        if not x_api_key or not hmac.compare_digest(token, x_api_key):
            raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
    else:
        # No token is acceptable only with a localhost caller. Bind Uvicorn to
        # 127.0.0.1 in this mode and configure a secret for remote n8n clients.
        peer = request.client.host if request.client else ""
        if peer not in {"127.0.0.1", "::1"}:
            raise HTTPException(status_code=403, detail="Set JOBBOTS_API_KEY for remote API access")


def _preflight(service: str, day: str) -> None:
    spec = SERVICES[service]
    if spec.get("current_date_only") and day != datetime.now().date().isoformat():
        raise HTTPException(
            status_code=422,
            detail=f"{service} internally uses the Windows system date; only today's local date is supported",
        )
    if spec.get("unscoped") and os.getenv("JOBBOTS_ALLOW_STATIC_CONNECTIONS") != "1":
        raise HTTPException(
            status_code=403,
            detail=("The connection-request service uses a static POSTED_BY_URLS list, not this date. "
                    "Set JOBBOTS_ALLOW_STATIC_CONNECTIONS=1 only if that list is correct."),
        )
    if service in {"job-grouping", "regex-grouping"}:
        if not (SCRAP_ROOT / f"{day}.json").is_file() and not (PROJECT_ROOT / "output" / "scarp" / f"{day}.json").is_file():
            raise HTTPException(status_code=409, detail=f"Scraped JSON missing for {day}")
    if service == "copy-grouped-jobs" and not (GROUPED_ROOT / day).is_dir():
        raise HTTPException(status_code=409, detail=f"Legacy regex grouped folder missing for {day}")
    if service in {"cv-generator", "email-sender", "linkedin-messages"}:
        folder = COMPANY_ROOT / day
        if not folder.is_dir():
            raise HTTPException(status_code=409, detail=f"Dated role folder missing: {folder}")
    if service == "cv-generator" and not _eligible_cv_roles(day):
        raise HTTPException(status_code=409, detail="No eligible role JD with jobs for this date")


def _public_job(record: dict) -> dict:
    return {
        "job_id": record["job_id"],
        "service": record["service"],
        "date": record["date"],
        "status": record["status"],
        "pid": record.get("pid"),
        "created_at": record.get("created_at"),
        "started_at": record.get("started_at"),
        "finished_at": record.get("finished_at"),
        "exit_code": record.get("exit_code"),
        "error": record.get("error"),
        "company_folder": str((COMPANY_ROOT / record["date"]).relative_to(PROJECT_ROOT)),
        "step_note": (
            "ChatGPT request submission only; ZIP generation may still be running"
            if record["service"] in {"job-grouping", "cv-generator"}
            else SERVICES[record["service"]]["about"]
        ),
        "log_endpoint": f"/api/v1/jobs/{record['job_id']}/logs",
    }


def _enqueue(service: str, payload: DateRequest) -> dict:
    day = checked_date(payload.date)
    _preflight(service, day)
    with _START_LOCK:
        history = _all_jobs()
        for old in history:
            if old["status"] in {"queued", "running"}:
                # n8n may retry the SAME CV-download request while its previous
                # worker is still active. Reuse that job instead of returning
                # 409 or starting a duplicate Chrome/Selenium run.
                if (service == "cv-download" and not payload.force
                        and old["service"] == service and old["date"] == day):
                    return {**_public_job(old), "already_running": True}
                raise HTTPException(
                    status_code=409,
                    detail={"message": "Another service job is running; poll it before starting the next step",
                            "job_id": old["job_id"], "service": old["service"]},
                )
        for old in history:
            if old["service"] == service and old["date"] == day:
                # Avoid unintended repeated messages, email and scraping.
                if service != "email-sender" and not payload.force and old["status"] == "completed":
                    return {**_public_job(old), "already_completed": True}
                if service != "email-sender" and not payload.force and SERVICES[service].get("outreach"):
                    raise HTTPException(
                        status_code=409,
                        detail="Outreach may have been partially sent. Review logs and specify force=true intentionally to retry",
                    )
                break

        job_id = str(uuid.uuid4())
        record = {
            "job_id": job_id,
            "service": service,
            "date": day,
            "status": "queued",
            "created_at": utc_now(),
            "started_at": None,
            "finished_at": None,
            "pid": None,
            "exit_code": None,
            "error": None,
            "force": bool(payload.force),
        }
        _atomic_save(record)
        # Independent worker: long-running Selenium tasks do not block n8n/API.
        argv = [sys.executable, "-u", "-m", "linkedin.linkedin_fastapi", "--worker", job_id]
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        try:
            with _log_path(job_id).open("ab", buffering=0) as stream:
                child = subprocess.Popen(
                    argv,
                    cwd=str(PROJECT_ROOT),
                    stdin=subprocess.DEVNULL,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    creationflags=flags,
                    env=os.environ.copy(),
                )
            record["pid"] = child.pid
            # Worker may have marked itself running before this update; never
            # overwrite a terminal state with 'queued'.
            latest = _load_job(job_id)
            if latest["status"] == "queued":
                latest["pid"] = child.pid
                _atomic_save(latest)
        except (OSError, ValueError) as exc:
            record["status"] = "failed"
            record["finished_at"] = utc_now()
            record["error"] = f"Worker launch failed: {exc}"
            _atomic_save(record)
            raise HTTPException(status_code=500, detail=record["error"]) from exc
        return _public_job(_load_job(job_id))


def _run_existing_service(service: str, day: str, force: bool) -> Any:
    """Import the original existing service and call its real entry point."""
    daily = COMPANY_ROOT / day

    if service == "scraper":
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from linkedin.services.scraper_service import scrape_feed_posts
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=options)
        try:
            return {"jobs_scraped": scrape_feed_posts(driver)}
        finally:
            # Do NOT call driver.quit(); user Chrome should remain running.
            try:
                driver.service.stop()
            except Exception:
                pass

    if service == "job-grouping":
        from linkedin.services.chatgpt_job_grouping import main
        argv = ["--date", day]
        if force:
            argv.append("--force")
        return main(argv)

    if service == "grouping-download":
        from linkedin.services.chatgpt_job_grouping_zip_downloader import main
        argv = ["--date", day, "--project-root", str(PROJECT_ROOT)]
        if force:
            argv.append("--overwrite")
        return main(argv)

    if service == "cv-generator":
        from linkedin.services.chatgpt_cvs_generator import main
        argv = [str(daily)]
        if force:
            argv.append("--force")
        return main(argv)

    if service == "cv-download":
        from linkedin.services.chatgpt_cv_zip_downloader import main
        # API force=true means "run the missing-role check again", NOT
        # "redownload/overwrite completed roles". The downloader safely
        # reuses valid local ZIPs and the previously imported five CV files.
        argv = ["--date", day, "--project-root", str(PROJECT_ROOT)]
        return main(argv)

    if service == "regex-grouping":
        from linkedin.services.find_similar_jobs import group_and_save_roles
        return group_and_save_roles()

    if service == "copy-grouped-jobs":
        from linkedin.services.copy_group_role_specific_data import copy_group_role_specific_data
        return copy_group_role_specific_data(GROUPED_ROOT / day, output_root=COMPANY_ROOT)

    if service == "email-sender":
        from linkedin.services.manual_email_sender import main
        return main(str(daily))

    if service == "linkedin-connections":
        from linkedin.services.connection_req_msg_linkedin import main
        return main()  # Static POSTED_BY_URLS list; date is metadata only.

    if service == "linkedin-messages":
        from linkedin.services.direct_msg_linkedin_hr import main
        return main(str(daily))

    raise ValueError(f"Unknown service: {service}")


def _worker(job_id: str) -> int:
    record = _load_job(job_id)
    record["pid"] = os.getpid()
    record["status"] = "running"
    record["started_at"] = utc_now()
    _atomic_save(record)
    service = record["service"]
    print(f"START {service} date={record['date']} pid={os.getpid()} cwd={PROJECT_ROOT}", flush=True)
    try:
        result = _run_existing_service(service, record["date"], record.get("force", False))
        # Most existing services return None/dict; CLI-oriented services return
        # an integer exit code. Treat nonzero exit as a real failure.
        if (service in {"job-grouping", "grouping-download", "cv-generator", "cv-download"}
                and isinstance(result, int) and not isinstance(result, bool) and result != 0):
            raise RuntimeError(f"Original service returned exit code {result}")
        record = _load_job(job_id)
        record["status"] = "completed"
        record["exit_code"] = 0
        record["finished_at"] = utc_now()
        _atomic_save(record)
        print(f"COMPLETE {service} date={record['date']}", flush=True)
        if service in {"job-grouping", "cv-generator"}:
            print("NOTE: ChatGPT submission completed; finished ZIPs are NOT guaranteed.", flush=True)
        return 0
    except BaseException as exc:
        traceback.print_exc()
        record = _load_job(job_id)
        record["status"] = "failed"
        record["exit_code"] = 1
        record["error"] = f"{type(exc).__name__}: {exc}"[:1200]
        record["finished_at"] = utc_now()
        _atomic_save(record)
        return 1


# ------- API: health, service list, dated outputs, job status and logs -------


@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "ok", "services": len(SERVICES)}


@app.get("/api/v1/services", tags=["System"], dependencies=[Depends(_authorize)])
def list_services() -> dict:
    return {"services": [
        {"name": name, "endpoint": f"POST /api/v1/{name}", **spec}
        for name, spec in SERVICES.items()
    ]}


@app.get("/api/v1/dates/{day}", tags=["System"], dependencies=[Depends(_authorize)])
def date_folders(day: str) -> dict:
    return _output_info(checked_date(day))


@app.get("/api/v1/jobs/{job_id}", tags=["Jobs"], dependencies=[Depends(_authorize)])
def get_job(job_id: str) -> dict:
    return _public_job(_refresh_orphan(_load_job(job_id)))


@app.get("/api/v1/jobs", tags=["Jobs"], dependencies=[Depends(_authorize)])
def list_jobs(date: str | None = None, limit: int = 30) -> dict:
    if date is not None:
        checked_date(date)
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be 1..100")
    records = [r for r in _all_jobs() if date is None or r["date"] == date][:limit]
    return {"jobs": [_public_job(r) for r in records]}


@app.get("/api/v1/jobs/{job_id}/logs", tags=["Jobs"], dependencies=[Depends(_authorize)])
def job_logs(job_id: str, tail: int = 80) -> dict:
    _load_job(job_id)
    if not 1 <= tail <= 500:
        raise HTTPException(status_code=422, detail="tail must be 1..500")
    path = _log_path(job_id)
    if not path.is_file():
        return {"job_id": job_id, "lines": []}
    # Bound memory use for long scraper logs; return last ~256 KB only.
    with path.open("rb") as stream:
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(max(0, size - 256 * 1024))
        chunk = stream.read().decode("utf-8", errors="replace")
    return {"job_id": job_id, "lines": chunk.splitlines()[-tail:]}


# ----- Blocking n8n interface: no body, waits for subprocess completion -----

def _tail_log(job_id: str, count: int = 12) -> list[str]:
    path = _log_path(job_id)
    if not path.is_file():
        return []
    with path.open("rb") as stream:
        stream.seek(0, 2)
        stream.seek(max(0, stream.tell() - 32 * 1024))
        text = stream.read().decode("utf-8", errors="replace")
    return text.splitlines()[-count:]


def _eligible_cv_roles(day: str) -> list[str]:
    """Match the CV downloader: process only dated role folders with a JD.

    Missing folders and empty/missing JDs mean no posting was classified for
    that role today. They must NOT be treated as failed CV downloads.
    """
    day_folder = COMPANY_ROOT / day
    eligible: list[str] = []
    for role in ROLE_NAMES:
        folder = day_folder / role
        if not folder.is_dir():
            continue
        names = {f"{role}_jd.txt", "jd.txt"}
        for candidate in folder.rglob("*"):
            if (candidate.is_file() and candidate.name.casefold() in names
                    and candidate.stat().st_size > 0):
                contents = candidate.read_text(encoding="utf-8-sig", errors="replace")
                match = re.search(r"(?im)^\s*#\s*Jobs\s+included\s*:\s*(\d+)\b", contents)
                if not contents.strip() or (match and int(match.group(1)) == 0):
                    continue
                eligible.append(role)
                break
    return eligible


def _artifacts(service: str, day: str) -> tuple[str, list[str], list[str]]:
    """Return (output folder, expected output files, missing required artifacts).

    Only downloaded ZIPs and actual file-producing stages have required artifacts.
    ChatGPT submission services are finished after they send the prompts, *not*
    when those remote ZIPs eventually appear.
    """
    company_day = COMPANY_ROOT / day
    group_zip = DOWNLOAD_ROOT / f"{day.replace('-', '_')}_job_groups.zip"
    # Require CV files only for roles that actually have a source JD today.
    cv_roles = _eligible_cv_roles(day) if service == "cv-download" else []
    cv_zips = [DOWNLOAD_ROOT / f"{day}_{role}.zip" for role in cv_roles]
    scraper_paths = [SCRAP_ROOT / f"{day}.json", PROJECT_ROOT / "output" / "scarp" / f"{day}.json"]
    scraper_file = next((p for p in scraper_paths if p.is_file()), scraper_paths[0])

    if service == "scraper":
        expected = [scraper_file]
        folder = scraper_file.parent
    elif service == "job-grouping":
        expected = []  # ChatGPT is still generating its ZIP remotely.
        folder = DOWNLOAD_ROOT
    elif service == "grouping-download":
        expected = [group_zip, company_day / "grouping_audit.json"]
        # Grouping master prompt omits role files for zero-job groups.
        # grouping_audit.json is the authoritative count source.
        audit_path = company_day / "grouping_audit.json"
        if audit_path.is_file():
            try:
                audit = json.loads(audit_path.read_text(encoding="utf-8"))
                group_counts = audit.get("group_counts", {})
                if isinstance(group_counts, dict):
                    expected.extend(company_day / role / f"{role}_jd.txt"
                                    for role in (*ROLE_NAMES, "others")
                                    if int(group_counts.get(role, 0)) > 0)
            except (ValueError, TypeError, OSError):
                pass  # Missing/invalid audit is already a required artifact.

        folder = company_day
    elif service == "cv-generator":
        expected = []  # ChatGPT is still generating its ZIPs remotely.
        folder = company_day
    elif service == "cv-download":
        expected = cv_zips[:]
        for role in cv_roles:
            role_dir = company_day / role
            expected.extend([
                role_dir / f"md_irsad_cv_{role}.md",
                role_dir / f"md_irsad_cv_{role}.pdf",
                role_dir / f"md_irsad_cv_{role}.docx",
                role_dir / f"jd_email_reply_{day}.txt",
                role_dir / f"interview_prep_{role}_{day}.pdf",
            ])
        folder = company_day
    elif service == "regex-grouping":
        expected = []
        folder = GROUPED_ROOT / day
    elif service == "copy-grouped-jobs":
        expected = []
        folder = company_day
    elif service in {"email-sender", "linkedin-messages"}:
        expected = []
        folder = company_day
    else:  # Static LinkedIn connections: only logs are date-scoped.
        expected = []
        folder = JOB_STATE_DIR

    missing = [str(p) for p in expected if not p.is_file() or p.stat().st_size == 0]
    if service in {"regex-grouping", "copy-grouped-jobs"} and not folder.is_dir():
        missing.append(str(folder))
    return str(folder), [str(p) for p in expected], missing


def _run_and_wait(service: str, force: bool = False) -> dict:
    """Block only the request's thread; other API routes remain responsive."""
    day = today_date()
    started = time.monotonic()
    info = _enqueue(service, DateRequest(date=day, force=force))
    job_id = info["job_id"]
    already = bool(info.get("already_completed"))

    # The service remains a separate process, preserving the original API logs,
    # multi-service exclusion and duplicate-run/outreach protections.
    while True:
        state = _refresh_orphan(_load_job(job_id))
        if state["status"] in {"completed", "failed"}:
            break
        time.sleep(0.5)

    folder, files, missing = _artifacts(service, day)
    elapsed = round(time.monotonic() - started, 2)
    base = {
        "service": service,
        "date": day,
        "output_folder": folder,
        "job_id": job_id,
        "elapsed_seconds": elapsed,
        "already_completed": already,
        "log_endpoint": f"/api/v1/jobs/{job_id}/logs",
    }

    if state["status"] != "completed":
        raise HTTPException(status_code=500, detail={
            **base, "success": False, "status": "failed",
            "message": state.get("error") or f"{service} failed. Check logs.",
            "log_tail": _tail_log(job_id),
        })

    if service == "cv-download" and missing:
        # A role with a source JD may have a ChatGPT ZIP that is not ready yet.
        # The downloader already tried three scroll-search passes and skipped it.
        # Return HTTP 200 with an explicit PARTIAL result, not HTTP 409: this
        # prevents n8n from repeatedly launching the entire workflow. It also
        # does NOT claim that missing files were downloaded successfully.
        # To intentionally retry later, POST /api/v1/cv-download?force=true.
        return {
            **base,
            "success": False,
            "status": "partial",
            "message": (
                "Checked today's eligible CV roles. Some ZIPs/files are still missing; "
                "skipped them without restarting completed roles. "
                "Use ?force=true to retry missing roles later."
            ),
            "eligible_roles": _eligible_cv_roles(day),
            "missing_files": missing,
            "verified_files": len(files) - len(missing),
            "zip_folder": str(DOWNLOAD_ROOT),
            "log_tail": _tail_log(job_id),
        }

    if missing:
        # A downloader might return exit code 0 after SKIPPING an unfinished
        # remote ChatGPT output. Never report these incomplete imports as success.
        # Mark this attempt failed in the persistent job log; otherwise the
        # existing duplicate-run guard would keep recycling this same
        # 'completed' job forever on subsequent calls without ?force=true.
        state["status"] = "failed"
        state["exit_code"] = 1
        state["error"] = "Required dated output artifacts were missing after the service returned"
        state["finished_at"] = utc_now()
        _atomic_save(state)
        raise HTTPException(status_code=409, detail={
            **base, "success": False, "status": "incomplete",
            "message": "Service exited, but required output files are not ready.",
            "missing_files": missing,
            "log_tail": _tail_log(job_id),
        })

    if service == "cv-download" and not _eligible_cv_roles(day):
        return {
            **base,
            "success": True,
            "status": "skipped",
            "message": "No eligible role folders with a nonempty JD today; no CV ZIP download needed.",
            "eligible_roles": [],
            "verified_files": 0,
            "zip_folder": str(DOWNLOAD_ROOT),
        }

    submission = service in {"job-grouping", "cv-generator"}
    if already:
        message = "Already completed for today's date; no new run was started."
    elif submission:
        message = "ChatGPT request submitted successfully; generated ZIP is not necessarily ready yet."
    else:
        message = f"{service} completed successfully."

    response = {
        **base,
        "success": True,
        "status": "completed",
        "message": message,
        "verified_files": len(files),
        "submission_only": submission,
    }
    if service == "scraper" and files:
        response["output_file"] = files[0]
    if service == "grouping-download":
        response["zip_file"] = str(DOWNLOAD_ROOT / f"{day.replace('-', '_')}_job_groups.zip")
    if service == "cv-download":
        response["zip_folder"] = str(DOWNLOAD_ROOT)
        response["eligible_roles"] = _eligible_cv_roles(day)
    return response


# HTTP 200 on completion; FastAPI/OpenAPI shows NO request body for these routes.
@app.post("/api/v1/scraper", tags=["Steps"], dependencies=[Depends(_authorize)])
def run_scraper(force: bool = Query(False, description="Intentional rerun of today's scraper")) -> dict:
    return _run_and_wait("scraper", force)


@app.post("/api/v1/job-grouping", tags=["Steps"], dependencies=[Depends(_authorize)])
def run_job_grouping(force: bool = Query(False)) -> dict:
    return _run_and_wait("job-grouping", force)


@app.post("/api/v1/grouping-download", tags=["Steps"], dependencies=[Depends(_authorize)])
def run_grouping_download(force: bool = Query(False)) -> dict:
    return _run_and_wait("grouping-download", force)


@app.post("/api/v1/cv-generator", tags=["Steps"], dependencies=[Depends(_authorize)])
def run_cv_generator(force: bool = Query(False)) -> dict:
    return _run_and_wait("cv-generator", force)


@app.post("/api/v1/cv-download", tags=["Steps"], dependencies=[Depends(_authorize)])
def run_cv_download(force: bool = Query(False)) -> dict:
    return _run_and_wait("cv-download", force)


@app.post("/api/v1/regex-grouping", tags=["Legacy"], dependencies=[Depends(_authorize)])
def run_regex_grouping(force: bool = Query(False)) -> dict:
    return _run_and_wait("regex-grouping", force)


@app.post("/api/v1/copy-grouped-jobs", tags=["Legacy"], dependencies=[Depends(_authorize)])
def run_copy_grouped_jobs(force: bool = Query(False)) -> dict:
    return _run_and_wait("copy-grouped-jobs", force)


@app.post("/api/v1/email-sender", tags=["Outreach"], dependencies=[Depends(_authorize)])
def run_email_sender(force: bool = Query(False)) -> dict:
    return _run_and_wait("email-sender", force)


@app.post("/api/v1/linkedin-connections", tags=["Outreach"], dependencies=[Depends(_authorize)])
def run_linkedin_connections(force: bool = Query(False)) -> dict:
    return _run_and_wait("linkedin-connections", force)


@app.post("/api/v1/linkedin-messages", tags=["Outreach"], dependencies=[Depends(_authorize)])
def run_linkedin_messages(force: bool = Query(False)) -> dict:
    return _run_and_wait("linkedin-messages", force)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        sys.exit(_worker(sys.argv[2]))
    print("Run: python -m uvicorn linkedin.linkedin_fastapi:app --host 127.0.0.1 --port 8000")
