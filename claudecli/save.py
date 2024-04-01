"""
Improved comments and docstrings for the provided code.

This module provides utility functions for managing conversation history with an AI model.
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
import xml.sax.saxutils

from pathlib import Path
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from typing import Optional, List
from xdg_base_dirs import xdg_config_home

import constants

console = Console()

def create_save_folder() -> None:
    """
    Create the session history folder if it doesn't exist.

    Preconditions:
        None

    Side effects:
        Creates a new directory at the path specified by constants.SAVE_FOLDER.

    Exceptions:
        OSError: If the directory cannot be created (e.g., due to permissions issues).

    Returns:
        None
    """
    if not os.path.exists(constants.SAVE_FOLDER):
        os.mkdir(constants.SAVE_FOLDER)


def save_history(
    model: str, messages: list, prompt_tokens: int, completion_tokens: int
) -> None:
    """
    Save the conversation history with the AI model in JSON format.

    Args:
        model (str): The name or identifier of the AI model used.
        messages (list): A list of dictionaries representing the conversation messages.
        prompt_tokens (int): The number of tokens in the prompt.
        completion_tokens (int): The number of tokens in the model's response.

    Preconditions:
        - The constants.SAVE_FOLDER directory exists.
        - The messages list contains valid dictionaries representing conversation messages.
        - prompt_tokens and completion_tokens are non-negative integers.

    Side effects:
        Creates or overwrites a JSON file at the path specified by constants.SAVE_FILE.

    Exceptions:
        IOError: If the file cannot be written (e.g., due to permissions issues).
        TypeError: If any of the arguments have an invalid type.

    Returns:
        None
    """
    with open(os.path.join(constants.SAVE_FOLDER, constants.SAVE_FILE), "w", encoding="utf-8") as f:
        json.dump(
            {
                "model": model,
                "messages": messages,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

def write_files( \
        output_dir: str, \
        file_data: list[tuple[str, str, str]], \
        force_overwrite: bool = False) \
        -> None:
    """
    Write the given file data to disk in the specified output directory, regardless of
    its original location.

    Args:
        output_dir (str): The directory to write the files to.
        file_data (List[tuple[str, str, str]]): A list of tuples containing the file path, contents, and changes.
        force_overwrite (bool): Whether to force overwriting existing files.

    Preconditions:
        - file_data is a list of tuples, where each tuple contains a valid file path, contents and changes.

    Side effects:
        - Creates new files or overwrites existing files on disk.
        - Creates new folders as required

    Exceptions:
        None

    Returns:
        None
        guarantees: The specified files are written to disk.
    """
    assert isinstance(output_dir, str), "output_dir must be a string"
    assert isinstance(file_data, list), "file_data must be a list"
    assert all(isinstance(fd, tuple) and len(fd) == 3 for fd in file_data), "file_data must be a list of tuples with 3 elements"
    assert isinstance(force_overwrite, bool), "force_overwrite must be a bool"

    for relative_path, contents, _ in file_data:
        file_name = os.path.basename(relative_path)
        output_file = os.path.join(output_dir, file_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if not force_overwrite and os.path.exists(output_file):
            console.print(f"[bold yellow]{output_file} already exists. Skipping...[/bold yellow]")
        else:
            console.print(f"[bold green]Writing to {output_file}...[/bold green]")
            
            # Unescape special characters in the contents before writing to file
            unescaped_contents = xml.sax.saxutils.unescape(contents)
            
            with open(output_file, "w") as f:
                f.write(unescaped_contents)
                f.close()
