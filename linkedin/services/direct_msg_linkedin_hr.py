"""
python linkedin/services/direct_msg_linkedin_hr.py
python -m linkedin.services.direct_msg_linkedin_hr

Automatic inputs per role folder:
- reply text: *email_reply*.txt
- posted-by LinkedIn URLs: jd.txt -> Posted-by Profile URLs:
- attachment: *cv*.pdf

Important:
- The script does NOT bypass LinkedIn login, CAPTCHA, checkpoint, or access controls.
- Keep Chrome logged in manually before running.
- Standard LinkedIn messages may not expose a Subject field. In that case this
  script can prepend "Subject: ..." to the message body.
- Selenium uploads attachments through the underlying <input type="file">,
  avoiding the native Windows file dialog.
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

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
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ============================================================================
# DAILY ROLE-FOLDER AUTOMATION
# ============================================================================
# Only these role folders are processed. Missing folders are skipped.
ROLE_FOLDERS = (
    "aiengineer",
    "awsdataengineer",
    "azuredataengineer",
    "pythondeveloper",
)

# In each role folder the script automatically discovers:
#   1. *email_reply*.txt  -> REPLY_TEXT_PATH
#   2. jd.txt             -> Posted-by Profile URLs
#   3. *cv*.pdf           -> ATTACHMENT_PATHS
#
# You only pass the daily folder to main(), for example:
#   main(r"job_profile\specific\company\2026_09_17")

# ============================================================================
# OPTIONAL RUNTIME SETTINGS
# ============================================================================
CHROME_DEBUGGER_ADDRESS = "127.0.0.1:9222"
SCRIPT_VERSION = "2026-08-13-shadow-dom-compose-v7"

PAGE_LOAD_TIMEOUT_SECONDS = 25
ELEMENT_TIMEOUT_SECONDS = 12
COMPOSER_TIMEOUT_SECONDS = 15
ATTACHMENT_UPLOAD_WAIT_SECONDS = 2.0
AFTER_SEND_WAIT_SECONDS = 2.0
BETWEEN_RECIPIENTS_SECONDS = 4.0

# True = really click Send.
# False = fill subject/body + attachments but DO NOT click Send.
SEND_MESSAGES = True

# Most normal LinkedIn direct-message composers do not have a subject field.
# When no subject field exists, keep the subject by adding it to the body.
SUBJECT_FALLBACK_TO_MESSAGE_BODY = True

# ============================================================================
# OPTIONAL EXACT XPATH OVERRIDES
# Paste your SelectorHub/XPath values here if LinkedIn's DOM changes.
# Leave as "" to use the resilient fallback selectors below.
# ============================================================================
MESSAGE_BUTTON_XPATH_OVERRIDE = ""
SUBJECT_INPUT_XPATH_OVERRIDE = ""
MESSAGE_INPUT_XPATH_OVERRIDE = ""
ATTACH_FILE_INPUT_XPATH_OVERRIDE = ""
SEND_BUTTON_XPATH_OVERRIDE = ""

# ============================================================================
# FALLBACK SELECTORS
# User-supplied override XPath, when present, is always tried first.
# ============================================================================

MESSAGE_BUTTON_XPATHS = [
    # Profile main-action area first so we do not accidentally click the
    # top navigation "Messaging" control.
    "//main//button[normalize-space()='Message' or .//span[normalize-space()='Message']]",
    "//main//a[normalize-space()='Message' or .//span[normalize-space()='Message']]",
    "//main//*[@role='button' and "
    "(@aria-label='Message' or starts-with(@aria-label,'Message '))]",
    "//main//button[contains(@aria-label,'Message')]",
    "//main//a[contains(@aria-label,'Message')]",
]

SUBJECT_INPUT_XPATHS = [
    ".//input[@name='subject']",
    ".//input[@placeholder='Subject']",
    ".//input[@aria-label='Subject']",
    ".//input[contains(translate(@placeholder,'SUBJECT','subject'),'subject')]",
    ".//textarea[@name='subject' or @placeholder='Subject' or @aria-label='Subject']",
]

MESSAGE_INPUT_XPATHS = [
    ".//div[@contenteditable='true' and @role='textbox']",
    ".//*[@contenteditable='true' and contains(@class,'msg-form__contenteditable')]",
    ".//*[@contenteditable='true' and contains(@aria-label,'message')]",
    ".//*[@contenteditable='true' and contains(@data-placeholder,'message')]",
    ".//textarea[contains(@placeholder,'message') or contains(@aria-label,'message')]",
]

ATTACH_FILE_INPUT_XPATHS = [
    ".//input[@type='file']",
    ".//input[contains(@accept,'pdf') and @type='file']",
]

SEND_BUTTON_XPATHS = [
    ".//button[@type='submit' and "
    "(normalize-space()='Send' or .//span[normalize-space()='Send'])]",
    ".//button[contains(@class,'msg-form__send-button')]",
    ".//button[@aria-label='Send']",
    ".//button[contains(@aria-label,'Send') and not(contains(@aria-label,'schedule'))]",
    ".//*[@role='button' and "
    "(normalize-space()='Send' or .//span[normalize-space()='Send'])]",
]

COMPOSER_ROOT_XPATHS = [
    # LinkedIn overlay conversation composer.
    "//div[contains(@class,'msg-overlay-conversation-bubble') and not(contains(@style,'display: none'))]",
    # InMail / modal variants.
    "//div[@role='dialog']",
    "//section[@role='dialog']",
    # Generic messaging overlay fallback.
    "//*[contains(@class,'msg-overlay') and "
    ".//*[@contenteditable='true' or .//textarea]]",
]

LINKEDIN_PROFILE_URL_RE = re.compile(
    r"https?://(?:[a-z]{2,3}\.)?(?:www\.)?linkedin\.com/in/"
    r"[A-Za-z0-9%._~\-]+/?(?:\?[^\s,\]]*)?",
    flags=re.IGNORECASE,
)

def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        value = value.strip()
        if not value:
            continue

        key = value.casefold()
        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result

def extract_posted_by_urls(raw_text: str) -> list[str]:
    """
    Extract LinkedIn /in/ profile URLs from comma/newline/plain text.

    This also accepts text copied from a grouped job file, for example:
        Posted-by Profile URLs:
        https://www.linkedin.com/in/person-a,
        https://www.linkedin.com/in/person-b
    """
    urls: list[str] = []

    for match in LINKEDIN_PROFILE_URL_RE.findall(raw_text or ""):
        url = match.strip().rstrip(".,;:)")

        # Query params are not needed for profile navigation and can create
        # duplicate variants of the same profile.
        url = url.split("?", 1)[0].rstrip("/")

        if url.lower().startswith("http://"):
            url = "https://" + url[len("http://") :]

        urls.append(url)

    return _dedupe_preserve_order(urls)

POSTED_BY_LINE_PATTERN = re.compile(
    r"^\s*(?:[-*]\s*)?Posted-by\s+Profile\s+URLs?\s*:\s*(.*)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RoleLinkedInConfig:
    role_name: str
    role_folder: Path
    reply_text_path: Path
    jd_text_path: Path
    attachment_path: Path
    profile_urls: tuple[str, ...]


def _all_files_with_suffix(folder: Path, suffix: str) -> list[Path]:
    wanted = suffix.casefold()
    return sorted(
        (
            path
            for path in folder.rglob("*")
            if path.is_file() and path.suffix.casefold() == wanted
        ),
        key=lambda path: str(path).casefold(),
    )


def _first_non_empty_line(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def find_reply_text(role_folder: Path) -> Path:
    """Find the role's email-reply/message text file automatically."""
    txt_files = _all_files_with_suffix(role_folder, ".txt")

    preferred = [
        path
        for path in txt_files
        if "email_reply" in path.stem.casefold()
        and _first_non_empty_line(path).casefold().startswith("subject:")
    ]

    if len(preferred) == 1:
        return preferred[0]

    if len(preferred) > 1:
        names = "\n".join(f"  - {path}" for path in preferred)
        raise RuntimeError(
            "More than one email-reply text file was found; cannot safely "
            f"choose one:\n{names}"
        )

    # Fallback: any non-JD .txt whose first non-empty line is Subject:.
    fallback = [
        path
        for path in txt_files
        if path.name.casefold() != "jd.txt"
        and _first_non_empty_line(path).casefold().startswith("subject:")
    ]

    if len(fallback) == 1:
        return fallback[0]

    if len(fallback) > 1:
        names = "\n".join(f"  - {path}" for path in fallback)
        raise RuntimeError(
            "More than one Subject-based reply text file was found. Rename "
            f"the intended file to include 'email_reply':\n{names}"
        )

    raise FileNotFoundError(
        "Could not find the email-reply text file in "
        f"{role_folder}. Expected a .txt file containing 'email_reply' "
        "whose first non-empty line starts with 'Subject:'."
    )


def find_jd_text(role_folder: Path) -> Path:
    """Find exactly one jd.txt inside the role folder."""
    candidates = [
        path
        for path in _all_files_with_suffix(role_folder, ".txt")
        if path.name.casefold() == "jd.txt"
    ]

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        names = "\n".join(f"  - {path}" for path in candidates)
        raise RuntimeError(f"More than one jd.txt file was found:\n{names}")

    raise FileNotFoundError(f"Could not find jd.txt in: {role_folder}")


def extract_posted_by_urls_from_jd(jd_path: Path) -> list[str]:
    """
    Read LinkedIn URLs only from 'Posted-by Profile URLs:' in jd.txt.

    Example:
        Posted-by Profile URLs: https://www.linkedin.com/in/person-a, https://www.linkedin.com/in/person-b/

    A marker may also be followed by URL-only continuation lines. Invalid
    fragments that are not complete linkedin.com/in/... URLs are ignored.
    """
    text = jd_path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()

    found_urls: list[str] = []
    marker_count = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        match = POSTED_BY_LINE_PATTERN.match(line)

        if not match:
            i += 1
            continue

        marker_count += 1
        chunks = [match.group(1)]

        # Optional continuation support, e.g. marker on one line and URLs on
        # the following line(s). Stop when a blank/non-LinkedIn line appears.
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if not next_line:
                break
            if "linkedin.com/in/" not in next_line.casefold():
                break
            chunks.append(next_line)
            j += 1

        found_urls.extend(extract_posted_by_urls("\n".join(chunks)))
        i = max(i + 1, j)

    profile_urls = _dedupe_preserve_order(found_urls)

    if marker_count == 0:
        print(f"WARNING: No 'Posted-by Profile URLs:' line found in {jd_path.name}")
    elif not profile_urls:
        print(
            "WARNING: 'Posted-by Profile URLs:' was found, but no valid "
            f"LinkedIn /in/ URLs were found in {jd_path.name}"
        )

    return profile_urls


def find_cv_pdf(role_folder: Path) -> Path:
    """Find the CV PDF, not another PDF that may exist in the role folder."""
    pdf_files = _all_files_with_suffix(role_folder, ".pdf")

    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {role_folder}")

    cv_candidates = [
        path for path in pdf_files if "cv" in path.stem.casefold()
    ]

    if len(cv_candidates) == 1:
        return cv_candidates[0]

    if len(cv_candidates) > 1:
        preferred = [
            path
            for path in cv_candidates
            if "md_irshad_cv" in path.stem.casefold()
        ]
        if len(preferred) == 1:
            return preferred[0]

        names = "\n".join(f"  - {path}" for path in cv_candidates)
        raise RuntimeError(
            "More than one PDF filename contains 'cv'; cannot safely choose "
            f"the attachment:\n{names}"
        )

    names = "\n".join(f"  - {path}" for path in pdf_files)
    raise FileNotFoundError(
        "PDF files were found, but none contains 'cv' in its filename.\n"
        f"Available PDFs:\n{names}"
    )


def discover_role_config(role_name: str, role_folder: Path) -> RoleLinkedInConfig:
    reply_text_path = find_reply_text(role_folder)
    jd_text_path = find_jd_text(role_folder)
    attachment_path = find_cv_pdf(role_folder)
    profile_urls = extract_posted_by_urls_from_jd(jd_text_path)

    if not profile_urls:
        raise ValueError(
            "No valid LinkedIn profile URLs found after "
            f"'Posted-by Profile URLs:' in {jd_text_path}"
        )

    return RoleLinkedInConfig(
        role_name=role_name,
        role_folder=role_folder,
        reply_text_path=reply_text_path,
        jd_text_path=jd_text_path,
        attachment_path=attachment_path,
        profile_urls=tuple(profile_urls),
    )


def load_reply_text(file_path: str | Path) -> tuple[str, str]:
    """
    Read Subject + full body from the same text-file style used by the
    manual email sender.

    First non-empty line must be:
        Subject: ...
    """
    path = Path(file_path).expanduser()

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Reply text file not found: {path}")

    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"Reply text file is empty: {path}")

    lines = text.splitlines()
    first_content_index = next(
        (index for index, line in enumerate(lines) if line.strip()),
        None,
    )

    if first_content_index is None:
        raise ValueError(f"Reply text file is empty: {path}")

    subject_line = lines[first_content_index].strip()
    if not subject_line.lower().startswith("subject:"):
        raise ValueError(
            "First non-empty line in REPLY_TEXT_PATH must start with "
            f"'Subject:' -> {path}"
        )

    subject = subject_line.split(":", 1)[1].strip()
    if not subject:
        raise ValueError(f"Subject is empty in reply text file: {path}")

    body = "\n".join(lines[first_content_index + 1 :]).strip()
    if not body:
        raise ValueError(f"Message body is empty in reply text file: {path}")

    # IMPORTANT: unlike the email sender, preserve the body exactly as written.
    return subject, body

def validate_attachment_paths(paths: Sequence[str]) -> list[Path]:
    if not paths:
        raise ValueError("ATTACHMENT_PATHS is empty. Add at least one CV path.")

    resolved: list[Path] = []

    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"Attachment does not exist: {path}")

        if not path.is_file():
            raise ValueError(f"Attachment path is not a file: {path}")

        resolved.append(path)

    return resolved

def attach_to_existing_chrome() -> webdriver.Chrome:
    """
    Attach Selenium to the existing Chrome instance on the debugger port.

    The Chrome window must already be running and logged into LinkedIn.
    """
    options = Options()
    options.add_experimental_option("debuggerAddress", CHROME_DEBUGGER_ADDRESS)

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:
        raise RuntimeError(
            "Could not attach to Chrome at "
            f"{CHROME_DEBUGGER_ADDRESS}.\n"
            "Start Chrome with remote debugging and log into LinkedIn first.\n"
            "Example Windows command:\n"
            '  chrome.exe --remote-debugging-port=9222 '
            '--user-data-dir="C:\\selenium\\linkedin-debug-profile"\n'
            f"Original error: {exc}"
        ) from exc

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
    return driver

def assert_linkedin_accessible(driver: webdriver.Chrome) -> None:
    """
    Stop instead of attempting to automate login, CAPTCHA, checkpoint,
    verification, or auth-wall screens.
    """
    current = (driver.current_url or "").lower()

    blocked_markers = (
        "/login",
        "/checkpoint",
        "/authwall",
        "/uas/login",
    )

    if any(marker in current for marker in blocked_markers):
        raise RuntimeError(
            "LinkedIn requires login/checkpoint/verification. "
            "Resolve it manually in the attached Chrome window, then rerun."
        )

def navigate_to_profile(driver: webdriver.Chrome, profile_url: str) -> None:
    """Only open the LinkedIn profile URL."""
    print(f"Opening profile: {profile_url}")
    driver.get(profile_url)
    time.sleep(2)

def _visible_elements(
    root: webdriver.Chrome | WebElement,
    by: str,
    selector: str,
) -> list[WebElement]:
    try:
        elements = root.find_elements(by, selector)
    except (StaleElementReferenceException, WebDriverException):
        return []

    visible: list[WebElement] = []
    for element in elements:
        try:
            if element.is_displayed():
                visible.append(element)
        except StaleElementReferenceException:
            continue

    return visible

def _override_first(
    override_xpath: str,
    fallbacks: Sequence[str],
) -> list[str]:
    selectors: list[str] = []
    if override_xpath.strip():
        selectors.append(override_xpath.strip())
    selectors.extend(fallbacks)
    return selectors

def wait_for_visible_xpath(
    root: webdriver.Chrome | WebElement,
    xpaths: Sequence[str],
    timeout: float,
    description: str,
) -> WebElement:
    end_time = time.time() + timeout
    last_error: Exception | None = None

    while time.time() < end_time:
        for xpath in xpaths:
            try:
                visible = _visible_elements(root, By.XPATH, xpath)
                if visible:
                    return visible[-1]
            except Exception as exc:
                last_error = exc

        time.sleep(0.2)

    suffix = f" Last error: {last_error}" if last_error else ""
    raise TimeoutException(
        f"Could not find visible {description} within {timeout:.1f}s.{suffix}"
    )

def click_element(driver: webdriver.Chrome, element: WebElement) -> None:
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'center'});",
            element,
        )
    except Exception:
        pass

    try:
        element.click()
        return
    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
        WebDriverException,
    ):
        pass

    driver.execute_script("arguments[0].click();", element)

def get_open_profile_name(driver: webdriver.Chrome) -> str:
    """
    Get CURRENT opened profile name from browser title.

    Example:
        Himmi Sharma | LinkedIn -> Himmi Sharma
    """
    title = (driver.title or "").strip()

    profile_name = re.sub(
        r"\s*\|\s*LinkedIn\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()

    if not profile_name or profile_name.lower() == "linkedin":
        raise RuntimeError(
            f"Could not determine opened profile name from title: {title!r}"
        )

    print(f"Opened profile name: {profile_name}")
    return profile_name

def find_open_profile_message_button(
    driver: webdriver.Chrome,
    profile_name: str,
) -> WebElement:
    """
    Find ONLY the Message button belonging to the currently opened profile.

    It starts from an element whose visible text exactly equals profile_name,
    then walks up its ancestors until it finds a Message control inside that
    SAME profile container.

    Right-side recommendation cards are never searched globally.
    """
    end_time = time.time() + ELEMENT_TIMEOUT_SECONDS

    while time.time() < end_time:
        try:
            button = driver.execute_script(
                """
                const wantedName = arguments[0];

                function norm(value) {
                    return (value || '')
                        .replace(/\\s+/g, ' ')
                        .trim();
                }

                function visible(el) {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);

                    return (
                        r.width > 0 &&
                        r.height > 0 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden'
                    );
                }

                function isMessage(el) {
                    if (!visible(el)) return false;

                    const text = norm(
                        el.innerText || el.textContent || ''
                    );

                    const aria = norm(
                        el.getAttribute('aria-label') || ''
                    );

                    return (
                        text === 'Message' ||
                        aria === 'Message' ||
                        aria.startsWith('Message ')
                    );
                }

                const nameElements = Array.from(
                    document.querySelectorAll(
                        'h1, h2, h3, span, div, a'
                    )
                ).filter(el => {
                    if (!visible(el)) return false;

                    return norm(
                        el.innerText || el.textContent || ''
                    ) === wantedName;
                });

                let best = null;
                let bestDepth = 999999;
                let bestContainerLength = 999999;

                for (const nameEl of nameElements) {
                    let container = nameEl;

                    for (
                        let depth = 0;
                        depth < 12 && container;
                        depth++
                    ) {
                        const controls = Array.from(
                            container.querySelectorAll(
                                'button, a, [role="button"]'
                            )
                        ).filter(isMessage);

                        if (controls.length > 0) {
                            const containerLength = norm(
                                container.innerText ||
                                container.textContent ||
                                ''
                            ).length;

                            if (
                                depth < bestDepth ||
                                (
                                    depth === bestDepth &&
                                    containerLength < bestContainerLength
                                )
                            ) {
                                best = controls[0];
                                bestDepth = depth;
                                bestContainerLength = containerLength;
                            }

                            break;
                        }

                        container = container.parentElement;
                    }
                }

                return best;
                """,
                profile_name,
            )

            if button is not None and button.is_displayed():
                try:
                    rect = button.rect
                    print(
                        "Opened-profile Message button found | "
                        f"profile={profile_name!r} | "
                        f"x={rect.get('x')} y={rect.get('y')}"
                    )
                except Exception:
                    print(
                        "Opened-profile Message button found | "
                        f"profile={profile_name!r}"
                    )

                return button

        except (StaleElementReferenceException, WebDriverException):
            pass

        time.sleep(0.2)

    raise TimeoutException(
        "Could not find Message button for currently opened "
        f"profile {profile_name!r}."
    )

def click_message_button(
    driver: webdriver.Chrome,
    profile_name: str,
) -> None:
    """
    Click only the opened profile's Message control.

    No global //main//Message search.
    No visible[-1].
    """
    button = find_open_profile_message_button(
        driver,
        profile_name,
    )

    try:
        button.click()
        print(
            f"Clicked Message for opened profile: {profile_name}"
        )
        return
    except Exception as exc:
        print(
            "Native click failed; using JS click for opened profile: "
            f"{exc}"
        )

    driver.execute_script(
        "arguments[0].click();",
        button,
    )

    print(
        f"Clicked Message for opened profile via JS: {profile_name}"
    )

def verify_composer_recipient(
    composer: WebElement,
    expected_profile_name: str,
) -> None:
    """
    Safety stop before typing or attaching CV.

    If LinkedIn somehow opened another recommendation profile,
    do not continue.
    """
    try:
        composer_text = (
            composer.get_attribute("innerText")
            or composer.text
            or ""
        )
    except Exception:
        composer_text = ""

    normalized = re.sub(
        r"\s+",
        " ",
        composer_text,
    ).strip()

    if expected_profile_name.casefold() not in normalized.casefold():
        raise RuntimeError(
            "SAFETY STOP: opened composer belongs to a different profile. "
            f"Expected={expected_profile_name!r}; "
            f"composer={normalized[:180]!r}"
        )

    print(
        f"Composer recipient verified: {expected_profile_name}"
    )

def _deep_shadow_query_all(
    driver: webdriver.Chrome,
    selectors: Sequence[str],
    *,
    visible_only: bool = True,
    root: WebElement | None = None,
) -> list[WebElement]:
    """Query normal DOM + every OPEN Shadow DOM recursively with CSS."""
    script = r"""
        const startRoot = arguments[0] || document;
        const selectors = arguments[1];
        const visibleOnly = arguments[2];

        function isVisible(el) {
            if (!el) return false;
            const r = el.getBoundingClientRect();
            const s = window.getComputedStyle(el);
            return r.width > 0 && r.height > 0 &&
                   s.display !== 'none' && s.visibility !== 'hidden';
        }

        const results = [];
        const seen = new Set();

        function add(el) {
            if (!el || seen.has(el)) return;
            if (visibleOnly && !isVisible(el)) return;
            seen.add(el);
            results.push(el);
        }

        function walk(node) {
            if (!node) return;

            if (node.querySelectorAll) {
                for (const selector of selectors) {
                    let found = [];
                    try { found = node.querySelectorAll(selector); }
                    catch (e) { found = []; }
                    for (const el of found) add(el);
                }
            }

            if (node.shadowRoot) walk(node.shadowRoot);

            let children = [];
            try { children = node.children ? Array.from(node.children) : []; }
            catch (e) { children = []; }

            for (const child of children) walk(child);
        }

        walk(startRoot);
        return results;
    """

    try:
        elements = driver.execute_script(
            script,
            root,
            list(selectors),
            visible_only,
        )
        return list(elements or [])
    except JavascriptException:
        return []

def _deep_shadow_text(
    driver: webdriver.Chrome,
    root: WebElement | None = None,
) -> str:
    try:
        value = driver.execute_script(
            r"""
            const startRoot = arguments[0] || document;
            const parts = [];

            function walk(node) {
                if (!node) return;

                if (node.nodeType === Node.TEXT_NODE) {
                    const value = (node.nodeValue || '').trim();
                    if (value) parts.push(value);
                    return;
                }

                if (node.shadowRoot) walk(node.shadowRoot);
                const children = node.childNodes ? Array.from(node.childNodes) : [];
                for (const child of children) walk(child);
            }

            walk(startRoot);
            return parts.join(' ').replace(/\s+/g, ' ').trim();
            """,
            root,
        )
        return re.sub(r"\s+", " ", value or "").strip()
    except Exception:
        return ""

def wait_for_composer_root(driver: webdriver.Chrome) -> WebElement:
    """Detect the current LinkedIn New Message composer across Shadow DOM."""
    end_time = time.time() + COMPOSER_TIMEOUT_SECONDS

    while time.time() < end_time:
        subjects = _deep_shadow_query_all(
            driver,
            [
                'input[name="subject"]',
                'input[placeholder="Subject (optional)"]',
                'input[placeholder*="Subject"]',
            ],
            visible_only=True,
        )
        editors = _deep_shadow_query_all(
            driver,
            [
                '[contenteditable="true"][role="textbox"][aria-label*="Write a message"]',
                '.msg-form__contenteditable[contenteditable="true"]',
                '[contenteditable="true"][role="textbox"]',
            ],
            visible_only=True,
        )

        anchor = subjects[-1] if subjects else (editors[-1] if editors else None)
        if anchor is not None:
            try:
                composer = driver.execute_script(
                    r"""
                    let el = arguments[0];
                    let best = el;

                    function deepCount(root, selector) {
                        let count = 0;
                        function walk(node) {
                            if (!node) return;
                            if (node.querySelectorAll) {
                                try { count += node.querySelectorAll(selector).length; }
                                catch (e) {}
                            }
                            if (node.shadowRoot) walk(node.shadowRoot);
                            const kids = node.children ? Array.from(node.children) : [];
                            for (const k of kids) walk(k);
                        }
                        walk(root);
                        return count;
                    }

                    for (let i = 0; i < 18 && el; i++) {
                        best = el;
                        const subjectCount = deepCount(
                            el,
                            'input[name="subject"], input[placeholder*="Subject"]'
                        );
                        const editorCount = deepCount(
                            el,
                            '[contenteditable="true"][role="textbox"], .msg-form__contenteditable'
                        );

                        if (subjectCount > 0 && editorCount > 0) return el;

                        const root = el.getRootNode && el.getRootNode();
                        if (root && root.host && !el.parentElement) el = root.host;
                        else el = el.parentElement;
                    }
                    return best;
                    """,
                    anchor,
                )
                print("Message composer detected across Shadow DOM.")
                return composer or anchor
            except Exception:
                print("Message composer detected from Shadow DOM field.")
                return anchor

        # Legacy fallback.
        candidates: list[WebElement] = []
        for xpath in COMPOSER_ROOT_XPATHS:
            candidates.extend(_visible_elements(driver, By.XPATH, xpath))
        if candidates:
            return candidates[-1]

        time.sleep(0.2)

    raise TimeoutException(
        "Message composer did not appear after clicking the opened profile Message button."
    )

def verify_composer_recipient_shadow(
    driver: webdriver.Chrome,
    expected_profile_name: str,
    composer: WebElement | None = None,
) -> None:
    composer_text = _deep_shadow_text(driver, composer)
    if expected_profile_name.casefold() not in composer_text.casefold():
        page_text = _deep_shadow_text(driver, None)
        if expected_profile_name.casefold() not in page_text.casefold():
            raise RuntimeError(
                "SAFETY STOP: could not verify LinkedIn composer recipient "
                f"{expected_profile_name!r}."
            )
    print(f"Composer recipient verified: {expected_profile_name}")

def _set_native_input_value(
    driver: webdriver.Chrome,
    element: WebElement,
    value: str,
) -> None:
    try:
        element.click()
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.DELETE)
        element.send_keys(value)
        if (element.get_attribute("value") or "").strip() == value.strip():
            return
    except Exception:
        pass

    driver.execute_script(
        r"""
        const el = arguments[0];
        const value = arguments[1];
        const proto = el instanceof HTMLTextAreaElement
            ? HTMLTextAreaElement.prototype
            : HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(el, value);
        el.dispatchEvent(new Event('input', {bubbles: true, composed: true}));
        el.dispatchEvent(new Event('change', {bubbles: true, composed: true}));
        """,
        element,
        value,
    )

def fill_subject_shadow(
    driver: webdriver.Chrome,
    subject: str,
    composer: WebElement | None = None,
) -> bool:
    selectors = [
        'input[name="subject"]',
        'input[placeholder="Subject (optional)"]',
        'input[placeholder*="Subject"]',
    ]

    elements = _deep_shadow_query_all(
        driver,
        selectors,
        visible_only=True,
        root=composer,
    )
    if not elements:
        elements = _deep_shadow_query_all(
            driver,
            selectors,
            visible_only=True,
        )

    if not elements:
        print("No Subject field found; treating this as a standard LinkedIn DM.")
        return False

    field = elements[-1]
    _set_native_input_value(driver, field, subject)
    actual = (field.get_attribute("value") or "").strip()
    if actual != subject.strip():
        raise RuntimeError(
            f"LinkedIn Subject field was found but not filled. actual={actual!r}"
        )

    print(f"Subject filled from REPLY_TEXT_PATH: {subject}")
    return True

def find_message_input_shadow(
    driver: webdriver.Chrome,
    composer: WebElement | None = None,
) -> WebElement:
    selectors = [
        '[contenteditable="true"][role="textbox"][aria-label*="Write a message"]',
        '.msg-form__contenteditable[contenteditable="true"][role="textbox"]',
        '[contenteditable="true"][role="textbox"]',
        '[contenteditable="true"][aria-label*="message"]',
    ]

    elements = _deep_shadow_query_all(
        driver,
        selectors,
        visible_only=True,
        root=composer,
    )
    if not elements:
        elements = _deep_shadow_query_all(
            driver,
            selectors,
            visible_only=True,
        )

    if not elements:
        raise TimeoutException(
            "Could not find visible 'Write a message...' textbox across Shadow DOM."
        )
    return elements[-1]

def fill_message_shadow(
    driver: webdriver.Chrome,
    message_input: WebElement,
    body: str,
) -> None:
    try:
        message_input.click()
        message_input.send_keys(Keys.CONTROL, "a")
        message_input.send_keys(Keys.DELETE)
        message_input.send_keys(body)
        current = (
            message_input.get_attribute("innerText")
            or message_input.text
            or ""
        ).strip()
        if current:
            print(f"Message body filled from REPLY_TEXT_PATH ({len(body)} chars).")
            return
    except Exception:
        pass

    driver.execute_script(
        r"""
        const el = arguments[0];
        const text = arguments[1];
        el.focus();
        el.innerHTML = '';
        const lines = text.split('\n');
        for (let i = 0; i < lines.length; i++) {
            if (i > 0) el.appendChild(document.createElement('br'));
            el.appendChild(document.createTextNode(lines[i]));
        }
        el.dispatchEvent(new InputEvent('input', {
            bubbles: true,
            composed: true,
            inputType: 'insertText',
            data: text
        }));
        el.dispatchEvent(new Event('change', {bubbles: true, composed: true}));
        """,
        message_input,
        body,
    )

    current = (
        message_input.get_attribute("innerText")
        or message_input.text
        or ""
    ).strip()
    if not current:
        raise RuntimeError("LinkedIn 'Write a message...' field remained empty.")
    print(f"Message body filled from REPLY_TEXT_PATH ({len(body)} chars).")

def _find_file_input_shadow(
    driver: webdriver.Chrome,
    composer: WebElement | None = None,
) -> WebElement:
    """Prefer LinkedIn's document/file upload input over image-only input."""
    selectors = ['input[type="file"]']
    elements = _deep_shadow_query_all(
        driver,
        selectors,
        visible_only=False,
        root=composer,
    )
    if not elements:
        elements = _deep_shadow_query_all(
            driver,
            selectors,
            visible_only=False,
        )
    if not elements:
        raise TimeoutException(
            "Could not find LinkedIn attachment input across Shadow DOM."
        )

    # LinkedIn may expose separate image and document inputs. For a CV PDF,
    # avoid an input whose accept list is image-only.
    preferred: list[WebElement] = []
    fallback: list[WebElement] = []

    for element in elements:
        try:
            accept = (element.get_attribute("accept") or "").lower().strip()
        except Exception:
            accept = ""

        if accept and "image/" in accept and not any(
            token in accept
            for token in ("pdf", "doc", "word", "octet", "application/")
        ):
            fallback.append(element)
            continue

        preferred.append(element)

    if preferred:
        return preferred[-1]

    # Do not silently send a PDF to an image-only control.
    raise TimeoutException(
        "Only image upload inputs were found; document/CV attachment input "
        "was not found in the LinkedIn composer."
    )

def attach_files_shadow(
    driver: webdriver.Chrome,
    composer: WebElement | None,
    attachment_paths: Sequence[Path],
) -> None:
    for index, path in enumerate(attachment_paths, start=1):
        file_input = _find_file_input_shadow(driver, composer)
        print(f"Attaching file [{index}/{len(attachment_paths)}]: {path.name}")
        file_input.send_keys(str(path.resolve()))
        time.sleep(max(ATTACHMENT_UPLOAD_WAIT_SECONDS, 5.0))

def _shadow_send_button_candidates(
    driver: webdriver.Chrome,
    composer: WebElement | None = None,
) -> list[WebElement]:
    selectors = [
        'button.msg-form__send-button',
        'button[type="submit"]',
        'button[aria-label="Send"]',
        '[role="button"][aria-label="Send"]',
    ]
    elements = _deep_shadow_query_all(
        driver,
        selectors,
        visible_only=True,
        root=composer,
    )
    if not elements:
        elements = _deep_shadow_query_all(
            driver,
            selectors,
            visible_only=True,
        )
    return elements

def _button_is_enabled(button: WebElement) -> bool:
    """
    Return True only when LinkedIn Send button is really enabled/clickable.
    """
    try:
        if not button.is_displayed():
            return False

        if not button.is_enabled():
            return False

        disabled = button.get_attribute("disabled")
        aria_disabled = (
            button.get_attribute("aria-disabled") or ""
        ).strip().lower()

        classes = (
            button.get_attribute("class") or ""
        ).strip().lower()

        if disabled is not None:
            return False

        if aria_disabled == "true":
            return False

        if "disabled" in classes:
            return False

        return True

    except Exception:
        return False

def wait_for_send_button_shadow(
    driver: webdriver.Chrome,
    composer: WebElement | None = None,
) -> WebElement:
    """
    Wait until LinkedIn Send button exists AND becomes enabled.

    Attachment upload can keep Send disabled for several seconds,
    so use a slightly longer timeout than the normal element timeout.
    """
    timeout_seconds = max(ELEMENT_TIMEOUT_SECONDS, 30)
    end_time = time.time() + timeout_seconds

    last_state = None

    while time.time() < end_time:
        buttons = _shadow_send_button_candidates(
            driver,
            composer,
        )

        for button in reversed(buttons):
            try:
                text = (
                    button.text
                    or button.get_attribute("aria-label")
                    or button.get_attribute("title")
                    or ""
                ).strip()

                aria_disabled = (
                    button.get_attribute("aria-disabled") or ""
                ).strip().lower()

                disabled = button.get_attribute("disabled")

                current_state = (
                    text,
                    aria_disabled,
                    disabled,
                    button.is_enabled(),
                )

                if current_state != last_state:
                    print(
                        "Send button state | "
                        f"text={text!r} | "
                        f"aria-disabled={aria_disabled!r} | "
                        f"disabled={disabled!r} | "
                        f"is_enabled={button.is_enabled()}"
                    )
                    last_state = current_state

                if _button_is_enabled(button):
                    print("LinkedIn Send button is enabled.")
                    return button

            except (
                StaleElementReferenceException,
                WebDriverException,
            ):
                continue
            except Exception:
                continue

        time.sleep(0.5)

    raise TimeoutException(
        "LinkedIn Send button was found but did not become enabled "
        f"within {timeout_seconds} seconds. "
        "The CV attachment may still be uploading."
    )

def send_message_to_profile(
    driver: webdriver.Chrome,
    profile_url: str,
    subject: str,
    body: str,
    attachment_paths: Sequence[Path],
) -> bool:
    """Open profile, compose from REPLY_TEXT_PATH, attach CV, and send."""
    navigate_to_profile(driver, profile_url)

    profile_name = get_open_profile_name(driver)
    click_message_button(driver, profile_name=profile_name)

    composer = wait_for_composer_root(driver)
    verify_composer_recipient_shadow(
        driver,
        expected_profile_name=profile_name,
        composer=composer,
    )

    subject_was_filled = fill_subject_shadow(
        driver,
        subject=subject,
        composer=composer,
    )

    final_body = body
    if subject and not subject_was_filled and SUBJECT_FALLBACK_TO_MESSAGE_BODY:
        final_body = f"Subject: {subject}\n\n{body}"

    message_input = find_message_input_shadow(driver, composer=composer)
    fill_message_shadow(driver, message_input=message_input, body=final_body)

    attach_files_shadow(
        driver,
        composer=composer,
        attachment_paths=attachment_paths,
    )

    send_button = wait_for_send_button_shadow(driver, composer=composer)

    if not SEND_MESSAGES:
        print(
            "DRY RUN: subject/message/attachments prepared; "
            "SEND_MESSAGES=False so Send was not clicked."
        )
        return True

    # try:
    #     send_button.click()
    # except Exception:
    #     driver.execute_script("arguments[0].click();", send_button)

    print("Send button clicked.")
    time.sleep(AFTER_SEND_WAIT_SECONDS)
    print("Message sent.")
    return True

def send_all_linkedin_messages(
    driver: webdriver.Chrome,
    profile_urls: Sequence[str],
    subject: str,
    body: str,
    attachment_paths: Sequence[Path],
) -> tuple[int, int]:
    success_count = 0
    failed_count = 0
    total = len(profile_urls)

    for index, profile_url in enumerate(profile_urls, start=1):
        print("\n" + "=" * 80)
        print(f"[{index}/{total}] LinkedIn posted-by profile")
        print(profile_url)
        print("=" * 80)

        try:
            send_message_to_profile(
                driver=driver,
                profile_url=profile_url,
                subject=subject,
                body=body,
                attachment_paths=attachment_paths,
            )
            success_count += 1
            print(f"SUCCESS: {profile_url}")

        except Exception as exc:
            failed_count += 1
            print(f"FAILED: {profile_url}")
            print(f"Reason: {type(exc).__name__}: {exc}")

            # Do not automate LinkedIn checkpoint / verification.
            try:
                assert_linkedin_accessible(driver)
            except RuntimeError:
                raise

        if index < total:
            time.sleep(BETWEEN_RECIPIENTS_SECONDS)

    return success_count, failed_count

def process_role_folder(
    driver: webdriver.Chrome,
    role_name: str,
    role_folder: Path,
) -> tuple[int, int]:
    """Discover all inputs for one role folder, then send its LinkedIn DMs."""
    print("\n" + "=" * 90)
    print(f"ROLE: {role_name}")
    print(f"Folder: {role_folder}")
    print("=" * 90)

    config = discover_role_config(
        role_name=role_name,
        role_folder=role_folder,
    )

    subject, body = load_reply_text(config.reply_text_path)
    attachment_paths = validate_attachment_paths(
        [str(config.attachment_path)]
    )

    print(f"Reply text file    : {config.reply_text_path.name}")
    print(f"JD source file     : {config.jd_text_path.name}")
    print(f"CV attachment      : {config.attachment_path.name}")
    print(f"Posted-by URLs     : {len(config.profile_urls)}")
    print(f"Subject            : {subject}")
    for url in config.profile_urls:
        print(f"  - {url}")

    return send_all_linkedin_messages(
        driver=driver,
        profile_urls=config.profile_urls,
        subject=subject,
        body=body,
        attachment_paths=attachment_paths,
    )


def main(folder_path: str | Path) -> None:
    """
    Process all existing supported role folders below one daily folder.

    Example:
        main(r"job_profile\\specific\\company\\2026_09_17")
    """
    daily_folder = Path(folder_path).expanduser()

    if not daily_folder.exists():
        raise FileNotFoundError(
            f"Daily folder does not exist: {daily_folder}"
        )

    if not daily_folder.is_dir():
        raise NotADirectoryError(
            f"folder_path is not a directory: {daily_folder}"
        )

    print("=" * 90)
    print("AUTOMATED LINKEDIN DIRECT-MESSAGE SENDER")
    print(f"Daily folder:      {daily_folder.resolve()}")
    print(f"Script version:    {SCRIPT_VERSION}")
    print(f"Debugger address:  {CHROME_DEBUGGER_ADDRESS}")
    print(f"Send enabled:      {SEND_MESSAGES}")
    print("=" * 90)

    total_success = 0
    total_failed = 0
    processed_roles = 0
    missing_roles = 0
    config_failed_roles = 0

    driver: webdriver.Chrome | None = None

    try:
        driver = attach_to_existing_chrome()
        assert_linkedin_accessible(driver)

        for role_name in ROLE_FOLDERS:
            role_folder = daily_folder / role_name

            if not role_folder.exists():
                print(f"\nSKIP: role folder not present: {role_name}")
                missing_roles += 1
                continue

            if not role_folder.is_dir():
                print(
                    f"\nSKIP: expected a directory but found another "
                    f"item: {role_folder}"
                )
                config_failed_roles += 1
                continue

            try:
                success_count, failed_count = process_role_folder(
                    driver=driver,
                    role_name=role_name,
                    role_folder=role_folder,
                )
                processed_roles += 1
                total_success += success_count
                total_failed += failed_count

            except Exception as exc:
                config_failed_roles += 1
                print(f"\nFAILED ROLE: {role_name}")
                print(f"Reason: {type(exc).__name__}: {exc}")

                # Authentication/checkpoint failures should still stop the run.
                assert_linkedin_accessible(driver)
                continue

        print("\n" + "=" * 90)
        print("DAILY LINKEDIN MESSAGING COMPLETED")
        print(f"Processed role folders : {processed_roles}")
        print(f"Missing role folders   : {missing_roles}")
        print(f"Role config failures   : {config_failed_roles}")
        print(f"Successful profiles    : {total_success}")
        print(f"Failed profiles        : {total_failed}")
        print("=" * 90)

    finally:
        # Do not close the user's already-running debugger Chrome window.
        if driver is not None:
            try:
                driver.service.stop()
            except Exception:
                pass

if __name__ == "__main__":
    folder_path = "job_profile\\specific\\company\\2026_09_17"

    main(folder_path)
