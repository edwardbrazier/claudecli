"""
This module provides functions for interacting with the Anthropic API.
"""

from typing import Optional
import anthropic
import requests

from claudecli.parseaicode import (
    parse_ai_responses,
    CodeResponse,
    ChatResponse,
    Usage,
    sum_usages,
)
from claudecli.printing import console


def setup_client(api_key: str) -> anthropic.Client:
    """
    Set up the Anthropic client using the provided API key.

    Args:
        api_key (str): The API key to use for authentication.

    Preconditions:
        - api_key is a valid Anthropic API key.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        anthropic.Client: The Anthropic client instance.
        guarantees: The returned client is properly initialized with the API key.
    """
    assert isinstance(api_key, str), "api_key must be a string"
    client: anthropic.Client = anthropic.Anthropic(api_key=api_key)
    return client


def prompt_ai(
    client: anthropic.Client,
    model: str,
    messages: list[dict[str, str]],
    system_prompt: str,
) -> Optional[ChatResponse]:
    """
    Generate an AI response to the given prompt using the Anthropic API.
    This is a general-purpose interaction with the AI, not specific to code generation.

    Args:
        client (anthropic.Client): The Anthropic client instance.
        model (str): The name of the AI model to use.
        messages (list[dict[str, str]]): The list of messages to send to the AI.
        system_prompt (str): The system prompt to provide to the AI.

    Preconditions:
        - client is a valid Anthropic client instance.
        - model is a valid model name supported by the Anthropic API.
        - messages is a non-empty list of message dictionaries with "role" and "content" keys.
        - system_prompt is a non-empty string.

    Side effects:
        - Sends a request to the Anthropic API.
        - Prints to the console if something goes wrong.

    Exceptions:
        - requests.ConnectionError: If there is a connection error with the API.
        - requests.Timeout: If the API request times out.

    Returns:
        Optional[str]: The AI-generated response string, or None if an error occurred.
        guarantees: The returned value is either a non-empty string or None.
    """
    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0,
            messages=messages,  # type: ignore
            system=system_prompt,
        )
    except requests.ConnectionError:
        console.print("[red bold]Connection error, try again...[/red bold]")
        return None
    except requests.Timeout:
        console.print("[red bold]Connection timed out, try again...[/red bold]")
        return None

    content = response.content
    content_string: str = ""

    if len(content) == 0:
        console.print("Received an empty list of contents blocks.")
        return None
    else:
        content_block = content[0]

        # Strip trailing whitespace from last message
        # so that if we pass it back, Anthropic will accept it
        # as an assistant message.
        content_string: str = content_block.text  # type: ignore

        if content_string == "":
            console.print("Received an empty response string.")
            return None
        else:
            return ChatResponse(
                content_string=content_string,
                usage=Usage(response.usage.input_tokens, response.usage.output_tokens),
            )


def gather_ai_code_responses(
    client: anthropic.Client,
    model: str,
    messages: list[dict[str, str]],
    system_prompt: str,
) -> Optional[CodeResponse]:
    """
    Generate a series of AI code responses to the given prompt using the Anthropic API until the stop signal is received.

    Args:
        client (anthropic.Client): The Anthropic client instance.
        model (str): The name of the AI model to use.
        messages (list[dict[str, str]]): The list of messages to send to the AI.
        system_prompt (str): The system prompt to provide to the AI.

    Preconditions:
        - client is a valid Anthropic client instance.
        - Each message must have a 'role' and 'content' key.
        - Elements in messages alternate betwen user prompts and assistant responses.
        - Message list is not empty.
        - First message is user prompt. (Last message may be either user prompt or (partial) assistant response.)

    Side effects:
        - Sends multiple requests to the Anthropic API.

    Exceptions:
        - requests.ConnectionError: Raised when there is a connection error with the API.
        - requests.Timeout: Raised when the API request times out.

    Returns:
        Optional[ResponseContent]: A ResponseContent object containing the concatenated responses and the list of FileData objects if the responses are successfully parsed, or None if an error occurred.
        guarantees: If the program receives a response from the AI, the returned value is a ResponseContent object without any Nones inside it.
    """
    assert isinstance(client, anthropic.Client), "Client must be an Anthropic Client"
    assert isinstance(model, str), "model must be a string"
    assert isinstance(messages, list), "messages must be a list"
    assert len(messages) > 0, "messages must be a non-empty list"
    assert all(
        isinstance(msg, dict) and "role" in msg and "content" in msg for msg in messages
    ), "messages must be a list of dicts with 'role' and 'content' keys"
    assert isinstance(system_prompt, str), "System prompt must be a string"

    responses: list[str] = []
    concatenated_responses: str = ""
    usage_tally = Usage(0, 0)
    finished = False
    max_turns = 10
    separator = "\n-------------------------------\n"

    for _ in range(max_turns):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.0,
                messages=messages,  # type: ignore
                system=system_prompt,
            )
        except requests.ConnectionError:
            print("[red bold]Connection error, try again...[/red bold]")
            return None
        except requests.Timeout:
            print("[red bold]Connection timed out, try again...[/red bold]")
            return None

        content = response.content
        usage_tally = sum_usages(
            usage_tally,
            Usage(response.usage.input_tokens, response.usage.output_tokens),
        )

        content_string: str = ""

        if len(content) == 0:
            print("Received an empty list of contents blocks.")
            force_parse: bool = True
        else:
            force_parse: bool = False

            content_block = content[0]

            # Strip trailing whitespace from last message
            # so that if we pass it back, Anthropic will accept it
            # as an assistant message.
            content_string: str = content_block.text  # type: ignore

            if content_string == "":
                console.print("Received an empty response string from AI.")
                return None

            responses.append(content_string)  # type: ignore

        parse_result = parse_ai_responses(responses, force_parse)
        finished = parse_result.finished

        if (finished or force_parse) and parse_result.file_data_list is None:
            console.print("[bold yellow]Failed to parse AI responses.[/bold yellow]")
            return CodeResponse(
                content_string=separator.join(responses),
                file_data_list=[],
                usage=usage_tally,
            )
        elif (finished or force_parse) and parse_result.file_data_list is not None:
            concatenated_responses = separator.join(responses)

            response_content = CodeResponse(
                content_string=concatenated_responses,
                file_data_list=parse_result.file_data_list,
                usage=usage_tally,
            )
            return response_content
        elif not finished:  # assume force_parse == False now
            type_of_last_message = messages[-1]["role"]  # type: ignore

            if type_of_last_message == "user":
                messages += {  # type: ignore
                    "role": "assistant",
                    "content": content_string,
                }
            else:
                # If you don't send a user prompt at the end of the list of messages,
                # but instead only provide the assistant's response back to it,
                # then the assistant will provide a continuation of its previous response.
                # So here we append the assistant response on to the assistant response
                # that was in the previous message list.
                # So the number of messages should still be two, but the assistant
                # message that we're providing back gets longer.
                messages[-1]["content"] += content_string
                messages[-1]["content"] = messages[-1]["content"].rstrip()  # type: ignore
                print("Requesting more data from the model...")

    print("[bold yellow]Reached turn limit.[/bold yellow]")

    return CodeResponse(
        content_string=concatenated_responses, file_data_list=[], usage=Usage(0, 0)
    )
