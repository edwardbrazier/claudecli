"""
Utility functions for loading configuration, history data, and codebase files.

This module provides functions to:
1. Load a YAML configuration file, creating it with default values if it doesn't exist.
2. Load a JSON session history file.
3. Get the timestamp of the last saved session.
4. Load and concatenate the contents of files in a directory and its subdirectories,
   with headers indicating each file's path relative to the base path.

Functions:
    load_config(logger, config_file)
    load_history_data(history_file)
    get_last_save_file()
    load_codebase(logger, base_path, extensions)
"""

import atexit
import click
import datetime
import json
import logging
import os
import pyperclip
import re
import requests
import sys
import yaml
import anthropic

from pathlib import Path
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from typing import Optional, List
from xdg_base_dirs import xdg_config_home

import constants

def load_config(logger: logging.Logger, config_file: str) -> dict:
    """
    Read a YAML config file and return its content as a dictionary.

    Args:
        logger (logging.Logger): Logger instance for logging messages.
        config_file (str): Path to the YAML configuration file.

    Preconditions:
        - The config_file path is a valid file path.

    Side effects:
        - If the config file does not exist, it is created with default configurations.
        - If the config file is missing keys, they are populated with default values.

    Exceptions:
        None

    Returns:
        dict: The configuration data loaded from the YAML file.
        Guarantees: The returned dictionary will contain all required configuration keys.
    """
    # If the config file does not exist, create one with default configurations
    if not Path(config_file).exists():
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as file:
            yaml.dump(constants.DEFAULT_CONFIG, file, default_flow_style=False)
        logger.info(f"New config file initialized: [green bold]{config_file}")

    # Load existing config
    with open(config_file, encoding="utf-8") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # Update the loaded config with any default values that are missing
    for key, value in constants.DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value

    return config


def load_history_data(history_file: str) -> dict:
    """
    Read a session history JSON file and return its content.

    Args:
        history_file (str): Path to the JSON history file.

    Preconditions:
        - The history_file path is a valid file path.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        dict: The session history data loaded from the JSON file.
        Guarantees: The returned dictionary will contain the session history data.
    """
    with open(history_file, encoding="utf-8") as file:
        content = json.loads(file.read())

    return content


def get_last_save_file() -> str:
    """
    Return the timestamp of the last saved session.

    Args:
        None

    Preconditions:
        - The SAVE_FOLDER directory exists and contains session history files.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        str: The timestamp of the last saved session, or None if no session files exist.
        Guarantees: The returned string will be a valid timestamp or None.
    """
    files = [f for f in os.listdir(constants.SAVE_FOLDER) if f.endswith(".json")]
    if files:
        ts = [f.replace("chatgpt-session-", "").replace(".json", "") for f in files]
        ts.sort()
        return ts[-1]
    return None



def load_codebase(logger: logging.Logger, base_path: str, extensions: List[str]) -> str:
    """
    Concatenate the contents of files in the given directory and its subdirectories
    that match the specified file extensions.

    Args:
        logger (logging.Logger): Logger instance for logging messages.
        base_path (str): The starting directory path to search for files.
        extensions (List[str]): A list of file extension strings to include (e.g., ['py', 'txt']).

    Preconditions:
        - The base_path is a valid directory path.
        - The extensions list contains valid file extension strings.

    Side effects:
        None

    Exceptions:
        ValueError: If base_path does not exist or is not a directory.
        FileNotFoundError: If no matching files are found.

    Returns:
        str: A single string containing the concatenated contents of all matching files,
             with headers indicating each file's path relative to base_path.
        Guarantees: The returned string will contain the concatenated file contents,
                    or an empty string if no matching files are found.
    """

    # Verify the base path exists and is a directory
    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        raise ValueError(f"The path {base_path} does not exist or is not a directory.")

    concatenated_contents = ""
    matched_files_found = False

    encodings = ['utf-8', 'cp1252', 'iso-8859-1']

    # Walk through the directory and subdirectories
    for root, dirs, files in os.walk(base_path):
        for file_name in files:
            if any(file_name.endswith(f".{ext}") for ext in extensions) or not(any(extensions)):
                matched_files_found = True
                file_path = Path(root) / file_name
                relative_path = file_path.relative_to(base_path)

                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as file:
                            contents = file.read()
                            concatenated_contents += f"### {relative_path} ###\n{contents}\n\n" 
                    except Exception as e:
                        logger.warning(f"Failed to open file {file_path} with encoding {encoding}: {e}")

    if not matched_files_found:
        raise FileNotFoundError("No matching files found.")

    return concatenated_contents
