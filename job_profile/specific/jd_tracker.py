"""
JD Duplicate Tracker Utility
Manages SHA-256 hashing, duplicate detection, and 30-day auto-cleanup for job descriptions.
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class JDTracker:
    """Manages job description history tracking and duplicate detection."""
    
    def __init__(self, history_file: str = "jd_history.json"):
        """Initialize tracker with history file path."""
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load history from JSON file or create new if doesn't exist."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Could not load history file: {e}")
                return {"history": []}
        return {"history": []}
    
    def _save_history(self) -> None:
        """Save history to JSON file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[ERROR] Could not save history file: {e}")
    
    def calculate_jd_hash(self, jd_content: str) -> str:
        """
        Calculate SHA-256 hash of JD content.
        Normalizes whitespace before hashing for consistency.
        """
        # Normalize: strip leading/trailing whitespace, collapse multiple spaces
        normalized = ' '.join(jd_content.strip().split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def cleanup_old_entries(self, days: int = 30) -> int:
        """
        Remove entries older than specified days from history.
        Returns number of entries removed.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        original_count = len(self.history["history"])
        
        self.history["history"] = [
            entry for entry in self.history["history"]
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
        ]
        
        removed_count = original_count - len(self.history["history"])
        
        if removed_count > 0:
            self._save_history()
            print(f"[CLEANUP] Removed {removed_count} entries older than {days} days")
        
        return removed_count
    
    def check_duplicate(self, jd_hash: str, days: int = 30) -> Optional[Dict]:
        """
        Check if JD hash exists in history within specified days.
        Returns entry dict if duplicate found, None otherwise.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for entry in self.history["history"]:
            if entry["jd_hash"] == jd_hash:
                entry_date = datetime.fromisoformat(entry["timestamp"])
                if entry_date > cutoff_date:
                    return entry
        
        return None
    
    def add_entry(self, jd_hash: str, job_slug: str, generated_files: List[str]) -> None:
        """
        Add new entry to history.
        """
        entry = {
            "jd_hash": jd_hash,
            "job_slug": job_slug,
            "timestamp": datetime.now().isoformat(),
            "generated_files": generated_files
        }
        
        self.history["history"].append(entry)
        self._save_history()
    
    def process_jd(self, jd_file_path: str, job_slug: str, 
                   generated_files: List[str], force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Complete JD processing workflow:
        1. Clean up old entries (30+ days)
        2. Calculate hash of JD content
        3. Check for duplicates within 30 days
        4. Add new entry if not duplicate or force=True
        
        Returns:
            (should_proceed, warning_message) tuple
            - should_proceed: True if generation should proceed
            - warning_message: None if no duplicate, warning string if duplicate found
        """
        # Step 1: Cleanup old entries
        self.cleanup_old_entries(days=30)
        
        # Step 2: Calculate hash
        try:
            with open(jd_file_path, 'r', encoding='utf-8') as f:
                jd_content = f.read()
        except IOError as e:
            print(f"[ERROR] Could not read JD file: {e}")
            return True, None  # Proceed anyway if can't read file
        
        jd_hash = self.calculate_jd_hash(jd_content)
        
        # Step 3: Check for duplicates
        duplicate_entry = self.check_duplicate(jd_hash, days=30)
        
        if duplicate_entry and not force:
            # Build warning message
            entry_date = datetime.fromisoformat(duplicate_entry["timestamp"])
            days_ago = (datetime.now() - entry_date).days
            
            warning = f"""
╔══════════════════════════════════════════════════════════════╗
║              ⚠️  DUPLICATE JD DETECTED  ⚠️                   ║
╚══════════════════════════════════════════════════════════════╝

This Job Description was previously processed:

  • Job Slug: {duplicate_entry['job_slug']}
  • Date: {entry_date.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago} days ago)
  • Hash: {jd_hash[:16]}...
  
  Previously Generated Files:
"""
            for file in duplicate_entry['generated_files']:
                warning += f"    - {file}\n"
            
            warning += """
╔══════════════════════════════════════════════════════════════╗
║  Recommendation: Review if this is an accidental duplicate   ║
║  To proceed anyway, use force=True parameter                 ║
╚══════════════════════════════════════════════════════════════╝
"""
            return False, warning
        
        # Step 4: Add new entry
        self.add_entry(jd_hash, job_slug, generated_files)
        print(f"[TRACKING] Added JD to history: {job_slug} (Hash: {jd_hash[:16]}...)")
        
        return True, None


def extract_job_slug_from_filename(filename: str) -> str:
    """
    Extract job slug from JD filename.
    Example: "idc_aba_jd_26_jul_2026.txt" -> "idc_aba"
    """
    basename = os.path.basename(filename)
    # Remove extension
    name_without_ext = os.path.splitext(basename)[0]
    
    # Try to extract pattern: <slug>_jd_<date>
    parts = name_without_ext.split('_jd_')
    if len(parts) >= 2:
        return parts[0]
    
    # Fallback: return first part before any date-like pattern
    # Remove common date patterns
    import re
    cleaned = re.sub(r'_\d{1,2}_[a-z]{3}_\d{4}', '', name_without_ext, flags=re.IGNORECASE)
    cleaned = re.sub(r'_jd$', '', cleaned, flags=re.IGNORECASE)
    
    return cleaned if cleaned else name_without_ext


def extract_date_from_filename(filename: str) -> str:
    """
    Extract date from JD filename.
    Example: "idc_aba_jd_26_jul_2026.txt" -> "26_jul_2026"
    """
    basename = os.path.basename(filename)
    name_without_ext = os.path.splitext(basename)[0]
    
    # Try to extract date pattern: dd_mmm_yyyy
    import re
    match = re.search(r'(\d{1,2}_[a-z]{3}_\d{4})', name_without_ext, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Fallback: return today's date
    return datetime.now().strftime("%d_%b_%Y").lower()


# Convenience function for CLI usage
def quick_check(jd_file: str) -> None:
    """Quick CLI check for duplicate JD."""
    tracker = JDTracker()
    
    with open(jd_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    jd_hash = tracker.calculate_jd_hash(content)
    duplicate = tracker.check_duplicate(jd_hash)
    
    if duplicate:
        print(f"[X] DUPLICATE FOUND")
        print(f"  Previously processed: {duplicate['job_slug']}")
        print(f"  Date: {duplicate['timestamp']}")
    else:
        print(f"[OK] No duplicate found (Hash: {jd_hash[:16]}...)")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        quick_check(sys.argv[1])
    else:
        print("Usage: python jd_tracker.py <jd_file_path>")
        print("Example: python jd_tracker.py idc_aba_jd_26_jul_2026.txt")
