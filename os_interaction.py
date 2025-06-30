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


    # Clean up dummy files and directories
    import shutil
    try:
        shutil.rmtree(test_dir)
        print(f"\nCleaned up temporary test directory: {test_dir}")
    except Exception as e:
        print(f"Error cleaning up test directory: {e}")
