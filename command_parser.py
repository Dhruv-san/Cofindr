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
            # Pattern for "search for <QUERY>" or "search <QUERY>"
            (re.compile(r"^search(?:\s+for)?\s+(?P<query>.+)$", re.IGNORECASE), "search"),
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
                elif action_type == "search":
                    query = match.group("query")
                    if query: # Ensure query is not empty
                        return {"action": "search", "query": query}

        print(f"Command not recognized: {command_text}")
        return None

# Example Usage (for testing this module directly)
if __name__ == "__main__":
    parser = CommandParser()

    commands_to_test = [
        "go to example.com",
        "open google.com",
        "search for latest python news",
        "search how to learn playwright",
        "go to https://playwright.dev",
        "open my_website.co.uk/path",
        "search for cats and dogs",
        "random command that should not match",
        "open", # Should not match
        "search", # Should not match
        "go to ", # Should not match
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
