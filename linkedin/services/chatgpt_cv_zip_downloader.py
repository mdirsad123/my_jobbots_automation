"""Download completed CV ZIPs from the LATEST chat in each ChatGPT Project.

Save to:
    linkedin/services/chatgpt_cv_zip_downloader.py

Run from the JobBots project root:
    python -m linkedin.services.chatgpt_cv_zip_downloader --dry-run
    python -m linkedin.services.chatgpt_cv_zip_downloader
    python -m linkedin.services.chatgpt_cv_zip_downloader --role pythondeveloper
    python -m linkedin.services.chatgpt_cv_zip_downloader --date 2026-10-18

Only roles with a nonempty <role>_jd.txt or jd.txt under today's date folder
are visited. Previously downloaded and imported ZIPs are reused locally, so
rerunning the script does not restart successfully completed roles. Missing
ZIP links are skipped after at most three up/down conversation scans.

Chrome must be running with remote debugger port 9222 and signed in to ChatGPT.
The script does NOT submit prompts or wait for CV generation. It checks the
newest chat in each Project, downloads the expected date-and-role ZIP if ready,
validates it, and imports five outputs into company/YYYY-MM-DD/<role>/. Original
JD files are never overwritten. Other roles continue even if one fails.

Important: Project conversations are selected from the project's Chats list
(newest at the top). If the newest chat has not completed, that role is skipped;
the script will NOT quietly download an older chat's ZIP. As a fallback only
when UI chat links are unavailable, the matching dated submission log can supply
the most recently submitted conversation URL.

Chrome downloads are configured through DevTools, so no Windows Save As
keystrokes are required. If Save As still appears, disable Chrome Settings >
Downloads > 'Ask where to save each file before downloading'.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import stat
import sys
import tempfile
import time
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

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

# ========================= USER SETTINGS =========================
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
ROLE_FOLDERS = tuple(ROLE_PROJECT_URLS)
DEBUGGER_ADDRESS = "127.0.0.1:9222"
PROJECT_TIMEOUT_SECONDS = 35
PROJECT_CHAT_LIST_TIMEOUT_SECONDS = 10
MAX_ZIP_SEARCH_ATTEMPTS = 3
ZIP_SEARCH_ATTEMPT_TIMEOUT_SECONDS = 30  # Timeout for EACH up/down scan.
SCROLL_SETTLE_SECONDS = 0.35
DOWNLOAD_TIMEOUT_SECONDS = 180
MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
SUBMISSION_RESULTS_FILENAME = "chatgpt_submission_results.json"


@dataclass(frozen=True)
class PackageInfo:
    date: str
    role: str
    filename: str


def valid_date(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must be YYYY-MM-DD") from exc
    if parsed.strftime("%Y-%m-%d") != value:
        raise argparse.ArgumentTypeError("Date must be YYYY-MM-DD")
    return value


def today_ist() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def attach_chrome() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", DEBUGGER_ADDRESS)
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:
        raise RuntimeError(
            "Chrome debugger is not available on 127.0.0.1:9222. "
            "Start Chrome with your debugger BAT file and sign in to ChatGPT first."
        ) from exc
    driver.set_page_load_timeout(45)
    return driver


def set_download_directory(driver: webdriver.Chrome, path: Path) -> None:
    """Use CDP to suppress Windows Save As and direct completed downloads."""
    path.mkdir(parents=True, exist_ok=True)
    params = {"behavior": "allow", "downloadPath": str(path.resolve())}
    try:
        driver.execute_cdp_cmd("Browser.setDownloadBehavior", params)
    except WebDriverException as browser_error:
        try:
            driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        except WebDriverException as page_error:
            raise RuntimeError(
                "Could not set Chrome download folder through DevTools. "
                f"Browser error: {browser_error}; Page error: {page_error}"
            ) from page_error


def _project_identifier(project_url: str) -> str:
    match = re.search(r"g-p-[a-z0-9]+", urlparse(project_url).path)
    if not match:
        raise ValueError(f"Invalid project URL: {project_url}")
    return match.group(0)


def _is_role_conversation(url: str, project_url: str) -> bool:
    parsed = urlparse(url)
    return bool(
        parsed.hostname in {"chatgpt.com", "www.chatgpt.com"}
        and re.search(r"/c/[a-z0-9-]+(?:/)?$", parsed.path, re.I)
        and _project_identifier(project_url) in parsed.path
    )


def _check_signed_in(driver: webdriver.Chrome, project_url: str) -> None:
    parsed = urlparse(driver.current_url)
    if parsed.hostname not in {"chatgpt.com", "www.chatgpt.com"}:
        raise RuntimeError(f"ChatGPT redirected outside its website: {driver.current_url}")
    if any(part in parsed.path.lower() for part in ("/auth", "/login", "/signup")):
        raise RuntimeError("Sign in to ChatGPT in the debugger Chrome profile")
    if _project_identifier(project_url) not in parsed.path:
        raise RuntimeError(f"Wrong ChatGPT Project opened: {driver.current_url}")


def open_role_project(driver: webdriver.Chrome, role: str) -> None:
    url = ROLE_PROJECT_URLS[role]
    driver.switch_to.new_window("tab")
    driver.get(url)
    WebDriverWait(driver, PROJECT_TIMEOUT_SECONDS).until(
        lambda d: d.execute_script("return document.readyState") in {"interactive", "complete"}
    )
    _check_signed_in(driver, url)
    if _is_role_conversation(driver.current_url, url):
        raise RuntimeError("Expected the Project landing page, not an existing chat")
    print(f"Opened {role} Project: {driver.current_url}")


def _latest_chat_from_ui(driver: webdriver.Chrome, project_url: str):
    """Find newest conversation displayed in this project's Chats list.

    ChatGPT has changed its markup across releases, so use visible links within
    main content where possible. Return (url, label, WebElement), or None.
    """
    project_id = _project_identifier(project_url)
    candidates = []
    for selector in (
        'main a[href*="/c/"]',
        '[role="main"] a[href*="/c/"]',
    ):
        found = []
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                href = element.get_attribute("href") or ""
                if not _is_role_conversation(href, project_url) or not element.is_displayed():
                    continue
                found.append((href, (element.text or "").strip(), element))
            except (WebDriverException, StaleElementReferenceException):
                continue
        if found:
            candidates = found
            break
    if not candidates:
        return None
    # The Project's Chats list is newest-first. Preserve the DOM order.
    # Ignore duplicates, including duplicate navigation links to the same chat.
    seen = set()
    for href, text, element in candidates:
        if href not in seen and project_id in urlparse(href).path:
            seen.add(href)
            return href, text, element
    return None


def _click_latest_chat_without_anchor(driver: webdriver.Chrome, role: str, day: str) -> bool:
    """Fallback for Project chat rows built as clickable divs rather than links.

    The newest chat is visually first in the Project's Chats list. Search only
    main content and click the FIRST likely chat preview. A changed UI might
    require adjusting these locators; never click navigation/sidebar elements.
    """
    main = None
    for selector in ("main", '[role="main"]'):
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            main = elements[0]
            break
    if main is None:
        return False
    searches = (
        # Modern automated chats show this as the first row's preview.
        ".//*[contains(text(),'DATE=') and contains(text(),'ROLE=')]",
        ".//*[contains(text(),'Generate') and contains(text(),'CV Package')]",
        ".//*[contains(text(),'Generate') and contains(text(),'Job Package')]",
    )
    for xpath in searches:
        for candidate in main.find_elements(By.XPATH, xpath):
            try:
                if not candidate.is_displayed():
                    continue
                target = driver.execute_script("""
                    let node = arguments[0];
                    for (let i=0; i<5 && node; i++, node=node.parentElement) {
                      if (node.matches('a,button,[role="link"],[role="button"],'
                          + '[tabindex]:not([tabindex="-1"]),.cursor-pointer')) {
                        return node;
                      }
                    }
                    return arguments[0];
                """, candidate)
                try:
                    target.click()
                except (ElementClickInterceptedException, WebDriverException):
                    driver.execute_script("arguments[0].click();", target)
                return True
            except (StaleElementReferenceException, WebDriverException):
                continue
    return False


def _logged_chat_for_date(root: Path, day: str, role: str) -> str | None:
    """Optional fallback when project chat links aren't exposed as anchors."""
    report_file = (
        root / "job_profile" / "specific" / "company" / day / SUBMISSION_RESULTS_FILENAME
    )
    if not report_file.is_file():
        return None
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
        entry = report.get("roles", {}).get(role, {})
        href = entry.get("chat_url", "")
        if (
            report.get("date") == day
            and entry.get("status") in {"sent", "sent_unconfirmed"}
            and _is_role_conversation(href, ROLE_PROJECT_URLS[role])
        ):
            return href
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    return None


def open_latest_role_chat(
    driver: webdriver.Chrome, role: str, day: str, root: Path
) -> str:
    """Open newest Project chat (not necessarily newest finished chat)."""
    project_url = ROLE_PROJECT_URLS[role]
    deadline = time.monotonic() + PROJECT_CHAT_LIST_TIMEOUT_SECONDS
    latest = None
    while time.monotonic() < deadline:
        latest = _latest_chat_from_ui(driver, project_url)
        if latest:
            break
        time.sleep(0.4)
    if latest is not None:
        href, label, element = latest
        print(f"Latest chat: {label or '(untitled)'}")
        try:
            element.click()
        except (ElementClickInterceptedException, StaleElementReferenceException, WebDriverException):
            driver.get(href)
        WebDriverWait(driver, PROJECT_TIMEOUT_SECONDS).until(
            lambda d: _is_role_conversation(d.current_url, project_url)
        )
        if not _is_role_conversation(driver.current_url, project_url):
            raise RuntimeError(f"Latest chat opened outside the expected project: {driver.current_url}")
        print(f"Opened latest chat: {driver.current_url}")
        return driver.current_url

    # ChatGPT sometimes makes each chat a clickable div instead of an anchor.
    # This fallback clicks the first visible chat preview within main content.
    if _click_latest_chat_without_anchor(driver, role, day):
        try:
            WebDriverWait(driver, PROJECT_TIMEOUT_SECONDS).until(
                lambda d: _is_role_conversation(d.current_url, project_url)
            )
            print(f"Opened latest chat from Project row: {driver.current_url}")
            return driver.current_url
        except TimeoutException:
            raise RuntimeError(
                "Clicked the Project chat preview, but no conversation opened. "
                "Check this Project manually; no ZIP was downloaded."
            )

    fallback = _logged_chat_for_date(root, day, role)
    if not fallback:
        raise RuntimeError(
            "Couldn't locate Project conversation links in the Chats list, "
            "and no valid chat URL is recorded for this date in the submission log. "
            "The ChatGPT Project UI may have changed."
        )
    print("Project chat rows weren't available; using this date's saved submission URL")
    driver.get(fallback)
    _check_signed_in(driver, project_url)
    if not _is_role_conversation(driver.current_url, project_url):
        raise RuntimeError("Recorded conversation URL did not open the expected project")
    print(f"Opened logged chat: {driver.current_url}")
    return driver.current_url


# These are visible download labels in ChatGPT replies (the link text may NOT
# include the ZIP filename, even when the file card above it does).
ROLE_DOWNLOAD_LABELS: dict[str, tuple[str, ...]] = {
    "aiengineer": (
        "Download AI Engineer ZIP",
        "Download AI Engineering ZIP",
    ),
    "awsdataengineer": (
        "Download AWS Data Engineer ZIP",
        "Download AWS Engineer ZIP",
    ),
    "dataengineer": (
        "Download Data Engineer ZIP",
    ),
    "pythondeveloper": (
        "Download Python Developer ZIP",
    ),
}


def _download_labels_for_zip(filename: str) -> tuple[str, ...]:
    """Select labels for this role only; never click another role's ZIP."""
    for role in ROLE_DOWNLOAD_LABELS:
        if filename.casefold().endswith(f"_{role}.zip"):
            return ROLE_DOWNLOAD_LABELS[role]
    return ()


def _clickable_zip_target(driver: webdriver.Chrome, element, filename: str, labels, *, from_filename: bool):
    """Resolve a filename in a file card to its neighboring actual Download link."""
    return driver.execute_script(
        r"""
        const element = arguments[0];
        const filename = arguments[1].toLowerCase();
        const labels = arguments[2].map(x => x.toLowerCase());
        const fromFilename = arguments[3];
        const parts = filename.match(/^(\d{4}-\d\d-\d\d)_(\w+)\.zip$/);
        const day = parts ? parts[1] : '';
        const role = parts ? parts[2] : '';
        const roleDate = (value) => {
            const s = (value || '').toLowerCase();
            return !!(day && role && s.includes(role) &&
                (s.includes(day) || s.includes(day.replaceAll('-', '_'))) && s.includes('.zip'));
        };
        function isDownloadControl(el) {
            if (!el) return false;
            const text = (el.innerText || el.textContent || '').trim().toLowerCase();
            const href = (el.getAttribute('href') || '').toLowerCase();
            const cardText = (el.parentElement && el.parentElement.innerText || '').toLowerCase();
            return href.includes(filename) || labels.some(label => text.includes(label)) ||
                   roleDate(href) || (roleDate(text) && el.matches('a[href],button,[role="link"],[role="button"]')) ||
                   (roleDate(cardText) && (text.includes('download') || href.includes('.zip')));
        }

        const ownControl = element.closest('a[href], button, [role="link"], [role="button"]');
        if (ownControl && isDownloadControl(ownControl)) return ownControl;
        if (element.matches('a[href], button, [role="link"], [role="button"]') &&
            isDownloadControl(element)) return element;

        // ZIP filename and download link are often siblings in a file card.
        let parent = element.parentElement;
        for (let depth = 0; depth < 6 && parent; depth++, parent = parent.parentElement) {
            const text = (parent.innerText || '').trim();
            if (text.length > 1400) break; // Don't search the whole conversation.
            if (!text.toLowerCase().includes(filename)) continue;
            const controls = Array.from(parent.querySelectorAll(
                'a[href], button, [role="link"], [role="button"]'
            ));
            const candidate = controls.find(isDownloadControl);
            if (candidate) return candidate;
        }

        // The label may be its own clickable span (handled by React).
        // Never click plain filename text; that isn't necessarily a download.
        return fromFilename ? null : element;
        """,
        element, filename, list(labels), from_filename,
    )


def _find_zip_link_in_rendered_chat(driver: webdriver.Chrome, filename: str, labels):
    """Try exact filename, its file-card link, then the matching role's label."""
    upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lower = "abcdefghijklmnopqrstuvwxyz"
    # First prefer an href carrying the exact ZIP, then filename text in a card.
    filename_xpaths = (
        f'//a[contains(@href, "{filename}")]',
        f'//a[contains(normalize-space(.), "{filename}")]',
        f'//span[contains(normalize-space(.), "{filename}")]',
        f'//button[contains(normalize-space(.), "{filename}")]',
    )
    for xpath in filename_xpaths:
        for element in reversed(driver.find_elements(By.XPATH, xpath)):
            try:
                if element.is_displayed():
                    target = _clickable_zip_target(
                        driver, element, filename, labels, from_filename=True,
                    )
                    if target is not None:
                        return target
            except (StaleElementReferenceException, WebDriverException):
                continue

    # ChatGPT may occasionally rename the ZIP while keeping the same date
    # and role. Try a matching date+role ZIP text/card as a secondary locator.
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})_([a-z]+)\.zip", filename, re.I)
    if match:
        day, role = match.groups()
        for date_token in (day, day.replace("-", "_")):
            for tag in ("a", "span", "button"):
                xpath = (
                    f'//{tag}[contains(normalize-space(.), "{date_token}") '
                    f'and contains(normalize-space(.), "{role}") '
                    'and contains(normalize-space(.), ".zip")]'
                )
                for element in reversed(driver.find_elements(By.XPATH, xpath)):
                    try:
                        if not element.is_displayed():
                            continue
                        target = _clickable_zip_target(
                            driver, element, filename, labels, from_filename=True,
                        )
                        if target is not None:
                            return target
                    except (StaleElementReferenceException, WebDriverException):
                        continue

    # Extra XPath support: //span[contains(text(),'Download Data Engineer ZIP')]
    # plus corresponding labels for AI, AWS and Python Developer.
    for label in labels:
        label_lower = label.casefold()
        for tag in ("span", "a", "button"):
            xpath = (
                f'//{tag}[contains(translate(normalize-space(.), '
                f'"{upper}", "{lower}"), "{label_lower}")]'
            )
            for element in reversed(driver.find_elements(By.XPATH, xpath)):
                try:
                    if element.is_displayed():
                        target = _clickable_zip_target(
                            driver, element, filename, labels, from_filename=False,
                        )
                        if target is not None:
                            return target
                except (StaleElementReferenceException, WebDriverException):
                    continue
    return None


def _find_conversation_scroll_container(driver: webdriver.Chrome):
    """Find the chat message scroll pane (not the left Projects/Chats sidebar)."""
    return driver.execute_script(
        r"""
        const main = document.querySelector('main') ||
                     document.querySelector('[role="main"]');
        if (!main) return document.scrollingElement;
        const message = main.querySelector(
            '[data-message-author-role], [data-testid="conversation-turn"]'
        );
        const candidates = [main, ...main.querySelectorAll('*')];
        let best = null;
        let bestScore = -Infinity;
        for (const el of candidates) {
            if (el.closest('nav, aside')) continue;
            if (el.clientHeight < 150 || el.clientWidth < 250) continue;
            if (el.scrollHeight - el.clientHeight < 100) continue;
            const overflow = window.getComputedStyle(el).overflowY;
            if (!['auto', 'scroll', 'overlay'].includes(overflow)) continue;
            const rect = el.getBoundingClientRect();
            if (rect.bottom < 0 || rect.top > window.innerHeight) continue;
            const score = (message && el.contains(message) ? 10000 : 0) +
                          Math.min(el.clientHeight, 1500) +
                          Math.min(el.clientWidth, 1500) / 3 -
                          Math.abs((rect.left + rect.right) / 2 - window.innerWidth / 2) / 2;
            if (score > bestScore) { bestScore = score; best = el; }
        }
        return best || (main.scrollHeight > main.clientHeight + 100 ? main : document.scrollingElement);
        """
    )


def _scroll_conversation(driver: webdriver.Chrome, pane, direction: int):
    """Scroll one viewport toward earlier (-1) or later (+1) chat messages."""
    return driver.execute_script(
        r"""
        const pane = arguments[0];
        const direction = arguments[1];
        const before = pane.scrollTop;
        const distance = Math.max(280, Math.floor(pane.clientHeight * 0.75));
        const maxTop = Math.max(0, pane.scrollHeight - pane.clientHeight);
        const target = Math.min(maxTop, Math.max(0, before + direction * distance));
        const oldBehavior = pane.style.scrollBehavior;
        pane.style.scrollBehavior = 'auto';
        pane.scrollTop = target;
        pane.style.scrollBehavior = oldBehavior;
        return { before, after: pane.scrollTop, maxTop };
        """,
        pane, direction,
    )


class ZipLinkNotFound(RuntimeError):
    """Expected ZIP was not found in the latest chat after limited scans."""


def locate_zip_link(driver: webdriver.Chrome, filename: str):
    """Search the current role's conversation at most 3 up/down passes.

    Each pass searches from the current position toward the top, then back
    toward the bottom. ChatGPT typically opens conversations at the bottom.
    A missing ZIP is a normal skip, not a reason to rerun completed roles.
    """
    labels = _download_labels_for_zip(filename)

    for attempt in range(1, MAX_ZIP_SEARCH_ATTEMPTS + 1):
        print(f"  ZIP search pass {attempt}/{MAX_ZIP_SEARCH_ATTEMPTS}: {filename}")
        deadline = time.monotonic() + ZIP_SEARCH_ATTEMPT_TIMEOUT_SECONDS
        pane = None
        direction = -1  # Search older messages first (scroll upward).
        scroll_steps = 0
        reached_bottom = False

        while time.monotonic() < deadline:
            try:
                target = _find_zip_link_in_rendered_chat(driver, filename, labels)
                if target is not None:
                    print(f"  Found ZIP on pass {attempt} after {scroll_steps} scroll steps")
                    return target
            except (StaleElementReferenceException, WebDriverException):
                pass

            try:
                if pane is None:
                    pane = _find_conversation_scroll_container(driver)

                if pane is None:
                    time.sleep(0.5)
                    continue

                progress = _scroll_conversation(driver, pane, direction)
                scroll_steps += 1
                if abs(progress["after"] - progress["before"]) < 2:
                    if direction == -1:
                        # Reached the top: search downward now.
                        direction = 1
                        pane = None  # Re-detect after ChatGPT lazy rendering.
                        time.sleep(0.4)
                    else:
                        reached_bottom = True
                        # Search the final visible messages before ending pass.
                        time.sleep(SCROLL_SETTLE_SECONDS)
                        target = _find_zip_link_in_rendered_chat(driver, filename, labels)
                        if target is not None:
                            return target
                        break
                else:
                    time.sleep(SCROLL_SETTLE_SECONDS)
            except (StaleElementReferenceException, WebDriverException):
                pane = None
                time.sleep(0.4)

        status = "completed top-to-bottom scan" if reached_bottom else "time limit reached"
        print(f"  No ZIP found in pass {attempt}: {status} ({scroll_steps} scroll steps)")

    raise ZipLinkNotFound(
        f"No matching ZIP link for {filename!r} in this chat after "
        f"{MAX_ZIP_SEARCH_ATTEMPTS} scroll-search passes. "
        f"Checked filename and download labels {labels}. Skipping this role."
    )


def click_zip_link(driver: webdriver.Chrome, element) -> None:
    target = driver.execute_script(
        "return arguments[0].closest('a[href], button, [role=link], [role=button]') "
        "|| arguments[0];",
        element,
    )
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'center'});", target
    )
    try:
        target.click()
    except (ElementClickInterceptedException, WebDriverException):
        try:
            ActionChains(driver).move_to_element(target).click().perform()
        except WebDriverException:
            driver.execute_script("arguments[0].click();", target)


def wait_for_download(temp_dir: Path, expected: str) -> Path:
    """Wait for ONE complete ZIP in a per-role empty staging directory.

    ChatGPT controls the downloaded basename, which may differ from the
    displayed filename. Content is strictly validated afterward before use.
    """
    deadline = time.monotonic() + DOWNLOAD_TIMEOUT_SECONDS
    previous: tuple[str, int] | None = None
    stable_since: float | None = None
    while time.monotonic() < deadline:
        partial = list(temp_dir.glob("*.crdownload")) + list(temp_dir.glob("*.tmp"))
        candidates = [p for p in temp_dir.iterdir()
                      if p.is_file() and p.suffix.casefold() == ".zip" and p.stat().st_size > 0]
        if not partial and candidates:
            # Prefer the canonical download name. For any other name, require a
            # single candidate; never guess among unrelated ZIP files.
            exact = [p for p in candidates if p.name.casefold() == expected.casefold()]
            if exact:
                candidate = exact[0]
            elif len(candidates) == 1:
                candidate = candidates[0]
            else:
                raise RuntimeError(f"Multiple downloaded ZIPs: {[p.name for p in candidates]}")
            signature = (candidate.name, candidate.stat().st_size)
            if signature == previous and stable_since is not None:
                if time.monotonic() - stable_since >= 1.5 and zipfile.is_zipfile(candidate):
                    if candidate.name != expected:
                        print(f"  Browser ZIP name {candidate.name!r} differs from canonical {expected!r}; validating contents")
                    return candidate
            else:
                previous, stable_since = signature, time.monotonic()
        time.sleep(0.4)
    found = [p.name for p in temp_dir.iterdir()]
    raise RuntimeError(
        f"Download incomplete after {DOWNLOAD_TIMEOUT_SECONDS}s. Files: {found}. "
        "If Chrome Save As appeared, disable Settings > Downloads > "
        "'Ask where to save each file'."
    )


def expected_output_names(info: PackageInfo) -> set[str]:
    """Canonical FIVE output names: CVs have role, NOT date."""
    return {
        f"md_irsad_cv_{info.role}.md",
        f"md_irsad_cv_{info.role}.pdf",
        f"md_irsad_cv_{info.role}.docx",
        f"jd_email_reply_{info.date}.txt",
        f"interview_prep_{info.role}_{info.date}.pdf",
    }


def _canonical_member_name(filename: str, info: PackageInfo) -> str:
    """Allow older downloaded CV ZIPs, but IMPORT their files under new names."""
    for suffix in ("md", "pdf", "docx"):
        if filename.casefold() == f"md_irsad_{info.date}.{suffix}".casefold():
            return f"md_irsad_cv_{info.role}.{suffix}"
    return filename


def validate_package(archive: Path, info: PackageInfo) -> list[tuple[str, bytes]]:
    """Verify exactly five files, normalize legacy CV names, block unsafe ZIPs."""
    prefix = f"{info.date}/{info.role}/"
    package: list[tuple[str, bytes]] = []
    total_uncompressed = 0
    seen: set[str] = set()
    with zipfile.ZipFile(archive, "r") as zf:
        damaged = zf.testzip()
        if damaged:
            raise ValueError(f"Damaged ZIP member: {damaged}")
        for member in zf.infolist():
            normalized = member.filename.replace("\\", "/")
            path = PurePosixPath(normalized)
            if member.filename.startswith("/") or ".." in path.parts or re.match(r"^[A-Za-z]:", member.filename):
                raise ValueError(f"Unsafe ZIP path: {member.filename}")
            kind = (member.external_attr >> 16) & 0o170000
            if kind == stat.S_IFLNK:
                raise ValueError(f"Symlinks in ZIP are not allowed: {member.filename}")
            if member.is_dir():
                continue
            if not normalized.startswith(prefix):
                raise ValueError(f"ZIP member {member.filename!r} is outside {prefix!r}")
            name = normalized[len(prefix):]
            if not name or "/" in name or name in {".", ".."}:
                raise ValueError(f"Unexpected nested file: {member.filename}")
            if name.lower().endswith("_jd.txt") or name.lower() == "jd.txt":
                raise ValueError("ZIP is trying to overwrite a source JD")
            canonical = _canonical_member_name(name, info)
            if canonical.casefold() in seen:
                raise ValueError(f"Duplicate output ZIP entry (possibly old/new): {canonical}")
            seen.add(canonical.casefold())
            total_uncompressed += member.file_size
            if total_uncompressed > MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES:
                raise ValueError("ZIP exceeds safe 100MB uncompressed limit")
            data = zf.read(member)
            if not data:
                raise ValueError(f"Empty generated file: {name}")
            if canonical.endswith(".pdf") and not data.startswith(b"%PDF-"):
                raise ValueError(f"Invalid PDF header: {name}")
            if canonical.endswith(".docx") and not zipfile.is_zipfile(io.BytesIO(data)):
                raise ValueError(f"Invalid DOCX archive: {name}")
            package.append((canonical, data))
    expected = expected_output_names(info)
    got = {name for name, _ in package}
    if got != expected:
        raise ValueError(f"Wrong ZIP contents. Expected: {sorted(expected)}; got: {sorted(got)}")
    return package


def write_download_archive(source: Path, destination: Path, *, overwrite: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256(source) == sha256(destination):
            print(f"ZIP already saved (identical): {destination}")
            return
        if not overwrite:
            raise FileExistsError(
                f"Different ZIP already exists: {destination}. "
                "Pass --overwrite to replace the generated ZIP."
            )
    shutil.copy2(source, destination)
    print(f"Saved ZIP: {destination}")


def import_package(files: list[tuple[str, bytes]], destination: Path, *, overwrite: bool) -> None:
    """Import CV outputs only. Original JD stays untouched."""
    destination.mkdir(parents=True, exist_ok=True)
    conflicts = [
        name for name, data in files
        if (destination / name).exists() and (destination / name).read_bytes() != data
    ]
    if conflicts and not overwrite:
        raise FileExistsError(
            f"Existing generated files have different content: {conflicts}. "
            "No new files imported. Use --overwrite to replace generated outputs."
        )
    for name, data in files:
        target = destination / name
        if target.exists() and target.read_bytes() == data:
            print(f"Unchanged: {target.name}")
            continue
        temporary = target.with_name(target.name + ".new")
        try:
            temporary.write_bytes(data)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"Imported: {target}")


def role_has_source_jd(role_folder: Path, role: str) -> bool:
    """Only visit roles for which today's jobs/JD were actually generated."""
    wanted = {f"{role}_jd.txt", "jd.txt"}
    for path in role_folder.rglob("*"):
        if (path.is_file() and path.name.casefold() in wanted
                and path.stat().st_size > 0):
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            match = re.search(r"(?im)^\s*#\s*Jobs\s+included\s*:\s*(\d+)\b", text)
            if match is not None and int(match.group(1)) == 0:
                continue
            return bool(text.strip())
    return False


def use_local_zip_if_complete(
    root: Path, day: str, role: str, *, dry_run: bool
) -> str | None:
    """Avoid opening Chrome when a valid ZIP is already downloaded.

    If the ZIP is present but extraction was interrupted, import its validated
    files locally instead of downloading the same ZIP a second time.
    """
    info = PackageInfo(day, role, f"{day}_{role}.zip")
    archive = root / "job_profile" / "download_zip_files" / info.filename
    if not archive.is_file():
        return None

    # The same strict archive validation used for fresh downloads.
    package = validate_package(archive, info)
    role_folder = root / "job_profile" / "specific" / "company" / day / role

    identical = all(
        (role_folder / name).is_file()
        and (role_folder / name).read_bytes() == data
        for name, data in package
    )
    if identical:
        print(f"  ALREADY COMPLETE: {role} (ZIP and five extracted files match)")
        return "already_complete"

    if dry_run:
        print(f"  ZIP already saved for {role}; dry run will not import missing files")
        return "cached_zip_needs_import"

    # Refuse to replace changed outputs unless the user explicitly opts into
    # a fresh download with --overwrite; protect original JD at all times.
    import_package(package, role_folder, overwrite=False)
    print(f"  RESTORED locally: {role} (no browser/download needed)")
    return "restored_from_local_zip"


def download_one_role(
    driver: webdriver.Chrome, root: Path, day: str, role: str,
    *, dry_run: bool, overwrite: bool
) -> str:
    info = PackageInfo(day, role, f"{day}_{role}.zip")
    output_dir = root / "job_profile" / "download_zip_files"
    role_folder = root / "job_profile" / "specific" / "company" / day / role
    print(f"  Project:   {ROLE_PROJECT_URLS[role]}")
    print(f"  ZIP:       {info.filename}")
    print(f"  Output:    {role_folder}")
    open_role_project(driver, role)
    open_latest_role_chat(driver, role, day, root)
    link = locate_zip_link(driver, info.filename)
    print(f"  Found completed ZIP link: {info.filename}")
    if dry_run:
        print("  DRY RUN: found expected ZIP; not downloading or importing")
        return "ready"

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"_cv_{role}_", dir=output_dir) as stage:
        staging = Path(stage)
        set_download_directory(driver, staging)
        try:
            print("  Clicking ZIP and waiting for Chrome download...")
            click_zip_link(driver, link)
            archive = wait_for_download(staging, info.filename)
            print(f"  Downloaded: {archive.name} ({archive.stat().st_size:,} bytes)")
            package = validate_package(archive, info)
            print(f"  Validated {len(package)} exact output files")
            # Refuse conflicting imports BEFORE copying a downloaded ZIP to the
            # final folder. This makes a failed rerun less surprising.
            if not overwrite:
                existing_zip = output_dir / info.filename
                if existing_zip.exists() and sha256(existing_zip) != sha256(archive):
                    raise FileExistsError(
                        f"Different ZIP already exists: {existing_zip}; use --overwrite"
                    )
                conflicts = [
                    name for name, data in package
                    if (role_folder / name).is_file()
                    and (role_folder / name).read_bytes() != data
                ]
                if conflicts:
                    raise FileExistsError(
                        f"Existing role output differs: {conflicts}; use --overwrite"
                    )
            write_download_archive(archive, output_dir / info.filename,
                                   overwrite=overwrite)
            import_package(package, role_folder, overwrite=overwrite)
        finally:
            # Never leave Chrome pointing at a deleted temporary directory.
            set_download_directory(driver, output_dir)
    return "downloaded"


def locate_project_root(start_file: Path) -> Path:
    """Works for either linkedin/services/ or linkedin/runners/."""
    candidate = start_file.resolve().parents[2]
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=valid_date, default=today_ist(),
                        help="Expected package date YYYY-MM-DD (default: today in IST)")
    parser.add_argument("--role", choices=ROLE_FOLDERS, default=None,
                        help="Check only one role (default: all four)")
    parser.add_argument("--project-root", type=Path,
                        default=locate_project_root(Path(__file__)),
                        help="JobBots project root")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check ZIP links without downloading or importing")
    parser.add_argument("--overwrite", action="store_true",
                        help="Force fresh download, replacing generated ZIPs/CVs (never JDs)")
    args = parser.parse_args(argv)

    root = args.project_root.expanduser().resolve()
    if not (root / "linkedin").is_dir():
        parser.error(f"Invalid JobBots project root: {root}")

    roles = [args.role] if args.role else list(ROLE_FOLDERS)
    day_folder = root / "job_profile" / "specific" / "company" / args.date
    print(f"Date (IST): {args.date}")
    print(f"Roles configured: {', '.join(roles)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'DOWNLOAD + IMPORT'}")
    print(f"Download: {root / 'job_profile' / 'download_zip_files'}")
    print(f"Import:   {day_folder}")

    # Preflight BEFORE connecting Chrome: no JD means no CV was requested.
    # A previously completed role is reused locally on future invocations,
    # including when an external BAT script launches this module again.
    results: dict[str, str] = {}
    pending_roles: list[str] = []
    for role in roles:
        role_folder = day_folder / role
        if not role_folder.is_dir():
            results[role] = "skipped_no_role_folder"
            print(f"  SKIP {role}: today's role folder does not exist")
            continue
        if not role_has_source_jd(role_folder, role):
            results[role] = "skipped_no_jd"
            print(f"  SKIP {role}: no JD with eligible jobs ({role}_jd.txt or jd.txt)")
            continue

        if not args.overwrite:
            try:
                cached_status = use_local_zip_if_complete(
                    root, args.date, role, dry_run=args.dry_run
                )
            except Exception as exc:
                results[role] = "failed"
                print(f"  FAILED {role}: existing local ZIP/output conflict: {exc}",
                      file=sys.stderr)
                continue
            if cached_status is not None:
                results[role] = cached_status
                continue

        pending_roles.append(role)

    if not pending_roles:
        print("No roles require ChatGPT ZIP downloading; Chrome was not opened.")
    else:
        driver: webdriver.Chrome | None = None
        try:
            driver = attach_chrome()
            for index, role in enumerate(pending_roles, 1):
                print(f"\n[{index}/{len(pending_roles)}] {role}")
                try:
                    results[role] = download_one_role(
                        driver, root, args.date, role,
                        dry_run=args.dry_run, overwrite=args.overwrite,
                    )
                    print(f"  SUCCESS: {role}")
                except ZipLinkNotFound as exc:
                    # A missing link is normal when generation is not yet ready.
                    # Returning success for this skip prevents outer retry loops.
                    results[role] = "skipped_zip_not_found"
                    print(f"  SKIP {role}: {exc}")
                except Exception as exc:
                    results[role] = "failed"
                    print(f"  FAILED {role}: {type(exc).__name__}: {exc}",
                          file=sys.stderr)
        finally:
            if driver is not None:
                # Only detach Selenium. Do not close the existing Chrome.
                try:
                    driver.service.stop()
                except Exception:
                    pass

    print("\n========= DOWNLOAD SUMMARY =========")
    for role in roles:
        print(f"{role:<18} {results.get(role, 'not started')}")
    print("Original JD source files were not modified.")
    # Missing role/JD/ZIP is a normal skip, not a process-level failure.
    return 1 if any(status == "failed" for status in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
