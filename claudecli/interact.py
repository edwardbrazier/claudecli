#!/bin/env python
"""
This script provides an interactive command-line interface for interacting with the Anthropic AI API.
It allows users to send prompts and receive responses from the AI model.
"""

from enum import Enum
import logging
import os
import sys

import anthropic
from prompt_toolkit import HTML, PromptSession
from rich.console import Console
from typing import Optional, Union
from rich.logging import RichHandler

import save
from ai_functions import gather_ai_responses
from parseaicode import ResponseContent

logger = logging.getLogger("rich")

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[
        RichHandler(show_time=False, show_level=False, show_path=False, markup=True) # type: ignore
    ],
)

# Initialize the console
console = Console()

ConversationHistory = list[dict[str,str]]

class UserPromptOutcome(Enum):
    CONTINUE = 1
    STOP = 0

PromptOutcome = Union[ConversationHistory, UserPromptOutcome]

def prompt_user(
    client: anthropic.Client,
    codebase_xml: Optional[str],
    conversation_history: ConversationHistory,
    session: PromptSession[str],
    config: dict,                       # type: ignore
    output_dir: Optional[str],
    force_overwrite: bool
) -> PromptOutcome:
    """
    Ask the user for input, build the request and perform it.

    Args:
        initial_context (str): The initial context or prompt to provide to the AI model.
        session (PromptSession): The prompt session object for interactive input.
        config (dict): The configuration dictionary containing settings for the API request.
        copyable_blocks (Optional[dict]): A dictionary containing code blocks that can be copied to the clipboard.
        proxy (dict | None): A dictionary containing proxy settings, or None if no proxy is used.
        output_dir (str): The output directory for generated files when using the /o command.
        force_overwrite (bool): Whether to force overwrite of output files if they already exist.

    Preconditions:
        - The `messages` list is initialized and contains the conversation history.
        - The `console` object is initialized for logging and output.
        - The conversation history does not contain more than one User message in a row
            or more than one Assistant message in a row, and it ends with an Assistant message if 
            it is not empty.
        - If there is an initial_context, then ConversationHistory is empty.

    Side effects:
        - Modifies the `messages` list by appending new messages from the user and the AI model.
        - Prints the AI model's response to the console.
        - Saves the conversation history to a file.
        - Copies code blocks to the clipboard if the user requests it.
        - Writes generated files to the output directory when using the /o command.

    Exceptions:
        - EOFError: Raised when the user enters "/q" to quit the program.
        - KeyboardInterrupt: Raised when the user enters an empty prompt or when certain errors occur during the API request.

    Returns:
        None
    """
    user_entry: str = ""

    context_data: str = ("Here is a codebase. Read it carefully, because I want you to work on it.\n\n" \
                    "\n\nCodebase:\n" + codebase_xml + "\n\n") \
                    if codebase_xml is not None \
                    else ""

    if config["non_interactive"]:
        user_entry = sys.stdin.read()
    else:
        user_entry = session.prompt(
            HTML(f"<b> >>> </b>") 
        )

    if user_entry.lower().strip() == "/q":
        return UserPromptOutcome.STOP
    if user_entry.lower() == "":
        return UserPromptOutcome.CONTINUE
    
    # Default system prompt, but not suitable for generating code in xml.
    system_prompt: str =    "You are a helpful AI assistant which answers questions about programming. " \
                            "Use markdown formatting where appropriate."

    # There are two cases: 
    # One is that the user wants the AI to talk to them.
    # The other is that the user wants the AI to send code to some files.
    if user_entry.lower().startswith("/o"):
        # Remove the "/o" from the message
        user_instruction = user_entry[2:].strip()
        write_output =  True
        
        # The Anthropic documentation says that Claude performs better when 
        # the input data comes first and the instructions come last.
        new_messages: list[dict[str,str]] = [
            {
                "role": "user",
                # The following is still ok if context_data is empty,
                # which should happen if it's not the first turn of 
                # the conversation.
                "content": context_data + user_instruction + \
                                "\nMake sure to escape special characters correctly inside the XML!"
            },
            {
                "role": "assistant",
                "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            }
        ]

        # TODO: Will need to package up the system prompt into the Python executable and/or make it user-configurable.
        with open("./claude-cli/claudecli/coder_system_prompt.txt", "r") as f:
            system_prompt = f.read()

    else: 
        # User is conversing with AI, not asking for code sent to files.
        user_prompt: str = user_entry
        new_messages: list[dict[str,str]] = [ \
            {
                "role": "user", 
                "content": context_data + user_prompt
            }
        ]
        write_output = False

    # concanenate the new messages to the existing ones
    messages = conversation_history + new_messages

    model: str = config["anthropic_model"]      # type: ignore

    response_content: Optional[ResponseContent] = gather_ai_responses(client, model, messages, system_prompt) # type: ignore

    if response_content is None:
        console.print("[bold red]Failed to get a response from the AI.[/bold red]")
    else:
        for element in response_content.content_string: # type: ignore
            print(element, end='')                      # type: ignore
        console.line()

        if write_output:
            try:
                if output_dir is not None:
                    output_dir_notnone: str = output_dir
                else:
                    output_dir_notnone: str = os.getcwd()

                save.save_ai_output(response_content, output_dir_notnone, force_overwrite) # type: ignore

                console.print("[bold green]Done![/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error processing AI response: {e}[/bold red]")

    return messages