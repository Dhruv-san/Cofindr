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

        elif action == "copy_item":
            source = structured_command.get("source")
            destination = structured_command.get("destination")
            if source and destination:
                self.os_interaction_module.copy_item(source, destination)
            else:
                print("Dispatcher: 'copy_item' action missing source or destination.")

        elif action == "move_item":
            source = structured_command.get("source")
            destination = structured_command.get("destination")
            if source and destination:
                self.os_interaction_module.move_item(source, destination)
            else:
                print("Dispatcher: 'move_item' action missing source or destination.")

        elif action == "delete_item":
            path_to_delete = structured_command.get("path")
            confirmed_in_cmd = structured_command.get("confirmed_in_command", False) # Default to False

            if path_to_delete:
                if confirmed_in_cmd:
                    # User typed "delete ... with confirmation yes"
                    print(f"Dispatcher: Deleting '{path_to_delete}' based on command confirmation.")
                    self.os_interaction_module.delete_item(path_to_delete, require_confirmation=False)
                else:
                    # Default behavior: check if confirmation is needed from module.
                    # In a real UI, this is where we'd prompt the user.
                    # For now, we'll simulate the first call that just checks.
                    print(f"Dispatcher: Checking if confirmation needed for delete '{path_to_delete}'.")
                    _success, needs_confirmation_flag = self.os_interaction_module.delete_item(path_to_delete, require_confirmation=True)
                    if needs_confirmation_flag:
                        # This is where a real agent would ask user: "Are you sure you want to delete X? (yes/no)"
                        # For this test script, we'll just log it.
                        # If running main_agent, the UI would handle this.
                        print(f"Dispatcher: USER CONFIRMATION REQUIRED to delete '{path_to_delete}'. (Simulated: Not deleting yet).")
                        # To actually delete in a test like this, one might add a follow-up simulated command,
                        # or the test setup would call delete_item(..., require_confirmation=False)
                    # else: item didn't exist or some other issue, os_interaction_module already printed.
            else:
                print("Dispatcher: 'delete_item' action missing path.")

        elif action == "launch_app":
            application = structured_command.get("application")
            args = structured_command.get("args", []) # Default to empty list
            if application:
                self.os_interaction_module.launch_application(application, args)
            else:
                print("Dispatcher: 'launch_app' action missing application name/path.")

        elif action == "notepad_note":
            title = structured_command.get("title")
            content = structured_command.get("content")
            if title is not None and content is not None: # Both must be present, though can be empty strings
                self.os_interaction_module.create_note_in_notepad(title=title, content=content)
            else:
                print("Dispatcher: 'notepad_note' action missing title or content.")

        elif action == "create_word_doc":
            filepath = structured_command.get("filepath")
            title = structured_command.get("title") # Can be None
            content = structured_command.get("content")
            if filepath and content is not None:
                self.os_interaction_module.create_word_document(
                    filepath=filepath,
                    title=title,
                    content=content
                )
            else:
                print("Dispatcher: 'create_word_doc' action missing filepath or content.")

        elif action == "rename_item":
            current_path = structured_command.get("current_path")
            new_path = structured_command.get("new_path")
            if current_path and new_path:
                self.os_interaction_module.rename_item(current_path, new_path)
            else:
                print("Dispatcher: 'rename_item' action missing current_path or new_path.")

        elif action == "get_cpu_usage":
            cpu_usage = self.os_interaction_module.get_cpu_usage()
            if cpu_usage is not None:
                print(f"Dispatcher: CPU Usage: {cpu_usage}%")
            # os_interaction_module already prints errors if any

        elif action == "get_memory_info":
            memory_info = self.os_interaction_module.get_memory_info()
            if memory_info:
                print(f"Dispatcher: Memory Info: Total={memory_info.get('total_gb')}GB, Available={memory_info.get('available_gb')}GB, Used={memory_info.get('percent_used')}%")

        elif action == "list_processes":
            processes = self.os_interaction_module.get_active_processes()
            if processes:
                print(f"Dispatcher: Active Processes (first 5 of {len(processes)}):")
                for p in processes[:5]: # Print first 5 for brevity
                    print(f"  - PID: {p['pid']}, Name: {p['name']}, CPU: {p.get('cpu_percent', 'N/A')}%")
            # os_interaction_module already prints if list is empty or error

        elif action == "run_script":
            script_path = structured_command.get("script_path")
            args = structured_command.get("args", [])
            if script_path:
                result = self.os_interaction_module.execute_script(script_path, args)
                print(f"Dispatcher: Script execution result for '{script_path}':")
                print(f"  Success: {result['success']}")
                print(f"  Return Code: {result['returncode']}")
                if result['stdout']: print(f"  STDOUT:\n{result['stdout']}")
                if result['stderr']: print(f"  STDERR:\n{result['stderr']}")
            else:
                print("Dispatcher: 'run_script' action missing script_path.")

        # Refined delete_item handling for testing (will call twice if confirmation needed)
        elif action == "delete_item": # Ensure this is processed AFTER other specific commands
            path_to_delete = structured_command.get("path")
            confirmed_in_cmd = structured_command.get("confirmed_in_command", False)

            if path_to_delete:
                if confirmed_in_cmd:
                    print(f"Dispatcher: Deleting '{path_to_delete}' based on command confirmation.")
                    self.os_interaction_module.delete_item(path_to_delete, require_confirmation=False)
                else:
                    print(f"Dispatcher: Checking if confirmation needed for delete '{path_to_delete}'.")
                    _success, needs_confirmation_flag = self.os_interaction_module.delete_item(path_to_delete, require_confirmation=True)
                    if needs_confirmation_flag:
                        print(f"Dispatcher: USER CONFIRMATION REQUIRED to delete '{path_to_delete}'. Simulating 'yes' for test.")
                        # Simulate user saying "yes" by calling again with require_confirmation=False
                        self.os_interaction_module.delete_item(path_to_delete, require_confirmation=False)
                    # else: item didn't exist or other issue, os_interaction_module already printed.
            else:
                print("Dispatcher: 'delete_item' action missing path.")

        else: # This should be the final else
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
    (test_dir / "report_final.pdf").write_text("PDF content (pretend).") # For find/read tests

    source_note_file = test_dir / "source_for_notes.txt" # For make_notes tests
    source_note_file.write_text("This is the source file from which notes will be made.\nIt has multiple lines.\nThis is the third line, which might be included in a short note.")

    # Setup for copy/move/delete tests
    os_ops_source_dir = test_dir / "os_ops_source"
    os_ops_source_dir.mkdir(exist_ok=True)
    (os_ops_source_dir / "file_A.txt").write_text("Content of File A for OS Ops.")
    (os_ops_source_dir / "file_B.txt").write_text("Content of File B for OS Ops.")
    folder_X = os_ops_source_dir / "FolderX"
    folder_X.mkdir(exist_ok=True)
    (folder_X / "file_X1.txt").write_text("Content of File X1 in FolderX.")

    os_ops_dest_dir = test_dir / "os_ops_destination"
    # os_ops_dest_dir.mkdir(exist_ok=True) # Create if needed for some tests, or let ops create.

    # Dummy script for run_script test
    dummy_py_script_for_dispatcher = test_dir / "dispatcher_test_script.py"
    dummy_py_script_for_dispatcher.write_text(
        "import sys\nprint(f'Script says hello! Args: {sys.argv[1:]}')\nsys.exit(0)"
    )

    test_commands = [
        # Web ops
        "go to google.com",
        "web search for python async",
        # File find/read/make_notes from previous tests
        f"find file *.txt in {str(test_dir.resolve())}",
        f"find file report_final.pdf in {str(test_dir.resolve())}",
        "find file non_existent_pattern.dat", # Will search home dir
        f"read file {str((test_dir / 'sample.txt').resolve())}",
        f"read file {str((test_dir / 'report_final.pdf').resolve())}", # Test reading non-txt
        "read file /path/to/a/file/that/doesnt/exist.txt",
        f"make notes from {str(source_note_file.resolve())}", # Default output and title
        f"make notes from {str(source_note_file.resolve())} to {str(test_dir / 'custom_notes.md')}", # Custom output, default title
        f"make notes from {str(source_note_file.resolve())} titled \"My Custom Note Title\"", # Default output, custom title
        f"make notes from {str(source_note_file.resolve())} to {str(test_dir / 'final_notes.txt')} titled \"Final Lecture Notes\"",
        "make notes from /path/to/non_existent_source.txt",
        # OS commands
        f"copy {str(os_ops_source_dir / 'file_A.txt')} to {str(os_ops_dest_dir / 'file_A_copied.txt')}",
        f"copy {str(folder_X)} to {str(os_ops_dest_dir / 'FolderX_copied')}",
        f"move {str(os_ops_source_dir / 'file_B.txt')} to {str(os_ops_dest_dir / 'file_B_moved.txt')}",
        "launch notepad.exe",
        "launch app_that_doesnt_exist",
        # Notepad note command
        "notepad note title \"Test Note for Dispatcher\" content \"This is content for notepad via dispatcher.\"",
        # Word doc commands
        f"create word doc \"{str(test_dir / 'AgentWordDoc1.docx')}\" content \"This is the first Word doc from agent.\"",
        f"create word doc \"{str(test_dir / 'AgentWordDoc2_titled.docx')}\" title \"My Document Title\" content \"Some interesting content here.\"",

        # New OS commands for rename, sysinfo, run script
        f"rename {str(os_ops_source_dir / 'file_A.txt')} to {str(os_ops_source_dir / 'file_A_renamed.txt')}",
        "get cpu usage",
        "get memory info",
        "list active processes",
        f"run script {str(dummy_py_script_for_dispatcher)} with arguments test_arg1 test_arg2",
        # Delete test commands (will be handled carefully, likely via direct dispatch or specific setup)
        # Example: "delete temp_dispatcher_test_files/os_ops_source/file_A_renamed.txt"
        # Note: For sequential command list, ensure dependent operations are logical.
        # We will test delete more robustly via direct dispatch.
        "delete temp_dispatcher_test_files/os_ops_source/no_such_file.txt with confirmation yes", # test delete non-existent

        # End of regular test commands
        "fly to the moon", # Unrecognized
        "find file *.log" # Test finding in home directory (can be many) - can be slow
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
        {'action': 'find_file', 'pattern': '*.py', 'path': '.'},
        {'action': 'read_file', 'filepath': str((test_dir / 'sample.txt').resolve())},
        {
            'action': 'make_notes',
            'source_filepath': str(source_note_file.resolve()),
            'output_filepath': str(test_dir / 'direct_dispatch_notes.md'),
            'title': 'Direct Dispatch Note Test'
        },
        # Specific OS ops for direct dispatch test
        # Setup for a direct delete test
        {'action': 'delete_item', 'path': str(os_ops_source_dir / "file_to_delete_directly.txt"), 'confirmed_in_command': True},
        # Launch test (ls should work on Linux/Codespaces)
        {'action': 'launch_app', 'application': 'ls', 'args': ['-la', str(test_dir)]},
        # Specific delete tests for dispatcher logic
        {'action': 'delete_item', 'path': str(os_ops_source_dir / "file_for_dispatch_delete_confirm_yes.txt"), 'confirmed_in_command': True},
        {'action': 'delete_item', 'path': str(os_ops_source_dir / "file_for_dispatch_delete_no_confirm.txt"), 'confirmed_in_command': False}, # Dispatcher will simulate "yes"
        # Specific run_script test
        {'action': 'run_script', 'script_path': str(dummy_py_script_for_dispatcher), 'args': ['dispatch_arg']}
    ]

    # Create files for the direct delete tests
    (os_ops_source_dir / "file_for_dispatch_delete_confirm_yes.txt").write_text("Delete me with cmd confirm.")
    (os_ops_source_dir / "file_for_dispatch_delete_no_confirm.txt").write_text("Delete me with dispatcher confirm.")


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
