import os
import glob
from pathlib import Path

class OSInteractionModule:
    """
    Handles interactions with the operating system, like file system operations.
    """

    def find_files(self, name_pattern: str, search_path: str = None) -> list[str]:
        """
        Finds files matching a name pattern within a given search path.
        Uses glob for pattern matching. Recursively searches subdirectories.

        :param name_pattern: The pattern to search for (e.g., "*.txt", "report.*").
        :param search_path: The directory to start searching from.
                             If None, defaults to the user's home directory.
        :return: A list of absolute paths to matching files.
        """
        if search_path is None:
            search_path = str(Path.home()) # Default to user's home directory
            print(f"No search path provided, defaulting to home directory: {search_path}")

        if not os.path.isdir(search_path):
            print(f"Error: Search path '{search_path}' is not a valid directory.")
            return []

        found_files = []
        try:
            # Construct a recursive glob pattern
            # For example, if search_path is /Users/Me and name_pattern is *.txt,
            # glob_pattern will be /Users/Me/**/*.txt
            glob_pattern = os.path.join(search_path, "**", name_pattern)

            print(f"Searching for pattern '{name_pattern}' in '{search_path}' (recursive). Glob pattern: '{glob_pattern}'")

            # glob.glob with recursive=True (or using **) finds files in subdirectories
            # We need to ensure the path is absolute for consistency
            for filepath in glob.glob(glob_pattern, recursive=True):
                found_files.append(os.path.abspath(filepath))

            if not found_files:
                print(f"No files found matching pattern '{name_pattern}' in '{search_path}'.")
            else:
                print(f"Found {len(found_files)} file(s):")
                for f in found_files:
                    print(f"  - {f}")

        except Exception as e:
            print(f"Error during file search: {e}")
            return []

        return found_files

    def read_file_content(self, filepath: str, max_chars: int = None) -> str | None:
        """
        Reads the text content of a specified file.
        Initially supports .txt files.

        :param filepath: The absolute path to the file.
        :param max_chars: Optional: Maximum number of characters to read from the beginning of the file.
        :return: The file content as a string, or None if an error occurs or file is not supported.
        """
        print(f"Attempting to read file: {filepath}")
        try:
            if not os.path.exists(filepath):
                print(f"Error: File not found at '{filepath}'.")
                return None
            if not os.path.isfile(filepath):
                print(f"Error: Path '{filepath}' is not a file.")
                return None

            # For now, let's assume text files.
            # A more robust solution would check MIME types or have specific handlers.
            # Simple extension check for this phase.
            if not filepath.lower().endswith(".txt"):
                print(f"Warning: Reading non-.txt file '{filepath}'. Attempting as plain text.")
                # We can decide later if we want to strictly limit to .txt or try others.

            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                if max_chars is not None and max_chars > 0:
                    content = f.read(max_chars)
                    if len(content) == max_chars:
                        print(f"Read first {max_chars} characters from '{filepath}'.")
                    else:
                        print(f"Read full content (less than {max_chars} chars) from '{filepath}'.")
                else:
                    content = f.read()
                    print(f"Successfully read full content from '{filepath}'.")
                return content
        except UnicodeDecodeError:
            print(f"Error: Could not decode file '{filepath}' as UTF-8 text. It might be a binary file or use a different encoding.")
            return None
        except Exception as e:
            print(f"Error reading file '{filepath}': {e}")
            return None

    def save_note_to_file(self, note_content: str, output_filepath: str, title: str = None) -> bool:
        """
        Saves (appends) the provided note content to the specified file.
        Creates the file if it doesn't exist.
        Prepends a title and timestamp if a title is provided.

        :param note_content: The main content of the note.
        :param output_filepath: The path to the file where the note should be saved.
        :param title: Optional title for the note section (e.g., derived from source filename).
        :return: True if successful, False otherwise.
        """
        print(f"Attempting to save note to file: {output_filepath}")
        try:
            # Ensure the directory for the output file exists
            output_dir = os.path.dirname(output_filepath)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"Created directory: {output_dir}")

            entry_to_write = ""
            if title:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry_to_write += f"## Notes for: {title}\n"
                entry_to_write += f"Date: {timestamp}\n"
                entry_to_write += "---\n"

            entry_to_write += note_content + "\n\n---\n\n" # Add separators

            with open(output_filepath, 'a', encoding='utf-8') as f: # 'a' for append
                f.write(entry_to_write)

            print(f"Successfully appended note to: {output_filepath}")
            return True
        except Exception as e:
            print(f"Error saving note to file '{output_filepath}': {e}")
            return False

    def copy_item(self, source_path: str, destination_path: str) -> bool:
        """
        Copies a file or directory from source_path to destination_path.
        If destination_path is a directory, the item is copied inside it.
        If destination_path is a full path (including filename for files), it's copied to that exact path.
        Overwrites if destination file exists. Creates destination directories if they don't exist.

        :param source_path: Path to the source file or directory.
        :param destination_path: Path to the destination file or directory.
        :return: True if successful, False otherwise.
        """
        print(f"Attempting to copy '{source_path}' to '{destination_path}'")
        import shutil
        try:
            if not os.path.exists(source_path):
                print(f"Error: Source path '{source_path}' does not exist.")
                return False

            # Ensure destination directory exists if destination_path is a full file path
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.basename(destination_path) == "": # i.e. dest_path is not just a dir like "folder/"
                 if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                    print(f"Created destination directory: {dest_dir}")
            elif not dest_dir and os.path.basename(destination_path) == "" and not os.path.exists(destination_path): #e.g. copying to "new_folder/"
                os.makedirs(destination_path)
                print(f"Created destination directory: {destination_path}")


            if os.path.isdir(source_path):
                # If destination is an existing directory, copy source_path *into* it
                if os.path.isdir(destination_path):
                    shutil.copytree(source_path, os.path.join(destination_path, os.path.basename(source_path)), dirs_exist_ok=True)
                else: # If destination is a new directory name or if it's a file (which shutil.copytree handles by replacing)
                    shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
            else: # It's a file
                shutil.copy2(source_path, destination_path) # copy2 preserves metadata

            print(f"Successfully copied '{source_path}' to '{destination_path}'.")
            return True
        except Exception as e:
            print(f"Error copying '{source_path}' to '{destination_path}': {e}")
            return False

    def move_item(self, source_path: str, destination_path: str) -> bool:
        """
        Moves a file or directory from source_path to destination_path.
        Behavior is similar to the 'mv' command in Linux.
        If destination_path is a directory, the item is moved inside it.
        If destination_path is a full path, it renames/moves to that exact path.
        Overwrites if destination file exists (shutil.move behavior).
        Creates destination directories if they don't exist for the final target.

        :param source_path: Path to the source file or directory.
        :param destination_path: Path to the destination.
        :return: True if successful, False otherwise.
        """
        print(f"Attempting to move '{source_path}' to '{destination_path}'")
        import shutil
        try:
            if not os.path.exists(source_path):
                print(f"Error: Source path '{source_path}' does not exist for move operation.")
                return False

            # Ensure destination directory exists if destination_path is a full file path (not just a dir)
            # shutil.move can often handle creating the final directory component if it's part of a rename,
            # but not intermediate directories. Let's be explicit for the parent of the target.
            dest_parent_dir = os.path.dirname(destination_path)
            if dest_parent_dir and not os.path.exists(dest_parent_dir):
                 os.makedirs(dest_parent_dir)
                 print(f"Created destination directory for move: {dest_parent_dir}")

            shutil.move(source_path, destination_path)

            print(f"Successfully moved '{source_path}' to '{destination_path}'.")
            return True
        except Exception as e:
            print(f"Error moving '{source_path}' to '{destination_path}': {e}")
            return False

    def delete_item(self, item_path: str, require_confirmation: bool = True) -> tuple[bool, bool]:
        """
        Deletes a file or directory.

        :param item_path: Path to the file or directory to delete.
        :param require_confirmation: If True, the method will not delete but indicate
                                     that confirmation is needed. If False, it deletes directly.
                                     This parameter is for the module's internal logic;
                                     actual user confirmation should be handled by the caller.
        :return: A tuple (success: bool, confirmation_was_required_and_pending: bool).
                 - If require_confirmation is True and item exists: (False, True) -> needs confirmation.
                 - If require_confirmation is False and deletion succeeds: (True, False).
                 - If deletion fails for other reasons: (False, False).
                 - If item does not exist: (False, False) with an error message.
        """
        print(f"Attempting to delete '{item_path}' (require_confirmation={require_confirmation})")
        import shutil
        try:
            if not os.path.exists(item_path):
                print(f"Error: Path '{item_path}' does not exist. Nothing to delete.")
                return False, False

            if require_confirmation:
                print(f"Confirmation required to delete '{item_path}'. Deletion not performed by this call.")
                return False, True # Indicates confirmation is pending

            # Proceed with deletion if confirmation is not required by this call
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"Successfully deleted directory: {item_path}")
            else: # It's a file
                os.remove(item_path)
                print(f"Successfully deleted file: {item_path}")
            return True, False

        except Exception as e:
            print(f"Error deleting '{item_path}': {e}")
            return False, False

    def launch_application(self, application_name_or_path: str, args: list[str] = None) -> bool:
        """
        Launches an application.

        :param application_name_or_path: The name of the application (if in PATH)
                                         or the full path to the executable.
        :param args: A list of command-line arguments to pass to the application.
        :return: True if launch was attempted successfully (doesn't guarantee app started without errors),
                 False if the command could not be constructed or subprocess failed to start.
        """
        if args is None:
            args = []

        command = [application_name_or_path] + args

        print(f"Attempting to launch application with command: {' '.join(command)}")
        import subprocess
        import sys

        try:
            # For Windows, using shell=True can sometimes help find executables in PATH
            # and handles spaces in paths more naturally if not quoting properly.
            # However, it's generally less secure if command parts are from untrusted input.
            # For now, assuming application_name_or_path is trusted.
            # Popen is non-blocking.
            if sys.platform == "win32":
                # On Windows, subprocess.Popen with shell=False might have trouble if app_name_or_path has spaces
                # and is not an .exe directly, but rather something that needs cmd's help to resolve.
                # For simple .exe calls or full paths, shell=False is fine.
                # Using shell=True for broader compatibility on Windows for finding apps like 'notepad'.
                # If using shell=True, command should be a string.
                subprocess.Popen(" ".join(command), shell=True)
            else: # For Linux/macOS
                subprocess.Popen(command) # shell=False is default and generally safer

            print(f"Successfully launched command for '{application_name_or_path}'. The application should open independently.")
            return True
        except FileNotFoundError:
            print(f"Error: Application not found at '{application_name_or_path}'. Check if it's in PATH or provide full path.")
            return False
        except Exception as e:
            print(f"Error launching application '{application_name_or_path}': {e}")
            return False

    def create_note_in_notepad(self, title: str, content: str, filename_prefix: str = "agent_note") -> bool:
        """
        Creates a temporary text file with the given content and attempts to open it with Notepad.
        This is primarily designed for Windows where 'notepad.exe' is standard.

        :param title: A title used to generate part of the temporary filename (sanitized).
        :param content: The text content to write to the temporary file.
        :param filename_prefix: A prefix for the temporary filename.
        :return: True if the file was created and notepad launch was attempted, False otherwise.
        """
        import tempfile
        import re
        import sys

        # Sanitize title to be part of a filename
        sane_title = re.sub(r'[^\w\-_]', '_', title if title else "untitled")
        temp_filename = f"{filename_prefix}_{sane_title}.txt"

        try:
            with tempfile.NamedTemporaryFile(mode='w+', prefix=f"{filename_prefix}_", suffix=f"_{sane_title}.txt", delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(f"Title: {title}\n\n")
                tmp_file.write(content)
                temp_filepath = tmp_file.name

            print(f"Temporary note content saved to: {temp_filepath}")

            if sys.platform == "win32":
                print(f"Attempting to open '{temp_filepath}' with notepad.exe...")
                # On Windows, notepad.exe should be in PATH.
                # We pass the filepath as an argument to notepad.
                launched = self.launch_application("notepad.exe", [temp_filepath])
                if launched:
                    print(f"Notepad launch attempted. Note should appear in Notepad.")
                    # Note: The temporary file is NOT deleted here. Notepad will have it open.
                    # A more robust solution might manage cleanup later, or save to a non-temp location.
                    # For now, it persists until manually deleted or temp dir cleanup by OS.
                    return True
                else:
                    print(f"Failed to launch Notepad for '{temp_filepath}'.")
                    # Clean up the temp file if notepad couldn't even be launched
                    try: os.remove(temp_filepath) catch: pass
                    return False
            else:
                print(f"Notepad integration is Windows-specific. On {sys.platform}, file saved at '{temp_filepath}' but not opened with Notepad.")
                # On non-Windows, we could try 'xdg-open' or another platform-specific default opener.
                # For now, just indicate it's saved.
                # launched = self.launch_application("xdg-open", [temp_filepath]) # Example for Linux
                return True # Consider it "successful" in terms of file creation for non-Windows test

        except Exception as e:
            print(f"Error creating note for Notepad: {e}")
            return False

    def create_word_document(self, filepath: str, content: str, title: str = None) -> bool:
        """
        Creates a new Word (.docx) document with the given title and content.
        Uses the python-docx library.

        :param filepath: The full path where the .docx file should be saved.
        :param content: The main text content for the document.
        :param title: Optional title to be added as a Heading 1 at the beginning.
        :return: True if document creation was successful, False otherwise.
        """
        print(f"Attempting to create Word document: {filepath}")
        try:
            from docx import Document # python-docx library
            from docx.shared import Inches

            document = Document()

            if title:
                document.add_heading(title, level=1)

            document.add_paragraph(content)

            # Ensure the directory for the output file exists
            output_dir = os.path.dirname(filepath)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"Created directory for Word document: {output_dir}")

            document.save(filepath)
            print(f"Successfully created Word document: {filepath}")
            return True
        except ImportError:
            print("Error: python-docx library not found. Please install it using 'pip install python-docx'.")
            return False
        except Exception as e:
            print(f"Error creating Word document '{filepath}': {e}")
            return False

# Example Usage (for testing this module directly)
if __name__ == "__main__":
    os_interaction = OSInteractionModule()

    print("--- Testing find_files ---")
    # To make this test runnable in various environments, let's create some dummy files.
    # In a real scenario, these files would exist on the user's system.

    # Create a temporary directory structure for testing
    test_dir = Path("temp_os_test_dir")
    test_dir.mkdir(exist_ok=True)
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir(exist_ok=True)

    # Create some test files
    (test_dir / "test_doc1.txt").write_text("This is document 1.")
    (test_dir / "test_report.pdf").write_text("This is a PDF (pretend).") # Content doesn't matter for find
    (sub_dir / "another_test.txt").write_text("Text in subdirectory.")
    (sub_dir / "script.py").write_text("print('hello')")

    print(f"\nSearching for '*.txt' in '{test_dir.resolve()}':")
    txt_files = os_interaction.find_files("*.txt", str(test_dir.resolve()))

    print(f"\nSearching for 'test_*' in '{test_dir.resolve()}':")
    test_star_files = os_interaction.find_files("test_*", str(test_dir.resolve()))

    print(f"\nSearching for '*.py' in '{test_dir.resolve()}':")
    py_files = os_interaction.find_files("*.py", str(test_dir.resolve()))

    print(f"\nSearching for non_existent_pattern in '{test_dir.resolve()}':")
    no_files = os_interaction.find_files("non_existent_pattern", str(test_dir.resolve()))

    print(f"\nSearching in a non-existent path:")
    os_interaction.find_files("*.txt", "path/that/does/not/exist")

    # Test with no path (should default to home, may find many files or be slow, use with caution)
    # print("\nSearching for a common pattern like '*.log' in home directory (might be slow):")
    # log_files_home = os_interaction.find_files("*.log")
    # print(f"Found {len(log_files_home)} .log files in home directory (output suppressed for brevity).")


    print("\n--- Testing read_file_content ---")
    if txt_files:
        print(f"\nReading first found .txt file: {txt_files[0]}")
        content = os_interaction.read_file_content(txt_files[0])
        if content:
            print(f"Content snippet: '{content[:100]}...'")

        print(f"\nReading first 5 chars from .txt file: {txt_files[0]}")
        content_snippet = os_interaction.read_file_content(txt_files[0], max_chars=5)
        if content_snippet:
            print(f"Snippet: '{content_snippet}'")

    if py_files:
        print(f"\nAttempting to read a .py file (as text): {py_files[0]}")
        content_py = os_interaction.read_file_content(py_files[0])
        # if content_py: print(f"Content of .py file: \n{content_py}")

    print("\nAttempting to read a non-existent file:")
    os_interaction.read_file_content("path/to/non_existent_file.txt")

    print("\n--- Testing save_note_to_file ---")
    notes_file_path = test_dir / "my_agent_notes.md"

    # Test 1: Save a simple note
    print(f"\nSaving note 1 to '{notes_file_path}'")
    success1 = os_interaction.save_note_to_file(
        note_content="This is the first note from the agent.",
        output_filepath=str(notes_file_path),
        title="First Test Note"
    )
    if success1 and notes_file_path.exists():
        print(f"Content of '{notes_file_path}':\n{notes_file_path.read_text()[:300]}...\n")

    # Test 2: Append another note to the same file
    print(f"\nSaving note 2 to '{notes_file_path}' (appending)")
    success2 = os_interaction.save_note_to_file(
        note_content="This is a second note, appended to the same file.",
        output_filepath=str(notes_file_path),
        title="Second Test Note (Appended)"
    )
    if success2 and notes_file_path.exists():
        print(f"Updated content of '{notes_file_path}' (showing more):\n{notes_file_path.read_text()}\n")

    # Test 3: Save a note without a title
    notes_no_title_path = test_dir / "notes_no_title.txt"
    print(f"\nSaving note without title to '{notes_no_title_path}'")
    success3 = os_interaction.save_note_to_file(
        note_content="A note that doesn't have a specific title section.",
        output_filepath=str(notes_no_title_path)
    )
    if success3 and notes_no_title_path.exists():
        print(f"Content of '{notes_no_title_path}':\n{notes_no_title_path.read_text()}\n")

    # Test 4: Saving to a path where directory needs to be created
    nested_notes_path = test_dir / "nested_dir" / "deep_notes.md"
    print(f"\nSaving note to a new directory: '{nested_notes_path}'")
    success4 = os_interaction.save_note_to_file(
        note_content="This note should create 'nested_dir'.",
        output_filepath=str(nested_notes_path),
        title="Deep Note"
    )
    if success4 and nested_notes_path.exists():
        print(f"Content of '{nested_notes_path}':\n{nested_notes_path.read_text()}\n")

    print("\n--- Testing copy_item ---")
    # Setup for copy tests
    copy_source_dir = test_dir / "copy_source"
    copy_source_dir.mkdir(exist_ok=True)
    (copy_source_dir / "file_to_copy.txt").write_text("Content of file to copy.")
    nested_source_dir = copy_source_dir / "nested_folder"
    nested_source_dir.mkdir(exist_ok=True)
    (nested_source_dir / "nested_file.txt").write_text("Content of nested file.")

    copy_dest_dir = test_dir / "copy_destination"
    # copy_dest_dir.mkdir(exist_ok=True) # Let copy_item create it or handle existing

    # Test 1: Copy file to new filename
    print("\nCopying file to new filename:")
    os_interaction.copy_item(
        str(copy_source_dir / "file_to_copy.txt"),
        str(copy_dest_dir / "file_copied.txt")
    )
    if (copy_dest_dir / "file_copied.txt").exists():
        print(f"Verified: '{(copy_dest_dir / "file_copied.txt")}' exists.")

    # Test 2: Copy file into existing directory (dest_dir itself)
    copy_dest_dir.mkdir(exist_ok=True) # Ensure dest dir exists for this test
    print("\nCopying file into existing directory:")
    os_interaction.copy_item(
        str(copy_source_dir / "file_to_copy.txt"),
        str(copy_dest_dir) # Just the directory path
    )
    if (copy_dest_dir / "file_to_copy.txt").exists():
         print(f"Verified: '{(copy_dest_dir / "file_to_copy.txt")}' exists inside destination.")

    # Test 3: Copy directory to a new directory location
    print("\nCopying directory to new directory location:")
    os_interaction.copy_item(
        str(copy_source_dir), # Source directory
        str(test_dir / "copy_dest_dir_new_name")
    )
    if (test_dir / "copy_dest_dir_new_name" / "file_to_copy.txt").exists():
        print(f"Verified: Copied directory '{(test_dir / "copy_dest_dir_new_name")}' contains expected file.")

    # Test 4: Copy directory into an existing directory
    existing_target_folder = test_dir / "existing_target_for_dir_copy"
    existing_target_folder.mkdir(exist_ok=True)
    print("\nCopying directory into an existing target directory:")
    os_interaction.copy_item(
        str(copy_source_dir),
        str(existing_target_folder) # Copy source_dir *into* existing_target_folder
    )
    if (existing_target_folder / os.path.basename(copy_source_dir) / "file_to_copy.txt").exists():
        print(f"Verified: Copied directory created inside '{(existing_target_folder)}' and contains expected file.")

    # Test 5: Copy non-existent source
    print("\nCopying non-existent source:")
    os_interaction.copy_item("path/to/non_existent_source.txt", str(copy_dest_dir))

    print("\n--- Testing move_item ---")
    # Setup for move tests - ensure fresh source items
    move_source_base = test_dir / "move_source_base"
    move_source_base.mkdir(exist_ok=True)

    file_to_move = move_source_base / "file_to_move.txt"
    file_to_move.write_text("Content of file to move.")

    dir_to_move = move_source_base / "folder_to_move"
    dir_to_move.mkdir(exist_ok=True)
    (dir_to_move / "sub_file.txt").write_text("Sub file in folder to move.")

    move_dest_base = test_dir / "move_destination_base"
    move_dest_base.mkdir(exist_ok=True)

    # Test 1: Move file to new filename (rename)
    print("\nMoving file to new filename (rename):")
    target_file_path_rename = str(move_dest_base / "file_moved_renamed.txt")
    os_interaction.move_item(str(file_to_move), target_file_path_rename)
    if not file_to_move.exists() and Path(target_file_path_rename).exists():
        print(f"Verified: Source '{file_to_move}' gone, Dest '{target_file_path_rename}' exists.")
    else:
        print(f"Verification FAILED for move file rename. Source exists: {file_to_move.exists()}, Dest exists: {Path(target_file_path_rename).exists()}")


    # Test 2: Move file into existing directory
    # Recreate source file for this test
    file_to_move_again = move_source_base / "file_to_move_again.txt"
    file_to_move_again.write_text("Content of file to move again.")
    target_dir_for_file = move_dest_base / "target_folder_for_file"
    target_dir_for_file.mkdir(exist_ok=True)
    print("\nMoving file into existing directory:")
    os_interaction.move_item(str(file_to_move_again), str(target_dir_for_file))
    moved_file_in_target_dir = target_dir_for_file / file_to_move_again.name
    if not file_to_move_again.exists() and moved_file_in_target_dir.exists():
        print(f"Verified: Source '{file_to_move_again}' gone, Dest '{moved_file_in_target_dir}' exists.")
    else:
        print(f"Verification FAILED for move file into dir. Source exists: {file_to_move_again.exists()}, Dest exists: {moved_file_in_target_dir.exists()}")


    # Test 3: Move directory to a new directory location (rename directory)
    print("\nMoving directory to new directory location (rename):")
    target_dir_path_rename = str(move_dest_base / "folder_moved_renamed")
    os_interaction.move_item(str(dir_to_move), target_dir_path_rename)
    if not dir_to_move.exists() and Path(target_dir_path_rename).is_dir() and (Path(target_dir_path_rename) / "sub_file.txt").exists():
        print(f"Verified: Source dir '{dir_to_move}' gone, Dest dir '{target_dir_path_rename}' exists with content.")
    else:
        print(f"Verification FAILED for move dir rename. Source exists: {dir_to_move.exists()}, Dest exists: {Path(target_dir_path_rename).exists()}")

    # Test 4: Move directory into an existing directory
    # Recreate source directory for this test
    dir_to_move_again = move_source_base / "folder_to_move_again"
    dir_to_move_again.mkdir(exist_ok=True)
    (dir_to_move_again / "sub_file_again.txt").write_text("Sub file in folder to move again.")
    existing_target_folder_for_dir = move_dest_base / "existing_target_for_dir_move"
    existing_target_folder_for_dir.mkdir(exist_ok=True)
    print("\nMoving directory into an existing target directory:")
    os_interaction.move_item(str(dir_to_move_again), str(existing_target_folder_for_dir))
    moved_dir_in_target_dir = existing_target_folder_for_dir / dir_to_move_again.name
    if not dir_to_move_again.exists() and moved_dir_in_target_dir.is_dir() and (moved_dir_in_target_dir / "sub_file_again.txt").exists():
        print(f"Verified: Source dir '{dir_to_move_again}' gone, Dest dir '{moved_dir_in_target_dir}' exists with content.")
    else:
        print(f"Verification FAILED for move dir into dir. Source exists: {dir_to_move_again.exists()}, Dest exists: {moved_dir_in_target_dir.exists()}")

    # Test 5: Move non-existent source
    print("\nMoving non-existent source:")
    os_interaction.move_item("path/to/non_existent_source_for_move.txt", str(move_dest_base))

    print("\n--- Testing delete_item ---")
    # Setup for delete tests
    delete_base = test_dir / "delete_base"
    delete_base.mkdir(exist_ok=True)

    # Test 1: Delete file - require confirmation
    file_to_delete_confirm = delete_base / "file_for_confirm_delete.txt"
    file_to_delete_confirm.write_text("Content for confirm delete.")
    print(f"\nAttempting delete with confirmation required for: {file_to_delete_confirm}")
    success, needs_confirm = os_interaction.delete_item(str(file_to_delete_confirm), require_confirmation=True)
    print(f"Result: success={success}, needs_confirm={needs_confirm}")
    if file_to_delete_confirm.exists() and needs_confirm:
        print(f"Verified: File '{file_to_delete_confirm}' still exists, confirmation was needed.")
    else:
        print(f"Verification FAILED for delete with confirm. File exists: {file_to_delete_confirm.exists()}, Needs Confirm: {needs_confirm}")

    # Test 2: Delete file - no confirmation (actually delete)
    print(f"\nAttempting delete without confirmation (actual delete) for: {file_to_delete_confirm}")
    success, needs_confirm = os_interaction.delete_item(str(file_to_delete_confirm), require_confirmation=False)
    print(f"Result: success={success}, needs_confirm={needs_confirm}")
    if not file_to_delete_confirm.exists() and success:
        print(f"Verified: File '{file_to_delete_confirm}' deleted.")
    else:
        print(f"Verification FAILED for actual delete. File exists: {file_to_delete_confirm.exists()}, Success: {success}")

    # Test 3: Delete directory - require confirmation
    dir_to_delete_confirm = delete_base / "dir_for_confirm_delete"
    dir_to_delete_confirm.mkdir()
    (dir_to_delete_confirm / "dummy.txt").write_text("dummy")
    print(f"\nAttempting delete with confirmation required for directory: {dir_to_delete_confirm}")
    success, needs_confirm = os_interaction.delete_item(str(dir_to_delete_confirm), require_confirmation=True)
    print(f"Result: success={success}, needs_confirm={needs_confirm}")
    if dir_to_delete_confirm.exists() and needs_confirm:
        print(f"Verified: Directory '{dir_to_delete_confirm}' still exists, confirmation was needed.")

    # Test 4: Delete directory - no confirmation (actually delete)
    print(f"\nAttempting delete without confirmation (actual delete) for directory: {dir_to_delete_confirm}")
    success, needs_confirm = os_interaction.delete_item(str(dir_to_delete_confirm), require_confirmation=False)
    print(f"Result: success={success}, needs_confirm={needs_confirm}")
    if not dir_to_delete_confirm.exists() and success:
        print(f"Verified: Directory '{dir_to_delete_confirm}' deleted.")

    # Test 5: Delete non-existent item
    print("\nAttempting to delete non-existent item:")
    success, needs_confirm = os_interaction.delete_item("path/to/non_existent_for_delete.txt")
    print(f"Result: success={success}, needs_confirm={needs_confirm}")

    print("\n--- Testing launch_application ---")
    # Note: Actual launching of GUI apps like notepad won't be visible in headless test env.
    # We are testing if the command to launch is successfully issued.
    # On Windows, 'notepad' or 'calc' are common. On Linux, 'ls' or 'echo'.
    import sys
    if sys.platform == "win32":
        print("\nAttempting to launch 'notepad.exe' (Windows specific test):")
        os_interaction.launch_application("notepad.exe")
        # Test with args (will likely open notepad and then notepad will complain about the arg)
        # os_interaction.launch_application("notepad.exe", ["test_file_for_notepad.txt"])
    else: # Linux/macOS
        print("\nAttempting to launch 'ls -l' (Linux/macOS specific test, output won't be captured here):")
        # Popen is non-blocking, so we won't see output directly unless we manage stdout/stderr
        os_interaction.launch_application("ls", ["-l", "/app"]) # List files in current dir
        # This test is mainly to see if Popen gets called without error.

    print("\nAttempting to launch a non-existent application:")
    os_interaction.launch_application("app_that_does_not_exist_anywhere")

    # To test launching a file with its default application on Windows, one might use:
    # os.startfile("some_document.txt") # This is Windows specific.
    # Our launch_application is more for executables.

    print("\n--- Testing create_note_in_notepad ---")
    print("\nAttempting to create a note for Notepad (behavior is OS-dependent):")
    notepad_success = os_interaction.create_note_in_notepad(
        title="My Test Note for Notepad",
        content="This is the content of the note.\nIt has multiple lines."
    )
    print(f"Result of create_note_in_notepad: {notepad_success}")
    # Note: If successful on Windows, a temp file was created and notepad.exe was launched with it.
    # That temp file is not automatically cleaned up by this test to allow Notepad to use it.
    # On Linux, a temp file is created, and a message about Windows-specificity is printed.

    print("\n--- Testing create_word_document ---")
    word_doc_path = test_dir / "MyAgentCreatedWordDoc.docx"
    print(f"\nAttempting to create a Word document at: {word_doc_path}")
    word_success = os_interaction.create_word_document(
        filepath=str(word_doc_path),
        title="Agent Report - Word",
        content="This document was generated by the Python agent using python-docx."
    )
    print(f"Result of create_word_document: {word_success}")
    if word_success and word_doc_path.exists():
        print(f"Verified: Word document '{word_doc_path}' created.")
    else:
        print(f"Verification FAILED for Word document creation. Exists: {word_doc_path.exists()}")


    # Clean up dummy files and directories
    import shutil
    try:
        shutil.rmtree(test_dir)
        print(f"\nCleaned up temporary test directory: {test_dir}")
    except Exception as e:
        print(f"Error cleaning up test directory: {e}")
