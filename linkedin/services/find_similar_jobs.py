"""
find_similar_jobs.py
====================
Groups newly scraped LinkedIn jobs by role family and writes one combined
text file per group to a date-only folder under ``linkedin/output``.

By default, only jobs created today are loaded from the database.  This avoids
mixing previous/older database rows into the current grouping step.  Callers
may optionally pass ``job_ids`` to restrict grouping to the exact jobs created
by one scraper run.

Output folder format:
  linkedin/output/<YYYY-MM-DD>/

Filename format:
  <role>_<company1>_<company2>_<YYYY-MM-DD>.txt

Example:
  dataengineer_hcltech_tcs_2026-08-02.txt
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime

# Allow running as __main__
project_root = Path(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.structured_logging import get_logger

logger = get_logger("find_similar_jobs")

ROLE_FAMILIES: Dict[str, List[str]] = {
    # IMPORTANT:
    # Keep the order intentional because _classify_title() returns
    # the FIRST matching family.

    # ============================================================
    # 1. ALGORITHMIC / ALGO / QUANT / TRADING
    # ============================================================
    "Algorithmic / Algo Trader": [
        # Algorithmic trading
        "algorithmic trader",
        "algorithmic trading",
        "algorithmictrader",
        "algorithmictrading",
        "algo trader",
        "algo trading",
        "algotrader",
        "algotrading",
        "algo developer",
        "algo engineer",
        "algorithmic developer",
        "algorithmic engineer",

        # Automated / systematic trading
        "automated trading",
        "automated trader",
        "automated trading developer",
        "automated trading engineer",
        "systematic trader",
        "systematic trading",
        "systematic trading developer",
        "systematic trading engineer",
        "systematic developer",
        "systematic engineer",

        # Quant
        "quant trader",
        "quant trading",
        "quantitative trader",
        "quantitative trading",
        "quant developer",
        "quant dev",
        "quant engineer",
        "quant software engineer",
        "quantitative developer",
        "quantitative engineer",
        "quantitative software engineer",
        "quant analyst",
        "quantitative analyst",
        "quant researcher",
        "quant research",
        "quantitative researcher",
        "quantitative research",
        "quant strategist",
        "quantitative strategist",
        "quantdeveloper",
        "quantengineer",

        # Trading development
        "trading developer",
        "trading engineer",
        "trading software developer",
        "trading software engineer",
        "trading systems developer",
        "trading systems engineer",
        "trading system developer",
        "trading system engineer",
        "trading platform developer",
        "trading platform engineer",
        "trading application developer",
        "trading application engineer",
        "trading technology developer",
        "trading technology engineer",
        "trading technology",
        "trading software",

        # Strategy / backtesting
        "strategy developer",
        "strategy engineer",
        "trading strategy developer",
        "trading strategy engineer",
        "quant strategy developer",
        "quant strategy",
        "backtesting developer",
        "backtesting engineer",
        "backtest developer",
        "backtest engineer",

        # Electronic / low latency / HFT
        "electronic trading",
        "electronic trader",
        "electronic trading developer",
        "electronic trading engineer",
        "e-trading",
        "etrading",
        "low latency trading",
        "low-latency trading",
        "low latency developer",
        "low latency engineer",
        "low-latency developer",
        "low-latency engineer",
        "hft trader",
        "hft developer",
        "hft engineer",
        "high frequency trader",
        "high frequency trading",
        "high-frequency trading",

        # Forex / FX
        "forex trader",
        "forex trading",
        "forex analyst",
        "forex market analyst",
        "fx trader",
        "fx trading",
        "fx analyst",
        "foreign exchange trader",
        "foreign exchange trading",

        # Prop / funded
        "prop trader",
        "prop trading",
        "proprietary trader",
        "proprietary trading",
        "funded trader",
        "funded trading",

        # Trading analytics / market data
        "trading analyst",
        "trading analytics",
        "market data engineer",
        "market data developer",
        "market data analyst",
        "market data",
        "trading data engineer",
        "trading data developer",

        # Broker / exchange technology
        "broker technology",
        "brokerage technology",
        "broker platform developer",
        "broker platform engineer",
        "broker integration developer",
        "broker integration engineer",
        "exchange technology",
        "exchange developer",
        "exchange engineer",

        # General trading title fallback
        "trader",
        "trading",
    ],

    # ============================================================
    # 2. AWS DATA ENGINEER
    # Must stay BEFORE Data Engineer.
    # ============================================================
    "AWS Data Engineer": [
        "aws data engineer",
        "aws data engineering",
        "awsdataengineer",
        "aws_data_engineer",
        "#awsdataengineer",
        "#aws_data_engineer",

        "data engineer aws",
        "data engineering aws",
        "data engineer - aws",
        "data engineer – aws",
        "data engineer with aws",
        "data engineer on aws",

        "aws big data engineer",
        "aws big data developer",
        "aws cloud data engineer",
        "aws data platform engineer",
        "aws data pipeline engineer",
        "aws data pipeline developer",

        "aws etl engineer",
        "aws etl developer",
        "aws elt engineer",
        "aws elt developer",

        "aws glue engineer",
        "aws glue developer",
        "aws glue data engineer",
        "glue data engineer",

        "redshift data engineer",
        "aws redshift engineer",
        "aws redshift developer",

        "aws lakehouse engineer",
        "aws data lake engineer",
        "aws data lake developer",

        "aws analytics engineer",
        "aws analytics developer",

        "aws spark engineer",
        "aws pyspark engineer",
        "aws databricks engineer",

        "aws snowflake data engineer",
        "snowflake aws data engineer",

        "aws data architect",
        "aws data architecture",
        "aws data specialist",
    ],

    # ============================================================
    # 3. DATA ENGINEER
    # Includes Data Engineering, Big Data, ETL, Spark, Databricks,
    # Snowflake, Hadoop, Azure/GCP data roles, BI engineering, etc.
    # ============================================================
    "Data Engineer": [
        # Core Data Engineer
        "data engineer",
        "data engineers",
        "data engineering",
        "dataengineer",
        "dataengineers",
        "dataengineering",
        "data_engineer",
        "data_engineering",
        "#dataengineer",
        "#dataengineering",

        # Senior / Lead automatically match "data engineer",
        # additional related role names
        "data platform engineer",
        "data platform developer",
        "data infrastructure engineer",
        "data infrastructure developer",

        # Data architecture
        "data architect",
        "data architecture",
        "data solution architect",
        "data solutions architect",
        "enterprise data architect",
        "cloud data architect",

        # Data integration
        "data integration engineer",
        "data integration developer",
        "data integration specialist",
        "data integration architect",

        # Big Data
        "big data engineer",
        "big data developer",
        "big data architect",
        "bigdata engineer",
        "bigdata developer",

        # ETL / ELT
        "etl developer",
        "etl engineer",
        "etl data engineer",
        "etl specialist",
        "etl architect",
        "elt developer",
        "elt engineer",
        "elt data engineer",

        # PySpark / Spark
        "pyspark data engineer",
        "pyspark engineer",
        "pyspark developer",
        "spark data engineer",
        "spark engineer",
        "spark developer",
        "apache spark engineer",

        # Databricks
        "databricks data engineer",
        "databricks engineer",
        "databricks developer",
        "databricks architect",
        "databricks specialist",

        # Snowflake
        "snowflake data engineer",
        "snowflake engineer",
        "snowflake developer",
        "snowflake architect",
        "snowflake data developer",

        # Hadoop
        "hadoop data engineer",
        "hadoop engineer",
        "hadoop developer",
        "hadoop architect",
        "hadoop data developer",

        # Kafka / streaming
        "streaming data engineer",
        "streaming engineer",
        "data streaming engineer",
        "kafka data engineer",
        "kafka engineer",
        "real time data engineer",
        "real-time data engineer",

        # Data warehouse
        "data warehouse engineer",
        "data warehouse developer",
        "data warehouse architect",
        "data warehousing engineer",
        "data warehousing developer",
        "dwh engineer",
        "dwh developer",
        "warehouse engineer",

        # Lake / Lakehouse
        "data lake engineer",
        "data lake developer",
        "data lakehouse engineer",
        "lakehouse engineer",
        "lakehouse developer",

        # Analytics engineering
        "analytics engineer",
        "analytics engineering",
        "data analytics engineer",

        # BI engineering
        "bi engineer",
        "bi engineering",
        "bi engineering solution developer",
        "business intelligence engineer",
        "business intelligence developer",
        "bi data engineer",

        # Data quality
        "data quality engineer",
        "data quality engineering",

        # Cloud Data Engineer - non AWS or generic
        "cloud data engineer",
        "cloud data engineering",

        # Azure
        "azure data engineer",
        "azure data engineering",
        "azuredataengineer",
        "#azuredataengineer",
        "azure databricks engineer",
        "azure data platform engineer",

        # GCP
        "gcp data engineer",
        "gcp data engineering",
        "gcpdataengineer",
        "#gcpdataengineer",
        "google cloud data engineer",
        "google data engineer",

        # Fabric
        "microsoft fabric engineer",
        "fabric data engineer",
        "ms fabric engineer",
        "ms fabric lead",

        # DBT
        "dbt data engineer",
        "dbt engineer",

        # Data management leadership
        "data engineering manager",
        "engineering manager - data engineering",
        "engineering manager – data engineering",
        "head of data engineering",
        "data engineering lead",
        "data engineering specialist",
        "specialist - data engineering",
        "specialist – data engineering",
    ],

    # ============================================================
    # 4. AI ENGINEER
    # Includes AI, ML, GenAI, LLM, NLP, MLOps and Data Scientist.
    # ============================================================
    "AI Engineer": [
        # AI Engineer
        "ai engineer",
        "ai engineers",
        "aiengineer",
        "ai engineering",
        "artificial intelligence engineer",
        "artificial intelligence developer",
        "artificial intelligence engineering",

        # AI / ML
        "ai/ml engineer",
        "ai ml engineer",
        "ai-ml engineer",
        "aiml engineer",
        "aimlengineer",
        "ai/ml developer",
        "ai ml developer",
        "aiml developer",

        # ML Engineer
        "machine learning engineer",
        "machine learning developer",
        "machine learning engineering",
        "ml engineer",
        "ml engineers",
        "mlengineer",
        "ml developer",
        "ml software engineer",

        # GenAI
        "genai engineer",
        "gen ai engineer",
        "gen-ai engineer",
        "generative ai engineer",
        "generative ai developer",
        "genai developer",
        "gen ai developer",
        "genai architect",
        "generative ai architect",

        # LLM
        "llm engineer",
        "llm developer",
        "llm application engineer",
        "llm application developer",
        "llmops engineer",
        "large language model engineer",

        # Agentic AI
        "agentic ai engineer",
        "agentic ai developer",
        "ai agent engineer",
        "ai agent developer",

        # RAG
        "rag engineer",
        "rag developer",
        "retrieval augmented generation engineer",
        "retrieval-augmented generation engineer",

        # NLP
        "nlp engineer",
        "nlp developer",
        "nlp scientist",
        "natural language processing engineer",
        "natural language processing developer",

        # Deep learning
        "deep learning engineer",
        "deep learning developer",
        "deep learning scientist",

        # Computer vision
        "computer vision engineer",
        "computer vision developer",
        "computer vision scientist",
        "vision engineer",

        # Applied AI
        "applied ai engineer",
        "applied ai developer",
        "applied machine learning engineer",
        "applied ml engineer",

        # MLOps
        "mlops engineer",
        "mlops developer",
        "mlops architect",
        "machine learning operations engineer",

        # AI architecture
        "ai architect",
        "ai solution architect",
        "ai solutions architect",
        "ai/ml architect",
        "ai ml architect",
        "machine learning architect",
        "ml architect",
        "data ai architect",
        "data & ai architect",

        # Data + AI role
        "data & ai engineer",
        "data and ai engineer",
        "data ai engineer",

        # Data Scientist -> AI Engineer group
        "data scientist",
        "data scientists",
        "datascientist",
        "data science",
        "senior data scientist",
        "lead data scientist",
        "machine learning scientist",
        "ai scientist",
        "applied scientist",
        "research scientist - ai",
        "research scientist – ai",
        "research scientist - machine learning",
        "research scientist – machine learning",

        # AI Python roles
        "ai python developer",
        "ai/ML python developer",
        "ai/ml python developer",
        "machine learning python developer",
        "python ai engineer",
        "python ml engineer",

        # Prompt / AI applications
        "prompt engineer",
        "prompt engineering",
        "ai application engineer",
        "ai application developer",
    ],

    # ============================================================
    # 5. PYTHON DEVELOPER
    # Keep AFTER AI/Data so Python inside Data/AI titles doesn't
    # steal those jobs.
    # ============================================================
    "Python Developer": [
        # Core
        "python developer",
        "python developers",
        "python engineer",
        "python engineers",
        "python software developer",
        "python software engineer",
        "python programmer",

        # LinkedIn hashtag / compact variations
        "pythondeveloper",
        "pythondevelopers",
        "pythonengineer",
        "pythonengineers",
        "#pythondeveloper",
        "#pythondevelopers",
        "#pythonengineer",
        "#pythonbackend",
        "#pythonfullstack",

        # Backend
        "python backend developer",
        "python backend engineer",
        "backend python developer",
        "backend python engineer",
        "python backend",
        "backend developer - python",
        "backend developer – python",
        "backend engineer - python",
        "backend engineer – python",

        # Full stack
        "python full stack developer",
        "python fullstack developer",
        "full stack python developer",
        "fullstack python developer",
        "python full stack engineer",
        "python fullstack engineer",

        # API
        "python api developer",
        "python api engineer",
        "python rest api developer",
        "python microservices developer",
        "python microservices engineer",

        # Framework specific
        "django developer",
        "django engineer",
        "python django developer",
        "python django engineer",
        "flask developer",
        "flask engineer",
        "python flask developer",
        "python flask engineer",
        "fastapi developer",
        "fastapi engineer",
        "python fastapi developer",
        "python fastapi engineer",

        # Automation
        "python automation developer",
        "python automation engineer",
        "automation python developer",
        "automation python engineer",
        "python automation",

        # Cloud + Python but NOT specifically Data Engineer
        "aws python developer",
        "aws python engineer",
        "python aws developer",
        "python aws engineer",
        "cloud python developer",
        "cloud python engineer",

        # Leads / architects
        "python lead",
        "python technical lead",
        "python tech lead",
        "lead python developer",
        "lead python engineer",
        "python architect",

        # Common combined roles
        "java & python developer",
        "java and python developer",
        "java/python developer",
        "python developer / cloud engineer",
        "python developer/cloud engineer",
    ],
}
OUTPUT_DIR = Path(project_root) / "linkedin" / "output" / "grouped_jobs"


def _classify_title(title: str) -> str:
    """Return the canonical role family or ``Other``."""
    title_lower = (title or "").lower()
    for family, keywords in ROLE_FAMILIES.items():
        if any(keyword in title_lower for keyword in keywords):
            return family
    return "Other"


def _filename_slug(text: str) -> str:
    """
    Convert role/company text to the compact lowercase filename form requested.

    ``Data Engineer`` -> ``dataengineer``
    ``HCL Tech``      -> ``hcltech``
    """
    value = re.sub(r"[^a-zA-Z0-9]+", "", text or "").lower()
    return value or "unknown"

def _normalise_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def _normalise_poster_profile_url(value: str) -> str:
    """
    Return a clean LinkedIn poster profile/company URL.

    The feed scraper stores this value in ``LinkedInJob.posted_by_url``.
    Query parameters and fragments are removed so the same profile is grouped
    under one stable URL.
    """
    url = _normalise_space(value)
    if not url or url.lower() in {"n/a", "na", "none", "unknown"}:
        return ""

    if url.startswith("/"):
        url = f"https://www.linkedin.com{url}"
    elif url.startswith(("linkedin.com/", "www.linkedin.com/")):
        url = f"https://{url}"

    if not url.startswith(("http://", "https://")):
        return ""

    try:
        parts = urlsplit(url)
        host = parts.netloc.lower()
        path = re.sub(r"/+$", "", parts.path)

        if "linkedin.com" not in host:
            return ""
        if not (
            path.startswith("/in/")
            or path.startswith("/company/")
            or path.startswith("/school/")
        ):
            return ""

        return urlunsplit((parts.scheme or "https", parts.netloc, path, "", ""))
    except Exception:
        return ""

def _poster_group_key(job: dict) -> str:
    """Return the second-level grouping key for one job."""
    profile_url = job.get("posted_by_profile_url") or ""
    if profile_url:
        return profile_url

    poster_name = _normalise_space(job.get("posted_by_name") or "")
    if poster_name:
        return f"name:{poster_name.casefold()}"

    return "unknown-poster"

def _extract_emails(text: str) -> List[str]:
    matches = re.findall(
        r"(?<![\w.+-])[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?![\w.-])",
        text or "",
    )
    return list(dict.fromkeys(match.strip(".,;:()[]<>") for match in matches))

def _extract_phone_numbers(text: str) -> List[str]:
    if not text:
        return []

    pattern = re.compile(
        r"(?<![\w@])(?:\+?\d{1,3}[\s().-]*)?"
        r"(?:\(?\d{2,5}\)?[\s.-]*)?"
        r"\d{3,5}(?:[\s.-]*\d{3,5}){1,3}(?![\w@])"
    )

    values: List[str] = []
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

        value = f"+{digits}" if raw.lstrip().startswith("+") else digits
        if value not in seen:
            seen.add(value)
            values.append(value)

    return values

def _collect_contacts(stored_contact: str, description: str) -> Tuple[List[str], List[str]]:
    """
    Collect every email and phone from both the database contact field and JD.

    The scraper may store a phone number in the existing ``email`` column when
    no email is present, so both values are parsed rather than assuming the
    database field always contains an email.
    """
    source = "\n".join(
        part for part in (stored_contact or "", description or "") if part
    )
    return _extract_emails(source), _extract_phone_numbers(source)


def _load_today_jobs() -> List[dict]:
    """Load today's scraper JSON; never query the database."""
    today = datetime.now()
    json_file = project_root / "output" / "scarp" / f"{today:%Y-%m-%d}.json"

    # Helpful fallback if the runner is started from a project layout where
    # the scraper output directory is under linkedin/.
    if not json_file.exists():
        fallback = project_root / "linkedin" / "output" / "scarp" / f"{today:%Y-%m-%d}.json"
        if fallback.exists():
            json_file = fallback

    if not json_file.exists():
        logger.warning(f"Today's scraper JSON was not found: {json_file}")
        return []

    try:
        import json
        data = json.loads(json_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.error(f"Could not read today's scraper JSON {json_file}: {exc}")
        return []

    if not isinstance(data, list):
        logger.warning(f"Expected a JSON list in {json_file}")
        return []

    logger.info(f"Loaded {len(data)} scraped jobs from {json_file}")
    return data


def _classify_title(title: str) -> str:
    """Return the first matching canonical role family or Other."""
    title_lower = (title or "").lower()
    for family, keywords in ROLE_FAMILIES.items():
        if any(keyword.lower() in title_lower for keyword in keywords):
            return family
    return "Other"


def _job_data_from_json(job: dict, index: int) -> dict:
    """Normalize the scraper JSON schema to the grouping schema."""
    description = (
        job.get("job_description")
        or job.get("description")
        or job.get("cleaned_description")
        or ""
    ).strip()

    stored_contact = str(job.get("email") or "").strip()

    # New scraper already stores arrays; also support older/simple JSON.
    emails = job.get("emails")
    phones = job.get("phone_numbers")

    if not isinstance(emails, list):
        emails = _extract_emails(stored_contact + "\n" + description)

    if not isinstance(phones, list):
        phones = _extract_phone_numbers(stored_contact + "\n" + description)

    poster_name = (
        job.get("posted_by_name")
        or job.get("job_poster_by")
        or "N/A"
    )

    poster_url = _normalise_poster_profile_url(
        job.get("posted_by_url")
        or job.get("posted_by_profile_url")
        or ""
    )

    return {
        "id": job.get("id") or job.get("job_hashkey") or f"json-{index}",
        "title": str(job.get("title") or "Unknown").strip(),
        "company": str(job.get("company") or "unknown").strip() or "unknown",
        "description": description,
        "stored_contact": stored_contact,
        "emails": list(dict.fromkeys(str(x) for x in emails if x)),
        "phones": list(dict.fromkeys(str(x) for x in phones if x)),
        "apply_url": str(job.get("url") or "").strip(),
        "posted_by_name": str(poster_name).strip(),
        "posted_by_profile_url": poster_url,
        "search_query": str(job.get("search_query") or "").strip(),
        "job_hashkey": str(job.get("job_hashkey") or "").strip(),
    }


def group_and_save_roles(
    days_back: int = 7,
    *,
    today_only: bool = True,
    job_ids: Optional[Iterable[int]] = None,
) -> Dict[str, dict]:
    """
    Load today's scraper JSON, group jobs by ROLE_FAMILIES, keep only jobs
    with an available email address, and write one clean JD-only file per role
    family. Posted By and email information appear only once in the header.

    Database access has intentionally been removed. `days_back` and `job_ids`
    remain in the signature for compatibility with older callers but are not
    used to query anything.
    """
    

    generated_at = datetime.now()

    # One date-only folder, for example:
    # linkedin/output/2026-08-07/
    run_output_dir = OUTPUT_DIR / generated_at.strftime("%Y-%m-%d")
    run_output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory for this run: {run_output_dir}")

    raw_jobs = _load_today_jobs()
    if not raw_jobs:
        logger.warning("No today's jobs found — nothing to group.")
        return {}

    # Normalize and remove exact duplicates from the JSON.
    job_data: List[dict] = []
    seen_hashes = set()

    for index, raw_job in enumerate(raw_jobs, 1):
        if not isinstance(raw_job, dict):
            continue

        job = _job_data_from_json(raw_job, index)

        fingerprint = (
            job["job_hashkey"]
            or "||".join(
                [
                    job["title"].casefold(),
                    job["company"].casefold(),
                    job["apply_url"].casefold(),
                    _normalise_space(job["description"][:500]).casefold(),
                ]
            )
        )

        if fingerprint in seen_hashes:
            continue

        seen_hashes.add(fingerprint)
        job_data.append(job)

    logger.info(f"Normalized {len(job_data)} unique jobs from today's JSON.")

    role_groups: Dict[str, List[dict]] = defaultdict(list)

    for job in job_data:
        # Grouping is based on title, preserving the existing behavior.
        role_groups[_classify_title(job["title"])].append(job)

    summary: Dict[str, dict] = {}
    generated_date = generated_at.strftime("%Y-%m-%d")

    for family, family_jobs in role_groups.items():
        if not family_jobs:
            continue

        # Only keep jobs where an email address is available.
        # Email may come from the dedicated JSON field or be discovered
        # inside the stored contact field / job description.
        email_jobs: List[dict] = []
        for job in family_jobs:
            extra_emails, _ = _collect_contacts(
                job["stored_contact"],
                job["description"],
            )
            job["emails"] = list(dict.fromkeys(job["emails"] + extra_emails))

            if job["emails"]:
                email_jobs.append(job)

        if not email_jobs:
            logger.info(
                f"Skipping [{family}] because no job has an email address."
            )
            continue

        seen_fingerprints = set()
        job_blocks: List[str] = []
        companies: List[str] = []
        group_emails: List[str] = []
        poster_names: List[str] = []
        written_job_count = 0

        for job in email_jobs:
            description = _normalise_space(job["description"])
            if not description:
                continue

            # Remove obvious repeated whitespace while preserving the JD text.
            description = re.sub(r"\n[ \t]+", "\n", job["description"].strip())
            description = re.sub(r"[ \t]+", " ", description)

            fingerprint = "||".join(
                [
                    _normalise_space(job["title"]).casefold(),
                    _normalise_space(job["company"]).casefold(),
                    _normalise_space(description[:500]).casefold(),
                ]
            )

            if fingerprint in seen_fingerprints:
                continue
            seen_fingerprints.add(fingerprint)

            company = _normalise_space(job["company"]) or "unknown"
            emails = list(dict.fromkeys(job["emails"]))

            if not emails:
                continue

            companies.append(company)
            group_emails.extend(emails)

            poster_name = _normalise_space(job["posted_by_name"])
            if poster_name and poster_name.casefold() != "n/a":
                poster_names.append(poster_name)

            # JD-only block. No repeated Posted By, Apply URL, phone number,
            # search query, or poster profile inside each individual job.
            job_blocks.append(
                "\n".join(
                    [
                        f"## {job['title']} | {company}",
                        description,
                    ]
                )
            )
            written_job_count += 1

        if not job_blocks:
            continue

        unique_companies = list(dict.fromkeys(companies))
        unique_emails = list(dict.fromkeys(group_emails))
        unique_posters = list(dict.fromkeys(poster_names))

        # Posted By is intentionally shown only once at the top.
        posted_by_header = (
            ", ".join(unique_posters)
            if unique_posters
            else "N/A"
        )

        email_header = ", ".join(unique_emails)

        role_part = _filename_slug(family)
        filename = f"{role_part}_{generated_date}.txt"
        filepath = run_output_dir / filename

        combined_text = (
            f"# Role Group: {family}\n"
            f"# Posted By: {posted_by_header}\n"
            f"# Emails: {email_header}\n"
            f"# Jobs included: {written_job_count}\n"
            f"# Companies: {', '.join(unique_companies)}\n"
            f"# Generated: {generated_at:%Y-%m-%d %H:%M:%S}\n"
            f"{'=' * 70}\n\n"
            + "\n\n".join(job_blocks)
            + "\n"
        )

        filepath.write_text(
            combined_text,
            encoding="utf-8",
        )

        logger.info(
            f"Wrote {written_job_count} email-qualified JDs for "
            f"[{family}] -> {filepath}"
        )

        summary[family] = {
            "file": str(
                filepath.relative_to(project_root)
            ).replace("\\", "/"),
            "job_count": written_job_count,
            "companies": unique_companies,
            "emails": unique_emails,
            "posted_by": unique_posters,
        }

    logger.info(
        "group_and_save_roles complete. "
        f"Groups written: {list(summary.keys())}"
    )

    return summary


if __name__ == "__main__":
    import json

    result = group_and_save_roles()
    print(json.dumps(result, indent=2))
