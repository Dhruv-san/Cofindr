import tkinter as tk
import asyncio
import threading
import queue # For thread-safe communication between Tkinter and Asyncio thread

from command_ui import CommandBar
from shortcut_listener import GlobalShortcutListener
from command_parser import CommandParser
from task_dispatcher import TaskDispatcher
from browser_interaction import BrowserManager
from os_interaction import OSInteractionModule # Import OSInteractionModule

# Configuration
AGENT_SHORTCUT = "ctrl+shift+space" # The shortcut to summon the command bar

class AgentApplication:
    def __init__(self):
        # self.root = tk.Tk() # Moved to run() method

        # Queue for passing commands from Tkinter thread to Asyncio thread
        self.command_queue = queue.Queue()

        # Initialize core components
        self.browser_manager = BrowserManager()
        self.command_parser = CommandParser()
        self.os_interaction_module = OSInteractionModule() # Instantiate OSInteractionModule
        self.task_dispatcher = TaskDispatcher( # Pass both modules
            browser_manager=self.browser_manager,
            os_interaction_module=self.os_interaction_module
        )

        # UI components will be initialized in run() if possible
        self.root = None
        self.command_bar = None

        # Shortcut listener can be initialized here, its callback will use self.command_bar once it's created
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

        # Initialize Tkinter UI and CommandBar inside run(), so errors are caught here.
        try:
            print("AgentApplication: Initializing UI...")
            self.root = tk.Tk()
            self.command_bar = CommandBar(self.root, self.handle_ui_command) # CommandBar now uses the root created here
            print("AgentApplication: UI initialized.")
        except tk.TclError as e:
            print(f"CRITICAL: Failed to initialize Tkinter UI: {e}")
            print("This application requires a graphical environment (display server).")
            print("If you are on a headless system, UI mode is not supported.")
            import sys
            sys.exit(1)
        except Exception as e: # Catch any other unexpected error during UI setup
            print(f"CRITICAL: An unexpected error occurred during UI initialization: {e}")
            import sys
            sys.exit(1)

        # Initialize CommandBar (now that root is confirmed)
        # self.command_bar = CommandBar(self.root, self.handle_ui_command)
        # Moved ^ into the try block for root init.

        # Start the shortcut listener
        try:
            self.shortcut_listener.start_listening() # Depends on self.command_bar being init
            if not self.shortcut_listener.is_running:
                print("WARNING: Shortcut listener failed to start. The agent might not be callable via shortcut.")
                print("This can happen in environments without a proper display server or specific OS permissions.")
                # We might not want to exit if only the shortcut fails, but UI is working.
                # However, the primary way to call the UI is the shortcut.
                # For now, we'll let it continue if UI initialized but shortcut failed, with a warning.
        except Exception as e:
             print(f"CRITICAL: Could not start shortcut listener: {e}")
             print("The application might not work as expected regarding shortcuts.")
             # Decide if this is fatal. If UI works but shortcut doesn't, is it still usable for debugging?
             # For now, let's make it fatal if the shortcut listener can't even attempt to start.
             # import sys # Already imported if UI failed
             # sys.exit(1) # Commenting out for now - allow running if UI is there but shortcut fails

        # Start the Tkinter main loop (this is blocking)
        print("Starting Tkinter main loop...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("KeyboardInterrupt caught in Tkinter main loop. Shutting down...")
        finally:
            self.shutdown()

    def shutdown(self):
        # Ensure root exists before trying to destroy it, in case init failed early
        if hasattr(self, 'root') and self.root:
            try:
                if self.root.winfo_exists(): # Check if window still exists
                    self.root.destroy()
            except tk.TclError as e:
                print(f"AgentApplication: Error destroying Tkinter root during shutdown: {e}")

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
