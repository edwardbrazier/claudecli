"""
This module provides functions for interacting with the Anthropic API.
"""

from typing import Optional
import anthropic
import requests

from parseaicode import parse_ai_responses, ResponseContent

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
    client: anthropic.Client = anthropic.Anthropic(api_key=api_key)
    return client

def gather_ai_responses(
        client: anthropic.Client,
        model: str, 
        messages: list[dict[str, str]],
        system_prompt: str) -> Optional[ResponseContent]:
    """
    Generate a series of AI responses to the given prompt using the Anthropic API until the stop signal is received.

    Args:
        api_key (str): The API key to use for authentication.
        model (str): The model to use for the prompt.
        messages (List[Dict[str, str]]): A list of messages to send to the AI.
    
    Preconditions:
        - api_key is a valid Anthropic API key.
        - messages contains two elements: First, a user message and then a (partial) assistant message.
    
    Side effects:
        - Interactions with AI over network.
    
    Exceptions:
        - requests.ConnectionError: Raised when there is a connection error with the API server.
        - requests.Timeout: Raised when the API request times out.
    
    Returns:
        ResponseContent: A ResponseContent object containing the concatenated responses and the list of FileData objects if the responses are successfully parsed, or an empty list if there is a parsing failure.
        guarantees: If the program receives a response from the AI, the returned value is a ResponseContent object without any Nones inside it.
    """
    assert isinstance(client, anthropic.Client), "Client must be an Anthropic Client"
    assert isinstance(model, str), "model must be a string"
    assert isinstance(messages, list), "messages must be a list"
    assert all(isinstance(msg, dict) and "role" in msg and "content" in msg for msg in messages), \
        "messages must be a list of dicts with 'role' and 'content' keys"
    assert isinstance(system_prompt, str), "System prompt must be a string"
        
    responses: list[str] = []
    concatenated_responses: str = ""
    finished = False
    max_turns = 10
    separator = "\n-------------------------------\n"

    for _ in range(max_turns):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4000, 
                temperature=0.0,
                messages=messages, # type: ignore
                system=system_prompt
            )
        except requests.ConnectionError:
            print("[red bold]Connection error, try again...[/red bold]")
            return None
        except requests.Timeout:
            print("[red bold]Connection timed out, try again...[/red bold]")
            return None

        content = response.content
        print(f"Received response.")

        content_string: str = ""
        
        if len(content) == 0:
            print("Received an empty list of contents blocks.")
            force_parse: bool = True
        else:
            force_parse: bool = False
        
            content_block = content[0]

            # Strip trailing whitespace from last mesage
            # so that if we pass it back, Anthropic will accept it
            # as an assistant message.
            content_string: str = content_block.text # ["text"] # type: ignore

            if content_string == "": 
                print("Received an empty response string.")
                return None
            
            responses.append(content_string) # type: ignore

        parse_result = parse_ai_responses(responses, force_parse)
        finished = parse_result.finished

        if (finished or force_parse) and parse_result.file_data_list is None:
            print("[bold yellow]Failed to parse AI responses.[/bold yellow]")
            return ResponseContent(
                content_string=separator.join(responses),
                file_data_list=[]
            )
        elif (finished or force_parse) and parse_result.file_data_list is not None:
            concatenated_responses = separator.join(responses)
            
            response_content = ResponseContent(
                content_string=concatenated_responses,
                file_data_list=parse_result.file_data_list
            )
            return response_content
        elif not finished: # assume force_parse == False now
            # If you don't send a user prompt at the end of the list of messages,
            # but instead only provide the assistant's response back to it,
            # then the assistant will provide a continuation of its previous response.
            # So here we append the assistant response on to the assistant response
            # that was in the previous message list.
            # So the number of messages should still be two, but the assistant
            # message that we're providing back gets longer.
            messages[1]["content"] += content_string
            messages[1]["content"] = messages[1]["content"].rstrip()
            print("Requesting a continuation from the model...")
    
    print("[bold yellow]Reached turn limit.[/bold yellow]")

    return ResponseContent(
        content_string=concatenated_responses,
        file_data_list=[]
    )
