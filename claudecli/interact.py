#!/bin/env python
"""
This script provides an interactive command-line interface for interacting with the Anthropic AI API.
It allows users to send prompts and receive responses from the AI model.
"""

from enum import Enum
import logging
import sys

import anthropic
from prompt_toolkit import HTML, PromptSession
from typing import Optional, Union
from rich.logging import RichHandler

from claudecli.printing import print_markdown, console
from claudecli.constants import (
    coder_system_prompt_hardcoded,
    coder_system_prompt_plaintext,
)
from claudecli import save
from claudecli.ai_functions import (
    gather_ai_code_responses,
    prompt_ai,
    get_plaintext_response,
)
from claudecli.parseaicode import CodeResponse
from claudecli.pure import format_cost
from claudecli.codebase_watcher import (
    Codebase,
    CodebaseUpdates,
    CodebaseState,
    find_codebase_change_contents,
    num_affected_files,
)

logger = logging.getLogger("rich")

logging.basicConfig(
    level="WARNING",
    format="%(message)s",
    handlers=[
        RichHandler(show_time=False, show_level=False, show_path=False, markup=True)  # type: ignore
    ],
)

ConversationHistory = list[dict[str, str]]


class UserPromptOutcome(Enum):
    CONTINUE = 1
    STOP = 0


PromptOutcome = Union[ConversationHistory, UserPromptOutcome, CodebaseUpdates]


def prompt_user(
    client: anthropic.Client,
    context: Optional[str],
    conversation_history: ConversationHistory,
    session: PromptSession[str],
    config: dict,  # type: ignore
    output_dir_notnone: str,
    force_overwrite: bool,
    user_system_prompt_code: str,
    system_prompt_general: str,
    codebases: list[Codebase],
    file_extensions: list[str],
) -> PromptOutcome:
    """
    Ask the user for input, build the request and perform it.

    Args:
        client (anthropic.Client): The Anthropic client instance.
        context (Optional[str]): The XML representation of the codebase or changes to the codebase, if provided.
        conversation_history (ConversationHistory): The history of the conversation so far.
        session (PromptSession): The prompt session object for interactive input.
        config (dict): The configuration dictionary containing settings for the API request.
        output_dir_notnone (str): The output directory for generated files when using the /o command.
        force_overwrite (bool): Whether to force overwrite of output files if they already exist.
        user_system_prompt_code (str): The user's part of the system prompt to use for code generation,
                                    additional to the hardcoded coder system prompt.
        system_prompt_general (str): The system prompt to use for general conversation.
        codebases (list[Codebase]): A list of Codebases being watched.
        file_extensions (list[str]): A list of file extensions to watch for in the codebases.

    Preconditions:
        - The `conversation_history` list is initialized and contains the conversation history.
        - The `console` object is initialized for logging and output.
        - The conversation history does not contain more than one User message in a row
            or more than one Assistant message in a row, and it ends with an Assistant message if
            it is not empty.
        - If there is a codebase_xml, then conversation_history is empty.

    Side effects:
        - Modifies the `conversation_history` list by appending new messages from the user and the AI model.
        - Prints the AI model's response to the console.
        - Writes generated files to the output directory when using the /o command.

    Exceptions:
        - EOFError: Raised when the user enters "/q" to quit the program.
        - KeyboardInterrupt: Raised when the user enters an empty prompt or when certain errors occur during the API request.

    Returns:
        None
    """
    user_entry: str = ""

    if context is not None:
        context_data: str = context
    else:
        context_data: str = ""

    model: str = config["anthropic_model"]  # type: ignore

    if config["non_interactive"]:
        user_entry = sys.stdin.read()
    else:
        user_entry = session.prompt(HTML(f"<b> >>> </b>"))

    if user_entry.lower().strip() == "/q":
        return UserPromptOutcome.STOP
    if user_entry.lower() == "":
        return UserPromptOutcome.CONTINUE

    render_markdown: bool = True
    user_instruction: str = user_entry

    if user_entry.lower().strip().startswith("/p"):
        render_markdown = False
        user_instruction = (user_entry.strip())[2:].strip()

    if user_entry.lower().strip() == "/u":
        codebase_locations: list[str] = [codebase.location for codebase in codebases]
        codebase_states: list[CodebaseState] = [
            codebase.state for codebase in codebases
        ]
        codebase_updates: CodebaseUpdates = find_codebase_change_contents(
            codebase_locations, file_extensions, codebase_states
        )

        if num_affected_files(codebase_updates) == 0:
            console.print("No changes were identified in the codebase.")
        else:
            console.print(codebase_updates.change_descriptive.change_descriptions)
            console.print(
                "Details of the changes will be prepended to your next message to the AI."
            )

        return codebase_updates

    # There are two cases:
    # One is that the user wants the AI to talk to them.
    # The other is that the user wants the AI to send code to some files.

    # The user wants the AI to output code to files
    if user_entry.lower().strip().startswith("/o"):
        # Remove the "/o" from the message
        user_instruction = (user_entry.strip())[2:].strip()

        # The Anthropic documentation says that Claude performs better when
        # the input data comes first and the instructions come last.
        new_messages_first_try = [ # type: ignore
            {
                "role": "user",
                # The following is still ok if context_data is empty,
                # which should happen if it's not the first turn of
                # the conversation.
                "content": [
                    { # TODO: Later, for codebase updates, make a list of context strings where each existing element will never change. That way, the changes to the codebase can form a newly cached element of context.
                        # So that you don't modify the context and necessitate expensive re-caching.
                        "type": "text",
                        "text": context_data,
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": context_data
                                    + f"<user_instructions>{user_instruction}</user_instructions>"
                                    + "\nMake sure to escape special characters correctly inside the XML, and always provide a change description!"
                    }
                ]
            },
            {"role": "assistant", "content": '<?xml version="1.0" encoding="UTF-8"?>'},
        ]

        messages_first_try = conversation_history + new_messages_first_try
        response_content: Optional[CodeResponse] = gather_ai_code_responses(client, model, messages_first_try, coder_system_prompt_hardcoded + user_system_prompt_code)  # type: ignore

        if response_content is None or response_content.file_data_list == []:
            console.print(
                "[bold red]Failed to get a validly formatted response from the AI.[/bold red]"
            )
            console.print(
                "Asking the AI for an alternative response without the XML formatting."
            )

            prefix = "--- file"

            new_messages_second_try: list[dict[str, str]] = [
                {
                    "role": "user",
                    # The following is still ok if context_data is empty,
                    # which should happen if it's not the first turn of
                    # the conversation.
                    "content": context_data
                    + user_instruction,
                },
                {"role": "assistant", "content": prefix},
            ]

            messages_second_try = conversation_history + new_messages_second_try

            (plaintext_response_content, usage) = get_plaintext_response(
                client, model, messages_second_try, coder_system_prompt_plaintext
            )  # type: ignore

            if (
                plaintext_response_content is None
                or plaintext_response_content.strip() == ""
            ):
                console.print(
                    "[bold red]Failed to get a valid response from the AI, even in plaintext format.[/bold red]"
                )
                return UserPromptOutcome.CONTINUE

            content = prefix + plaintext_response_content
            success = save.save_plaintext_output(content, output_dir_notnone, force_overwrite)  # type: ignore
            
            if success:
                console.print(
                    "[bold yellow]Finished saving plain AI output without XML formatting.[/bold yellow]"
                )
                console.print(
                    "Please note that this output may contain code intended for multiple source files."
                )
            else:
                console.print("[bold yellow]Something went wrong. Did not write the file.")

            # Remove dummy assistant message from end of conversation history
            conversation_ = messages_second_try[:-1]
            # Add assistant message onto the conversation history
            conversation_contents = conversation_ + [
                {"role": "assistant", "content": plaintext_response_content}
            ]

            console.print(format_cost(usage, model))  # type: ignore

            return conversation_contents
        else:  # success
            try:
                num_written = save.save_ai_output(response_content, output_dir_notnone, force_overwrite)  # type: ignore
                console.print(f"[bold green]Wrote AI output to {num_written} files.[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error processing AI response: {e}[/bold red]")

            # Remove dummy assistant message from end of conversation history
            conversation_ = messages_first_try[:-1]
            # Add assistant message onto the conversation history
            conversation_contents = conversation_ + [
                {"role": "assistant", "content": response_content.content_string}
            ]

            console.print(format_cost(response_content.usage, model))  # type: ignore

            return conversation_contents
    else:
        # User is conversing with AI, not asking for code sent to files.
        user_prompt: str = user_instruction

        new_messages_first_try: list[dict[str, str]] = [
            {"role": "user", "content": context_data + user_prompt}
        ]

        messages = conversation_history + new_messages_first_try

        chat_response_optional = prompt_ai(client, model, messages, system_prompt_general)  # type: ignore

        if chat_response_optional is None:
            console.print("[bold red]Failed to get a response from the AI.[/bold red]")
            return UserPromptOutcome.CONTINUE
        else:
            if render_markdown:
                print_markdown(console, chat_response_optional.content_string)  # type: ignore
            else:
                console.print(chat_response_optional.content_string)

            response_string = chat_response_optional.content_string
            usage = chat_response_optional.usage
            console.print(format_cost(usage, model))  # type: ignore
            chat_history = messages + [
                {"role": "assistant", "content": response_string}
            ]
            return chat_history
