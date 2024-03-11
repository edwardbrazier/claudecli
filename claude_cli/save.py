#!/bin/env python

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

def create_save_folder() -> None:
    """
    Create the session history folder if not exists
    """
    if not os.path.exists(constants.SAVE_FOLDER):
        os.mkdir(constants.SAVE_FOLDER)


def save_history(
    model: str, messages: list, prompt_tokens: int, completion_tokens: int
) -> None:
    """
    Save the conversation history in JSON format
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



