"""
python -m linkedin.services.connection_req_msg_linkedin

Supported profile flows:

A) Profile has a visible Connect button:
   Open profile -> Connect -> Add a note -> Fill note -> Send

B) Profile does NOT have a visible Connect button:
   Open profile -> More -> Connect -> Add a note -> Fill note -> Send

The connection dialog used by newer LinkedIn pages can be inside OPEN Shadow DOM.
This script therefore searches normal DOM + open Shadow DOM recursively for:
- Add a note
- note textarea
- final Send button

Run:
    python -m linkedin.services.connection_req_msg_linkedin
    python -m linkedin.services.connection_req_msg_linkedin --preview-urls

Before running:
1. Start Chrome with remote debugging.
2. Log in to LinkedIn manually.
3. Do not automate login/CAPTCHA/checkpoint/verification.

Example Windows command:
    chrome.exe --remote-debugging-port=9222 ^
      --user-data-dir="C:\\selenium\\linkedin-debug-profile"
"""

from __future__ import annotations

import re
import sys
import time
from datetime import date
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


# ============================================================================
# USER SETTINGS
# ============================================================================

# Recruiter/profile links are now loaded from each role's JD file;
# no hardcoded POSTED_BY_URLS list is needed.

# Keep the note <= 300 characters.
# {first_name} is replaced with the opened profile's first name.
CONNECTION_NOTE = (
    """Hi {first_name}, I work with Python, PySpark, AWS, and data engineering. I came across your profile and would be glad to connect, exchange ideas, and stay in touch."""

)

CHROME_DEBUGGER_ADDRESS = "127.0.0.1:9222"

PAGE_LOAD_TIMEOUT_SECONDS = 25
ELEMENT_TIMEOUT_SECONDS = 15
DIRECT_CONNECT_TIMEOUT_SECONDS = 5

AFTER_PROFILE_LOAD_SECONDS = 2.0
AFTER_ACTION_SECONDS = 1.0
AFTER_SEND_SECONDS = 2.0
BETWEEN_PROFILES_SECONDS = 4.0

# True  = really click final Send.
# False = fill the note and stop before Send.
SEND_CONNECTION_REQUESTS = True


# ============================================================================
# URL HELPERS
# ============================================================================

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


def extract_profile_urls(raw_text: str) -> list[str]:
    urls: list[str] = []

    for match in LINKEDIN_PROFILE_URL_RE.findall(raw_text or ""):
        url = match.strip().rstrip(".,;:)")
        url = url.split("?", 1)[0].rstrip("/")

        if url.lower().startswith("http://"):
            url = "https://" + url[len("http://") :]

        urls.append(url)

    return _dedupe_preserve_order(urls)


# ============================================================================
# AUTO-DISCOVERY: TODAY'S COMPANY FOLDER AND LINKEDIN URLs IN ROLE JD FILES
# ============================================================================

ROLE_FOLDERS = (
    "aiengineer",
    "awsdataengineer",
    "dataengineer",
    "pythondeveloper",
)

# Handles:  # postedbyurl: ...
#           # PostedByURL: ...
#           Posted-by Profile URLs: ...  (older JD format)
POSTED_BY_LINE_PATTERN = re.compile(
    r"^\s*(?:[-*]\s*)?(?:#\s*)?posted[\s_-]*by[\s_-]*"
    r"(?:profile[\s_-]*)?urls?\s*:\s*(.*)$",
    re.IGNORECASE,
)


def resolve_daily_company_folder(folder_path: str | Path | None = None) -> Path:
    """Find today's company folder using the machine's local date.

    Supports BOTH YYYY-MM-DD (as in VS Code screenshot) and YYYY_MM_DD.
    Works when invoked from the project root or via `python -m ...`.
    An explicit path overrides today's automatic selection.
    """
    script_dir = Path(__file__).resolve().parent
    anchors = list(dict.fromkeys([
        Path.cwd(), *Path.cwd().parents,
        script_dir, *script_dir.parents,
    ]))

    if folder_path is not None:
        raw = Path(folder_path).expanduser()
        possibilities = [raw] if raw.is_absolute() else [
            anchor / raw for anchor in anchors
        ]
    else:
        today = date.today()
        date_names = (today.strftime("%Y-%m-%d"), today.strftime("%Y_%m_%d"))
        possibilities = [
            anchor / partial / date_name
            for anchor in anchors
            for partial in (
                Path("job_profile/specific/company"),
                Path("specific/company"),
                Path("company"),
                Path("."),
            )
            for date_name in date_names
        ]

    for candidate in possibilities:
        if candidate.is_dir():
            return candidate.resolve()

    expected = date.today().strftime("%Y-%m-%d")
    raise FileNotFoundError(
        "Company date folder not found. Expected a folder such as "
        f"job_profile/specific/company/{expected}/ (also supports underscores). "
        "Run from your project root, or pass the date-folder path explicitly."
    )


def find_role_jd_file(role_folder: Path) -> Path:
    """Prefer <role>_jd.txt; also support legacy jd.txt in that role folder."""
    candidates = sorted(
        (p for p in role_folder.rglob("*")
         if p.is_file() and p.suffix.casefold() == ".txt"
         and "email_reply" not in p.stem.casefold()),
        key=lambda p: str(p).casefold(),
    )
    for wanted in (f"{role_folder.name}_jd.txt", "jd.txt"):
        matches = [p for p in candidates if p.name.casefold() == wanted.casefold()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RuntimeError(
                f"Multiple {wanted} files in {role_folder}; choose one."
            )

    fallbacks = [p for p in candidates if "jd" in p.stem.casefold()
                 and "reply" not in p.stem.casefold()]
    if len(fallbacks) == 1:
        return fallbacks[0]
    if len(fallbacks) > 1:
        raise RuntimeError(
            f"Multiple JD candidates in {role_folder}: "
            + ", ".join(p.name for p in fallbacks)
        )
    raise FileNotFoundError(
        f"No JD .txt found in {role_folder}. Expected "
        f"{role_folder.name}_jd.txt (or jd.txt)."
    )


def extract_posted_by_urls_from_jd(jd_path: Path) -> list[str]:
    """Read *only* labeled postedbyurl lines; retain valid /in/ profiles.

    Handles repeated markers, comma-separated URLs, and subsequent URL-only
    lines. Ignores unrelated JD links and LinkedIn /company/ pages.
    """
    lines = jd_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    found = []
    markers = 0
    i = 0
    while i < len(lines):
        match = POSTED_BY_LINE_PATTERN.match(lines[i])
        if not match:
            i += 1
            continue
        markers += 1
        chunks = [match.group(1)]
        i += 1
        while i < len(lines):
            continuation = lines[i].strip().lstrip("-* ").strip()
            if not continuation.lower().startswith(("https://", "http://")):
                break
            chunks.append(continuation)
            i += 1
        found.extend(extract_profile_urls("\n".join(chunks)))

    urls = _dedupe_preserve_order(found)
    if not markers:
        print(f"WARNING: No '# postedbyurl:' marker in {jd_path}")
    elif not urls:
        print(f"WARNING: Marker present, but no valid LinkedIn /in/ URLs in {jd_path}")
    return urls

def collect_today_posted_by_urls(daily_folder: Path) -> list[str]:
    """Combine all today's supported role JDs, deduplicating globally."""
    all_urls: list[str] = []
    for role_name in ROLE_FOLDERS:
        role_folder = daily_folder / role_name
        if not role_folder.is_dir():
            print(f"SKIP missing role folder: {role_name}")
            continue
        try:
            jd_path = find_role_jd_file(role_folder)
            urls = extract_posted_by_urls_from_jd(jd_path)
        except (FileNotFoundError, RuntimeError, OSError) as exc:
            print(f"WARNING: Cannot load JD for {role_name}: {exc}")
            continue
        print(f"{role_name}: {len(urls)} unique /in/ profiles from {jd_path.name}")
        all_urls.extend(urls)

    return _dedupe_preserve_order(all_urls)


# ============================================================================
# CHROME / LINKEDIN
# ============================================================================

def attach_to_existing_chrome() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", CHROME_DEBUGGER_ADDRESS)

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:
        raise RuntimeError(
            "Could not attach to Chrome at "
            f"{CHROME_DEBUGGER_ADDRESS}.\n"
            "Start Chrome with remote debugging and log into LinkedIn first.\n"
            "Example:\n"
            '  chrome.exe --remote-debugging-port=9222 '
            '--user-data-dir="C:\\selenium\\linkedin-debug-profile"\n'
            f"Original error: {exc}"
        ) from exc

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
    return driver


def assert_linkedin_accessible(driver: webdriver.Chrome) -> None:
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
    print(f"Opening profile: {profile_url}")
    driver.get(profile_url)
    time.sleep(AFTER_PROFILE_LOAD_SECONDS)
    assert_linkedin_accessible(driver)


def get_open_profile_name(driver: webdriver.Chrome) -> str:
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


def get_first_name(profile_name: str) -> str:
    cleaned = re.sub(r"\s+", " ", profile_name).strip()
    return cleaned.split(" ", 1)[0] if cleaned else "there"


# ============================================================================
# GENERIC NORMAL-DOM HELPERS
# ============================================================================

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


# ============================================================================
# OPEN SHADOW DOM HELPERS
# ============================================================================

def _deep_shadow_query_all(
    driver: webdriver.Chrome,
    selectors: Sequence[str],
    *,
    visible_only: bool = True,
) -> list[WebElement]:
    """
    Search the normal DOM and every OPEN Shadow DOM recursively.

    This is needed for LinkedIn's newer connection invitation modal.
    XPath cannot cross Shadow DOM boundaries.
    """
    script = r"""
        const selectors = arguments[0];
        const visibleOnly = arguments[1];

        function isVisible(el) {
            if (!el) return false;

            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);

            return (
                rect.width > 0 &&
                rect.height > 0 &&
                style.display !== 'none' &&
                style.visibility !== 'hidden'
            );
        }

        const results = [];
        const seen = new Set();

        function addElement(el) {
            if (!el || seen.has(el)) return;
            if (visibleOnly && !isVisible(el)) return;

            seen.add(el);
            results.push(el);
        }

        function walk(root) {
            if (!root) return;

            if (root.querySelectorAll) {
                for (const selector of selectors) {
                    let matches = [];

                    try {
                        matches = root.querySelectorAll(selector);
                    } catch (e) {
                        matches = [];
                    }

                    for (const el of matches) {
                        addElement(el);
                    }
                }
            }

            if (root.shadowRoot) {
                walk(root.shadowRoot);
            }

            let children = [];

            try {
                children = root.children
                    ? Array.from(root.children)
                    : [];
            } catch (e) {
                children = [];
            }

            for (const child of children) {
                walk(child);
            }
        }

        walk(document);
        return results;
    """

    try:
        found = driver.execute_script(
            script,
            list(selectors),
            visible_only,
        )
        return list(found or [])
    except JavascriptException:
        return []


def wait_for_deep_shadow_element(
    driver: webdriver.Chrome,
    selectors: Sequence[str],
    *,
    timeout: float,
    description: str,
    predicate=None,
) -> WebElement:
    end_time = time.time() + timeout

    while time.time() < end_time:
        elements = _deep_shadow_query_all(
            driver,
            selectors,
            visible_only=True,
        )

        for element in reversed(elements):
            try:
                if predicate is None or predicate(element):
                    return element
            except (
                StaleElementReferenceException,
                WebDriverException,
            ):
                continue

        time.sleep(0.2)

    raise TimeoutException(
        f"Could not find visible {description} across normal DOM + "
        f"open Shadow DOM within {timeout:.1f}s."
    )


def element_text_or_aria(element: WebElement) -> str:
    try:
        return (
            element.get_attribute("aria-label")
            or element.text
            or element.get_attribute("title")
            or ""
        ).strip()
    except Exception:
        return ""


# ============================================================================
# STEP 1: CLICK CONNECT
# - First try the DIRECT Connect button in the opened profile header.
# - If it is not present, fall back to More -> Connect.
# ============================================================================

def find_open_profile_action_button(
    driver: webdriver.Chrome,
    profile_name: str,
    wanted_action: str,
    timeout: float,
) -> WebElement:
    """
    Find an action button belonging to the currently opened profile header.

    Anchoring the search to the current profile name avoids accidentally
    clicking Connect/More controls in "People you may know" cards.
    """
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            button = driver.execute_script(
                r"""
                const wantedName = arguments[0];
                const wantedAction = arguments[1].toLowerCase();

                function norm(value) {
                    return (value || '').replace(/\s+/g, ' ').trim();
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

                function isWantedAction(el) {
                    if (!visible(el)) return false;

                    const text = norm(
                        el.innerText || el.textContent || ''
                    ).toLowerCase();

                    const aria = norm(
                        el.getAttribute('aria-label') || ''
                    ).toLowerCase();

                    const title = norm(
                        el.getAttribute('title') || ''
                    ).toLowerCase();

                    if (wantedAction === 'connect') {
                        return (
                            text === 'connect' ||
                            aria === 'connect' ||
                            aria.startsWith('connect ') ||
                            aria.includes(' to connect') ||
                            aria.startsWith('invite ') &&
                            aria.includes('connect')
                        );
                    }

                    if (wantedAction === 'more') {
                        return (
                            text === 'more' ||
                            aria === 'more' ||
                            aria.startsWith('more ') ||
                            title === 'more'
                        );
                    }

                    return (
                        text === wantedAction ||
                        aria === wantedAction
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
                        depth < 14 && container;
                        depth++
                    ) {
                        const controls = Array.from(
                            container.querySelectorAll(
                                'button, a, [role="button"]'
                            )
                        ).filter(isWantedAction);

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
                                    containerLength <
                                    bestContainerLength
                                )
                            ) {
                                best = controls[0];
                                bestDepth = depth;
                                bestContainerLength =
                                    containerLength;
                            }

                            break;
                        }

                        container = container.parentElement;
                    }
                }

                return best;
                """,
                profile_name,
                wanted_action,
            )

            if button is not None and button.is_displayed():
                return button

        except (
            StaleElementReferenceException,
            WebDriverException,
        ):
            pass

        time.sleep(0.2)

    raise TimeoutException(
        f"Could not find {wanted_action!r} action for opened "
        f"profile {profile_name!r}."
    )


CONNECT_MENU_XPATHS = [
    "//*[@role='menu']//button[normalize-space()='Connect']",
    "//*[@role='menu']//*[@role='menuitem' and normalize-space()='Connect']",
    "//*[@role='menu']//*[@role='menuitem' and .//*[normalize-space()='Connect']]",
    "//*[@role='menu']//*[self::button or self::a or @role='button'][.//*[normalize-space()='Connect']]",
    "//*[contains(@class,'artdeco-dropdown__content')]//*[@role='menuitem' and .//*[normalize-space()='Connect']]",
    "//*[contains(@class,'artdeco-dropdown__content')]//*[self::button or self::a or @role='button'][normalize-space()='Connect']",
]


def click_connect(driver: webdriver.Chrome, profile_name: str) -> None:
    """
    Prefer the direct Connect button visible in the profile header.

    Example from the supplied screenshot:
        Connect | Message | More

    Profiles such as Debi Kar may instead expose Connect only under More,
    so More -> Connect remains as a fallback.
    """

    # ---------------------------------------------------------
    # 1A. DIRECT CONNECT
    # ---------------------------------------------------------
    try:
        connect_button = find_open_profile_action_button(
            driver,
            profile_name=profile_name,
            wanted_action="connect",
            timeout=DIRECT_CONNECT_TIMEOUT_SECONDS,
        )

        click_element(driver, connect_button)
        print("Clicked DIRECT Connect button from profile header.")
        time.sleep(AFTER_ACTION_SECONDS)
        return

    except TimeoutException:
        print(
            "Direct Connect button not found. "
            "Trying More -> Connect fallback..."
        )

    # ---------------------------------------------------------
    # 1B. MORE -> CONNECT FALLBACK
    # ---------------------------------------------------------
    more_button = find_open_profile_action_button(
        driver,
        profile_name=profile_name,
        wanted_action="more",
        timeout=ELEMENT_TIMEOUT_SECONDS,
    )

    click_element(driver, more_button)
    print("Clicked More.")
    time.sleep(AFTER_ACTION_SECONDS)

    try:
        connect_menu_item = wait_for_visible_xpath(
            driver,
            CONNECT_MENU_XPATHS,
            timeout=ELEMENT_TIMEOUT_SECONDS,
            description="Connect option inside More menu",
        )
    except TimeoutException as exc:
        body_text = ""

        try:
            body_text = (
                driver.find_element(By.TAG_NAME, "body").text
                or ""
            ).lower()
        except Exception:
            pass

        if "pending" in body_text:
            raise RuntimeError(
                "A connection request may already be pending for "
                f"{profile_name}."
            ) from exc

        raise RuntimeError(
            "Connect was not found directly or under More. "
            "The profile may already be connected, may have a pending "
            "request, or may not allow connection requests."
        ) from exc

    click_element(driver, connect_menu_item)
    print("Clicked Connect from More menu.")
    time.sleep(AFTER_ACTION_SECONDS)


# ============================================================================
# STEP 2: CLICK "ADD A NOTE" THROUGH SHADOW DOM
# ============================================================================

ADD_NOTE_CSS_SELECTORS = [
    'button[aria-label="Add a note"]',
    '[role="button"][aria-label="Add a note"]',
    'button.artdeco-button[aria-label="Add a note"]',
]


def _is_add_note_button(element: WebElement) -> bool:
    value = element_text_or_aria(element).casefold()

    if value == "add a note":
        return True

    try:
        text = (element.text or "").strip().casefold()
        return text == "add a note"
    except Exception:
        return False


def click_add_note(driver: webdriver.Chrome) -> None:
    """
    LinkedIn's Add a note button can be inside Shadow DOM.

    The supplied DevTools screenshot shows:
        <button aria-label="Add a note" ...>

    XPath cannot cross this Shadow DOM boundary, so we use recursive CSS
    searching through open shadow roots.
    """
    # If the note textarea is already open, do not click Add a note again.
    if find_note_textarea_if_visible(driver) is not None:
        print("Connection note textarea is already visible.")
        return

    button = wait_for_deep_shadow_element(
        driver,
        ADD_NOTE_CSS_SELECTORS,
        timeout=ELEMENT_TIMEOUT_SECONDS,
        description="Add a note button",
        predicate=_is_add_note_button,
    )

    click_element(driver, button)
    print("Clicked Add a note through Shadow DOM.")
    time.sleep(AFTER_ACTION_SECONDS)


# ============================================================================
# STEP 3: FIND + FILL NOTE THROUGH SHADOW DOM
# ============================================================================

NOTE_TEXTAREA_CSS_SELECTORS = [
    'textarea[placeholder*="We know each other"]',
    'textarea[placeholder*="know each other"]',
    'textarea[aria-label*="note"]',
    'textarea',
]


def find_note_textarea_if_visible(
    driver: webdriver.Chrome,
) -> WebElement | None:
    elements = _deep_shadow_query_all(
        driver,
        NOTE_TEXTAREA_CSS_SELECTORS,
        visible_only=True,
    )

    for element in reversed(elements):
        try:
            if element.tag_name.lower() != "textarea":
                continue

            placeholder = (
                element.get_attribute("placeholder") or ""
            ).casefold()

            aria = (
                element.get_attribute("aria-label") or ""
            ).casefold()

            # Prefer obvious connection-note fields.
            if (
                "know each other" in placeholder
                or "note" in aria
            ):
                return element
        except Exception:
            continue

    # If there is exactly one visible textarea in the whole page, it is
    # normally the open connection-note field.
    visible_textareas = []

    for element in elements:
        try:
            if element.tag_name.lower() == "textarea":
                visible_textareas.append(element)
        except Exception:
            continue

    if len(visible_textareas) == 1:
        return visible_textareas[0]

    return None


def wait_for_note_textarea(driver: webdriver.Chrome) -> WebElement:
    end_time = time.time() + ELEMENT_TIMEOUT_SECONDS

    while time.time() < end_time:
        textarea = find_note_textarea_if_visible(driver)

        if textarea is not None:
            return textarea

        time.sleep(0.2)

    raise TimeoutException(
        "Could not find the connection-note textarea across "
        "normal DOM + open Shadow DOM."
    )


def build_connection_note(profile_name: str) -> str:
    first_name = get_first_name(profile_name)

    note = CONNECTION_NOTE.format(
        first_name=first_name,
        profile_name=profile_name,
    ).strip()

    if not note:
        raise ValueError("CONNECTION_NOTE is empty.")

    if len(note) > 300:
        raise ValueError(
            "LinkedIn connection notes are limited to 300 characters. "
            f"Current note length: {len(note)}."
        )

    return note


def fill_connection_note(
    driver: webdriver.Chrome,
    note: str,
) -> WebElement:
    textarea = wait_for_note_textarea(driver)

    # First try normal Selenium keyboard input.
    try:
        textarea.click()
        textarea.send_keys(Keys.CONTROL, "a")
        textarea.send_keys(Keys.DELETE)
        textarea.send_keys(note)

        actual = (
            textarea.get_attribute("value") or ""
        ).strip()

        if actual == note:
            print(
                f"Filled connection note "
                f"({len(note)}/300 characters)."
            )
            return textarea

    except Exception:
        pass

    # Shadow-DOM-safe JS fallback using the native textarea value setter.
    driver.execute_script(
        r"""
        const el = arguments[0];
        const value = arguments[1];

        el.focus();

        const setter = Object.getOwnPropertyDescriptor(
            HTMLTextAreaElement.prototype,
            'value'
        ).set;

        setter.call(el, value);

        el.dispatchEvent(
            new InputEvent(
                'input',
                {
                    bubbles: true,
                    composed: true,
                    inputType: 'insertText',
                    data: value
                }
            )
        );

        el.dispatchEvent(
            new Event(
                'change',
                {
                    bubbles: true,
                    composed: true
                }
            )
        );
        """,
        textarea,
        note,
    )

    actual = (
        textarea.get_attribute("value") or ""
    ).strip()

    if actual != note:
        raise RuntimeError(
            "The connection note textarea was found but could not be "
            f"filled correctly. Expected {len(note)} chars; "
            f"actual {len(actual)} chars."
        )

    print(
        f"Filled connection note through JS "
        f"({len(note)}/300 characters)."
    )
    return textarea


# ============================================================================
# STEP 4: CLICK FINAL "SEND" THROUGH SHADOW DOM
# ============================================================================

SEND_CSS_SELECTORS = [
    'button[aria-label="Send"]',
    '[role="button"][aria-label="Send"]',
    'button[type="submit"]',
    'button.artdeco-button',
]


def _button_enabled(button: WebElement) -> bool:
    try:
        if not button.is_displayed():
            return False

        if not button.is_enabled():
            return False

        if button.get_attribute("disabled") is not None:
            return False

        aria_disabled = (
            button.get_attribute("aria-disabled") or ""
        ).strip().casefold()

        if aria_disabled == "true":
            return False

        return True

    except Exception:
        return False


def _is_final_send_button(button: WebElement) -> bool:
    if not _button_enabled(button):
        return False

    try:
        aria = (
            button.get_attribute("aria-label") or ""
        ).strip().casefold()

        text = (
            button.text or ""
        ).strip().casefold()

        # IMPORTANT:
        # Do not match the initial "Send without a note" button.
        return (
            aria == "send"
            or text == "send"
        )

    except Exception:
        return False


def wait_for_enabled_send_button(
    driver: webdriver.Chrome,
) -> WebElement:
    return wait_for_deep_shadow_element(
        driver,
        SEND_CSS_SELECTORS,
        timeout=ELEMENT_TIMEOUT_SECONDS,
        description="enabled final Send button",
        predicate=_is_final_send_button,
    )


def click_send_connection_request(
    driver: webdriver.Chrome,
) -> None:
    send_button = wait_for_enabled_send_button(driver)

    if not SEND_CONNECTION_REQUESTS:
        print(
            "DRY RUN: note is filled. "
            "SEND_CONNECTION_REQUESTS=False, so final Send was not clicked."
        )
        return

    click_element(driver, send_button)
    print("Clicked final Send through Shadow DOM.")
    time.sleep(AFTER_SEND_SECONDS)


# ============================================================================
# COMPLETE PROFILE FLOW
# ============================================================================

def send_connection_request_to_profile(
    driver: webdriver.Chrome,
    profile_url: str,
) -> bool:
    navigate_to_profile(driver, profile_url)

    profile_name = get_open_profile_name(driver)

    # 1. Direct Connect if visible, otherwise More -> Connect.
    click_connect(
        driver,
        profile_name=profile_name,
    )

    # 2. Add a note (normal DOM + Shadow DOM).
    click_add_note(driver)

    # 3. Fill note.
    note = build_connection_note(profile_name)
    fill_connection_note(
        driver,
        note=note,
    )

    # 4. Final Send.
    click_send_connection_request(driver)

    print(
        f"SUCCESS: connection request flow completed for "
        f"{profile_name}"
    )
    return True


def send_all_connection_requests(
    driver: webdriver.Chrome,
    profile_urls: Sequence[str],
) -> tuple[int, int]:
    success_count = 0
    failed_count = 0
    total = len(profile_urls)

    for index, profile_url in enumerate(
        profile_urls,
        start=1,
    ):
        print("\n" + "=" * 80)
        print(f"[{index}/{total}] LinkedIn profile")
        print(profile_url)
        print("=" * 80)

        try:
            send_connection_request_to_profile(
                driver=driver,
                profile_url=profile_url,
            )

            success_count += 1

        except Exception as exc:
            failed_count += 1

            print(f"FAILED: {profile_url}")
            print(
                f"Reason: {type(exc).__name__}: {exc}"
            )

            # Do not automate login/checkpoint/verification.
            assert_linkedin_accessible(driver)

        if index < total:
            time.sleep(BETWEEN_PROFILES_SECONDS)

    return success_count, failed_count


# ============================================================================
# MAIN
# ============================================================================

def main(folder_path: str | Path | None = None, *, preview_only: bool = False) -> None:
    daily_folder = resolve_daily_company_folder(folder_path)
    print(f"Daily company folder: {daily_folder}")
    profile_urls = collect_today_posted_by_urls(daily_folder)

    if not profile_urls:
        print("No LinkedIn /in/ profile URLs found in today's role JD files.")
        return

    print(f"Unique LinkedIn profiles across roles: {len(profile_urls)}")
    if preview_only:
        print("URL PREVIEW ONLY - Chrome was not opened and no requests sent.")
        for url in profile_urls:
            print(f"  {url}")
        return

    preview_note = CONNECTION_NOTE.format(
        first_name="Name",
        profile_name="Name",
    ).strip()

    if len(preview_note) > 300:
        raise ValueError(
            "CONNECTION_NOTE is longer than LinkedIn's "
            "300-character limit. "
            f"Current preview length: "
            f"{len(preview_note)}."
        )

    print("LinkedIn connection-request sender")
    print(f"Profiles:          {len(profile_urls)}")
    print(
        f"Debugger address: "
        f"{CHROME_DEBUGGER_ADDRESS}"
    )
    print(
        f"Send enabled:     "
        f"{SEND_CONNECTION_REQUESTS}"
    )
    print(
        f"Note length:      "
        f"{len(preview_note)}/300"
    )

    driver: webdriver.Chrome | None = None

    try:
        driver = attach_to_existing_chrome()
        assert_linkedin_accessible(driver)

        success_count, failed_count = (
            send_all_connection_requests(
                driver=driver,
                profile_urls=profile_urls,
            )
        )

        print("\n" + "=" * 80)
        print(
            "LinkedIn connection-request "
            "processing completed."
        )
        print(f"Successful: {success_count}")
        print(f"Failed:     {failed_count}")
        print("=" * 80)

    finally:
        # Keep the user's existing debugger Chrome window open.
        if driver is not None:
            try:
                driver.service.stop()
            except Exception:
                pass


if __name__ == "__main__":
    args = [arg for arg in sys.argv[1:] if arg != "--preview-urls"]
    main(args[0] if args else None, preview_only="--preview-urls" in sys.argv[1:])
