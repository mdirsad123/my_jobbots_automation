"""Submit four independent role-CV requests to ChatGPT, then stop.

The script DOES NOT wait for generated CVs, download documents, or merge ZIPs.
Each role opens a new chat in its OWN ChatGPT Project.
Each new chat receives ONE attachment: its current role JD.
The master prompt and resume files are already in each ChatGPT Project's Sources.
The JD attachment MUST be verified inside the composer before Send.

Project landing pages can reopen with an UN-SENT old prompt draft. Before attaching
new files, this script backs up old draft text locally and clears just the new-chat
composer. It NEVER edits an existing /c/<conversation-id> conversation.

From your project root (Python 3.10+):
    pip install -U selenium
    python -m linkedin.services.chatgpt_cvs_generator \
        "job_profile\\specific\\company\\2026-10-18" --dry-run
    python -m linkedin.services.chatgpt_cvs_generator \
        "job_profile\\specific\\company\\2026-10-18"

Or run this file directly:
    python chatgpt_cvs_generator.py "job_profile\\specific\\company\\2026-10-18"

Chrome must ALREADY be open and signed in to ChatGPT, for example:
    chrome.exe --remote-debugging-port=9222 ^
      --user-data-dir="C:\\selenium\\chatgpt-debug-profile"

The role-specific /project landing URLs below are intentional: never open an
existing /c/<id> conversation when submitting a new role. Changes to ChatGPT's UI may require
updating the Selenium selectors. No CAPTCHA/login bypass is attempted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    JavascriptException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

# ============================= USER SETTINGS ==============================

ROLE_FOLDERS = (
    "aiengineer",
    "awsdataengineer",
    "dataengineer",
    "pythondeveloper",
)

# Dedicated ChatGPT PROJECT landing pages, one project per ROLE.
# Use /project pages, NOT existing conversations ending in /c/<id>.
ROLE_PROJECT_URLS: dict[str, str] = {
    "aiengineer": (
        "https://chatgpt.com/g/g-p-6ad4d288ac7c81918f8a37d44b485efa/project"
    ),
    "awsdataengineer": (
        "https://chatgpt.com/g/g-p-6ad4d3df646481919b57dc116e98be5b/project"
    ),
    "dataengineer": (
        "https://chatgpt.com/g/g-p-6ad4d3eb4e3881918beb94639237e5fb/project"
    ),
    "pythondeveloper": (
        "https://chatgpt.com/g/g-p-6ad4d3d115b88191a0927cd7080b617d/project"
    ),
}
CHROME_DEBUGGER_ADDRESS = "127.0.0.1:9222"

# True: submit each prompt and proceed immediately to the next role.
# Use --dry-run to inspect the attachments and prompts without sending.
SEND_REQUESTS = True

PAGE_LOAD_TIMEOUT_SECONDS = 40
ELEMENT_TIMEOUT_SECONDS = 35
ATTACHMENT_TIMEOUT_SECONDS = 55
SEND_TIMEOUT_SECONDS = 35
AFTER_UPLOAD_SECONDS = 1.5
BETWEEN_REQUESTS_SECONDS = 2.0

RESULTS_FILENAME = "chatgpt_submission_results.json"
DRAFT_BACKUP_FILENAME = "chatgpt_replaced_drafts.json"


@dataclass(frozen=True)
class RoleRequest:
    role: str
    project_url: str
    jd_path: Path
    date: str
    prompt: str


def validate_role_projects() -> None:
    """Fail before opening Chrome if a role/project mapping is wrong."""
    if set(ROLE_PROJECT_URLS) != set(ROLE_FOLDERS):
        raise ValueError("Each supported role must have one project URL")
    if len(set(ROLE_PROJECT_URLS.values())) != len(ROLE_FOLDERS):
        raise ValueError("Each role must point to a DIFFERENT ChatGPT Project")
    for role, url in ROLE_PROJECT_URLS.items():
        parsed = urlparse(url)
        if (parsed.scheme != "https" or parsed.hostname != "chatgpt.com"
                or not re.fullmatch(r"/g/g-p-[a-z0-9]+/project", parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError(f"Invalid Project landing URL for {role}: {url}")


# ============================= ROLE DISCOVERY =============================

def find_jd_text(role: str, role_folder: Path) -> Path:
    """Prefer jd.txt / <role>_jd.txt, reject ambiguous JD selection."""
    files = sorted(
        (p for p in role_folder.rglob("*") if p.is_file() and p.suffix.lower() == ".txt"),
        key=lambda p: str(p).casefold(),
    )
    # Prefer the explicitly named role JD over a generic jd.txt.
    for expected in (f"{role}_jd.txt", "jd.txt"):
        matches = [p for p in files if p.name.casefold() == expected]
        if len(matches) == 1:
            return matches[0].resolve()
        if len(matches) > 1:
            raise ValueError(f"Multiple {expected} candidates: {matches}")

    matches = [
        p for p in files
        if "jd" in p.stem.casefold() and "reply" not in p.stem.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected ONE JD in {role_folder}, found {len(matches)} possible files: {matches}"
        )
    return matches[0].resolve()


def build_prompt(role: str, jd_filename: str, day: str) -> str:
    """Pin both OUTER ZIP name and the five INNER filenames explicitly."""
    archive = f"{day}_{role}.zip"
    return (
        f"DATE={day}; ROLE={role}. "
        f"Use the attached current JD {jd_filename} and the truthful canonical "
        f"candidate context from specific/master_prompt.txt and md_irsad.md. "
        f"For this request, the EXACT five file names inside {day}/{role}/ are: "
        f"md_irsad_cv_{role}.md, md_irsad_cv_{role}.pdf, "
        f"md_irsad_cv_{role}.docx, jd_email_reply_{day}.txt, "
        f"interview_prep_{role}_{day}.pdf. "
        f"The three CV file names MUST NOT contain a date. "
        f"Generate and link exactly ONE downloadable archive named {archive} "
        f"(hyphens in date; no prefix/suffix/version). "
        f"These exact filenames OVERRIDE any older date-based names in cached "
        f"Project files or prior chats. Follow the current Section 13 for all "
        f"other requirements: truthful role-level CV, 2-page portrait CV PDF and "
        f"DOCX, email TXT and anonymous 16:9 interview-prep PDF. "
        f"Validate ZIP integrity and five files; never mix employers. "
        f"If Project source files are inaccessible, say so."
    )


def jd_has_jobs(jd_path: Path) -> bool:
    """Exclude zero-job grouped JD files without blocking genuine plain JDs."""
    raw = jd_path.read_text(encoding="utf-8-sig", errors="replace")
    if not raw.strip():
        return False
    match = re.search(r"(?im)^\s*#\s*Jobs\s+included\s*:\s*(\d+)\b", raw)
    return match is None or int(match.group(1)) > 0


def discover_role_requests(daily_folder: Path) -> list[RoleRequest]:
    # Date must come from the selected folder, not from an old JD's scrape date.
    try:
        parsed = datetime.strptime(daily_folder.name, "%Y-%m-%d")
        if parsed.strftime("%Y-%m-%d") != daily_folder.name:
            raise ValueError
    except ValueError as exc:
        raise ValueError(
            f"Daily folder should have format YYYY-MM-DD: {daily_folder}"
        ) from exc

    result: list[RoleRequest] = []
    for role in ROLE_FOLDERS:
        folder = daily_folder / role
        if not folder.is_dir():
            print(f"SKIP: {role} folder not found")
            continue
        try:
            jd = find_jd_text(role, folder)
        except Exception as exc:
            print(f"SKIP: {role} - JD discovery failed: {exc}")
            continue
        if not jd_has_jobs(jd):
            print(f"SKIP: {role} - grouped JD has zero jobs or is empty")
            continue
        result.append(RoleRequest(
            role=role,
            project_url=ROLE_PROJECT_URLS[role],
            jd_path=jd,
            date=daily_folder.name,
            prompt=build_prompt(role, jd.name, daily_folder.name),
        ))
    return result




# ============================== SELENIUM ================================

def attach_to_existing_chrome() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", CHROME_DEBUGGER_ADDRESS)
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:
        raise RuntimeError(
            "Cannot attach to Chrome. Start Chrome with --remote-debugging-port=9222 "
            "and a separate --user-data-dir, sign in to ChatGPT, then retry. "
            f"Details: {exc}"
        ) from exc
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
    return driver


def visible_elements(driver: webdriver.Chrome, selectors: Sequence[tuple[str, str]]) -> list[WebElement]:
    for by, selector in selectors:
        try:
            found = [x for x in driver.find_elements(by, selector) if x.is_displayed()]
            if found:
                return found
        except (StaleElementReferenceException, WebDriverException):
            continue
    return []


def first_visible(driver: webdriver.Chrome, selectors: Sequence[tuple[str, str]]) -> WebElement | None:
    found = visible_elements(driver, selectors)
    return found[-1] if found else None


# Selectors are intentionally ChatGPT-specific, not Claude selectors.
COMPOSER_SELECTORS: tuple[tuple[str, str], ...] = (
    (By.CSS_SELECTOR, '#prompt-textarea[contenteditable="true"]'),
    (By.CSS_SELECTOR, '[data-testid="prompt-textarea"][contenteditable="true"]'),
    (By.CSS_SELECTOR, 'div.ProseMirror[contenteditable="true"]'),
    (By.CSS_SELECTOR, 'textarea#prompt-textarea'),
    (By.CSS_SELECTOR, 'textarea[data-testid="prompt-textarea"]'),
)

ATTACH_BUTTON_SELECTORS: tuple[tuple[str, str], ...] = (
    (By.CSS_SELECTOR, 'button[data-testid="composer-plus-btn"]'),
    (By.CSS_SELECTOR, 'button[aria-label="Attach files"]'),
    (By.CSS_SELECTOR, 'button[aria-label="Add files"]'),
    (By.CSS_SELECTOR, 'button[aria-label="Add photos and files"]'),
    (By.XPATH, "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'attach')]") ,
    (By.XPATH, "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add files')]") ,
)

UPLOAD_MENU_SELECTORS: tuple[tuple[str, str], ...] = (
    (By.XPATH, "//*[@role='menuitem'][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'upload')]") ,
    (By.XPATH, "//*[self::button or @role='menuitem'][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'photos and files')]") ,
    (By.XPATH, "//*[self::button or @role='menuitem'][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'from computer')]") ,
)

SEND_SELECTORS: tuple[tuple[str, str], ...] = (
    (By.CSS_SELECTOR, 'button[data-testid="send-button"]'),
    (By.CSS_SELECTOR, 'button[aria-label="Send prompt"]'),
    (By.CSS_SELECTOR, 'button[aria-label="Send message"]'),
    (By.CSS_SELECTOR, 'button[aria-label="Send"]'),
    (By.CSS_SELECTOR, 'button[title="Send prompt"]'),
    (By.CSS_SELECTOR, 'button[title="Send"]'),
    (By.XPATH, "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'send prompt')]") ,
)


def assert_chatgpt_login_and_new_chat(driver: webdriver.Chrome, expected_url: str) -> None:
    url = driver.current_url or ""
    parsed = urlparse(url)
    if parsed.hostname not in {"chatgpt.com", "www.chatgpt.com"}:
        raise RuntimeError(f"Not a signed-in ChatGPT chat page: {url}")
    low = url.lower()
    if any(part in low for part in ("/auth/", "/login", "/signup")):
        raise RuntimeError("Please log in to ChatGPT manually before running Selenium.")
    if "/c/" in parsed.path.lower():
        raise RuntimeError(
            f"ChatGPT opened an EXISTING conversation ({url}). Skipping to "
            "avoid interrupting or overwriting another in-progress chat. "
            "Check ROLE_PROJECT_URLS; a project landing/new-chat URL is required."
        )
    # Don't silently fall out of the specified Project into a normal chat.
    expected_path = urlparse(expected_url).path
    match = re.search(r"g-p-[a-z0-9]+", expected_path)
    if match and match.group(0) not in parsed.path:
        raise RuntimeError(
            f"Expected project {match.group(0)} but ChatGPT navigated to {url}. "
            "Open the project manually and verify its landing URL."
        )


def wait_for_composer(driver: webdriver.Chrome) -> WebElement:
    try:
        return WebDriverWait(driver, ELEMENT_TIMEOUT_SECONDS).until(
            lambda d: first_visible(d, COMPOSER_SELECTORS) or False
        )
    except TimeoutException as exc:
        raise RuntimeError(
            "ChatGPT prompt composer not found. Check login, access to the "
            "Project, and whether the ChatGPT UI changed."
        ) from exc


def composer_text(composer: WebElement) -> str:
    try:
        if composer.tag_name.lower() == "textarea":
            return composer.get_attribute("value") or ""
        return composer.get_attribute("innerText") or composer.text or ""
    except StaleElementReferenceException:
        return ""


def open_fresh_chat_tab(driver: webdriver.Chrome, url: str) -> str:
    """Open a fresh Project landing tab; return any PREEXISTING draft text.

    ChatGPT may restore an unsent draft for the Project even in a brand-new tab.
    Merely opening a new tab is not the same as clearing that saved draft.
    """
    driver.switch_to.new_window("tab")
    driver.get(url)
    WebDriverWait(driver, PAGE_LOAD_TIMEOUT_SECONDS).until(
        lambda d: d.execute_script("return document.readyState") in {"interactive", "complete"}
    )
    assert_chatgpt_login_and_new_chat(driver, url)
    return composer_text(wait_for_composer(driver)).strip()


def backup_existing_draft(
    backup_path: Path, *, role: str, project_url: str, draft: str,
) -> None:
    """Persist a copy BEFORE replacing the unsent draft in the Project landing page."""
    if not draft:
        return
    existing: list[dict] = []
    if backup_path.exists():
        try:
            loaded = json.loads(backup_path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = loaded
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                f"Cannot read previous draft backup {backup_path}. "
                "Refusing to change the Project draft."
            ) from exc
    existing.append({
        "role": role,
        "project_url": project_url,
        "draft_text": draft,
        "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    })
    tmp = backup_path.with_suffix(backup_path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(backup_path)


def clear_project_landing_draft(driver: webdriver.Chrome) -> None:
    """Clear ONLY the unsent composer of an already-verified Project landing page.

    Existing conversations remain untouched. The caller must back up the draft
    first, before calling this function.
    """
    editor = wait_for_composer(driver)
    if not composer_text(editor).strip():
        return
    safe_click(driver, editor)
    editor.send_keys(Keys.CONTROL, "a")
    editor.send_keys(Keys.BACKSPACE)
    end = time.monotonic() + 5
    while time.monotonic() < end:
        if not composer_text(wait_for_composer(driver)).strip():
            return
        time.sleep(0.2)
    raise RuntimeError(
        "Could not clear the saved Project landing-page draft; "
        "files and the new prompt were NOT submitted."
    )


def safe_click(driver: webdriver.Chrome, element: WebElement) -> None:
    try:
        element.click()
    except (ElementClickInterceptedException, StaleElementReferenceException, WebDriverException):
        # Click fallback is only for a known, explicitly located button.
        driver.execute_script("arguments[0].click();", element)


def get_file_input(driver: webdriver.Chrome) -> WebElement | None:
    try:
        return driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')[-1]
    except (WebDriverException, IndexError):
        return None


def ensure_file_input(driver: webdriver.Chrome) -> WebElement:
    current = get_file_input(driver)
    if current is not None:
        return current

    button = first_visible(driver, ATTACH_BUTTON_SELECTORS)
    if button is None:
        raise RuntimeError("ChatGPT Attach/plus button not found.")
    safe_click(driver, button)

    end = time.monotonic() + 8
    while time.monotonic() < end:
        found = get_file_input(driver)
        if found is not None:
            return found
        menu = first_visible(driver, UPLOAD_MENU_SELECTORS)
        if menu is not None:
            safe_click(driver, menu)
        time.sleep(0.25)
    raise RuntimeError("ChatGPT file upload input not found after opening attachment menu.")


def attachment_visible(driver: webdriver.Chrome, filename: str) -> bool:
    """Check the attachment chips within the CURRENT composer form, not page body.

    This avoids false positives from older messages or the ChatGPT sidebar. The
    editable prompt text is excluded as well, so simply typing a filename in
    the prompt never counts as a successful upload.
    """
    try:
        composer = wait_for_composer(driver)
        return bool(driver.execute_script(r"""
            const composer = arguments[0], filename = arguments[1].toLowerCase();
            // The ChatGPT editor can be inside a form OR inside a composer
            // panel without a form, depending on the current UI version.
            let root = composer.closest('form');
            if (!root) {
                let node = composer;
                for (let depth = 0; depth < 7 && node; depth++, node = node.parentElement) {
                    if (node.querySelector && node.querySelector(
                        'button[data-testid="composer-plus-btn"], ' +
                        'button[aria-label="Attach files"], ' +
                        'button[aria-label="Add files"], ' +
                        'input[type="file"]'
                    )) {
                        root = node;
                        break;
                    }
                }
            }
            if (!root || root === document.body) return false;
            const clone = root.cloneNode(true);
            clone.querySelectorAll(
                '#prompt-textarea, [data-testid="prompt-textarea"], '
                + 'textarea, [contenteditable="true"]'
            ).forEach(el => el.remove());
            const parts = [clone.textContent || ''];
            clone.querySelectorAll('[title],[aria-label],[data-file-name],[data-filename]')
                .forEach(el => {
                    for (const attr of ['title','aria-label','data-file-name','data-filename']) {
                        const val = el.getAttribute(attr);
                        if (val) parts.push(val);
                    }
                });
            return parts.join('\n').toLowerCase().includes(filename);
        """, composer, filename))
    except (StaleElementReferenceException, WebDriverException, RuntimeError):
        return False


def verify_all_attachments(driver: webdriver.Chrome, files: Sequence[Path]) -> None:
    """Refuse to send unless the required JD has its own attachment chip."""
    names = [p.name for p in files]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError(f"Duplicate attachment filenames: {names}")
    missing = [name for name in names if not attachment_visible(driver, name)]
    if missing:
        raise RuntimeError(
            f"SEND BLOCKED: attachment chip(s) missing: {missing}. "
            f"Expected attachment: {names}. Check this ChatGPT tab."
        )


def attach_file(driver: webdriver.Chrome, file_path: Path) -> None:
    if not file_path.is_file() or file_path.stat().st_size == 0:
        raise FileNotFoundError(f"Missing or empty attachment: {file_path}")
    wait_for_composer(driver)
    ensure_file_input(driver).send_keys(str(file_path.resolve()))

    end = time.monotonic() + ATTACHMENT_TIMEOUT_SECONDS
    while time.monotonic() < end:
        if attachment_visible(driver, file_path.name):
            time.sleep(AFTER_UPLOAD_SECONDS)
            return
        time.sleep(0.3)
    raise TimeoutException(
        f"ChatGPT did not show the '{file_path.name}' attachment chip "
        f"within its composer form. Send was NOT clicked."
    )

def fill_prompt(driver: webdriver.Chrome, message: str) -> None:
    composer = wait_for_composer(driver)
    safe_click(driver, composer)
    if composer_text(composer).strip():
        raise RuntimeError("Composer already has text; not overwriting it.")
    # Send prompt as one paragraph to avoid Enter inadvertently sending early.
    composer.send_keys(message)
    actual = " ".join(composer_text(wait_for_composer(driver)).split())
    expected = " ".join(message.split())
    if actual != expected:
        raise RuntimeError(
            f"ChatGPT composer text verification failed ({len(actual)} vs {len(expected)} chars)."
        )

def submit_prompt(driver: webdriver.Chrome) -> str:
    """Click Send exactly ONCE. Never retry an ambiguous submission."""
    time.sleep(20)  # Wait 20 seconds for ChatGPT file upload to finish
    until = time.monotonic() + SEND_TIMEOUT_SECONDS
    send: WebElement | None = None
    while time.monotonic() < until:
        for element in visible_elements(driver, SEND_SELECTORS):
            try:
                if element.is_enabled():
                    send = element
                    break
            except StaleElementReferenceException:
                pass
        if send is not None:
            break
        time.sleep(0.3)
    if send is None:
        raise TimeoutException("ChatGPT Send button not enabled or not found.")

    safe_click(driver, send)
    until = time.monotonic() + SEND_TIMEOUT_SECONDS
    while time.monotonic() < until:
        try:
            if "/c/" in urlparse(driver.current_url).path:
                return "sent"
            if not composer_text(wait_for_composer(driver)).strip():
                return "sent_unconfirmed"
        except (StaleElementReferenceException, WebDriverException):
            pass
        time.sleep(0.3)
    return "sent_unconfirmed"


# ============================ RESULTS / MAIN =============================

def read_results(path: Path, date: str) -> dict:
    if path.is_file():
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            if obj.get("date") == date and isinstance(obj.get("roles"), dict):
                return obj
        except (json.JSONDecodeError, UnicodeError, OSError):
            pass
    return {"date": date, "roles": {}}


def save_results(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def run(daily_folder: Path, *, send: bool, force: bool) -> int:
    daily_folder = daily_folder.expanduser().resolve()
    if not daily_folder.is_dir():
        raise NotADirectoryError(f"Daily JD folder not found: {daily_folder}")

    validate_role_projects()
    requests = discover_role_requests(daily_folder)
    if not requests:
        raise RuntimeError(f"No valid JD role folders in {daily_folder}")
    if daily_folder.parent.name != "company":
        raise ValueError("Expected directory layout: specific/company/YYYY-MM-DD/<role>/JD.txt")

    results_path = daily_folder / RESULTS_FILENAME
    draft_backup_path = daily_folder / DRAFT_BACKUP_FILENAME
    report = read_results(results_path, daily_folder.name)

    print(f"Date: {daily_folder.name}")
    print(f"Requests discovered: {len(requests)}")
    print("Project context: use previously uploaded specific.zip (NO context upload)")
    print("Role-specific ChatGPT Project URLs:")
    for request in requests:
        print(f"  {request.role}: {request.project_url}")
    print(f"Mode: {'SEND' if send else 'DRY RUN'}")
    print("No files will be downloaded or merged by this script.\n")

    pending = []
    for role_request in requests:
        previous = report["roles"].get(role_request.role, {})
        if send and not force and previous.get("status") in {"sent", "sent_unconfirmed"}:
            print(f"SKIP {role_request.role}: previously submitted; use --force to resend")
        else:
            pending.append(role_request)
    if not pending:
        print(f"No new requests. See {results_path}")
        return 0

    driver: webdriver.Chrome | None = None
    fail_count = 0
    try:
        driver = attach_to_existing_chrome()
        for idx, req in enumerate(pending):
            status = "failed"
            details = ""
            url = ""
            print(f"\n[{idx + 1}/{len(pending)}] {req.role} - {req.jd_path.name}")
            print(f"  PROJECT: {req.project_url}")
            print(f"  JD PATH: {req.jd_path}")
            print(f"  ROLE-SPECIFIC PROMPT JD: {req.jd_path.name}")
            try:
                old_draft = open_fresh_chat_tab(driver, req.project_url)
                if old_draft:
                    backup_existing_draft(
                        draft_backup_path,
                        role=req.role,
                        project_url=req.project_url,
                        draft=old_draft,
                    )
                    clear_project_landing_draft(driver)
                    print(
                        "  Removed old unsent Project draft "
                        f"(backup: {draft_backup_path.name})"
                    )
                # If a prior unsent draft has file chips, do not mix them with
                # today's JD. Clearing prompt text does not necessarily remove
                # previously uploaded attachments in ChatGPT.
                known_attachments = [
                    "chatgpt_cv_context.zip",  # Legacy unsent attachment only; never uploaded
                    *(f"{role}_jd.txt" for role in ROLE_FOLDERS),
                    "jd.txt",
                ]
                previous_files = [
                    name for name in known_attachments
                    if attachment_visible(driver, name)
                ]
                if previous_files:
                    raise RuntimeError(
                        "Old file attachment(s) are still present in this "
                        f"Project draft: {previous_files}. Remove those old "
                        "attachment chips manually and rerun this role; "
                        "new files will not be mixed with old uploads."
                    )
                print("  Using Project's existing specific.zip / master_prompt.txt")
                print("  Attaching ONLY the current role JD")
                attach_file(driver, req.jd_path)
                required_files = (req.jd_path,)
                verify_all_attachments(driver, required_files)
                print(f"  VERIFIED JD attachment: {req.jd_path.name}")
                fill_prompt(driver, req.prompt)
                verify_all_attachments(driver, required_files)
                print("  VERIFIED prompt and JD attachment; ready for Send")
                if send:
                    status = submit_prompt(driver)
                    print(f"  {status.upper()}: chat remains open")
                else:
                    status = "draft_ready"
                    print("  DRY RUN: request staged only; Send not clicked")
                url = driver.current_url
            except Exception as exc:
                fail_count += 1
                details = f"{type(exc).__name__}: {exc}"
                print(f"  ERROR: {details}")
                if driver is not None:
                    try:
                        url = driver.current_url
                    except WebDriverException:
                        pass
            finally:
                report["roles"][req.role] = {
                    "status": status,
                    "jd_filename": req.jd_path.name,
                    "jd_path": str(req.jd_path),
                    "project_url": req.project_url,
                    "required_attachments": [req.jd_path.name],
                    "chat_url": url,
                    "timestamp_local": datetime.now().astimezone().isoformat(timespec="seconds"),
                    **({"error": details} if details else {}),
                }
                save_results(results_path, report)
            if idx < len(pending) - 1:
                time.sleep(BETWEEN_REQUESTS_SECONDS)
    finally:
        if driver is not None:
            # Disconnect chromedriver, do NOT close or quit Chrome or its tabs.
            try:
                driver.service.stop()
            except Exception:
                pass
    print(f"\nCompleted submission pass; failed={fail_count}; results={results_path}")
    print("Tabs remain open. ChatGPT can work on each role separately.")
    return 1 if fail_count else 0


def latest_daily_folder(project_root: Path) -> Path:
    company = project_root / "job_profile" / "specific" / "company"
    if not company.is_dir():
        raise FileNotFoundError(f"Daily job folder not found: {company}")
    valid = []
    for path in company.iterdir():
        if not path.is_dir():
            continue
        try:
            date = datetime.strptime(path.name, "%Y-%m-%d")
            if path.name == date.strftime("%Y-%m-%d"):
                valid.append(path)
        except ValueError:
            pass
    if not valid:
        raise FileNotFoundError(f"No valid YYYY-MM-DD folders found in {company}")
    return max(valid, key=lambda p: p.name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("daily_folder", nargs="?", type=Path,
                        help="Path to job_profile/specific/company/YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Attach and fill; do not send")
    parser.add_argument("--force", action="store_true", help="Resend roles already logged as sent")
    args = parser.parse_args(argv)
    daily_folder = args.daily_folder or latest_daily_folder(Path.cwd())
    return run(daily_folder, send=SEND_REQUESTS and not args.dry_run,
               force=args.force)


if __name__ == "__main__":
    sys.exit(main())
