import keyboard
import time

class GlobalShortcutListener:
    def __init__(self, shortcut: str, callback_func):
        """
        Initializes the listener with a specific shortcut and a callback function.

        :param shortcut: The shortcut string (e.g., "ctrl+shift+space").
        :param callback_func: The function to call when the shortcut is pressed.
        """
        self.shortcut = shortcut
        self.callback_func = callback_func
        self._listener_hook = None
        self.is_running = False

    def start_listening(self):
        """
        Starts listening for the global shortcut.
        This is a blocking call if not run in a separate thread.
        """
        if not self.is_running:
            try:
                # keyboard.add_hotkey returns a function to remove the hotkey
                self._listener_hook = keyboard.add_hotkey(self.shortcut, self.on_shortcut_pressed, suppress=False)
                self.is_running = True
                print(f"Shortcut listener started for '{self.shortcut}'. Press the shortcut.")
                # Keep the listener alive (keyboard library might handle this in its own thread,
                # but for explicit control or if run in main thread, a wait loop is needed)
                # keyboard.wait() can be used if this is the only thing the thread/process does.
                # For integration, this needs to be managed carefully.
            except Exception as e:
                print(f"Error starting shortcut listener: {e}")
                # This might happen if on a headless Linux system without appropriate permissions or display server
                # For Windows, this should generally work.
                self.is_running = False


    def on_shortcut_pressed(self):
        """
        Internal handler for when the shortcut is detected.
        Calls the provided callback function.
        """
        print(f"Shortcut '{self.shortcut}' pressed!")
        if self.callback_func:
            self.callback_func()

    def stop_listening(self):
        """
        Stops listening for the global shortcut.
        """
        if self.is_running and self._listener_hook:
            try:
                keyboard.remove_hotkey(self._listener_hook)
                # Or keyboard.unhook_all() if appropriate
                self.is_running = False
                print(f"Shortcut listener stopped for '{self.shortcut}'.")
            except Exception as e:
                print(f"Error stopping shortcut listener: {e}")
        elif not self._listener_hook and self.is_running: # If add_hotkey failed but flag was set
             self.is_running = False
             print(f"Shortcut listener for '{self.shortcut}' was not properly started, now marked as stopped.")


# Example usage for testing GlobalShortcutListener directly
if __name__ == '__main__':
    # Placeholder callback for testing
    def my_test_callback():
        print("Test Callback: Shortcut was activated!")

    # Define the shortcut to listen for
    # IMPORTANT: Choose a shortcut that is unlikely to conflict with system shortcuts.
    # For testing, 'ctrl+alt+h' might be okay.
    # For the actual app, we decided on something like 'ctrl+shift+space'
    test_shortcut = "ctrl+alt+h"

    print(f"Starting shortcut listener test for: {test_shortcut}")
    print(f"Press {test_shortcut} to trigger the callback.")
    print("Press Ctrl+C in the console to stop this test script.")

    listener = GlobalShortcutListener(shortcut=test_shortcut, callback_func=my_test_callback)

    # The keyboard library's listener runs in the background once add_hotkey is called.
    # The main thread needs to be kept alive.
    listener.start_listening()

    if listener.is_running:
        try:
            # Keep the main thread alive to allow the listener to work.
            # keyboard.wait() would block here, which is fine for a standalone test.
            # Or a simple loop:
            while True:
                time.sleep(0.1) # Keep alive, checking for KeyboardInterrupt
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received. Stopping listener.")
        finally:
            listener.stop_listening()
            print("Shortcut listener test finished.")
    else:
        print("Listener did not start. This might be due to environment limitations (e.g., no display server for 'keyboard' lib on some Linux systems).")
        print("This test is more reliable on a desktop environment like Windows.")
