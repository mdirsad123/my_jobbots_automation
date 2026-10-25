import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
project_root = Path(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def scrape_feed_posts(driver):
    """
    Scrape relevant LinkedIn feed/content job posts and save them to:

        output/scarp/YYYY-MM-DD.json

    Returns:
        int: Number of unique jobs written to the JSON file.
    """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    # OUTPUT_DIR = Path("output") / "scarp"
    OUTPUT_DIR = Path(project_root) / "linkedin" / "output" / "scarp"
    TODAY = datetime.now().strftime("%Y-%m-%d")
    OUTPUT_FILE = OUTPUT_DIR / f"{TODAY}.json"

    # Search phrases are intentionally broad so we can discover jobs that
    # may not contain exactly the same wording as the target category.
    SEARCH_QUERIES = [
        "Python Developer", "Data Engineer", "Devops Engineer", "Data Analyst",
        "Machine Learning Engineer", "AI Engineer", "AI Agent Engineer", "Agentic AI", "Generative AI", 
        "AI Systems Engineer", "MLops", "AI Developer", "Data Scientist","cloud",
        "Backend Engineer", "Backend Developer", "devops",
        "backend", "pythonjobs", "machinelearning", "datascience",
        "dataengineer", "dataengineering", "awsdataengineer", "bigdata"
    ]

    # Search each query over the past week. Change to "past-24h" if you
    # want only today's LinkedIn posts.
    DATE_FILTER = "past-24h"

    # Scroll settings.
    MAX_SCROLLS = 6

    # Only browser interactions require pacing. HTML parsing, filtering,
    # deduplication and JSON saving are local and do not contact LinkedIn.
    # Set (min_seconds, max_seconds) here; keep min <= max.
    ACTION_PAUSE = (1.0, 2.5)       # After navigation / result rendering.
    SCROLL_PAUSE = (2.0, 4.0)       # After each page scroll.
    EXPAND_PAUSE = (0.8, 1.5)       # Between "see more" clicks.
    SEARCH_PAUSE = (4.0, 7.0)       # Between separate search queries.

    # Page/result waits.
    RESULT_WAIT_SECONDS = 6.0
    RESULT_POLL_SECONDS = 0.25
    ROUTE_WAIT_SECONDS = 2.5

    # Keep this True if you only want posts that look like actual job
    # opportunities. It filters out generic trading discussions/news.
    JOB_ONLY = True

    # ------------------------------------------------------------------
    # Pacing and LinkedIn restriction handling (from V2, no role changes)
    # ------------------------------------------------------------------
    def pause(low_seconds, high_seconds):
        """Configurable delay between browser actions; not a detection bypass."""
        low = max(0.0, float(low_seconds))
        high = max(low, float(high_seconds))
        time.sleep(random.uniform(low, high))

    class LinkedInRestrictionError(RuntimeError):
        """Stop scraping when LinkedIn requires verification or limits access."""

    def check_linkedin_restriction():
        try:
            current_url = (driver.current_url or "").lower()
        except WebDriverException:
            return

        for marker in (
            "/checkpoint/", "/authwall", "/uas/login",
            "linkedin.com/login",
        ):
            if marker in current_url:
                raise LinkedInRestrictionError(
                    f"LinkedIn checkpoint/login page: {current_url}"
                )

        # Look only at the title, headings, and alert/dialog UI; a job post
        # mentioning "unusual activity" should not stop the scraper.
        try:
            visible_text = driver.execute_script(
                "var text = [document.title || ''];"
                "document.querySelectorAll("
                "'h1, h2, [role=\"dialog\"], [role=\"alert\"], .artdeco-modal'"
                ").forEach(function (el) { text.push(el.innerText || ''); });"
                "return text.join(' | ');"
            ) or ""
        except WebDriverException:
            return

        visible_text = str(visible_text).lower().replace("\u2019", "'")
        for marker in (
            "unusual activity", "unusual traffic",
            "search activity has been paused", "paused your search",
            "commercial use limit", "quick security check",
            "verify you're a human", "sign in to view more",
            "join linkedin to see",
        ):
            if marker in visible_text:
                raise LinkedInRestrictionError(
                    f"LinkedIn verification/restriction: {marker}"
                )

    # ------------------------------------------------------------------
    # Local helpers
    # ------------------------------------------------------------------
    def normalise_space(value):
        return re.sub(r"\s+", " ", value or "").strip()

    def clean_text(value):
        value = value or ""
        value = re.sub(r"\r\n?", "\n", value)
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()

    def extract_emails(text):
        matches = re.findall(
            r"(?<![\w.+-])[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?![\w.-])",
            text or "",
        )
        return list(
            dict.fromkeys(
                match.strip(".,;:()[]<>") for match in matches
            )
        )

    def extract_phone_numbers(text):
        if not text:
            return []

        pattern = re.compile(
            r"(?<![\w@])(?:\+?\d{1,3}[\s().-]*)?"
            r"(?:\(?\d{2,5}\)?[\s.-]*)?"
            r"\d{3,5}(?:[\s.-]*\d{3,5}){1,3}(?![\w@])"
        )

        results = []
        seen = set()

        for match in pattern.finditer(text):
            raw = match.group(0).strip()

            if re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", raw):
                continue
            if re.fullmatch(r"\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}", raw):
                continue

            digits = re.sub(r"\D", "", raw)

            if not 9 <= len(digits) <= 15:
                continue
            if len(set(digits)) <= 2:
                continue

            value = f"+{digits}" if raw.startswith("+") else digits

            if value not in seen:
                seen.add(value)
                results.append(value)

        return results

    def generate_hashtags(text):
        tags = set(re.findall(r"#\w+", (text or "").lower()))
        tags.add("#remote")
        return " ".join(sorted(tags))

    def build_search_url(query):
        base = "https://www.linkedin.com/search/results/content/"

        date_map = {
            "24h": '["past-24h"]',
            "past-24h": '["past-24h"]',
            "week": '["past-week"]',
            "past-week": '["past-week"]',
            "month": '["past-month"]',
            "past-month": '["past-month"]',
        }

        params = {
            "keywords": query,
            "origin": "FACETED_SEARCH",
            # "sortBy": '["date_posted"]',
            "datePosted": date_map.get(DATE_FILTER, '["past-24h"]'),
            # "contentType": '["jobs"]',
        }

        return (
            f"{base}?"
            f"{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
        )

    def extract_poster(post):
        link = (
            post.select_one(
                ".update-components-actor__container a[href*='/in/']"
            )
            or post.select_one(
                "span.update-components-actor__title a[href*='/in/'], "
                "a.update-components-actor__meta-link[href*='/in/'], "
                "a.update-components-actor__image[href*='/in/']"
            )
            or post.select_one(
                "a[href*='linkedin.com/in/'], "
                "a[href^='/in/'], "
                "a[href*='linkedin.com/company/'], "
                "a[href^='/company/']"
            )
        )

        if not link:
            return None, None

        href = (link.get("href") or "").strip()
        if not href:
            return None, None

        if href.startswith("/"):
            href = "https://www.linkedin.com" + href

        href = href.split("?")[0]

        lines = [
            normalise_space(line)
            for line in link.get_text("\n", strip=True).splitlines()
            if normalise_space(line)
        ]

        ignored = {"follow", "view profile", "message", "connect"}

        name = next(
            (
                line
                for line in lines
                if line.lower() not in ignored
                and not re.fullmatch(
                    r"[•·\s]*(1st|2nd|3rd)\+?",
                    line,
                    re.IGNORECASE,
                )
            ),
            None,
        )

        return name, href

    def clean_company(value):
        candidate = normalise_space(value).strip(" -–—|:;,.")

        if not candidate:
            return None

        lowered = candidate.lower()

        blocked = {
            "unknown",
            "n/a",
            "na",
            "view job",
            "apply",
            "easy apply",
            "promoted",
            "actively reviewing applicants",
            "follow",
            "message",
            "connect",
            "remote",
            "hybrid",
            "on-site",
            "onsite",
        }

        context_noise = (
            "mandatory skill",
            "mandatory skills",
            "nice-to-have",
            "nice to have",
            "experience",
            "location",
            "duration",
            "contract type",
            "responsibilities",
            "requirements",
            "knowledge",
            "proficiency",
            "expertise",
            "technology stack",
        )

        if lowered in blocked:
            return None

        if len(candidate) < 2 or len(candidate) > 100:
            return None

        if len(candidate.split()) > 10:
            return None

        if "@" in candidate:
            return None

        if "http://" in lowered or "https://" in lowered:
            return None

        if candidate.startswith("#"):
            return None

        if any(item in lowered for item in context_noise):
            return None

        if re.fullmatch(r"[\d\s()+./-]+", candidate):
            return None

        return candidate

    def extract_company(post_text):
        if not post_text:
            return "unknown"

        lines = [
            normalise_space(line)
            for line in post_text.splitlines()
            if normalise_space(line)
        ]

        labelled_patterns = [
            r"^(?:company|employer|hiring company|client|end client|customer)"
            r"\s*[:\-]\s*(.+)$",
            r"^(?:working for|role with|opportunity with|hiring for)\s+(.+)$",
        ]

        for line in lines:
            for pattern in labelled_patterns:
                match = re.match(pattern, line, flags=re.IGNORECASE)
                if match:
                    candidate = clean_company(match.group(1))
                    if candidate:
                        return candidate

        sentence_patterns = [
            r"\bjoin\s+([A-Z][A-Za-z0-9&.'()\- ]{1,80}?)"
            r"(?=\s+(?:as|for|in)\b|[,.!]|$)",
            r"\bat\s+([A-Z][A-Za-z0-9&.'()\- ]{1,80}?)"
            r"(?=\s+(?:as|for|in)\b|[,.!]|$)",
            r"\bfor\s+client\s+([A-Z][A-Za-z0-9&.'()\- ]{1,80}?)"
            r"(?=[,.!]|$)",
        ]

        for pattern in sentence_patterns:
            match = re.search(pattern, post_text)
            if match:
                candidate = clean_company(match.group(1))
                if candidate:
                    return candidate

        corporate_suffix = re.compile(
            r"^(?P<name>[A-Z][A-Za-z0-9&.'()\-]*"
            r"(?:\s+[A-Z][A-Za-z0-9&.'()\-]*){0,7})"
            r"\s+(?P<suffix>Inc\.?|Incorporated|Ltd\.?|Limited|LLC|"
            r"L\.L\.C\.|Pvt\.?\s+Ltd\.?|Private\s+Limited|Corp\.?|"
            r"Corporation|PLC|GmbH|S\.A\.)$"
        )

        for line in lines:
            match = corporate_suffix.fullmatch(line)
            if match:
                candidate = clean_company(
                    f"{match.group('name')} {match.group('suffix')}"
                )
                if candidate:
                    return candidate

        return "unknown"

    title_signals = [
        "engineer",
        "developer",
        "scientist",
        "analyst",
        "architect",
        "manager",
        "lead",
        "consultant",
        "specialist",
        "researcher",
        "intern",
        "trader",
        "quant",
        "quantitative",
        "devops",
        "mlops",
        "python",
        "data",
        "ai",
        "ml",
        "backend",
        "fullstack",
        "frontend",
        "software",
        "cloud",
        "platform",
        "automation",
        "trading",
        "finance",
        "fintech",
        "forex",
        "market",
        "risk",
        "portfolio",
        "investment",
        "broker",
        "backtesting",
        "strategy",
    ]

    title_noise = {
        "follow",
        "like",
        "comment",
        "repost",
        "share",
        "send",
        "connect",
        "message",
        "more",
        "view",
        "profile",
        "post",
        "linkedin",
        "home",
        "jobs",
        "network",
        "notifications",
        "report",
        "save",
        "copy",
        "embed",
        "reactions",
        "see",
        "hide",
        "apply",
    }

    def extract_title(post_text, card_title=None):
        if card_title:
            candidate = normalise_space(card_title)
            if candidate and candidate.lower() not in title_noise:
                return candidate

        lines = [
            normalise_space(line)
            for line in post_text.splitlines()
            if normalise_space(line)
        ]

        trigger_words = (
            "hiring",
            "we are hiring",
            "we're hiring",
            "looking for",
            "open role",
            "job opportunity",
            "position",
            "job title",
            "job by",
            "role:",
        )

        for index, line in enumerate(lines):
            lowered = line.lower()

            if any(trigger in lowered for trigger in trigger_words):
                candidates = []

                if index > 0:
                    candidates.append(lines[index - 1])

                if index + 1 < len(lines):
                    candidates.append(lines[index + 1])

                for candidate in candidates:
                    if (
                        2 <= len(candidate.split()) <= 12
                        and 3 <= len(candidate) <= 120
                        and candidate.lower() not in title_noise
                    ):
                        return candidate

        for line in lines:
            lowered = line.lower()
            words = len(line.split())

            if (
                1 <= words <= 10
                and any(signal in lowered for signal in title_signals)
                and lowered not in title_noise
                and not lowered.startswith(("http://", "https://"))
            ):
                return line

        return "Unknown"

    def is_relevant_job(text, title):
        combined = f"{title} {text}".lower()

        job_terms = (
            "hiring",
            "job",
            "role",
            "position",
            "vacancy",
            "opening",
            "career",
            "careers",
            "recruit",
            "recruiting",
            "looking for",
            "join our",
            "apply",
            "opportunity",
            "internship",
        )

        domain_terms = (
            "#ai engineer",
            "#ml engineer",
            "data engineer",
            "data scientist",
            "machine learning",
            "python developer",
            "python engineer",
            "backend engineer",
            "backend developer",
            "devops engineer",
            "software engineer",
            "software developer",
            "fullstack engineer",
            "fullstack developer",
            "cloud engineer",
            "cloud developer",
        )

        has_job = any(term in combined for term in job_terms)
        domain_hits = sum(
            1 for term in domain_terms if term in combined
        )

        if not JOB_ONLY:
            return domain_hits >= 1

        return has_job and domain_hits >= 1

    def post_text_from_tag(element):
        text_box = element.select_one("[data-testid='expandable-text-box']")
        target = text_box or element
        return target.get_text(separator="\n", strip=True)

    def is_real_post(element):
        text = normalise_space(post_text_from_tag(element))

        if len(text) < 60:
            return False

        lowered = text.lower()

        signal_words = (
            "hiring",
            "job",
            "role",
            "position",
            "engineer",
            "developer",
            "scientist",
            "analyst",
            "apply",
            "experience",
            "skills",
            "looking for",
            "opportunity",
            "intern",
            "opening",
            "vacancy",
        )

        return any(signal in lowered for signal in signal_words)

    def nearest_post_container(text_box):
        parent = text_box.parent
        best = parent

        for _ in range(14):
            if parent is None or getattr(parent, "name", None) in {
                "body",
                "html",
            }:
                break

            boxes = parent.select("[data-testid='expandable-text-box']")

            if len(boxes) == 1:
                best = parent

                identity_or_job = parent.select_one(
                    "a[href*='/in/'], "
                    "a[href*='/company/'], "
                    "a[href*='/jobs/view/']"
                )

                if (
                    identity_or_job
                    and len(
                        normalise_space(
                            parent.get_text(" ", strip=True)
                        )
                    )
                    >= 60
                ):
                    return parent

            elif len(boxes) > 1:
                break

            parent = parent.parent

        return best

    def dedupe_posts(posts):
        unique = []
        seen = set()

        for post in posts:
            key = normalise_space(
                post_text_from_tag(post)
            ).lower()

            if not key or key in seen:
                continue

            seen.add(key)
            unique.append(post)

        return unique

    def extract_posts(soup):
        text_boxes = soup.select(
            "[data-testid='expandable-text-box']"
        )

        if text_boxes:
            posts = dedupe_posts(
                [
                    nearest_post_container(text_box)
                    for text_box in text_boxes
                ]
            )

            posts = [
                post
                for post in posts
                if is_real_post(post)
            ]

            if posts:
                return posts

        selectors = [
            "li:has([data-testid='expandable-text-box'])",
            "article:has([data-testid='expandable-text-box'])",
            "div[data-view-name*='feed-update']",
            "div[data-view-name='search-entity-result-universal-template']",
            "div[data-urn*='urn:li:activity']",
            "div[data-urn*='urn:li:ugcPost']",
            "div[data-activity-urn]",
            "div[data-chameleon-result-urn*='urn:li:activity']",
            "li.reusable-search__result-container",
            "div.search-result__wrapper",
            "div.feed-shared-update-v2",
            "article",
        ]

        for selector in selectors:
            try:
                candidates = soup.select(selector)
            except Exception:
                continue

            if not candidates:
                continue

            posts = dedupe_posts(
                [
                    candidate
                    for candidate in candidates
                    if is_real_post(candidate)
                ]
            )

            if posts:
                return posts

        return []

    def expand_visible_posts():
        clicked = 0
        seen_ids = set()

        more_xpaths = [
            "//button[@data-testid='expandable-text-button']",
            "//*[@data-testid='expandable-text-button']",
            "//button[.//span[normalize-space()='more' or normalize-space()='…more']]",
            "//span[normalize-space()='more' or normalize-space()='…more']"
            "/ancestor::button[1]",
        ]

        for xpath in more_xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
            except Exception:
                continue

            for button in buttons:
                if clicked >= 30:
                    return clicked

                try:
                    element_id = getattr(button, "id", None)

                    if element_id and element_id in seen_ids:
                        continue

                    if element_id:
                        seen_ids.add(element_id)

                    if not button.is_displayed():
                        continue

                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});",
                        button,
                    )
                    pause(*EXPAND_PAUSE)
                    driver.execute_script(
                        "arguments[0].click();",
                        button,
                    )

                    clicked += 1
                    pause(*EXPAND_PAUSE)

                except Exception:
                    continue

        return clicked

    def collect_posts():
        collected_html = []
        seen_text = set()
        unchanged_rounds = 0
        last_seen_count = 0

        for round_number in range(MAX_SCROLLS + 1):
            check_linkedin_restriction()
            expand_visible_posts()
            check_linkedin_restriction()

            soup = BeautifulSoup(
                driver.page_source,
                "html.parser",
            )

            posts = extract_posts(soup)

            for post in posts:
                authored_text = normalise_space(
                    post_text_from_tag(post)
                ).lower()

                if not authored_text or authored_text in seen_text:
                    continue

                seen_text.add(authored_text)
                collected_html.append(str(post))

            if len(collected_html) == last_seen_count:
                unchanged_rounds += 1
            else:
                unchanged_rounds = 0
                last_seen_count = len(collected_html)

            if (
                round_number >= MAX_SCROLLS
                or unchanged_rounds >= 2
            ):
                break

            driver.execute_script(
                "window.scrollBy("
                "0, Math.max(window.innerHeight * 0.85, 700)"
                ");"
            )
            pause(*SCROLL_PAUSE)
            check_linkedin_restriction()

        return [
            BeautifulSoup(fragment, "html.parser").find()
            for fragment in collected_html
        ]

    def extract_linked_job_details(post):
        link = post.select_one(
            "a[href*='/jobs/view/']"
        )

        if not link:
            return None, None, None

        href = (link.get("href") or "").strip()

        if href.startswith("/"):
            href = "https://www.linkedin.com" + href

        href = href.split("?")[0] if href else None

        # Find the smallest job-card-like ancestor.
        card = link
        current = link

        for _ in range(10):
            parent = getattr(current, "parent", None)

            if parent is None or parent is post:
                break

            if parent.select_one(
                "[data-testid='expandable-text-box']"
            ):
                break

            job_links = parent.select(
                "a[href*='/jobs/view/']"
            )

            if len(job_links) > 1:
                break

            if len(job_links) == 1:
                compact_text = normalise_space(
                    parent.get_text(" ", strip=True)
                )

                if compact_text and len(compact_text) <= 800:
                    card = parent

            current = parent

        lines = [
            normalise_space(line)
            for line in card.get_text(
                "\n",
                strip=True,
            ).splitlines()
            if normalise_space(line)
        ]

        ignored = {
            "view job",
            "apply",
            "easy apply",
            "promoted",
            "save",
            "actively reviewing applicants",
        }

        card_title = next(
            (
                line
                for line in lines
                if line.casefold() not in ignored
                and 1 <= len(line.split()) <= 12
                and any(
                    signal in line.lower()
                    for signal in title_signals
                )
            ),
            None,
        )

        # Company profile link is the strongest company signal.
        company = None

        for company_link in card.select(
            "a[href*='/company/']"
        ):
            candidate = clean_company(
                company_link.get_text(" ", strip=True)
            )

            if candidate:
                company = candidate
                break

        if not company:
            title_index = None

            if card_title:
                title_cf = card_title.casefold()

                for index, line in enumerate(lines):
                    if line.casefold() == title_cf:
                        title_index = index
                        break

            ordered_lines = (
                lines[title_index + 1:] + lines[:title_index]
                if title_index is not None
                else lines
            )

            for line in ordered_lines:
                if line.casefold() in ignored:
                    continue

                if (
                    card_title
                    and line.casefold()
                    == card_title.casefold()
                ):
                    continue

                candidate = clean_company(line)

                if candidate:
                    company = candidate
                    break

        return card_title, company, href

    def extract_apply_link(post, preferred_url=None):
        if preferred_url:
            return preferred_url

        anchors = post.select("a[href]")

        for link in anchors:
            href = (link.get("href") or "").strip()

            if not href:
                continue

            visible = normalise_space(
                " ".join(
                    filter(
                        None,
                        [
                            link.get_text(" ", strip=True),
                            link.get("aria-label"),
                            link.get("title"),
                        ],
                    )
                )
            ).lower()

            if not any(
                token in visible
                for token in (
                    "apply",
                    "view job",
                    "job details",
                    "open job",
                )
            ):
                continue

            if href.startswith("/"):
                href = "https://www.linkedin.com" + href

            if href.startswith("http"):
                return href.split("#")[0]

        excluded = (
            "linkedin.com/in/",
            "linkedin.com/company/",
            "linkedin.com/feed/",
            "linkedin.com/posts/",
            "linkedin.com/search/",
            "/share",
        )

        for link in anchors:
            href = (link.get("href") or "").strip()

            if href.startswith("/"):
                href = "https://www.linkedin.com" + href

            if not href.startswith(
                ("http://", "https://")
            ):
                continue

            if any(
                fragment in href.lower()
                for fragment in excluded
            ):
                continue

            return href.split("#")[0]

        return None

    def fast_navigate(url):
        previous_url = driver.current_url

        target_keywords = urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query
        ).get("keywords", [None])[0]

        try:
            driver.execute_script(
                "window.location.replace(arguments[0]);",
                url,
            )
        except WebDriverException:
            try:
                driver.get(url)
            except TimeoutException:
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass

        def route_active(driver_instance):
            current_url = driver_instance.current_url

            if current_url == previous_url:
                return False

            if "/search/results/content/" not in current_url:
                return False

            if target_keywords is None:
                return True

            current_keywords = urllib.parse.parse_qs(
                urllib.parse.urlparse(current_url).query
            ).get("keywords", [None])[0]

            return current_keywords == target_keywords

        try:
            WebDriverWait(
                driver,
                ROUTE_WAIT_SECONDS,
                poll_frequency=0.2,
            ).until(route_active)
        except TimeoutException:
            pass

        check_linkedin_restriction()
        pause(*ACTION_PAUSE)

    def wait_for_results(query):
        post_css = (
            "[data-testid='expandable-text-box'], "
            "a[href*='/jobs/view/'], "
            "div[data-activity-urn], "
            "div[data-urn*='urn:li:activity'], "
            "div[data-urn*='urn:li:ugcPost'], "
            "div[data-chameleon-result-urn*='urn:li:activity'], "
            "div[data-view-name*='feed-update']"
        )

        no_results_xpath = (
            "//main//*[self::h1 or self::h2 or self::h3 "
            "or self::p or self::div]"
            "[contains(normalize-space(.),'No results for')]"
            " | //main//*[contains(@class,'search-no-results')]"
            " | //main//*[@data-test-search-no-results]"
        )

        def probe(driver_instance):
            try:
                results = driver_instance.find_elements(
                    By.CSS_SELECTOR,
                    post_css,
                )

                if results:
                    return True

                empty = driver_instance.find_elements(
                    By.XPATH,
                    no_results_xpath,
                )

                if empty:
                    return "no_results"

            except Exception:
                return False

            return False

        try:
            return WebDriverWait(
                driver,
                RESULT_WAIT_SECONDS,
                poll_frequency=RESULT_POLL_SECONDS,
            ).until(probe)
        except TimeoutException:
            return False

    def make_hash(title, company, url, description):
        raw = "::".join(
            [
                normalise_space(title).lower(),
                normalise_space(company).lower(),
                normalise_space(url).lower(),
                normalise_space(description).lower(),
            ]
        )

        return hashlib.md5(
            raw.encode("utf-8")
        ).hexdigest()

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------
    jobs = []
    seen_hashes = set()
    search_errors = 0

    for search_index, search_query in enumerate(SEARCH_QUERIES):
        # Also pause after an empty or failed search before starting the next.
        if search_index > 0:
            pause(*SEARCH_PAUSE)
        url = build_search_url(search_query)

        try:
            print(
                f"[scraper] Searching: {search_query}"
            )

            fast_navigate(url)

            loaded = wait_for_results(search_query)
            check_linkedin_restriction()
            pause(*ACTION_PAUSE)

            if loaded == "no_results":
                print(
                    f"[scraper] No results: {search_query}"
                )
                continue

            posts = collect_posts()

            print(
                f"[scraper] Found {len(posts)} candidate posts: "
                f"{search_query}"
            )

            for post in posts:
                try:
                    post_text = clean_text(
                        post_text_from_tag(post)
                    )

                    if not post_text:
                        continue

                    linked_title, linked_company, linked_job_url = (
                        extract_linked_job_details(post)
                    )

                    title = extract_title(
                        post_text,
                        linked_title,
                    )

                    if not is_relevant_job(
                        post_text,
                        title,
                    ):
                        continue

                    poster_name, poster_url = extract_poster(
                        post
                    )

                    company = (
                        linked_company
                        or extract_company(post_text)
                    )

                    emails = extract_emails(post_text)
                    phones = extract_phone_numbers(post_text)

                    contact = (
                        emails[0]
                        if emails
                        else (
                            phones[0]
                            if phones
                            else "N/A"
                        )
                    )

                    apply_url = extract_apply_link(
                        post,
                        preferred_url=linked_job_url,
                    )

                    # If the post is clearly a job but title extraction
                    # failed, keep it instead of throwing it away.
                    if title == "Unknown":
                        title = (
                            "Trading / Finance Job Opportunity"
                        )

                    job_hash = make_hash(
                        title,
                        company,
                        apply_url or "",
                        post_text,
                    )

                    if job_hash in seen_hashes:
                        continue

                    seen_hashes.add(job_hash)

                    job = {
                        "job_hashkey": job_hash,
                        "source": "linkedin_feed_post",
                        "title": title,
                        "company": company,
                        "post_date": TODAY,
                        "url": apply_url,
                        "posted_by_url": (
                            poster_url or "N/A"
                        ),
                        "job_poster_by": (
                            poster_name or "N/A"
                        ),
                        "job_description": post_text[:10000],
                        "hashtags": generate_hashtags(
                            post_text
                        ),
                        "email": contact,
                        "emails": emails,
                        "phone_numbers": phones,
                        "status": "scraped",
                        "search_query": search_query,
                        "scraped_at": datetime.now().isoformat(
                            timespec="seconds"
                        ),
                    }

                    jobs.append(job)

                except Exception as post_error:
                    print(
                        "[scraper] Post parsing error: "
                        f"{post_error}"
                    )

        except LinkedInRestrictionError as restriction:
            print(
                f"[scraper] LinkedIn access restriction; stopping searches: "
                f"{restriction}. No automatic retry."
            )
            break

        except Exception as search_error:
            search_errors += 1
            print(
                f"[scraper] Search error for "
                f"'{search_query}': {search_error}"
            )

    # ------------------------------------------------------------------
    # Save locally as JSON
    # ------------------------------------------------------------------
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # If today's file already exists, merge it with the new scrape.
    # This prevents a second run on the same day from deleting jobs
    # collected by an earlier run.
    existing_jobs = []

    if OUTPUT_FILE.exists():
        try:
            with OUTPUT_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:
                existing_data = json.load(file)

            if isinstance(existing_data, list):
                existing_jobs = existing_data

        except (
            json.JSONDecodeError,
            OSError,
        ):
            existing_jobs = []

    merged = []
    merged_hashes = set()

    for job in existing_jobs + jobs:
        job_hash = job.get("job_hashkey")

        if not job_hash:
            job_hash = make_hash(
                job.get("title", ""),
                job.get("company", ""),
                job.get("url", ""),
                job.get("job_description", ""),
            )
            job["job_hashkey"] = job_hash

        if job_hash in merged_hashes:
            continue

        merged_hashes.add(job_hash)
        merged.append(job)

    # Atomic write: write a temporary file first, then replace the
    # final JSON file.
    temp_file = OUTPUT_FILE.with_suffix(
        OUTPUT_FILE.suffix + ".tmp"
    )

    with temp_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            merged,
            file,
            indent=2,
            ensure_ascii=False,
        )

    temp_file.replace(OUTPUT_FILE)

    print(
        f"[scraper] Finished. "
        f"New jobs: {len(jobs)}, "
        f"total jobs in today's file: {len(merged)}, "
        f"search errors: {search_errors}"
    )

    print(
        f"[scraper] JSON saved to: "
        f"{OUTPUT_FILE}"
    )

    return len(jobs)
