#!/bin/env python
"""
This module contains configuration settings and utility functions for the Claude CLI.
"""

from pathlib import Path
from xdg_base_dirs import xdg_config_home
import datetime
from typing import Dict, Tuple

# Define type aliases for better readability and maintainability
ConnectionOptions = Dict[str, str]
Address = Tuple[str, int]
Server = Tuple[Address, ConnectionOptions]

# Define paths for configuration and history files
BASE = Path(xdg_config_home(), "claudecli")
CONFIG_FILE = BASE / "config.yaml"
HISTORY_FILE = BASE / "history"
SAVE_FOLDER: Path = BASE / "session-history"
SAVE_FILE = (
    "claude-session-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
)
ENV_VAR_ANTHROPIC = "ANTHROPIC_API_KEY"

# PRICING_RATE = {
#     "claude-3-opus-20240229": {"prompt": 0.0005, "completion": 0.0015},
#     "claude-3-sonnet-20240229": {"prompt": 0.0005, "completion": 0.0015},
# }

DEFAULT_CONFIG = {
    "supplier": "anthropic",
    "anthropic-api-key": "<INSERT YOUR ANTHROPIC API KEY HERE>",
    "anthropic_api_url": "https://api.anthropic.com",
    "anthropic_model": "claude-3-haiku-20240307",
    "temperature": 1,
    "markdown": True,
    "easy_copy": True,
    "non_interactive": False,
    "json_mode": False,
    "use_proxy": False,
    "proxy": "socks5://127.0.0.1:2080",
}


opus = "claude-3-opus-20240229"
sonnet = "claude-3-sonnet-20240229"
haiku = "claude-3-haiku-20240307"