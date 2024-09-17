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

import logging
import os
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

# Constants for file paths and exclusions
if __package__ is None:
    PACKAGE = ""
else:
    PACKAGE = __package__
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__).removesuffix(PACKAGE))
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


def rotate_log_file():
    """
    Renames the existing 'latest.jsonl' file to a timestamped file based on the first log entry's asctime.

    If 'latest.jsonl' exists, it's renamed to the first timestamp found in the log entry.
    """
    if os.path.exists(LATEST_LOG_FILE):
        with open(LATEST_LOG_FILE, "r", encoding="utf-8") as f:
            first_line = f.readline()
            try:
                first_log = json.loads(first_line)
                first_timestamp = first_log.get("asctime")
                first_timestamp = first_timestamp.split(",")[0]
            except (json.JSONDecodeError, KeyError):
                first_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        safe_timestamp = first_timestamp.replace(":", "-").replace(" ", "_")
        old_log_filename = os.path.join(LOG_DIR, f"{safe_timestamp}.jsonl")

        os.rename(LATEST_LOG_FILE, old_log_filename)


def setup_logger():
    """
    Configures the logging system with a custom format and outputs logs in JSON format.

    The logger will write to the 'logs/latest.jsonl' file, and it will include
    multiple attributes such as the time of logging, the filename, function name, log level, etc.
    If 'latest.jsonl' already exists, it will be renamed to a timestamped file before creating a new one.

    Returns:
        logging.Logger: A configured logger instance that can be used to log messages.
    """
    rotate_log_file()
    _logger = logging.getLogger()

    supported_keys = ["asctime", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "name", "pathname", "process", "processName", "relativeCreated", "thread", "threadName", "taskName"]

    custom_format = " ".join(log_format(supported_keys))
    formatter = jsonlogger.JsonFormatter(custom_format)

    log_handler = logging.FileHandler(LATEST_LOG_FILE)
    log_handler.setFormatter(formatter)

    _logger.addHandler(log_handler)
    _logger.setLevel(logging.INFO)

    return _logger


def setup_consolelogger():
    """
    Configures the logging system to output logs in console format.

    Returns:
        logging.Logger: A configured logger instance that can be used to log messages.
    """
    _logger = setup_logger()
    _logger.addHandler(logging.StreamHandler())
    return _logger


logger = setup_logger()
consolelogger = setup_consolelogger()
