
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

def calculate_expense(
    prompt_tokens: int,
    completion_tokens: int,
    prompt_pricing: float,
    completion_pricing: float,
) -> float:
    """
    Calculate the expense, given the number of tokens and the pricing rates
    """
    expense = ((prompt_tokens / 1000) * prompt_pricing) + (
        (completion_tokens / 1000) * completion_pricing
    )

    # Format to display in decimal notation rounded to 6 decimals
    expense = "{:.6f}".format(round(expense, 6))

    return expense


###############################################################################
def get_size(contents: str) -> str:
    """
    Get the size of the string in KB and format the output as a string.
    """
    size = len(contents) / 1024
    return f"{size:.2f} KB"