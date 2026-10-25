"""Submit today's scraped LinkedIn JSON to ChatGPT for full-JD role grouping.

Put this file at: linkedin/services/chatgpt_job_grouping.py
Also put chatgpt_job_grouping_master_prompt.md in the same services folder.

Run from the project root:
    python -m linkedin.services.chatgpt_job_grouping --dry-run
    python -m linkedin.services.chatgpt_job_grouping
    python -m linkedin.services.chatgpt_job_grouping --date 2026-10-18 --max-years 4
    python -m linkedin.services.chatgpt_job_grouping --force

Only SUBMITS one request (JSON + master prompt) to the dedicated ChatGPT
Project. It does not wait for AI generation, download, or extract the ZIP.

Requires your EXISTING, working linkedin.services.chatgpt_cvs_generator
for its already-tested Selenium Chrome/ChatGPT attachment methods.
Chrome with remote debugging on 127.0.0.1:9222 must be signed in.
"""

from __future__ import annotations
import time
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from linkedin.services import chatgpt_cvs_generator as browser
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

# -----------------------------------------------------------------------------
# USER SETTINGS - update MAX_REQUIRED_YEARS later as your experience increases
# -----------------------------------------------------------------------------
CHATGPT_GROUPING_PROJECT_URL = (
    "https://chatgpt.com/g/g-p-6ad503c1e61c819188158eb94d51f314/project"
)
MAX_REQUIRED_YEARS = 4
MASTER_PROMPT_NAME = "chatgpt_job_grouping_master_prompt.md"

# script: <project_root>/linkedin/services/chatgpt_job_grouping.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICES_DIR = Path(__file__).resolve().parent
SCRAPED_JSON_DIR = PROJECT_ROOT / "linkedin" / "output" / "scarp"
LEGACY_JSON_DIR = PROJECT_ROOT / "output" / "scarp"
LOG_DIR = PROJECT_ROOT / "linkedin" / "output" / "grouping_chatgpt_logs"

ROLE_FOLDERS = (
    "aiengineer", "awsdataengineer", "dataengineer", "pythondeveloper", "others",
)


def today_in_ist() -> str:
    """UTC+05:30 year-month-day (works on Windows without tzdata)."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d")


def iso_date(value: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d")
    if parsed.strftime("%Y-%m-%d") != value:
        raise ValueError("Date must be YYYY-MM-DD")
    return value


def locate_json(date: str, supplied: Path | None = None) -> Path:
    if supplied is not None:
        candidates = [supplied.expanduser()]
    else:
        candidates = [SCRAPED_JSON_DIR / f"{date}.json", LEGACY_JSON_DIR / f"{date}.json"]
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate.is_file():
            if candidate.stat().st_size <= 0:
                raise RuntimeError(f"Scraped JSON is empty: {candidate}")
            return candidate
    raise FileNotFoundError(
        "Scraped daily JSON was not found. Tried:\n" +
        "\n".join(f"  - {p}" for p in candidates)
    )


def summarize_json(path: Path) -> tuple[int, list[str]]:
    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            raw = json.load(stream)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Source is not valid UTF-8 JSON: {path}: {exc}") from exc

    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        for key in ("jobs", "data", "items", "results", "posts"):
            candidate = raw.get(key)
            if isinstance(candidate, list):
                records = candidate
                break
        else:
            raise ValueError("JSON object has no recognized jobs list (jobs/data/items/results/posts)")
    else:
        raise ValueError("Input JSON must be a list of scraped posts or a dict containing a list")

    if not records:
        raise ValueError("The JSON file contains no job records; not sending an empty request")
    keys: set[str] = set()
    for record in records[: min(len(records), 50)]:
        if isinstance(record, dict):
            keys.update(str(k) for k in record.keys())
    return len(records), sorted(keys)


def sha256_file(path: Path) -> str:
    hash_ = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hash_.update(chunk)
    return hash_.hexdigest()


def make_short_prompt(date: str, filename: str, max_years: int, rows: int) -> str:
    folder = date.replace("-", "_")
    return (
        f"DATE={date}; INPUT={filename}; MAX_REQUIRED_YEARS={max_years}; "
        f"OUTPUT_ZIP={folder}_job_groups.zip. "
        f"Follow the ATTACHED {MASTER_PROMPT_NAME} exactly and analyze ALL "
        f"{rows} input records in the ATTACHED {filename}. "
        f"Remove job-seeker/non-hiring posts and vacancies with a mandatory "
        f"minimum experience above {max_years} years. "
        f"Classify by FULL job description (not title only) into aiengineer, "
        f"awsdataengineer, dataengineer, pythondeveloper or others. "
        f"Keep relevant ads without email but never put N/A in email headers. "
        f"Create role JD TXT files ONLY for groups with at least 1 eligible job; "
        f"omit all zero-job role folders and TXT files. Always include "
        f"grouping_audit.json with counts for all five groups inside "
        f"{folder}/, then deliver ONE real downloadable ZIP. "
        f"Report counts and reconcile every input record."
    )


# -----------------------------------------------------------------------------
# RESILIENT CHATGPT SEND / CONFIRMATION
# -----------------------------------------------------------------------------
# Preserve the original 30-second settling period, then additionally poll until
# ChatGPT exposes an enabled Send control. Never claim the job succeeded merely
# because an attachment or prompt was typed into the composer.
PRE_SEND_SETTLE_SECONDS = 30
SEND_BUTTON_WAIT_SECONDS = 75
SEND_CONFIRM_WAIT_SECONDS = 35
MAX_SAFE_SEND_ATTEMPTS = 3


# These are the two XPaths verified in the user's ChatGPT Project.
# The second XPath selects the SVG; we resolve it back to its button before
# clicking, because clicking the actual button is more reliable.
SEND_BUTTON_XPATHS = (
    "//button[@aria-label='Send']",
    "//button[@aria-label='Send']//*[name()='svg']",
)


def _composer_send_button(driver):
    """Find an enabled Send BUTTON by the provided XPaths, then DOM fallback.

    Invoked only after the existing 30-second pre-send pause. Ignore hidden or
    disabled controls; never click the SVG node itself.
    """
    for xpath in SEND_BUTTON_XPATHS:
        try:
            matches = driver.find_elements(By.XPATH, xpath)
        except WebDriverException:
            matches = []
        for element in reversed(matches):
            try:
                button = (
                    element if element.tag_name.lower() == "button"
                    else element.find_element(
                        By.XPATH, "./ancestor::button[@aria-label='Send'][1]"
                    )
                )
                if not button.is_displayed() or not button.is_enabled():
                    continue
                if button.get_attribute("disabled") is not None:
                    continue
                if (button.get_attribute("aria-disabled") or "").lower() == "true":
                    continue
                print(f"  Enabled Send button found via XPath: {xpath}", flush=True)
                return button
            except (StaleElementReferenceException, WebDriverException):
                continue

    # Existing composer-scoped JavaScript fallback, retained for UI changes.
    return driver.execute_script(r"""
        const editorSelectors = [
            '#prompt-textarea',
            '[data-testid="prompt-textarea"]',
            'textarea[placeholder*="Message"]',
            '[contenteditable="true"][data-placeholder]'
        ];
        const buttonSelectors = [
            'button[data-testid="send-button"]',
            'button[data-testid="composer-send-button"]',
            'button[data-testid="composer-submit-button"]',
            'button[aria-label="Send prompt"]',
            'button[aria-label="Send message"]',
            'button[aria-label="Send"]',
            'button[title="Send"]',
            'button[type="submit"]'
        ];
        function visible(el) {
            if (!el) return false;
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 &&
                style.visibility !== 'hidden' && style.display !== 'none';
        }
        const editors = editorSelectors.flatMap(sel =>
            Array.from(document.querySelectorAll(sel))
        );
        const editor = editors.find(visible);
        if (!editor) return null;
        const roots = [];
        const form = editor.closest('form');
        if (form) roots.push(form);
        let current = editor.parentElement;
        for (let depth = 0; depth < 7 && current; depth++) {
            if (!roots.includes(current)) roots.push(current);
            current = current.parentElement;
        }
        for (const root of roots) {
            for (const selector of buttonSelectors) {
                for (const button of root.querySelectorAll(selector)) {
                    if (!visible(button) || button.disabled ||
                        button.getAttribute('aria-disabled') === 'true') continue;
                    const testid = (button.getAttribute('data-testid') || '').toLowerCase();
                    const aria = (button.getAttribute('aria-label') || '').toLowerCase();
                    const title = (button.getAttribute('title') || '').toLowerCase();
                    const isSend = testid.includes('send') || testid.includes('submit') ||
                        aria.startsWith('send') || title === 'send' ||
                        (button.type === 'submit' && button.closest('form') === form);
                    if (isSend) return button;
                }
            }
        }
        return null;
    """)


def _normalize_prompt(value: str) -> str:
    """Use the same whitespace-tolerant comparison before and after Send."""
    return re.sub(r"\s+", " ", (value or "").replace("\u200b", "").replace("\ufeff", "")).strip().casefold()


def _submission_state(driver, prompt: str) -> dict:
    """Detect the draft OR sent message without depending on an exact 55-char prefix.

    ChatGPT's ProseMirror editor may reflow prompt text across DOM children,
    inserting whitespace/newlines. The previous exact `.includes(prompt[:55])`
    returned False even when the prompt was visibly present in the composer.

    Match distinctive start/end fragments after whitespace normalization,
    and fall back to the SAME Selenium composer reader used by fill_prompt().
    """
    normalized = _normalize_prompt(prompt)
    head = normalized[:min(72, len(normalized))].strip()
    tail = normalized[-min(90, len(normalized)):].strip()

    state = driver.execute_script(r"""
        const head = arguments[0];
        const tail = arguments[1];
        function normalize(s) {
            return String(s || '')
                .replace(/[\u200B-\u200D\uFEFF]/g, '')
                .replace(/\s+/g, ' ')
                .trim().toLowerCase();
        }
        function variants(el) {
            return [el.value, el.innerText, el.textContent]
                .filter(x => typeof x === 'string')
                .map(normalize);
        }
        function matchesAny(el) {
            return variants(el).some(text =>
                text.length > 30 &&
                ((head && text.includes(head)) || (tail && text.includes(tail)))
            );
        }
        const chatUrl = /\/c\/[0-9a-z-]+(?:\/)?$/i.test(location.pathname);
        const editors = Array.from(document.querySelectorAll(
            '#prompt-textarea, [data-testid="prompt-textarea"], ' +
            'textarea[placeholder*="Message"], .ProseMirror[contenteditable="true"]'
        ));
        const draftPresent = editors.some(matchesAny);
        const editorLengths = editors.map(el =>
            Math.max(...variants(el).map(text => text.length), 0)
        );
        const userTurns = Array.from(document.querySelectorAll(
            '[data-message-author-role="user"]'
        ));
        const matchingUserTurn = userTurns.some(matchesAny);
        return {
            chat_url: chatUrl,
            draft_present: draftPresent,
            matching_user_turn: matchingUserTurn,
            confirmed: chatUrl && matchingUserTurn,
            editor_count: editors.length,
            editor_lengths: editorLengths,
            detection: draftPresent ? 'dom' : 'not_matched'
        };
    """, head, tail)

    # If React has just swapped editor DOM elements, Selenium can still read
    # the active composer using the existing verified CV generator helpers.
    # This fallback is read-only; it never types, clicks, or sends anything.
    if not state.get("draft_present") and not state.get("chat_url"):
        try:
            editor = browser.first_visible(driver, browser.COMPOSER_SELECTORS)
            if editor is not None:
                actual = _normalize_prompt(browser.composer_text(editor))
                if actual and (head in actual or tail in actual):
                    state["draft_present"] = True
                    state["detection"] = "selenium_composer"
                state["selenium_composer_length"] = len(actual)
        except (StaleElementReferenceException, WebDriverException, RuntimeError):
            pass
    return state


def _wait_for_submitted_message(driver, prompt: str, *, timeout: float) -> tuple[bool, dict]:
    deadline = time.monotonic() + timeout
    latest = {}
    while time.monotonic() < deadline:
        latest = _submission_state(driver, prompt)
        if latest.get('confirmed'):
            return True, latest
        time.sleep(0.5)
    return False, latest


def submit_prompt_verified(driver, prompt: str, *, before_click=None) -> str:
    """Wait for enabled Send, click ONCE, and return immediately.

    Deliberately does NOT wait for a conversation URL or response. The caller
    treats a Selenium click without exception as submission success.
    """
    deadline = time.monotonic() + SEND_BUTTON_WAIT_SECONDS
    button = None
    while time.monotonic() < deadline:
        button = _composer_send_button(driver)
        if button is not None:
            break
        time.sleep(0.5)
    if button is None:
        raise RuntimeError("Enabled ChatGPT Send button not found after waiting.")

    # Persist the attempt before the click; avoids accidental duplicate reruns
    # when Selenium raises after an uncertain click.
    if before_click is not None:
        before_click()
    print("Clicking Send once; no post-send verification.", flush=True)
    try:
        button.click()
    except Exception as exc:
        raise RuntimeError(
            "Selenium Send click raised an error. Check ChatGPT manually "
            "before retrying to avoid duplicate submissions."
        ) from exc
    print("Send click completed. Returning success to FastAPI/n8n.", flush=True)
    return "sent"


def read_status(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(record, dict):
            return record
    except (ValueError, OSError) as exc:
        raise RuntimeError(f"Cannot read submission log {path}: {exc}") from exc
    raise RuntimeError(f"Invalid submission log structure: {path}")


def write_status(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _attachment_alias_pattern(filename: str) -> re.Pattern:
    """ChatGPT often displays file.md as file(3).md on repeat uploads."""
    name = Path(filename).name
    stem, suffix = Path(name).stem, Path(name).suffix
    return re.compile(r"(?<![\w.-])" + re.escape(stem) +
                      r"(?:\s*\(\d+\))?" + re.escape(suffix) +
                      r"(?![\w.-])", re.IGNORECASE)


def _composer_attachment_labels(driver) -> str:
    """Read attachment chips only, excluding the typed prompt editor."""
    editor = browser.wait_for_composer(driver)
    return driver.execute_script(r"""
        const editor = arguments[0];
        let root = editor.closest('form');
        if (!root) {
            let el = editor;
            for (let i = 0; i < 8 && el; i++, el = el.parentElement) {
                if (el.querySelector && el.querySelector('input[type="file"], button[data-testid="composer-plus-btn"]')) {
                    root = el; break;
                }
            }
        }
        if (!root) return '';
        const clone = root.cloneNode(true);
        clone.querySelectorAll('#prompt-textarea,[data-testid="prompt-textarea"],textarea,[contenteditable="true"]')
          .forEach(el => el.remove());
        const parts = [clone.textContent || ''];
        clone.querySelectorAll('[title],[aria-label],[data-file-name],[data-filename]')
          .forEach(el => ['title','aria-label','data-file-name','data-filename'].forEach(key => {
              const v = el.getAttribute(key); if(v) parts.push(v);
          }));
        return parts.join('\n');
    """, editor) or ''


def _attachment_visible_renamed(driver, filename: str) -> bool:
    return bool(_attachment_alias_pattern(filename).search(_composer_attachment_labels(driver)))


def attach_grouping_file(driver, path: Path) -> None:
    """Attach once; tolerate numbered display name while waiting for the chip."""
    if not path.is_file() or path.stat().st_size <= 0:
        raise FileNotFoundError(f'Missing or empty attachment: {path}')
    browser.wait_for_composer(driver)
    browser.ensure_file_input(driver).send_keys(str(path.resolve()))
    end = time.monotonic() + browser.ATTACHMENT_TIMEOUT_SECONDS
    while time.monotonic() < end:
        if _attachment_visible_renamed(driver, path.name):
            time.sleep(browser.AFTER_UPLOAD_SECONDS)
            return
        time.sleep(0.3)
    raise RuntimeError(f'Attachment chip for {path.name} was not visible (numbered suffix accepted).')


def verify_grouping_attachments(driver, files) -> None:
    """Check both types of attachments, without requiring their exact UI names."""
    labels = _composer_attachment_labels(driver)
    missing = [p.name for p in files if not _attachment_alias_pattern(p.name).search(labels)]
    if missing:
        raise RuntimeError(f'Attachment chip(s) absent (including numbered variants): {missing}')


def already_uploaded_filename(driver, filename: str) -> bool:
    """Detect a stale file chip in this *composer*, not the chat history."""
    return _attachment_visible_renamed(driver, filename)


def stale_attachment_names(driver) -> list[str]:
    """Best-effort detect old attached files in a restored ChatGPT draft.

    A Project can restore unsent attachments after an old dry run. We must NOT
    mix those files with a new JSON, so fail closed if detected.
    """
    editor = browser.wait_for_composer(driver)
    try:
        labels = driver.execute_script(r"""
            const editor = arguments[0];
            let root = editor.closest('form');
            if (!root) {
                let node = editor;
                for (let depth = 0; depth < 7 && node; depth++, node = node.parentElement) {
                    if (node.querySelector && node.querySelector(
                        'button[data-testid="composer-plus-btn"],input[type="file"]')) {
                        root = node; break;
                    }
                }
            }
            if (!root) return [];
            const clone = root.cloneNode(true);
            clone.querySelectorAll('#prompt-textarea,[data-testid="prompt-textarea"],textarea,[contenteditable="true"]')
              .forEach(e => e.remove());
            const labels = [clone.innerText || clone.textContent || ''];
            clone.querySelectorAll('[aria-label],[title],[data-file-name],[data-filename]')
              .forEach(el => ['aria-label','title','data-file-name','data-filename']
                .forEach(a => { const s = el.getAttribute(a); if (s) labels.push(s); }));
            return labels;
        """, editor)
    except Exception:
        labels = []
    seen: set[str] = set()
    for label in labels or []:
        for match in re.findall(r"(?<![\w.-])[^\s/\\<>\"'\[\],:;]+\.(?:json|md|txt|zip)(?![\w.-])", label, re.I):
            seen.add(match)
    return sorted(seen)


def check_project_url(url: str) -> None:
    parts = urlparse(url)
    if parts.scheme != "https" or parts.hostname != "chatgpt.com" or not re.fullmatch(
        r"/g/g-p-[a-z0-9]+/project", parts.path
    ):
        raise ValueError(f"Expected a new-chat ChatGPT Project URL, not an existing chat: {url}")


def submit(date: str, json_path: Path, master_path: Path, limit: int,
           *, dry_run: bool, force: bool) -> int:
    check_project_url(CHATGPT_GROUPING_PROJECT_URL)
    rows, fields = summarize_json(json_path)
    folder_date = date.replace("-", "_")
    prompt = make_short_prompt(date, json_path.name, limit, rows)
    source_sha = sha256_file(json_path)
    master_sha = sha256_file(master_path)
    status_path = LOG_DIR / f"{date}.json"
    existing = read_status(status_path)

    print("\nChatGPT full-JD job grouping")
    print(f"Date (IST):          {date}")
    print(f"Project:             {CHATGPT_GROUPING_PROJECT_URL}")
    print(f"JSON source:         {json_path} ({json_path.stat().st_size:,} bytes)")
    print(f"Raw record count:    {rows}")
    print(f"Master prompt:       {master_path}")
    print(f"Max experience:      {limit} required years")
    print(f"Output ZIP requested: {folder_date}_job_groups.zip")
    print(f"JSON fields sample:  {', '.join(fields[:30])}")
    print(f"Mode:                {'DRY RUN (offline only)' if dry_run else 'SEND'}")

    if dry_run:
        print("\n--- SHORT PROMPT (no browser opened, no attachments sent) ---")
        print(prompt)
        return 0

    if not force and existing.get("status") == "sent":
        print(f"\nSKIPPED: this date was already CONFIRMED submitted. Log: {status_path}")
        return 0

    if not force and existing.get("status") in {
        "sent_unconfirmed", "attempting_send", "send_unconfirmed",
    }:
        print(
            "ERROR: An earlier submission has an uncertain send status. "
            "Check the existing ChatGPT conversation/draft and "
            f"{status_path} before using --force. Not reporting false success.",
            file=sys.stderr,
        )
        return 1

    driver = browser.attach_to_existing_chrome()
    record = {
        "date": date,
        "source": str(json_path),
        "source_sha256": source_sha,
        "master_prompt": str(master_path),
        "master_sha256": master_sha,
        "max_required_years": limit,
        "input_records": rows,
        "requested_zip": f"{folder_date}_job_groups.zip",
        "project_url": CHATGPT_GROUPING_PROJECT_URL,
        "required_attachments": [json_path.name, master_path.name],
        "status": "failed_before_send",
        "send_click_attempted": False,
        "chat_url": "",
        "timestamp_ist": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(timespec="seconds"),
    }
    try:
        old_draft = browser.open_fresh_chat_tab(driver, CHATGPT_GROUPING_PROJECT_URL)
        if old_draft:
            draft_backup = LOG_DIR / f"{date}_replaced_drafts.json"
            browser.backup_existing_draft(
                draft_backup,
                role="job_grouping",
                project_url=CHATGPT_GROUPING_PROJECT_URL,
                draft=old_draft,
            )
            browser.clear_project_landing_draft(driver)
            print(f"Backed up an old unsent draft: {draft_backup}")

        old_attachments = stale_attachment_names(driver)
        if old_attachments or any(
            already_uploaded_filename(driver, name)
            for name in (json_path.name, master_path.name)
        ):
            raise RuntimeError(
                "An older unsent Project draft still has attachments: "
                f"{old_attachments or 'known input files'}. "
                "Remove the old attachment chips manually and re-run."
            )

        print("Attaching grouping master prompt ...")
        attach_grouping_file(driver, master_path)
        print(f"Attaching scraped JSON ({rows} records) ...")
        attach_grouping_file(driver, json_path)
        verify_grouping_attachments(driver, (master_path, json_path))
        print("Both attachment types verified (numbered filenames accepted).")

        browser.fill_prompt(driver, prompt)
        print("Short prompt verified; attachment name re-check skipped.")

        print(
            f"Allowing {PRE_SEND_SETTLE_SECONDS}s for ChatGPT attachments "
            "and composer to settle before sending...", flush=True
        )
        time.sleep(PRE_SEND_SETTLE_SECONDS)
        print("Waiting for enabled Send button...", flush=True)

        # Persist BEFORE clicking Send: prevents an ambiguous browser action
        # from being silently retried as if nothing happened.
        record["status"] = "attempting_send"
        record["chat_url"] = driver.current_url
        write_status(status_path, record)
        def mark_click_attempted() -> None:
            record["send_click_attempted"] = True
            write_status(status_path, record)

        record["status"] = submit_prompt_verified(
            driver, prompt, before_click=mark_click_attempted
        )
        record["chat_url"] = driver.current_url
        write_status(status_path, record)
        print(f"\n{record['status'].upper()} — ChatGPT chat left open to generate the ZIP.")
        print(f"Conversation: {record['chat_url']}")
        print(f"Submission log: {status_path}")
        return 0
    except Exception as exc:
        if record["status"] == "attempting_send":
            # A false-negative draft check BEFORE any click is not an ambiguous
            # send. Mark it as pre-send failure so the log is accurate.
            if not record.get("send_click_attempted"):
                record["status"] = "failed_before_send"
            else:
                # If a click was attempted, only mark safe when still an
                # unsent draft on the project landing page.
                try:
                    state = _submission_state(driver, prompt)
                    if state.get("draft_present") and not state.get("chat_url"):
                        record["status"] = "failed_before_send"
                    else:
                        record["status"] = "send_unconfirmed"
                except Exception:
                    record["status"] = "send_unconfirmed"
        else:
            record["status"] = "failed_before_send"
        record["error"] = f"{type(exc).__name__}: {exc}"
        try:
            record["chat_url"] = driver.current_url
        except Exception:
            pass
        write_status(status_path, record)
        print(f"\nERROR: {record['error']}", file=sys.stderr)
        return 1
    finally:
        # Deliberately leave the user's Chrome / ChatGPT chat running.
        try:
            driver.service.stop()
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date", default=today_in_ist(), help="YYYY-MM-DD; defaults to today's IST date")
    p.add_argument("--max-years", type=int, default=MAX_REQUIRED_YEARS,
                   help="Maximum *minimum required* years in JD (default: 4)")
    p.add_argument("--json-path", type=Path,
                   help="Optional explicit scraper JSON instead of the day's default file")
    p.add_argument("--master-prompt", type=Path,
                   help=f"Optional path to {MASTER_PROMPT_NAME}")
    p.add_argument("--dry-run", action="store_true", help="Validate JSON and print prompt; NO browser action")
    p.add_argument("--force", action="store_true", help="Intentionally resend a date already logged as sent")
    args = p.parse_args(argv)
    try:
        date = iso_date(args.date)
        if args.max_years < 0 or args.max_years > 50:
            raise ValueError("--max-years must be between 0 and 50")
        json_path = locate_json(date, args.json_path)
        master_path = (args.master_prompt or SERVICES_DIR / MASTER_PROMPT_NAME).resolve()
        if not master_path.is_file() or not master_path.stat().st_size:
            raise FileNotFoundError(f"Missing grouping master prompt: {master_path}")
        return submit(date, json_path, master_path, args.max_years,
                      dry_run=args.dry_run, force=args.force)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
