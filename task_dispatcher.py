# Assuming browser_interaction.py, command_parser.py, os_interaction.py are in the same directory
from browser_interaction import BrowserManager
from os_interaction import OSInteractionModule
# CommandParser isn't directly used by dispatcher, but dispatcher acts on its output.

import asyncio

class TaskDispatcher:
    """
    Dispatches tasks to the appropriate modules based on parsed commands.
    """
    def __init__(self, browser_manager: BrowserManager, os_interaction_module: OSInteractionModule):
        self.browser_manager = browser_manager
        self.os_interaction_module = os_interaction_module

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
        elif action == "web_search":
            query = structured_command.get("query")
            if query:
                await self.browser_manager.search_web(query)
            else:
                print("Dispatcher: 'web_search' action missing query.")
        elif action == "find_file":
            pattern = structured_command.get("pattern")
            path = structured_command.get("path") # Can be None
            if pattern:
                # This is a synchronous function, but dispatcher is async.
                # For now, run it directly. If it becomes long-running, consider asyncio.to_thread
                found_files = self.os_interaction_module.find_files(name_pattern=pattern, search_path=path)
                # For now, just print. UI would need a way to display this.
                print(f"Dispatcher: Found files for pattern '{pattern}' in path '{path}': {found_files}")
            else:
                print("Dispatcher: 'find_file' action missing pattern.")
        elif action == "read_file":
            filepath = structured_command.get("filepath")
            if filepath:
                # Also synchronous for now
                content = self.os_interaction_module.read_file_content(filepath=filepath)
                if content is not None:
                    # For now, print a snippet. Actual use would need UI display or further processing.
                    print(f"Dispatcher: Content of '{filepath}' (first 200 chars):\n{content[:200]}")
                    if len(content) > 200:
                        print("...")
                # If content is None, os_interaction_module already printed an error
            else:
                print("Dispatcher: 'read_file' action missing filepath.")
        elif action == "make_notes":
            source_filepath = structured_command.get("source_filepath")
            output_filepath = structured_command.get("output_filepath")
            title = structured_command.get("title")

            if not source_filepath:
                print("Dispatcher: 'make_notes' action missing source_filepath.")
                return

            # 1. Read source file content
            source_content = self.os_interaction_module.read_file_content(filepath=source_filepath, max_chars=1000) # Read up to 1000 chars for notes

            if source_content is None:
                print(f"Dispatcher: Could not read source file '{source_filepath}' for note making.")
                return

            # 2. Basic note generation (e.g., first 500 chars, or a summary if we had one)
            # For now, the note content IS the (potentially truncated) source content.
            # A more sophisticated approach would summarize or select key points.
            note_body = source_content
            if len(source_content) == 1000: # If content was truncated
                note_body += "\n... (content truncated for note)"


            # 3. Determine output filepath
            if output_filepath is None:
                # Default output file: agent_notes.md in user's home or documents.
                # For simplicity here, let's use a fixed name in the current directory if not specified.
                # A better default would involve Path.home() / "Documents" / "agent_notes.md"
                # This should be improved for robustness (e.g. ensure "Documents" exists)
                from pathlib import Path
                # For testing, let's default to current dir to avoid writing to user's actual home/docs
                # during component tests.
                # In main_agent.py, a better default path strategy would be used.
                # Let's implement the better default path strategy here now.
                from pathlib import Path
                try:
                    # Try to use ~/Documents/AgentNotes/agent_notes.md
                    # On Windows, Path.home() / "Documents" is typical.
                    # On Linux, it's often Path.home() / "Documents" as well, or just Path.home().
                    # For simplicity and Windows target, we'll assume "Documents" exists or can be inferred.
                    docs_dir_name = "Documents"
                    home_path = Path.home()
                    documents_path = home_path / docs_dir_name

                    # Check if "Documents" directory actually exists, if not, use home.
                    # This is a basic check; more robust would be OS-specific API calls.
                    if not documents_path.is_dir():
                        print(f"Dispatcher: '{documents_path}' not found or not a directory. Using home directory as base for notes.")
                        documents_path = home_path # Fallback to home if "Documents" isn't there

                    agent_notes_dir = documents_path / "AgentNotes"
                    agent_notes_dir.mkdir(parents=True, exist_ok=True) # Create if not exists
                    output_filepath = agent_notes_dir / "agent_notes.md"
                    print(f"Dispatcher: No output filepath specified for notes, defaulting to '{output_filepath}'.")
                except Exception as path_e:
                    print(f"Dispatcher: Error creating default notes path: {path_e}. Defaulting to CWD.")
                    output_filepath = "agent_generated_notes.md" # Fallback to CWD
                    print(f"Dispatcher: Using fallback default notes path: '{output_filepath}'.")

            # 4. Determine title for the note
            actual_title = title
            if actual_title is None:
                # Default title from source filename
                from pathlib import Path
                actual_title = Path(source_filepath).name

            # 5. Save the note
            success = self.os_interaction_module.save_note_to_file(
                note_content=note_body,
                output_filepath=output_filepath,
                title=actual_title
            )
            if success:
                print(f"Dispatcher: Successfully processed 'make_notes' for '{source_filepath}' into '{output_filepath}'.")
                print(f"Dispatcher: Note content is an excerpt from the source file (up to 1000 characters).")
            else:
                print(f"Dispatcher: Failed to save notes for '{source_filepath}'.")
        else:
            print(f"Dispatcher: Unknown action type '{action}'. No module to handle it.")

# Example Usage (for testing the dispatcher with other modules)
async def main_test():
    # We need an instance of CommandParser to generate input for the dispatcher
    from command_parser import CommandParser # Local import for testing
    # We also need OSInteractionModule for the new commands
    from os_interaction import OSInteractionModule # Local import for testing

    parser = CommandParser()
    browser_mgr = BrowserManager()
    os_module = OSInteractionModule()

    # The dispatcher now needs both manager instances
    # dispatcher = TaskDispatcher(browser_manager=browser_mgr, os_interaction_module=os_module)
    # This global dispatcher will be used by the test logic below, defined at the end of the file.

    # Create dummy files for os interaction tests
    test_dir = Path("temp_dispatcher_test_files")
    test_dir.mkdir(exist_ok=True)
    (test_dir / "sample.txt").write_text("This is a sample text file for dispatcher testing. It has enough content to be truncated for note-making if the limit is small. Let's add more lines. Line 2. Line 3. Line 4. Line 5. This should definitely be more than a few characters, allowing us to test truncation. The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. This is a very long line to ensure we hit the 1000 character limit for notes if possible and see the truncation message in action during the test run. We need a lot of text to verify this particular feature of the note-making process. Adding even more filler text to be absolutely sure. One two three four five six seven eight nine ten. Eleven twelve thirteen fourteen fifteen. Sixteen seventeen eighteen nineteen twenty. This should be plenty.")
    (test_dir / "another_doc.txt").write_text("Another document here.")
    (test_dir / "report_final.pdf").write_text("PDF content (pretend).")
    source_note_file = test_dir / "source_for_notes.txt"
    source_note_file.write_text("This is the source file from which notes will be made.\nIt has multiple lines.\nThis is the third line, which might be included in a short note.")

    test_commands = [
        "go to google.com",
        "web search for python async",
        f"find file *.txt in {str(test_dir.resolve())}",
        f"find file report_final.pdf in {str(test_dir.resolve())}",
        "find file non_existent_pattern.dat", # Will search home dir
        f"read file {str((test_dir / 'sample.txt').resolve())}",
        f"read file {str((test_dir / 'report_final.pdf').resolve())}", # Test reading non-txt
        "read file /path/to/a/file/that/doesnt/exist.txt",
        f"make notes from {str(source_note_file.resolve())}", # Default output and title
        f"make notes from {str(source_note_file.resolve())} to {str(test_dir / 'custom_notes.md')}", # Custom output, default title
        f"make notes from {str(source_note_file.resolve())} titled \"My Custom Note Title\"", # Default output, custom title
        f"make notes from {str(source_note_file.resolve())} to {str(test_dir / 'final_notes.txt')} titled \"Final Lecture Notes\"", # All custom
        "make notes from /path/to/non_existent_source.txt", # Test non-existent source
        "fly to the moon", # Unrecognized
        "find file *.log" # Test finding in home directory (can be many)
    ]

    print("--- Starting Task Dispatcher Test ---")
    for cmd_text in test_commands:
        print(f"\nProcessing raw command: '{cmd_text}'")
        structured_cmd = parser.parse_command(cmd_text)
        if structured_cmd:
            # Use the global dispatcher instance for the test
            await dispatcher.dispatch(structured_cmd)
            if structured_cmd.get("action") in ["goto", "web_search"]:
                 await asyncio.sleep(1) # Pause for browser actions
            else:
                await asyncio.sleep(0.1) # Shorter pause for OS actions
        else:
            print(f"Command '{cmd_text}' was not recognized by parser, not dispatched.")

    print("\n--- Testing direct dispatch with valid structured commands (including OS) ---")
    valid_structured_commands = [
        {'action': 'goto', 'url': 'dev.to'},
        {'action': 'web_search', 'query': 'python tkinter tutorial'},
        {'action': 'find_file', 'pattern': '*.py', 'path': '.'}, # Find .py files in current dir
        {'action': 'read_file', 'filepath': str((test_dir / 'sample.txt').resolve())},
        {
            'action': 'make_notes',
            'source_filepath': str(source_note_file.resolve()),
            'output_filepath': str(test_dir / 'direct_dispatch_notes.md'),
            'title': 'Direct Dispatch Note Test'
        }
    ]
    for s_cmd in valid_structured_commands:
        print(f"\nDispatching structured command: {s_cmd}")
        await dispatcher.dispatch(s_cmd)
        if s_cmd.get("action") in ["goto", "web_search"]:
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(0.1)


    # Important: Close the browser manager when done with all tasks
    await browser_mgr.close()

    # Clean up dummy files for dispatcher test
    import shutil
    try:
        shutil.rmtree(test_dir)
        print(f"\nCleaned up temporary dispatcher test directory: {test_dir}")
    except Exception as e:
        print(f"Error cleaning up dispatcher test directory: {e}")

    print("--- Task Dispatcher Test Finished ---")

if __name__ == "__main__":
    # For the test, create instances of all managers/modules the dispatcher needs
    browser_manager_instance = BrowserManager()
    os_interaction_instance = OSInteractionModule()

    # Global dispatcher instance for the test function main_test to use
    dispatcher = TaskDispatcher(
        browser_manager=browser_manager_instance,
        os_interaction_module=os_interaction_instance
    )

    # pathlib.Path needed for main_test's setup
    from pathlib import Path
    asyncio.run(main_test())
