"""Download and import the newest completed ChatGPT job-grouping ZIP.

Place in: linkedin/services/chatgpt_job_grouping_zip_downloader.py

Run from the JobBots project root:
    python -m linkedin.services.chatgpt_job_grouping_zip_downloader --dry-run
    python -m linkedin.services.chatgpt_job_grouping_zip_downloader
    python -m linkedin.services.chatgpt_job_grouping_zip_downloader --date 2026-10-18
    python -m linkedin.services.chatgpt_job_grouping_zip_downloader --overwrite

Workflow:
  1. Attach to Chrome remote debugger 127.0.0.1:9222 (already signed in).
  2. Open the Job Grouping Project in a NEW tab and CLICK its first/latest chat.
  3. Wait for loading, then scroll up/down (including lazy content) to find
     a real, clickable ZIP link; never mistake filename-only text for a link.
  4. Validate the ZIP, non-empty JD groups, and grouping audit JSON.
  5. Import to job_profile/specific/company/YYYY-MM-DD/<role>/.

The ZIP created by the ChatGPT grouping prompt has an UNDERSCORE date root
(YYYY_MM_DD). Import converts it to HYPHENS (YYYY-MM-DD), which your CV
submission generator expects. Existing different JDs are not overwritten unless
--overwrite is explicitly supplied. In either case existing JDs are backed up
before replacement. No scraper JSON, CV files, or other files are deleted.

This script waits for the page to render and scrolls through completed chat
messages; it does not generate a ZIP on ChatGPT. Run it once the ZIP exists. If Chrome shows the Save As dialog,
disable Chrome Settings > Downloads > Ask where to save each file before downloading.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# ========================= CONFIGURATION =========================
GROUPING_PROJECT_URL = (
    "https://chatgpt.com/g/g-p-6ad503c1e61c819188158eb94d51f314/project"
)
CHROME_DEBUGGER_ADDRESS = "127.0.0.1:9222"
ROLES: dict[str, str] = {
    "aiengineer": "AI Engineer",
    "awsdataengineer": "AWS Data Engineer",
    "dataengineer": "Data Engineer",
    "pythondeveloper": "Python Developer",
    "others": "Others",
}
PROJECT_TIMEOUT_SECONDS = 75
LATEST_CHAT_TIMEOUT_SECONDS = 55
ZIP_LINK_TIMEOUT_SECONDS = 180
DOWNLOAD_TIMEOUT_SECONDS = 240
# For slow Windows/Chrome systems: change these values if necessary.
PAGE_SETTLE_SECONDS = 8.0       # Wait after opening a chat (time.sleep).
SCROLL_PAUSE_SECONDS = 1.7      # Wait after every scroll for lazy rendering.
EXTRA_LAZY_WAIT_SECONDS = 6.0   # Wait at bottom between scanning passes.
SCROLL_STEPS_PER_PASS = 85
SCROLL_PASSES = 3
MAX_UNCOMPRESSED_BYTES = 150 * 1024 * 1024

# file located at <project>/linkedin/services/<script.py>
DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def today_ist() -> str:
    # Fixed UTC+05:30 is sufficient for India and works without tzdata on Windows.
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")


def checked_date(value: str) -> str:
    try:
        d = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use --date YYYY-MM-DD") from exc
    if d.strftime("%Y-%m-%d") != value:
        raise argparse.ArgumentTypeError("Use --date YYYY-MM-DD")
    return value


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def project_id() -> str:
    match = re.search(r"g-p-[a-z0-9]+", urlparse(GROUPING_PROJECT_URL).path)
    if not match:
        raise ValueError("GROUPING_PROJECT_URL must be a ChatGPT Project URL")
    return match.group(0)


def valid_grouping_chat(url: str) -> bool:
    parsed = urlparse(url)
    return bool(
        parsed.hostname in {"chatgpt.com", "www.chatgpt.com"}
        and project_id() in parsed.path
        and re.search(r"/c/[a-z0-9-]+/?$", parsed.path, re.IGNORECASE)
    )


def connect_chrome():
    options = Options()
    options.add_experimental_option("debuggerAddress", CHROME_DEBUGGER_ADDRESS)
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:
        raise RuntimeError(
            "Chrome debugger 127.0.0.1:9222 is unavailable. Start your Chrome "
            "debugger BAT and sign in to ChatGPT."
        ) from exc
    driver.set_page_load_timeout(PROJECT_TIMEOUT_SECONDS)
    return driver


def configure_downloads(driver, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    payload = {"behavior": "allow", "downloadPath": str(directory.resolve())}
    try:
        driver.execute_cdp_cmd("Browser.setDownloadBehavior", payload)
    except WebDriverException:
        try:
            driver.execute_cdp_cmd("Page.setDownloadBehavior", payload)
        except WebDriverException as exc:
            raise RuntimeError("Unable to configure Chrome's download folder") from exc


def wait_document(driver) -> None:
    WebDriverWait(driver, PROJECT_TIMEOUT_SECONDS).until(
        lambda d: d.execute_script("return document.readyState") in {"complete", "interactive"}
    )


def check_expected_site(driver) -> None:
    parsed = urlparse(driver.current_url)
    if parsed.hostname not in {"chatgpt.com", "www.chatgpt.com"}:
        raise RuntimeError(f"Chrome redirected away from ChatGPT: {driver.current_url}")
    if any(part in parsed.path.lower() for part in ("/login", "/auth", "/signup")):
        raise RuntimeError("Sign into ChatGPT manually in your debugger Chrome profile")
    if project_id() not in parsed.path:
        raise RuntimeError(f"Wrong ChatGPT Project: {driver.current_url}")


def locate_latest_link(driver):
    """Search only the Project's central Chats list, not the left sidebar."""
    for css in ("main a[href*='/c/']", '[role="main"] a[href*="/c/"]'):
        for el in driver.find_elements(By.CSS_SELECTOR, css):
            try:
                if el.is_displayed() and valid_grouping_chat(el.get_attribute("href") or ""):
                    return el
            except (WebDriverException, StaleElementReferenceException):
                continue
    return None


def click_latest_row_fallback(driver) -> bool:
    """Fallback for modern Project list rows that aren't rendered as anchors."""
    for css in ("main", '[role="main"]'):
        mains = driver.find_elements(By.CSS_SELECTOR, css)
        if not mains:
            continue
        main = mains[0]
        for xpath in (
            ".//*[normalize-space(text())='Job Grouping ZIP']",
            ".//*[contains(text(),'DATE=') and contains(text(),'INPUT=')]",
        ):
            for el in main.find_elements(By.XPATH, xpath):
                try:
                    if not el.is_displayed():
                        continue
                    target = driver.execute_script("""
                        let node = arguments[0];
                        for (let i = 0; i < 7 && node; i++, node = node.parentElement) {
                            if (node.matches('a,button,[role="link"],[role="button"],'
                                + '[tabindex]:not([tabindex="-1"]),.cursor-pointer')) return node;
                        }
                        return arguments[0];
                    """, el)
                    try:
                        target.click()
                    except (ElementClickInterceptedException, WebDriverException):
                        driver.execute_script("arguments[0].click()", target)
                    return True
                except (WebDriverException, StaleElementReferenceException):
                    continue
    return False


def grouping_submission_chat(root: Path, day: str) -> str | None:
    """Use saved current-date chat if ChatGPT has changed the Project markup."""
    log = root / "linkedin" / "output" / "grouping_chatgpt_logs" / f"{day}.json"
    if not log.is_file():
        return None
    try:
        record = json.loads(log.read_text(encoding="utf-8"))
        url = str(record.get("chat_url") or "")
        if (record.get("date") == day
                and record.get("status") in {"sent", "sent_unconfirmed", "attempting_send"}
                and valid_grouping_chat(url)):
            return url
    except (OSError, ValueError, AttributeError, TypeError):
        return None
    return None


def _safe_get(driver, url: str) -> None:
    """Navigate once; ChatGPT sometimes never reaches 'complete' on slow PCs."""
    try:
        driver.get(url)
    except TimeoutException:
        if urlparse(driver.current_url).hostname not in {"chatgpt.com", "www.chatgpt.com"}:
            raise
        print("Navigation load timeout; continuing with the opened ChatGPT tab")
    wait_document(driver)
    time.sleep(PAGE_SETTLE_SECONDS)


def open_latest_chat(driver, root: Path, day: str, override_url: str | None = None) -> str:
    """ORIGINAL navigation: NEW TAB -> PROJECT -> FIRST/LATEST CHAT CLICK.

    Do not reuse an already-open conversation or prefer the submission log:
    those shortcuts prevented the user's intended Project navigation.  The
    filename is checked after opening the first chat, by find_zip_link().
    """
    # Always open a NEW tab like the user's original working script.
    driver.switch_to.new_window("tab")

    if override_url:
        if not valid_grouping_chat(override_url):
            raise ValueError("--chat-url must point to a conversation in the Grouping Project")
        _safe_get(driver, override_url)
        check_expected_site(driver)
        if not valid_grouping_chat(driver.current_url):
            raise RuntimeError("--chat-url did not open the expected grouping chat")
        print(f"Opened supplied chat: {driver.current_url}")
        return driver.current_url

    print("Opening Job Grouping Project in a NEW Chrome tab...")
    _safe_get(driver, GROUPING_PROJECT_URL)
    check_expected_site(driver)
    if valid_grouping_chat(driver.current_url):
        raise RuntimeError("Project URL redirected into an existing conversation")
    print("Project opened. Finding and clicking the FIRST/LATEST Project chat...")

    # Keep the ORIGINAL central Project-list first-chat selection.  React can
    # take several seconds to populate it even after document.readyState.
    deadline = time.monotonic() + LATEST_CHAT_TIMEOUT_SECONDS
    clicked = False
    while time.monotonic() < deadline:
        newest = locate_latest_link(driver)
        if newest is not None:
            try:
                href = newest.get_attribute("href") or ""
                label = (newest.text or "").strip()
            except StaleElementReferenceException:
                time.sleep(1.5)
                continue
            if not valid_grouping_chat(href):
                time.sleep(1.5)
                continue
            print(f"First/latest Project chat: {label or '(untitled)'}")
            # Important: CLICK the first row, as in the original script.
            try:
                newest.click()
            except (ElementClickInterceptedException,
                    StaleElementReferenceException, WebDriverException):
                print("Chat row click intercepted; opening the same row URL directly")
                _safe_get(driver, href)
            clicked = True
            # If the click didn't navigate, use the exact href of the first row.
            try:
                WebDriverWait(driver, 20, poll_frequency=0.8).until(
                    lambda d: valid_grouping_chat(d.current_url)
                )
            except TimeoutException:
                print("Click did not navigate; opening selected first chat URL")
                _safe_get(driver, href)
            break

        # Original fallback for Project rows displayed as non-anchor elements.
        if click_latest_row_fallback(driver):
            print("Clicked the first matching Project chat row")
            try:
                WebDriverWait(driver, 16, poll_frequency=0.8).until(
                    lambda d: valid_grouping_chat(d.current_url)
                )
                clicked = True
                break
            except TimeoutException:
                print("Project row did not navigate; retrying first chat detection")
        time.sleep(2.0)

    if not clicked:
        # Original last-resort fallback only if the Project list can't be read.
        fallback = grouping_submission_chat(root, day)
        if not fallback:
            raise RuntimeError(
                "Could not identify/click the first chat in the Project. "
                "Pass --chat-url with its complete conversation URL."
            )
        print("Could not click Project row; using today's saved chat URL")
        _safe_get(driver, fallback)

    WebDriverWait(driver, PROJECT_TIMEOUT_SECONDS).until(
        lambda d: valid_grouping_chat(d.current_url)
    )
    check_expected_site(driver)
    print(f"Opened conversation: {driver.current_url}")
    print(f"Waiting {PAGE_SETTLE_SECONDS:g}s for slow ChatGPT messages to load...")
    time.sleep(PAGE_SETTLE_SECONDS)
    return driver.current_url


# JavaScript inspects real clickable controls, not arbitrary <span> elements.
# A filename written as plain text is *not* a download link.
FIND_DOWNLOAD_JS = r"""
const name = arguments[0];
const norm = s => (s || '').replace(/\\_/g, '_').replace(/[\u200b-\u200d\ufeff]/g, '');
const root = document.querySelector('main') || document.querySelector('[role="main"]') || document.body;
const assistant = [...root.querySelectorAll('[data-message-author-role="assistant"]')];
const scopes = assistant.length ? assistant : [root];
let candidates = [];
for (const scope of scopes) {
  for (const el of scope.querySelectorAll('a[href],button,[role="button"],[role="link"]')) {
    const rect = el.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) continue;
    const label = norm([el.innerText, el.textContent, el.getAttribute('aria-label'),
      el.getAttribute('title'), el.getAttribute('download')].filter(Boolean).join(' '));
    const href = norm(el.getAttribute('href') || '');
    const parentText = norm(el.parentElement?.textContent || '').slice(0, 500);
    const isNamed = label.includes(name) || href.includes(name);
    const relatedDownload = !isNamed && /download|save/i.test(label) &&
        parentText.includes(name) && parentText.length < 500;
    if (!isNamed && !relatedDownload) continue;
    if (el.tagName === 'A' && (!href || href === '#' || href.startsWith('javascript:'))) continue;
    // Reject a huge button wrapping the whole message.
    if (label.length > 350) continue;
    let score = 0;
    if (el.tagName === 'A') score += 30;
    if (/sandbox:|backend-api|download|\.zip/i.test(href)) score += 25;
    if (isNamed) score += 15;
    if (/download|save/i.test(label)) score += 5;
    if (scope.getAttribute('data-message-author-role') === 'assistant') score += 10;
    candidates.push({element: el, score, kind: el.tagName, href, label: label.slice(0, 180)});
  }
}
candidates.sort((a, b) => b.score - a.score);
return {
  element: candidates[0]?.element || null,
  href: candidates[0]?.href || '',
  kind: candidates[0]?.kind || '',
  label: candidates[0]?.label || '',
  filename_in_assistant: assistant.some(el => norm(el.textContent).includes(name)),
  filename_in_page: norm(root.textContent).includes(name),
  assistant_count: assistant.length
};
"""


def _scan_zip_control(driver, filename: str) -> dict:
    try:
        return driver.execute_script(FIND_DOWNLOAD_JS, filename) or {}
    except (WebDriverException, StaleElementReferenceException):
        return {}


# Find the actual chat scroller (not the left sidebar). Works with ChatGPT's
# nested-scroll layouts and plain window scrolling, and reselects every time.
SCROLL_CONVERSATION_JS = r"""
const action = arguments[0];
const main = document.querySelector('main') || document.querySelector('[role="main"]') || document.body;
const turn = main.querySelector('[data-message-author-role],[data-testid^="conversation-turn-"]');
const set = new Set([document.scrollingElement, main, ...main.querySelectorAll('*')]);
let options = [];
for (const el of set) {
  if (!el || el.clientHeight < 130 || el.scrollHeight - el.clientHeight < 80) continue;
  const style = getComputedStyle(el);
  if (el !== document.scrollingElement && !/auto|scroll|overlay/.test(style.overflowY)) continue;
  const rect = el.getBoundingClientRect();
  if (rect.width < Math.min(250, window.innerWidth * .25)) continue;
  // Exclude narrow sidebar/chat-list panes.
  if (rect.right < window.innerWidth * .5) continue;
  let score = 0;
  if (turn && el.contains(turn)) score += 100;
  if (el === main) score += 25;
  if (el === document.scrollingElement) score += 10;
  score += Math.min(25, rect.width / 80);
  score += Math.min(25, el.scrollHeight / 1200);
  options.push({el, score});
}
// Prefer the innermost eligible scroller containing the conversation.
// Some ChatGPT layouts nest a scrollable chat pane inside a scrollable main.
if (turn) {
  for (const parent of options) {
    if (options.some(child => child !== parent && parent.el.contains(child.el)
        && child.el.contains(turn))) parent.score -= 45;
  }
}
options.sort((a, b) => b.score - a.score);
const scroller = options[0]?.el || document.scrollingElement;
if (!scroller) return {moved:false, at_end:true, position:0, maximum:0, kind:'none'};
const before = scroller.scrollTop;
const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
const step = Math.max(380, Math.round(scroller.clientHeight * .82));
if (action === 'top') scroller.scrollTop = 0;
if (action === 'bottom') scroller.scrollTop = max;
if (action === 'down') scroller.scrollTop = Math.min(max, before + step);
if (action === 'up') scroller.scrollTop = Math.max(0, before - step);
return {
  moved: Math.abs(scroller.scrollTop - before) > 2,
  at_end: scroller.scrollTop >= max - 3,
  position: Math.round(scroller.scrollTop), maximum: Math.round(max),
  kind: scroller.tagName
};
"""


def _scroll_chat(driver, direction: str) -> dict:
    try:
        return driver.execute_script(SCROLL_CONVERSATION_JS, direction) or {}
    except WebDriverException:
        return {}


def find_zip_link(driver, filename: str):
    """Search real links while scrolling bottom -> top -> down; no navigation."""
    deadline = time.monotonic() + ZIP_LINK_TIMEOUT_SECONDS
    text_seen = False
    total_steps = 0

    def probe():
        nonlocal text_seen
        info = _scan_zip_control(driver, filename)
        text_seen |= bool(info.get('filename_in_assistant'))
        if info.get('element'):
            print(f"Located clickable ZIP control ({info.get('kind')}): {info.get('label')!r}")
            return info['element']
        return None

    found = probe()
    if found:
        return found

    for pass_no in range(1, SCROLL_PASSES + 1):
        if time.monotonic() >= deadline:
            break
        print(f"Searching conversation, scroll pass {pass_no}/{SCROLL_PASSES}...")
        # The answer containing a new ZIP is usually at the bottom.
        _scroll_chat(driver, 'bottom')
        time.sleep(SCROLL_PAUSE_SECONDS)
        found = probe()
        if found:
            return found

        # Read every virtualized segment from top to bottom; scrolling may
        # mount previously invisible messages only when they enter the viewport.
        _scroll_chat(driver, 'top')
        time.sleep(SCROLL_PAUSE_SECONDS)
        found = probe()
        if found:
            return found

        for step in range(SCROLL_STEPS_PER_PASS):
            if time.monotonic() >= deadline:
                break
            info = _scroll_chat(driver, 'down')
            total_steps += 1
            time.sleep(SCROLL_PAUSE_SECONDS)
            found = probe()
            if found:
                return found
            if total_steps % 12 == 0:
                print(f"  Scrolled {total_steps} times; position "
                      f"{info.get('position', '?')}/{info.get('maximum', '?')}")
            if info.get('at_end') or not info.get('moved', True):
                break

        if time.monotonic() < deadline and pass_no < SCROLL_PASSES:
            print('Waiting for slow/lazy ChatGPT messages to render...')
            time.sleep(EXTRA_LAZY_WAIT_SECONDS)

    if text_seen:
        raise RuntimeError(
            f"Found text mentioning {filename}, but no REAL clickable file "
            "link or download button in the assistant messages. "
            "The final-archive filename/code text is not downloadable. "
            "Ask ChatGPT to attach a real ZIP, or provide --chat-url for the "
            "conversation that actually contains the file."
        )
    raise RuntimeError(
        f"Could not find a downloadable {filename} after scrolling "
        f"{total_steps} times. Check the grouping date and selected chat; "
        "use --chat-url to target the exact finished conversation."
    )


def click_zip_link(driver, element, filename: str) -> None:
    """Click a verified real anchor/button; handle slow React re-rendering."""
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center',inline:'nearest'})", element
        )
    except StaleElementReferenceException:
        element = _scan_zip_control(driver, filename).get('element')
        if element is None:
            raise RuntimeError("ZIP link disappeared while scrolling into view")
    time.sleep(1.4)
    try:
        element.click()
        return
    except StaleElementReferenceException:
        element = _scan_zip_control(driver, filename).get('element')
        if element is None:
            raise RuntimeError("ZIP link disappeared before it could be clicked")
        element.click()
        return
    except (ElementClickInterceptedException, WebDriverException):
        pass
    try:
        ActionChains(driver).move_to_element(element).click().perform()
    except WebDriverException:
        driver.execute_script("arguments[0].click()", element)


def wait_for_zip_download(staging: Path, filename: str) -> Path:
    deadline = time.monotonic() + DOWNLOAD_TIMEOUT_SECONDS
    last_size = -1
    stable_since = 0.0
    while time.monotonic() < deadline:
        partial_files = list(staging.glob("*.crdownload")) + list(staging.glob("*.tmp"))
        candidate = staging / filename
        if candidate.is_file() and candidate.stat().st_size > 0 and not partial_files:
            size = candidate.stat().st_size
            if size == last_size and time.monotonic() - stable_since >= 1.5:
                if zipfile.is_zipfile(candidate):
                    return candidate
            elif size != last_size:
                last_size = size
                stable_since = time.monotonic()
        time.sleep(0.4)
    found = sorted(p.name for p in staging.iterdir())
    raise RuntimeError(
        f"Download not completed within {DOWNLOAD_TIMEOUT_SECONDS} seconds; files: {found}. "
        "If Chrome opened a Save As dialog, turn off 'Ask where to save each file' "
        "in Chrome Downloads settings."
    )


def validate_grouping_zip(archive: Path, day: str) -> tuple[dict[str, bytes], dict]:
    """Validate downloaded ZIP; zero-job roles MUST NOT require TXT files."""
    prefixes = {day.replace('-', '_'), day}
    possible = {f"{role}/{role}_jd.txt" for role in ROLES}
    allowed = possible | {"grouping_audit.json"}
    files: dict[str, bytes] = {}
    size_sum = 0
    prefixes_seen: set[str] = set()

    with zipfile.ZipFile(archive, 'r') as zf:
        bad = zf.testzip()
        if bad:
            raise ValueError(f"Corrupt ZIP entry: {bad}")
        for info in zf.infolist():
            raw = info.filename.replace('\\', '/')
            parts = PurePosixPath(raw).parts
            if (info.filename.startswith(('/', '\\'))
                    or re.match(r'^[A-Za-z]:', info.filename)
                    or '..' in parts or not parts):
                raise ValueError(f"Unsafe ZIP entry: {info.filename}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError(f"ZIP symlink is not accepted: {info.filename}")
            if info.is_dir():
                continue
            if len(parts) not in (2, 3) or parts[0] not in prefixes:
                raise ValueError(f"Unexpected ZIP path: {raw}")
            prefixes_seen.add(parts[0])
            relative = '/'.join(parts[1:])
            if relative not in allowed or relative in files:
                raise ValueError(f"Unexpected or duplicate ZIP member: {raw}")
            size_sum += info.file_size
            if size_sum > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("ZIP uncompressed data exceeds 150 MB limit")
            content = zf.read(info)
            if not content:
                raise ValueError(f"Empty ZIP member: {raw}")
            files[relative] = content

    if len(prefixes_seen) != 1:
        raise ValueError("ZIP mixes dated roots or contains no files")
    if 'grouping_audit.json' not in files:
        raise ValueError("Missing mandatory grouping_audit.json")

    group_counts = {role: 0 for role in ROLES}
    for role, display_name in ROLES.items():
        relative = f"{role}/{role}_jd.txt"
        if relative not in files:
            continue  # Valid for zero-job groups.
        try:
            content = files[relative].decode('utf-8-sig')
        except UnicodeError as exc:
            raise ValueError(f"TXT not valid UTF-8: {relative}") from exc
        labels = (
            f"# Role Group: {display_name}",
            '# Emails:',
            '# postedbyurl:',
            '# Jobs included:',
        )
        if not content.startswith(labels[0]):
            raise ValueError(f"Incorrect # Role Group heading in {relative}")
        for label in labels:
            if label not in content[:25000]:
                raise ValueError(f"Missing {label!r} in {relative}")
        match = re.search(r'(?m)^# Jobs included:\s*(\d+)\s*$', content)
        if not match:
            raise ValueError(f"Invalid job count in {relative}")
        count = int(match.group(1))
        if count == 0:
            raise ValueError(f"Zero-job role file must be omitted: {relative}")
        headings = re.findall(r'(?m)^## Job\s+\d+\s*:', content)
        if headings and len(headings) != count:
            raise ValueError(f"{relative}: says {count} jobs but has {len(headings)} blocks")
        if re.search(r'(?mi)^# Emails:.*\bN/A\b', content):
            raise ValueError(f"N/A in email header: {relative}")
        group_counts[role] = count

    try:
        audit = json.loads(files['grouping_audit.json'].decode('utf-8-sig'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("grouping_audit.json must be valid UTF-8 JSON") from exc
    if not isinstance(audit, dict):
        raise ValueError("grouping_audit.json must be a JSON object")
    # Compare with standardized audit counts when present; enforce all five roles.
    audit_counts = audit.get('group_counts')
    if isinstance(audit_counts, dict):
        for role, count in group_counts.items():
            reported = audit_counts.get(role)
            if not isinstance(reported, int) or isinstance(reported, bool):
                raise ValueError(f"Audit missing valid group_counts[{role!r}]")
            if reported != count:
                raise ValueError(
                    f"Audit mismatch {role}: audit={reported}, ZIP TXT={count}"
                )
    return files, {'group_counts': group_counts, 'audit': audit}


def plan_import(files: dict[str, bytes], destination: Path, overwrite: bool) -> list[str]:
    changes: list[str] = []
    conflicts = []
    for relative, content in files.items():
        target = destination / Path(relative)
        if target.is_file():
            if target.read_bytes() == content:
                continue
            if not overwrite:
                conflicts.append(str(target))
        elif target.exists():
            raise RuntimeError(f"Cannot replace a directory with a file: {target}")
        changes.append(relative)
    if conflicts:
        raise FileExistsError(
            "Existing JD/audit files differ; no files were imported. "
            "Use --overwrite to replace these generated files and back up originals:\n"
            + "\n".join(conflicts)
        )
    return changes


def save_zip_copy(source: Path, output_path: Path, overwrite: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        if sha256(source) == sha256(output_path):
            print(f"ZIP already downloaded (identical): {output_path}")
            return
        if not overwrite:
            raise FileExistsError(
                f"Existing downloaded ZIP differs: {output_path}; use --overwrite"
            )
    temp = output_path.with_name(output_path.name + ".new")
    try:
        shutil.copy2(source, temp)
        temp.replace(output_path)
    finally:
        temp.unlink(missing_ok=True)
    print(f"ZIP saved: {output_path}")


def import_files(
    files: dict[str, bytes], destination: Path, *, overwrite: bool, backup_root: Path,
) -> list[str]:
    """Copy validated package; backup changed files before --overwrite."""
    changes = plan_import(files, destination, overwrite)
    if not changes:
        print("All grouped files already exist with identical contents")
        return []

    # Plan and save backups before changing anything.
    backup_files: list[tuple[Path, Path]] = []
    for relative in changes:
        target = destination / Path(relative)
        if target.is_file():
            backup_files.append((target, backup_root / Path(relative)))
    for original, backup in backup_files:
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists():
            raise FileExistsError(f"Backup already exists; cannot overwrite it: {backup}")
        shutil.copy2(original, backup)
        print(f"Backed up original: {backup}")

    for relative in changes:
        target = destination / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".importing")
        try:
            tmp.write_bytes(files[relative])
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
        print(f"Imported: {target}")
    return changes


def execute(root: Path, day: str, dry_run: bool, overwrite: bool,
            chat_url: str | None) -> int:
    output_dir = root / "job_profile" / "download_zip_files"
    dest = root / "job_profile" / "specific" / "company" / day
    name = f"{day.replace('-', '_')}_job_groups.zip"
    archive_path = output_dir / name
    print("ChatGPT LinkedIn job-grouping ZIP downloader")
    print(f"Project:           {GROUPING_PROJECT_URL}")
    print(f"Date (IST):        {day}")
    print(f"Expected ZIP:      {name}")
    print(f"Download folder:   {output_dir}")
    print(f"Extract folder:    {dest}")
    print(f"Mode:              {'DRY RUN' if dry_run else 'DOWNLOAD + IMPORT'}")
    print(f"Page wait:         {PAGE_SETTLE_SECONDS}s, scroll pause: {SCROLL_PAUSE_SECONDS}s")

    driver = None
    try:
        driver = connect_chrome()
        open_latest_chat(driver, root, day, chat_url)
        try:
            link = find_zip_link(driver, name)
        except RuntimeError:
            # Helpful screenshot on the user's own PC; useful with changing UI markup.
            try:
                debug_dir = root / 'linkedin' / 'output' / 'grouping_downloader_debug'
                debug_dir.mkdir(parents=True, exist_ok=True)
                screenshot = debug_dir / f'{day}_zip_search_failed.png'
                driver.save_screenshot(str(screenshot))
                print(f'Debug screenshot: {screenshot}')
            except Exception:
                pass
            raise
        print(f"Found completed ZIP link: {name}")
        if dry_run:
            print("DRY RUN SUCCESS: download and extraction were not started")
            return 0

        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="_jobgroups_", dir=output_dir) as stage_name:
            stage = Path(stage_name)
            configure_downloads(driver, stage)
            try:
                print("Clicking ChatGPT ZIP link; waiting for the download...")
                click_zip_link(driver, link, name)
                staged_zip = wait_for_zip_download(stage, name)
                print(f"Downloaded: {staged_zip.name} ({staged_zip.stat().st_size:,} bytes)")
                files, report = validate_grouping_zip(staged_zip, day)
                counts = report["group_counts"]
                print("Validated ZIP and grouping files:")
                for role, count in counts.items():
                    print(f"  {role:18} {count} jobs")

                # Preflight ALL conflicts before saving or importing.
                plan_import(files, dest, overwrite)
                if archive_path.exists() and sha256(archive_path) != sha256(staged_zip) and not overwrite:
                    raise FileExistsError(
                        f"Different ZIP already saved: {archive_path}. Use --overwrite."
                    )
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_root = output_dir / "backups" / day / f"grouping_{timestamp}"
                save_zip_copy(staged_zip, archive_path, overwrite)
                changed = import_files(
                    files, dest, overwrite=overwrite, backup_root=backup_root,
                )
                print(f"SUCCESS: {len(changed)} files imported, {len(files)} validated total")
                print(f"ZIP retained: {archive_path}")
                print(f"Date-wise destination: {dest}")
                return 0
            finally:
                # Do not leave Chrome downloads redirected to a removed temp folder.
                configure_downloads(driver, output_dir)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        if driver is not None:
            # Leave the browser, its tabs and ChatGPT session open.
            try:
                driver.service.stop()
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=checked_date, default=today_ist(),
                        help="Group date YYYY-MM-DD (default: today in IST)")
    parser.add_argument("--project-root", type=Path, default=DEFAULT_PROJECT_ROOT,
                        help="JobBots root directory (normally automatic)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Find latest chat and expected ZIP without clicking")
    parser.add_argument("--overwrite", action="store_true",
                        help="Replace differing dated role JDs; first back up originals")
    parser.add_argument("--chat-url", help="Optional explicit grouping conversation URL")
    args = parser.parse_args(argv)
    root = args.project_root.expanduser().resolve()
    if not (root / "linkedin").is_dir():
        parser.error(f"JobBots root not found: {root}")
    return execute(root, args.date, args.dry_run, args.overwrite, args.chat_url)


if __name__ == "__main__":
    sys.exit(main())
