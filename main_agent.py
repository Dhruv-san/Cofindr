import tkinter as tk
import asyncio
import threading
import queue # For thread-safe communication between Tkinter and Asyncio thread

from command_ui import CommandBar
from shortcut_listener import GlobalShortcutListener
from command_parser import CommandParser
from task_dispatcher import TaskDispatcher
from browser_interaction import BrowserManager

# Configuration
AGENT_SHORTCUT = "ctrl+shift+space" # The shortcut to summon the command bar

class AgentApplication:
    def __init__(self):
        self.root = tk.Tk() # Main Tkinter window (will be managed by CommandBar)

        # Queue for passing commands from Tkinter thread to Asyncio thread
        self.command_queue = queue.Queue()

        # Initialize core components
        self.browser_manager = BrowserManager() # For web tasks
        self.command_parser = CommandParser()   # To parse text commands
        # TaskDispatcher needs the browser_manager
        self.task_dispatcher = TaskDispatcher(browser_manager=self.browser_manager)

        # Initialize UI and Shortcut components
        # CommandBar needs a handler that can put commands onto the queue
        self.command_bar = CommandBar(self.root, self.handle_ui_command)
        # ShortcutListener needs a callback to show the command bar
        self.shortcut_listener = GlobalShortcutListener(AGENT_SHORTCUT, self.show_command_bar)

        self.async_thread = None
        self.is_running = False

    def handle_ui_command(self, command_text: str):
        """
        This method is called by CommandBar (from Tkinter thread) when a command is entered.
        It puts the command onto a queue to be processed by the asyncio thread.
        """
        print(f"AgentApplication: Queuing command from UI: {command_text}")
        self.command_queue.put(command_text)

    def show_command_bar(self):
        """Callback for the shortcut listener to show the command bar."""
        # This might be called from the keyboard listener's thread.
        # Tkinter updates should be done in the main thread.
        # Use root.after to ensure thread safety with Tkinter.
        if self.root and self.command_bar:
            self.root.after(0, self.command_bar.show)
        else:
            print("AgentApplication: Cannot show command bar, root or command_bar not initialized.")


    async def process_commands_async(self):
        """
        Runs in the asyncio event loop (separate thread).
        Continuously checks the queue for commands and processes them.
        """
        print("Async Command Processor: Started.")
        while self.is_running:
            try:
                command_text = self.command_queue.get_nowait() # Non-blocking get
                if command_text:
                    print(f"Async Command Processor: Dequeued command: {command_text}")
                    structured_command = self.command_parser.parse_command(command_text)
                    if structured_command:
                        await self.task_dispatcher.dispatch(structured_command)
                    else:
                        print(f"Async Command Processor: Command '{command_text}' not recognized by parser.")
                    self.command_queue.task_done()
            except queue.Empty:
                await asyncio.sleep(0.1) # Wait a bit if queue is empty
            except Exception as e:
                print(f"Async Command Processor: Error processing command: {e}")

        print("Async Command Processor: Shutting down.")
        # Clean up browser manager when the loop ends
        await self.browser_manager.close()
        print("Async Command Processor: Browser manager closed.")


    def start_async_loop(self):
        """Starts the asyncio event loop in a new thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_commands_async())
        finally:
            loop.close()
        print("Asyncio event loop finished.")

    def run(self):
        """Starts the agent application."""
        print(f"Starting Agent Application. Press '{AGENT_SHORTCUT}' to show command bar.")
        self.is_running = True

        # Start the asyncio command processor in a separate thread
        self.async_thread = threading.Thread(target=self.start_async_loop, daemon=True)
        self.async_thread.start()
        print("Asyncio thread started.")

        # Start the shortcut listener
        # The 'keyboard' library often manages its own thread or integrates with OS event loop.
        # If listener.start_listening() is blocking, it MUST run in its own thread too.
        # The current keyboard.add_hotkey is non-blocking.
        try:
            self.shortcut_listener.start_listening()
            if not self.shortcut_listener.is_running:
                print("WARNING: Shortcut listener failed to start. The agent might not be callable via shortcut.")
                print("This can happen in environments without a proper display server or permissions.")
        except Exception as e:
            # This is particularly for Linux systems where 'keyboard' might need root or X server.
             print(f"CRITICAL: Could not start shortcut listener: {e}")
             print("The application might not work as expected regarding shortcuts.")


        # Start the Tkinter main loop (this is blocking)
        print("Starting Tkinter main loop...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("KeyboardInterrupt caught in Tkinter main loop. Shutting down...")
        finally:
            self.shutdown()

    def shutdown(self):
        print("AgentApplication: Initiating shutdown...")
        self.is_running = False # Signal async loop to stop

        if self.shortcut_listener and self.shortcut_listener.is_running:
            self.shortcut_listener.stop_listening()

        # Give the async thread some time to process remaining queue items and shut down gracefully
        if self.async_thread and self.async_thread.is_alive():
            print("AgentApplication: Waiting for async thread to finish...")
            # Put a sentinel value to ensure the loop wakes up if it's sleeping on an empty queue
            self.command_queue.put(None) # Or a specific sentinel
            self.async_thread.join(timeout=5.0) # Wait for up to 5 seconds
            if self.async_thread.is_alive():
                print("AgentApplication: Async thread did not finish in time.")

        # Tkinter window should close as mainloop exits.
        # If root is still there, explicitly destroy.
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError as e:
            print(f"AgentApplication: Error destroying Tkinter root: {e}")

        print("AgentApplication: Shutdown complete.")

if __name__ == "__main__":
    app = AgentApplication()
    app.run()
