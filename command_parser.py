import re

class CommandParser:
    """
    Parses natural language commands into structured action dictionaries.
    """
    def __init__(self):
        # Define patterns for commands
        # Order matters: more specific patterns should come before general ones if overlap is possible.
        self.command_patterns = [
            # Pattern for "go to <URL>" or "open <URL>"
            (re.compile(r"^(?:go\s+to|open)\s+(?P<url>\S+\.\S+.*)$", re.IGNORECASE), "goto"),
            # Pattern for "search for <QUERY>" or "search <QUERY>" (web search)
            (re.compile(r"^(?:web\s+)?search(?:\s+for)?\s+(?P<query>.+)$", re.IGNORECASE), "web_search"),
            # Pattern for "find file <PATTERN> (in <PATH>)"
            (re.compile(r"^find\s+file\s+(?P<pattern>\S+)(?:\s+in\s+(?P<path>.+))?$", re.IGNORECASE), "find_file"),
            # Pattern for "read file <FILEPATH>" or "read book <FILEPATH>"
            (re.compile(r"^(?:read\s+file|read\s+book)\s+(?P<filepath>.+)$", re.IGNORECASE), "read_file"),
            # Pattern for "make notes from <FILEPATH> (to <OUTPUT_FILEPATH>) (titled <TITLE>)"
            # All parts after "from" are optional for now, but "from" is key.
            (re.compile(
                r"^make\s+notes\s+from\s+(?P<source_filepath>.+?)"
                r"(?:\s+to\s+(?P<output_filepath>.+?))?"
                r"(?:\s+titled\s+(?P<title>.+))?$", re.IGNORECASE), "make_notes"),
        ]

    def parse_command(self, command_text: str) -> dict | None:
        """
        Parses the command text and returns a structured command dictionary
        or None if the command is not recognized.

        Example output:
        {'action': 'goto', 'url': 'example.com'}
        {'action': 'search', 'query': 'python programming'}
        """
        for pattern, action_type in self.command_patterns:
            match = pattern.match(command_text.strip())
            if match:
                if action_type == "goto":
                    url = match.group("url")
                    # Basic URL validation or cleaning could be added here
                    # For now, just ensure it's not empty
                    if url:
                        return {"action": "goto", "url": url}
                elif action_type == "web_search":
                    query = match.group("query")
                    if query: # Ensure query is not empty
                        return {"action": "web_search", "query": query}
                elif action_type == "find_file":
                    pattern = match.group("pattern")
                    path = match.group("path") # This can be None if not provided
                    if pattern:
                        return {"action": "find_file", "pattern": pattern, "path": path.strip() if path else None}
                elif action_type == "read_file":
                    filepath = match.group("filepath")
                    if filepath:
                        # Remove potential quotes around filepath if user adds them
                        filepath = filepath.strip().strip('\'"')
                        return {"action": "read_file", "filepath": filepath}
                elif action_type == "make_notes":
                    source_filepath = match.group("source_filepath").strip().strip('\'"')
                    output_filepath = match.group("output_filepath")
                    title = match.group("title")

                    if source_filepath:
                        return {
                            "action": "make_notes",
                            "source_filepath": source_filepath,
                            "output_filepath": output_filepath.strip().strip('\'"') if output_filepath else None,
                            "title": title.strip().strip('\'"') if title else None
                        }

        print(f"Command not recognized: {command_text}")
        return None

# Example Usage (for testing this module directly)
if __name__ == "__main__":
    parser = CommandParser()

    commands_to_test = [
        "go to example.com",
        "open google.com",
        "web search for latest python news",
        "search how to learn playwright", # Should still work as web_search due to regex
        "go to https://playwright.dev",
        "open my_website.co.uk/path",
        "web search for cats and dogs",
        "find file *.txt",
        "find file report.docx in C:\\Users\\Me\\Documents",
        "find file image.png in /tmp/my_stuff",
        "read file C:\\My Documents\\notes.txt",
        "read book /path/to/my/book.txt",
        "read file \"D:\\Folder With Spaces\\file.txt\"",
        "make notes from my_document.txt",
        "make notes from \"another document.txt\" to my_notes.md",
        "make notes from important_lecture.txt titled \"Lecture Highlights\"",
        "make notes from research_paper.pdf to research_summary.txt titled \"Paper Summary\"",
        "random command that should not match",
        "open",
        "search", # This alone won't match web_search without a query
        "find file", # Incomplete
        "read file", # Incomplete
        "go to ",
        "make notes from", # Incomplete
    ]

    for cmd in commands_to_test:
        parsed = parser.parse_command(cmd)
        if parsed:
            print(f"Input: '{cmd}' -> Parsed: {parsed}")
        else:
            print(f"Input: '{cmd}' -> Not recognized")

    # Test specific cases
    print("\nTesting URL extraction:")
    parsed_url = parser.parse_command("go to my.new-domain.com/path?query=123")
    print(f"Input: 'go to my.new-domain.com/path?query=123' -> Parsed: {parsed_url}")

    parsed_url_https = parser.parse_command("open https://sub.domain.co.uk")
    print(f"Input: 'open https://sub.domain.co.uk' -> Parsed: {parsed_url_https}")

    print("\nTesting query extraction:")
    parsed_search = parser.parse_command("search complex query with multiple words & symbols!")
    print(f"Input: 'search complex query with multiple words & symbols!' -> Parsed: {parsed_search}")
