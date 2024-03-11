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
import load
import print
import save

global prompt_tokens, completion_tokens

logger = logging.getLogger("rich")
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[
        RichHandler(show_time=False, show_level=False, show_path=False, markup=True)
    ],
)


# Initialize the messages history list
# It's mandatory to pass it at each API call in order to have a conversation
messages = []
# Initialize the token counters
prompt_tokens = 0
completion_tokens = 0
# Initialize the console
console = Console()

def add_markdown_system_message() -> None:
    """
    Try to force ChatGPT to always respond with well formatted code blocks and tables if markdown is enabled.
    """
    instruction = "Always use code blocks with the appropriate language tags. If asked for a table always format it using Markdown syntax."
    messages.append({"role": "system", "content": instruction})

def start_prompt(
    session: PromptSession,
    config: dict,
    copyable_blocks: Optional[dict],
    proxy: dict | None,
) -> None:
    """
    Ask the user for input, build the request and perform it
    """

    # TODO: Refactor to avoid a global variables
    global prompt_tokens, completion_tokens

    message = ""

    if config["non_interactive"]:
        message = sys.stdin.read()
    else:
        message = session.prompt(
            HTML(f"<b>[{prompt_tokens + completion_tokens}] >>> </b>")
        )

    if message.lower().strip() == "/q":
        # this is a bit strange to be raising exceptions for normal conditions
        raise EOFError
    if message.lower() == "":
        raise KeyboardInterrupt

    if config["easy_copy"] and message.lower().startswith("/c"):
        # Use regex to find digits after /c or /copy
        match = re.search(r"^/c(?:opy)?\s*(\d+)", message.lower())
        if match:
            block_id = int(match.group(1))
            if block_id in copyable_blocks:
                try:
                    pyperclip.copy(copyable_blocks[block_id])
                    logger.info(f"Copied block {block_id} to clipboard")
                except pyperclip.PyperclipException:
                    logger.error(
                        "Unable to perform the copy operation. Check https://pyperclip.readthedocs.io/en/latest/#not-implemented-error"
                    )
            else:
                logger.error(
                    f"No code block with ID {block_id} available",
                    extra={"highlighter": None},
                )
        elif messages:
            pyperclip.copy(messages[-1]["content"])
            logger.info(f"Copied previous response to clipboard")
        raise KeyboardInterrupt

    messages.append({"role": "user", "content": message})

    api_key = config["anthropic_api_key"]
    model = config["anthropic_model"]
    base_endpoint = config["anthropic_api_url"]

    # Base body parameters
    body = {
        "model": model,
        "temperature": config["temperature"],
        "messages": messages,
    }
    # Optional parameters
    if "max_tokens" in config:
        body["max_tokens"] = config["max_tokens"]
    if config["json_mode"]:
        body["response_format"] = {"type": "json_object"}

    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        }
        body = {
            "model": model,
            "prompt": f"{messages[-2]['content']}\n\nHuman: {messages[-1]['content']}\n\nAssistant:",
            "max_tokens_to_sample": config.get("max_tokens", 500),
            "stop_sequences": ["\n\nHuman:"],
            "temperature": config["temperature"],
        }
        r = requests.post(
            f"{base_endpoint}/v1/complete",
            headers=headers,
            json=body,
            proxies=proxy,
        )
    except requests.ConnectionError:
        logger.error(
            "[red bold]Connection error, try again...", extra={"highlighter": None}
        )
        messages.pop()
        raise KeyboardInterrupt
    except requests.Timeout:
        logger.error(
            "[red bold]Connection timed out, try again...", extra={"highlighter": None}
        )
        messages.pop()
        raise KeyboardInterrupt

    match r.status_code:
        case 200:
            response = r.json()

            message_response = {"content": response["content"][0]["text"]}
            usage_response = {"prompt_tokens": response["usage"]["input_tokens"], "completion_tokens": response["usage"]["output_tokens"]}

            if not config["non_interactive"]:
                console.line()
            if config["markdown"]:
                print.print_markdown(message_response["content"].strip(), copyable_blocks)
            else:
                print(message_response["content"].strip())
            if not config["non_interactive"]:
                console.line()

            # Update message history and token counters
            messages.append({"role": response["role"], "content": message_response["content"]})
            prompt_tokens += usage_response["prompt_tokens"]
            completion_tokens += usage_response["completion_tokens"]
            save.save_history(model, messages, prompt_tokens, completion_tokens)

            if config["non_interactive"]:
                # In non-interactive mode there is no looping back for a second prompt, you're done.
                raise EOFError

        case 400:
            response = r.json()
            if "error" in response:
                logger.error(
                    f"[red bold]{response['error']}",
                    extra={"highlighter": None},
                )
            logger.error("[red bold]Invalid request", extra={"highlighter": None})
            raise EOFError

        case 401:
            logger.error("[red bold]Invalid API Key", extra={"highlighter": None})
            raise EOFError

        case 429:
            logger.error(
                "[red bold]Rate limit or maximum monthly limit exceeded",
                extra={"highlighter": None},
            )
            messages.pop()
            raise KeyboardInterrupt

        case 500:
            logger.error(
                "[red bold]Internal server error",
                extra={"highlighter": None},
            )
            messages.pop()
            raise KeyboardInterrupt

        case 502 | 503:
            logger.error(
                "[red bold]The server seems to be overloaded, try again",
                extra={"highlighter": None},
            )
            messages.pop()
            raise KeyboardInterrupt

        case _:
            logger.error(
                f"[red bold]Unknown error, status code {r.status_code}",
                extra={"highlighter": None},
            )
            logger.error(r.json(), extra={"highlighter": None})
            raise EOFError



