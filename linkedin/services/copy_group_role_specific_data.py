"""
python -m linkedin.services.copy_group_role_specific_data

Copy grouped LinkedIn role files into:

job_profile/specific/company/<YYYY_MM_DD>/<role>/<role>_jd.txt

Important:
- No cleaning, filtering, parsing, or modification of the JD content.
- The complete text from each supported input file is copied.
- If multiple input files belong to the same role, their full contents are
  combined into the same <role>_jd.txt file.
- Existing output files for the processed date are overwritten on rerun.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_ROOT = PROJECT_ROOT / "linkedin" / "output" / "grouped_jobs"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "job_profile" / "specific" / "company"


ROLE_PREFIXES: Dict[str, List[str]] = {
    "aiengineer": ["aiengineer", "ai-engineer", "ai_engineer"],
    "dataengineer": [
        "dataengineer",
        "data-engineer",
        "data_engineer"
    ],
    "pythondeveloper": [
        "pythondeveloper",
        "python-developer",
        "python_developer",
    ],
}


def detect_role(filename: str) -> Optional[str]:
    """Detect the destination role from the beginning of the input filename."""
    name = Path(filename).stem.lower()

    for role, prefixes in ROLE_PREFIXES.items():
        for prefix in prefixes:
            if (
                name == prefix
                or name.startswith(prefix + "_")
                or name.startswith(prefix + "-")
            ):
                return role

    return None

def normalise_output_date(folder_name: str) -> str:
    """
    Normalize common date folder formats to YYYY_MM_DD.

    Examples:
        2026-09-21 -> 2026_09_21
        2026_09_21 -> 2026_09_21
        21-09-2026 -> 2026_09_21
        21_09_2026 -> 2026_09_21
    """
    value = folder_name.strip()

    match = re.fullmatch(r"(\d{4})[-_](\d{2})[-_](\d{2})", value)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"

    match = re.fullmatch(r"(\d{2})[-_](\d{2})[-_](\d{4})", value)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"

    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_") or "unknown_date"

def resolve_input_folder(folder_path: Optional[str | Path] = None) -> Path:
    """
    Resolve the grouped-job input folder.

    If omitted, today's folder is used:
        linkedin/output/YYYY-MM-DD
    """
    if folder_path:
        return Path(folder_path).expanduser().resolve()

    today = datetime.now().strftime("%Y-%m-%d")
    return (DEFAULT_INPUT_ROOT / today).resolve()


def copy_group_role_specific_data(
    folder_path: Optional[str | Path] = None,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> Dict[str, dict]:
    """
    Copy complete source text into role-specific destination files.

    No cleaning or filtering is performed.
    """
    input_dir = resolve_input_folder(folder_path)

    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    output_root = Path(output_root).expanduser().resolve()
    output_date = normalise_output_date(input_dir.name)
    date_output_dir = output_root / output_date
    date_output_dir.mkdir(parents=True, exist_ok=True)

    role_contents: Dict[str, List[str]] = defaultdict(list)
    role_source_files: Dict[str, List[str]] = defaultdict(list)
    skipped_files: List[str] = []

    for input_file in sorted(input_dir.glob("*.txt")):
        role = detect_role(input_file.name)

        if not role:
            skipped_files.append(input_file.name)
            continue

        content = input_file.read_text(
            encoding="utf-8",
            errors="replace",
        )

        role_contents[role].append(content)
        role_source_files[role].append(input_file.name)

    summary: Dict[str, dict] = {}

    for role, contents in role_contents.items():
        role_dir = date_output_dir / role
        role_dir.mkdir(parents=True, exist_ok=True)

        output_file = role_dir / f"{role}_jd.txt"

        combined_content = "\n\n".join(
            content.rstrip("\n") for content in contents
        ).rstrip() + "\n"

        output_file.write_text(
            combined_content,
            encoding="utf-8",
        )

        summary[role] = {
            "source_files": role_source_files[role],
            "files_combined": len(role_source_files[role]),
            "output_file": str(output_file),
        }

    if skipped_files:
        summary["skipped"] = {"files": skipped_files}

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Copy grouped job text files into role-specific folders "
            "without cleaning or filtering."
        )
    )

    parser.add_argument(
        "folder_path",
        nargs="?",
        default=None,
        help=(
            "Input folder, for example linkedin/output/2026-09-21. "
            "If omitted, today's folder is used."
        ),
    )

    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Default: <project>/job_profile/specific/company",
    )

    return parser

def main(input_path: Optional[str] = None) -> None:
    if input_path is not None:
        args = build_parser().parse_args([input_path])
    else:
        args = build_parser().parse_args()

    summary = copy_group_role_specific_data(
        folder_path=args.folder_path,
        output_root=args.output_root,
    )

    if not summary:
        print("No supported role files found. Nothing was written.")
        return

    print("Role-specific file copy completed.")

    for role, details in summary.items():
        if role == "skipped":
            print(f"Skipped files: {', '.join(details['files'])}")
            continue

        print(
            f"- {role}: {details['files_combined']} source file(s) -> "
            f"{details['output_file']}"
        )

if __name__ == "__main__":
    input_path = "linkedin/output/grouped_jobs/2026-09-21"
    main(input_path)