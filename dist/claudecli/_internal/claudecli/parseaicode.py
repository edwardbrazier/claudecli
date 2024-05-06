import re
from typing import NamedTuple, Optional

import xml.etree.ElementTree as ET


class FileData(NamedTuple):
    """
    Represents the data of the files from the AI's response.
    """

    relative_path: str
    contents: str
    changes: str


class ParseResult(NamedTuple):
    """
    Represents the result from attempting to parse a code response from the AI.
    """

    finished: bool
    file_data_list: Optional[list[FileData]]


class Usage(NamedTuple):
    """
    Represents the number of tokens used by the model for the input and output.
    """

    input_tokens: int
    output_tokens: int

    def __repr__(self):
        return f"Input - {self.input_tokens}; Output - {self.output_tokens}"


def sum_usages(u1: Usage, u2: Usage):
    """
    Overload the + operator to add two Usage tallies.
    """
    assert isinstance(u1, Usage) and isinstance(
        u2, Usage
    ), "Both arguments must be Usage objects"
    return Usage(u1.input_tokens + u2.input_tokens, u1.output_tokens + u2.output_tokens)


class CodeResponse(NamedTuple):
    """
    Represents the response from the Anthropic API for a code prompt.
    """

    content_string: str
    file_data_list: list[FileData]
    usage: Usage


class ChatResponse(NamedTuple):
    """
    Represents the response from the Anthropic API for a chat prompt.
    """

    content_string: str
    usage: Usage


def get_element_text(element: ET.Element, tag: str) -> Optional[str]:
    """
    Safely retrieve the text content of a child element with the specified tag.

    Args:
        element (ET.Element): The parent element to search within.
        tag (str): The tag name of the child element.

    Preconditions:
        - element is a valid ET.Element instance.
        - tag is a non-empty string.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        Optional[str]: The text content if the child element is found, or None if not found.
        guarantees: The returned value is either a string or None.
    """
    assert isinstance(
        element, ET.Element
    ), "element must be a valid ET.Element instance"
    assert isinstance(tag, str) and tag, "tag must be a non-empty string"
    child = element.find(tag)
    return child.text if child is not None else None


def process_file_element(file_element: ET.Element) -> Optional[FileData]:
    """
    Process a <file> element and extract the file data.

    Args:
        file_element (ET.Element): The <file> element to process.

    Preconditions:
        - file_element is a valid ET.Element instance representing a <file> element.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        Optional[FileData]: A FileData object if the path and content are successfully extracted, or None if either is missing.
        guarantees: The returned value is either a FileData object or None.
    """
    assert isinstance(
        file_element, ET.Element
    ), "file_element must be a valid ET.Element instance"
    path_maybe: str | None = get_element_text(file_element, "path")
    content_maybe: str | None = get_element_text(file_element, "content")
    changes_maybe: str | None = get_element_text(file_element, "changes")

    if path_maybe and content_maybe:
        return FileData(
            path_maybe,
            content_maybe,
            (
                changes_maybe
                if changes_maybe is not None
                else "No change description provided."
            ),
        )
    else:
        print(
            "Failed to extract one of the following from <file> element: path, content, or changes."
        )
        return None


def extract_up_to_close_code(text: str) -> str:
    """
    Extracts the text up to the first closing code tag, including the code tag and any other tags in between.
    Subsequently strips any preceding or trailing whitespace and returns the result.
    If there isn't a </code> tag, then the entire text is returned.

    Args:
        text (str): The input text to extract from.

    Preconditions:
        - text is a string.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        str: The extracted text up to the first closing code tag, including the code tag and any other tags in between.
        guarantees: The returned value is a string.
    """
    assert isinstance(text, str) and text, "text must be a non-empty string"

    try:
        code_end_index = text.index("</code>") + 7
        result = text[:code_end_index]
        return result.strip()
    except ValueError:
        return text


def extract_between_angle_brackets(text: str) -> str:
    """
    Extracts the text between the first opening angle bracket and the last closing angle bracket, including those outer angle brackets and any other angle brackets in between.
    Subsequently strips any preceding or trailing whitespace and returns the result.

    Args:
        text (str): The input text to extract from.

    Preconditions:
        - text is a non-empty string.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        str: The extracted text between the first opening angle bracket and the last closing angle bracket, including the angle brackets.
        guarantees: The returned value is a non-empty string.
    """
    assert isinstance(text, str) and text, "text must be a non-empty string"

    # Also includes the <?xml ...> tag as well as the whole root.
    pattern = r"<.*>"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        # strip preceding or trailing whitespace
        return match.group().strip()
    else:
        return ""


def extract_after_last_close_angle_bracket(text: str) -> str:
    """
    Extracts the text after the last closing angle bracket, including the angle bracket.
    Subsequently strips any preceding or trailing whitespace and returns the result.

    Args:
        text (str): The input text to extract from.

    Preconditions:
        - text is a non-empty string.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        str: The extracted text after the last closing angle bracket, including the angle bracket.
        guarantees: The returned value is a string.
    """
    assert isinstance(text, str) and text, "text must be a non-empty string"

    pattern = r">.*"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        # strip preceding or trailing whitespace
        return match.group().strip()
    else:
        return ""


def process_assistant_response(response: str) -> Optional[list[FileData]]:
    """
    Process the assistant's response and extract the file data.

    Args:
        response (str): The assistant's response to process.

    Preconditions:
        - response is a non-empty string.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        Optional[list[FileData]]: A list of FileData objects if the path and content are successfully extracted,
        or None if either is missing.
        guarantees: The returned value is either a list of FileData objects or None.
    """
    assert isinstance(response, str) and response, "response must be a non-empty string"

    # Remove everything before the first '<' from the response
    # and then remove everything after the last '>' in the response.
    response_stripped = extract_up_to_close_code(response)

    # print(f"stripped response:\n{response_stripped}")

    try:
        root = ET.fromstring(response_stripped)
        files = root.findall(".//file")
        file_data_list: list[FileData] = list(
            filter(None, map(process_file_element, files))
        )
        return file_data_list
    except ET.ParseError as e:
        print(f"Error parsing XML response: {e}")
        print("Skipping file processing.")
        return None


def contains_stop_signal(response: str) -> bool:
    """
    Check if the response contains the stop signal.

    Args:
        response (str): The response to check.

    Preconditions:
        - response is a non-empty string.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        bool: True if the response contains the stop signal, False otherwise.
        guarantees: The returned value is a boolean.
    """
    assert isinstance(response, str) and response, "response must be a non-empty string"

    return "</code>" in response


def parse_ai_responses(responses: list[str], force_parse: bool) -> ParseResult:
    """
    Parse a series of AI responses and combine the file data.

    Args:
        responses (list[str]): The list of AI responses to parse.
        force_parse (bool): Parse even if stop signal not detected.

    Preconditions:
        - responses is a non-empty list of non-empty strings.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        ParseResult:
        - The `finished` field is a boolean indicating whether the AI has signaled that it has finished all of its output.
        - The `file_data_list` field is an optional list of FileData objects, where the contents of files with the same relative path have been combined.
        - If there is an error parsing the responses, the `file_data_list` field will be None.
    """
    assert (
        isinstance(responses, list) and responses
    ), "responses must be a non-empty list"
    assert all(
        isinstance(r, str) for r in responses
    ), "responses must be a list of strings"
    assert all(r for r in responses), "responses must be a list of non-empty strings"

    file_data_dict: dict[str, FileData] = {}

    concatenated_responses = "".join(responses)

    finished = contains_stop_signal(concatenated_responses)

    if not finished and not force_parse:
        return ParseResult(finished, None)
    else:
        file_data_list = process_assistant_response(concatenated_responses)

        if file_data_list is not None:
            for file_data in file_data_list:
                if file_data.relative_path in file_data_dict:
                    existing_file_data = file_data_dict[file_data.relative_path]
                    file_data_dict[file_data.relative_path] = FileData(
                        existing_file_data.relative_path,
                        existing_file_data.contents + file_data.contents,
                        f"{existing_file_data.changes}\n{file_data.changes}",
                    )
                else:
                    file_data_dict[file_data.relative_path] = file_data

        return ParseResult(
            finished, list(file_data_dict.values()) if file_data_dict else None
        )
