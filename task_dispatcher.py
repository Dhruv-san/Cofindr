# Assuming browser_interaction.py and command_parser.py are in the same directory
from browser_interaction import BrowserManager
# CommandParser isn't directly used by dispatcher, but dispatcher acts on its output.

import asyncio

class TaskDispatcher:
    """
    Dispatches tasks to the appropriate modules based on parsed commands.
    """
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager

    async def dispatch(self, structured_command: dict | None):
        """
        Dispatches the command to the relevant module.

        :param structured_command: A dictionary from CommandParser,
                                   e.g., {'action': 'goto', 'url': 'example.com'}
                                   or {'action': 'search', 'query': 'python programming'}
        """
        if not structured_command or "action" not in structured_command:
            print("Dispatcher: Invalid or empty command received.")
            return

        action = structured_command["action"]
        print(f"Dispatcher: Received action '{action}' with params {structured_command}")

        if action == "goto":
            url = structured_command.get("url")
            if url:
                await self.browser_manager.open_url(url)
            else:
                print("Dispatcher: 'goto' action missing URL.")
        elif action == "search":
            query = structured_command.get("query")
            if query:
                await self.browser_manager.search_web(query)
            else:
                print("Dispatcher: 'search' action missing query.")
        else:
            print(f"Dispatcher: Unknown action type '{action}'. No module to handle it.")

# Example Usage (for testing the dispatcher with other modules)
async def main_test():
    # We need an instance of CommandParser to generate input for the dispatcher
    from command_parser import CommandParser # Local import for testing

    parser = CommandParser()
    browser_mgr = BrowserManager() # BrowserManager will be initialized on first use

    test_commands = [
        "go to bbc.co.uk",
        "search for asyncio playwright",
        "open nonexistentsite", # BrowserManager will handle this error
        "search", # Parser will return None for this
        "fly to the moon" # Parser will return None for this
    ]

    print("--- Starting Task Dispatcher Test ---")
    for cmd_text in test_commands:
        print(f"\nProcessing raw command: '{cmd_text}'")
        structured_cmd = parser.parse_command(cmd_text)
        if structured_cmd:
            await dispatcher.dispatch(structured_cmd)
            await asyncio.sleep(1) # Pause to observe browser actions if any
        else:
            print(f"Command '{cmd_text}' was not recognized by parser, not dispatched.")

    print("\n--- Testing direct dispatch with valid structured commands ---")
    valid_structured_commands = [
        {'action': 'goto', 'url': 'dev.to'},
        {'action': 'search', 'query': 'python tkinter tutorial'}
    ]
    for s_cmd in valid_structured_commands:
        print(f"\nDispatching structured command: {s_cmd}")
        await dispatcher.dispatch(s_cmd)
        await asyncio.sleep(1)

    # Important: Close the browser manager when done with all tasks
    await browser_mgr.close()
    print("--- Task Dispatcher Test Finished ---")

if __name__ == "__main__":
    # Setup for the test
    dispatcher = TaskDispatcher(BrowserManager()) # Create a BrowserManager instance for the dispatcher

    # In a real app, the BrowserManager might be a singleton or passed around.
    # The dispatcher itself doesn't create it, it expects one.

    asyncio.run(main_test())
