"""
This module provides a command-line interface for interacting with the Anthropic AI model.
It allows users to provide context from local files or directories, set various options,
and engage in a conversational session with the model.
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

import pure
from interact import *

@click.command()
@click.option(
    "-s",
    "--source",
    "sources",
    type=click.Path(exists=True),
    help="Pass an entire codebase to the model as context, from the specified location. "
         "Repeat this option and its argument any number of times.",
    multiple=True,
)
@click.option(
    "-e", 
    "--file-extensions", 
    "file_extensions",
    required=False,
    help="File name extensions of files to look at in the codebase, separated by commas without spaces, e.g. py,txt,md "
         "Only use this option once, even for multiple codebases."
)
@click.option(
    "-c",
    "--context",
    "context",
    type=click.File("r"),
    help="Path to a context file",
    multiple=True,
)
@click.option("-k", "--key", "api_key", help="Set the API Key")
@click.option("-m", "--model", "model", help="Set the model")
@click.option(
    "-ml", "--multiline", "multiline", is_flag=True, help="Use the multiline input mode"
)
@click.option(
    "-r",
    "--restore",
    "restore",
    help="Restore a previous chat session (input format: YYYYMMDD-hhmmss or 'last')",
)
@click.option(
    "-n",
    "--non-interactive",
    "non_interactive",
    is_flag=True,
    help="Non interactive/command mode for piping",
)
@click.option(
    "-j", "--json", "json_mode", is_flag=True, help="Activate json response mode"
)
def main(
    sources, context, api_key, model, multiline, restore, non_interactive, json_mode,
    file_extensions
) -> None:
    """
    Main entry point for the CLI.

    Args:
        sources (List[str]): Paths to directories containing source code to provide as context.
        context (List[File]): Files containing additional context to provide.
        api_key (str): API key to use for authentication.
        model (str): Name of the AI model to use.
        multiline (bool): Whether to enable multiline input mode.
        restore (str): Identifier for a previous chat session to restore.
        non_interactive (bool): Whether to run in non-interactive mode (for piping).
        json_mode (bool): Whether to enable JSON response mode.
        file_extensions (str): Comma-separated list of file extensions to consider in source directories.

    Preconditions:
        - The provided source directories and context files must exist and be readable.
        - The API key must be valid and have sufficient permissions.

    Side effects:
        - Prints output to the console.
        - Saves chat history to disk.
        - Copies output to the clipboard (if enabled).

    Exceptions:
        - FileNotFoundError: Raised if a provided source directory or context file does not exist.
        - Other exceptions may be raised by external libraries or the AI model.

    Returns:
        None
    """

    # If non interactive suppress the logging messages
    if non_interactive:
        logger.setLevel("ERROR")

    logger.info("[bold]Claude CLI", extra={"highlighter": None})

    history = FileHistory(constants.HISTORY_FILE)

    if multiline:
        session = PromptSession(history=history, multiline=True)
    else:
        session = PromptSession(history=history)

    try:
        config = load.load_config(logger=logger, config_file=constants.CONFIG_FILE)
    except FileNotFoundError:
        logger.error(
            "[red bold]Configuration file not found", extra={"highlighter": None}
        )
        sys.exit(1)

    save.create_save_folder()

    # Check proxy setting
    if config["use_proxy"]:
        proxy = {"http": config["proxy"], "https": config["proxy"]}
    else:
        proxy = None

    # Order of precedence for API Key configuration:
    # Command line option > Environment variable > Configuration file

    # If the environment variable is set, overwrite the configuration
    if os.environ.get(constants.ENV_VAR_ANTHROPIC):
        config["anthropic_api_key"] = os.environ[constants.ENV_VAR_ANTHROPIC].strip()
    
    # If the --key command line argument is used, overwrite the configuration
    if api_key:
        config["anthropic_api_key"] = api_key.strip()

    # If the --model command line argument is used, overwrite the configuration
    if model:
        config["anthropic_model"] = model.strip()

    config["non_interactive"] = non_interactive

    # Do not emit markdown in non-interactive mode, as ctrl character formatting interferes in several contexts including json output.
    if config["non_interactive"]:
        config["markdown"] = False

    config["json_mode"] = json_mode

    copyable_blocks = {} if config["easy_copy"] else None

    model = config["anthropic_model"]

    # Run the display expense function when exiting the script
#    atexit.register(print.display_expense, logger=logger, model=model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    config["supplier"] = "anthropic"

    logger.info(
        f"Supplier: [green bold]{config['supplier']}", extra={"highlighter": None}
    )
    logger.info(f"Model in use: [green bold]{model}", extra={"highlighter": None})

    # Add the system message for code blocks in case markdown is enabled in the config file
    if config["markdown"]:
        add_markdown_system_message()

    initial_context = ""

    # Source code location from command line option
    if sources:
        for source in sources:
            logger.info(
                f"Codebase location: [green bold]{source}\n",
                extra={"highlighter": None},
            )
            logger.info(
                "The entire codebase will be prepended to your first message."
            )

            extensions = []

            if file_extensions != ():
                logger.info(
                    f"Looking only at source files with extensions: [green bold]{file_extensions}\n",
                    extra={"highlighter": None},
                )
                extensions = [ext.strip() for ext in file_extensions.split(",")]

            try:
                codebase = load.load_codebase(logger, source, extensions)
                initial_context += codebase
                
                # Show the user how big the entire codebase is, in kb. 
                logger.info(
                    f"Codebase size: [green bold]{pure.get_size(codebase)}\n",
                )
            except FileNotFoundError as e:
                print(f"Error reading codebase: {e}")

    # Context from the command line option
    if context:
        for c in context:
            logger.info(
                f"Context file: [green bold]{c.name}", extra={"highlighter": None}
            )
            initial_context = codebase
    #         messages.append({"role": "user", "content": c.read().strip()})

    # Restore a previous session
    if restore:
        if restore == "last":
            last_session = load.get_last_save_file()
            restore_file = f"chatgpt-session-{last_session}.json"
        else:
            restore_file = f"chatgpt-session-{restore}.json"
        try:

            # If this feature is used --context is cleared
            messages.clear()
            history_data = load.load_history_data(os.path.join(constants.SAVE_FOLDER, restore_file))
            for message in history_data["messages"]:
                messages.append(message)
            prompt_tokens += history_data["prompt_tokens"]
            completion_tokens += history_data["completion_tokens"]
            logger.info(
                f"Restored session: [bold green]{restore}",
                extra={"highlighter": None},
            )
        except FileNotFoundError:
            logger.error(
                f"[red bold]File {restore_file} not found", extra={"highlighter": None}
            )

    if json_mode:
        logger.info(
            "JSON response mode is active. Your message should contain the [bold]'json'[/bold] word.",
            extra={"highlighter": None},
        )

    if not non_interactive:
        console.rule()

    while True:
        try:
            start_prompt(initial_context, session, config, copyable_blocks, proxy)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break



if __name__ == "__main__":
    main()