#!/bin/env python

from pathlib import Path
from xdg_base_dirs import xdg_config_home
import datetime

BASE = Path(xdg_config_home(), "chatgpt-cli")
CONFIG_FILE = BASE / "config.yaml"
HISTORY_FILE = BASE / "history"
SAVE_FOLDER = BASE / "session-history"
SAVE_FILE = (
    "claude-session-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
)
ENV_VAR_ANTHROPIC = "ANTHROPIC_API_KEY"

# Azure price is not accurate, it depends on your subscription
PRICING_RATE = {
    "claude-3-opus-20240229": {"prompt": 0.0005, "completion": 0.0015},
    "claude-3-sonnet-20240229": {"prompt": 0.0005, "completion": 0.0015},
}

DEFAULT_CONFIG = {
    "supplier": "anthropic",
    "anthropic-api-key": "<INSERT YOUR ANTHROPIC API KEY HERE>",
    "anthropic_api_url": "https://api.anthropic.com",
    "anthropic_model": "claude-3-opus-20240229",
    "temperature": 1,
    "markdown": True,
    "easy_copy": True,
    "non_interactive": False,
    "json_mode": False,
    "use_proxy": False,
    "proxy": "socks5://127.0.0.1:2080",
}