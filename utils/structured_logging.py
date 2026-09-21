import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

# ----------------------------
# Lambda detection + log dir
# ----------------------------
def _is_lambda() -> bool:
    return bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

def _default_log_dir() -> str:
    """
    Local: ./logs (relative to current dir)
    Lambda: /tmp/logs (ONLY writable location)
    You can override with env var LOG_DIR if you want.
    """
    env_dir = os.environ.get("LOG_DIR")
    if env_dir:
        return env_dir

    return "/tmp/logs" if _is_lambda() else "logs"


# ----------------------------
# Custom Rotating File Handler
# ----------------------------
class CustomRotatingFileHandler(RotatingFileHandler):
    """
    Rotating file handler with filenames like:
      base_name_YYYYMMDD_index.log

    NOTE: In Lambda, write only to /tmp (ephemeral).
    """

    def __init__(
        self,
        base_name: str,
        log_dir: str,
        maxBytes: int = 5 * 1024 * 1024,
        backupCount: int = 5,
        days_to_keep: int = 30,
        **kwargs,
    ):
        self.base_name = base_name
        self.log_dir = log_dir
        self.days_to_keep = days_to_keep
        self.backupCount = backupCount  # ensure we can limit files

        Path(self.log_dir).mkdir(parents=True, exist_ok=True)

        self.current_time = datetime.now().strftime("%Y%m%d")
        self.rotation_count = 0

        filename = os.path.join(self.log_dir, self._make_filename())
        super().__init__(
            filename,
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding="utf-8",
            **kwargs,
        )

        self._cleanup_old_logs()
        self._cleanup_excess_rotations_for_today()

    def _make_filename(self, date_str: str = None, index: int = None) -> str:
        date_str = date_str or self.current_time
        index = self.rotation_count if index is None else index
        return f"{self.base_name}_{date_str}_{index}.log"

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        now_date = datetime.now().strftime("%Y%m%d")
        if now_date != self.current_time:
            self.current_time = now_date
            self.rotation_count = 0
        else:
            self.rotation_count += 1

        # rename current file to new index
        if os.path.exists(self.baseFilename):
            rotated = os.path.join(self.log_dir, self._make_filename())
            try:
                os.replace(self.baseFilename, rotated)  # safer than rename on Windows/Linux
            except OSError:
                # If replace fails, continue with console logs; don't crash Lambda
                pass

        # new active file
        self.baseFilename = os.path.join(self.log_dir, self._make_filename())
        self.stream = self._open()

        self._cleanup_old_logs()
        self._cleanup_excess_rotations_for_today()

    def _cleanup_excess_rotations_for_today(self):
        """
        Keep only (backupCount + 1) files for today's date (including current).
        Prevent /tmp filling up in Lambda.
        """
        try:
            files = sorted(
                Path(self.log_dir).glob(f"{self.base_name}_{self.current_time}_*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            keep = self.backupCount + 1
            for p in files[keep:]:
                try:
                    p.unlink()
                except OSError:
                    pass
        except Exception:
            pass

    def _cleanup_old_logs(self):
        now = datetime.now()
        cutoff = now - timedelta(days=self.days_to_keep)

        for path in Path(self.log_dir).glob(f"{self.base_name}_*.log"):
            try:
                # parse date from filename: base_YYYYMMDD_index.log
                parts = path.name.split("_")
                dt = None
                if len(parts) >= 3:
                    date_str = parts[-2]
                    try:
                        dt = datetime.strptime(date_str, "%Y%m%d")
                    except ValueError:
                        dt = None

                if dt is None:
                    dt = datetime.fromtimestamp(path.stat().st_mtime)

                if dt < cutoff:
                    path.unlink()
            except Exception:
                pass


# ----------------------------
# Logger Getter
# ----------------------------
def get_logger(module_name: str, log_level=logging.INFO, log_dir: str | None = None):
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)
    logger.propagate = False

    # avoid duplicate handlers (important in Lambda warm starts)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s - Line: %(lineno)d'
    )

    # Console handler (CloudWatch reads stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional; in Lambda uses /tmp/logs)
    log_dir = log_dir or _default_log_dir()

    try:
        file_handler = CustomRotatingFileHandler(
            base_name=module_name,
            log_dir=log_dir,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            days_to_keep=30,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Don't crash Lambda if filesystem is not writable
        logger.warning("File logging disabled (could not init file handler): %s", e)

    return logger
