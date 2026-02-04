"""
logger.py

This module provides functionality for setting up a centralized logging system using the
`logging` library and the `python-json-logger` to output logs in JSON format. It handles
log rotation by renaming old log files and saving them based on the first timestamp entry.

Functions:
- log_format(keys): Generates the logging format string based on the list of keys.
- rotate_log_file(): Handles renaming the existing log file to a timestamp-based name.
- setup_logger(): Configures the logging system, applies a JSON format, and returns a logger instance.
- setup_consolelogger(): Configures the logging system to output logs in console format.
"""

import os
import json
import gzip
import shutil
import logging
from datetime import datetime
from pythonjsonlogger import json as jsonlogger

# Constants for file paths and exclusions
SCRIPTDIR = os.path.dirname(os.path.realpath(__file__)).removesuffix(__package__ if __package__ else "")
LOG_DIR = os.path.join(SCRIPTDIR, "logs")
LATEST_LOG_FILE = os.path.join(LOG_DIR, "latest.jsonl")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def log_format(keys):
    """
    Generates a list of format strings based on the given keys.

    Args:
        keys (list): A list of string keys that represent the log attributes (e.g., 'asctime', 'levelname').

    Returns:
        list: A list of formatted strings for each key, in the format "%(key)s".
    """
    return [f"%({i})s" for i in keys]


def rotate_log_file(compress=False):
    """
    Truncates the 'latest.jsonl' file after optionally compressing its contents to a timestamped file.
    The 'latest.jsonl' file is not deleted or moved, just emptied.

    Args:
        compress (bool): If True, compress the old log file using gzip.
    """
    if os.path.exists(LATEST_LOG_FILE):
        with open(LATEST_LOG_FILE, "r+", encoding="utf-8") as f:
            first_line = f.readline()
            try:
                first_log = json.loads(first_line)
                first_timestamp = first_log.get("asctime")
                first_timestamp = first_timestamp.split(",")[0]
            except (json.JSONDecodeError, KeyError):
                first_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            safe_timestamp = first_timestamp.replace(":", "-").replace(" ", "_")
            old_log_filename = os.path.join(LOG_DIR, f"{safe_timestamp}.jsonl")

            # Write contents to the new file
            with open(old_log_filename, "w", encoding="utf-8") as old_log_file:
                f.seek(0)  # Go back to the beginning of the file
                shutil.copyfileobj(f, old_log_file)

            if compress:
                with open(old_log_filename, "rb") as f_in:
                    with gzip.open(f"{old_log_filename}.gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(old_log_filename)

            # Truncate the original file
            f.seek(0)
            f.truncate()


def setup_logger(level=logging.INFO):
    """
    Configures the logging system with a custom format and outputs logs in JSON format.

    The logger will write to the 'logs/latest.jsonl' file, and it will include
    multiple attributes such as the time of logging, the filename, function name, log level, etc.

    Returns:
        logging.Logger: A configured logger instance that can be used to log messages.
    """
    _logger = logging.getLogger(name="defaultlogger")

    supported_keys = ["asctime", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "process", "processName", "relativeCreated", "thread", "threadName"]

    custom_format = " ".join(log_format(supported_keys))
    formatter = jsonlogger.JsonFormatter(custom_format)

    log_handler = logging.FileHandler(LATEST_LOG_FILE)
    log_handler.setFormatter(formatter)

    _logger.addHandler(log_handler)
    _logger.setLevel(level=level)

    return _logger


def setup_consolelogger(level=logging.INFO):
    """
    Configures the logging system to output logs in console and JSON format.

    The logger will write to the 'logs/latest.jsonl' file, and it will include
    multiple attributes such as the time of logging, the filename, function name, log level, etc.

    Returns:
        logging.Logger: A configured logger instance that can be used to log messages.
    """
    _logger = logging.getLogger(name="consolelogger")

    supported_keys = ["asctime", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "process", "processName", "relativeCreated", "thread", "threadName"]

    custom_format = " ".join(log_format(supported_keys))
    formatter = jsonlogger.JsonFormatter(custom_format)

    log_handler = logging.FileHandler(LATEST_LOG_FILE)
    log_handler.setFormatter(formatter)

    _logger.addHandler(log_handler)
    _logger.addHandler(logging.StreamHandler())
    _logger.setLevel(level=level)
    return _logger


rotate_log_file(compress=True)
logger = setup_logger()
consolelogger = setup_consolelogger()
