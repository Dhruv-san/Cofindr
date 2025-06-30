import tkinter as tk

class CommandBar:
    def __init__(self, root: tk.Tk, command_handler_func):
        self.root = root
        self.command_handler_func = command_handler_func # Function to call when command is entered

        # Configure the root window
        self.root.title("Command Bar")
        self.root.attributes('-topmost', True) # Keep it on top

        # Make the window frameless (no title bar, borders, etc.)
        self.root.overrideredirect(True)

        # Entry widget for command input
        self.entry_font = ("Arial", 16)
        self.entry = tk.Entry(self.root, width=50, font=self.entry_font, bd=2, relief="solid")
        self.entry.pack(padx=10, pady=10)
        self.entry.bind("<Return>", self.handle_command_entered)
        self.entry.bind("<Escape>", self.hide)

        self._center_window()
        self.hide_on_start() # Hidden by default

    def _center_window(self):
        self.root.update_idletasks() # Ensure dimensions are calculated
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Position it at the top-center of the screen
        x = (screen_width // 2) - (width // 2)
        y = 50 # A small offset from the top
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def handle_command_entered(self, event=None):
        command_text = self.entry.get()
        self.hide() # Hide after command is entered
        if command_text:
            print(f"CommandBar: Command entered: {command_text}")
            if self.command_handler_func:
                try:
                    self.command_handler_func(command_text) # Call the handler
                except Exception as e:
                    # Basic error handling: print to console.
                    # In a more advanced UI, could show an error message.
                    print(f"CommandBar: Error during command handling: {e}")
        self.entry.delete(0, tk.END) # Clear the entry field

    def show(self):
        self.root.deiconify() # Show the window
        self.entry.focus_set() # Set focus to the entry field
        print("CommandBar: Shown")

    def hide(self, event=None):
        self.root.withdraw() # Hide the window
        print("CommandBar: Hidden")

    def hide_on_start(self):
        self.root.withdraw()


# Example usage for testing CommandBar directly
if __name__ == '__main__':
    # Placeholder command handler for testing
    def test_command_handler(command):
        print(f"Test Handler received: {command}")
        # In a real app, this would trigger parsing and dispatching.
        # For this test, if command is 'exit', we quit.
        if command.lower() == "exit test ui":
            app_root.quit()

    app_root = tk.Tk()
    command_bar = CommandBar(app_root, test_command_handler)

    # For testing, let's provide a button to show the command bar
    # In the real app, the global shortcut will call command_bar.show()
    def show_command_bar_test():
        command_bar.show()

    test_button = tk.Button(app_root, text="Show Command Bar (Test)", command=show_command_bar_test)
    # Initially, the root window for the button is also hidden because command_bar hides its root.
    # So, we need to manage the visibility of the root if we want to see the button.

    # We'll make the CommandBar's root a Toplevel window if we want a separate control window
    # For simplicity here, the CommandBar takes over the main root.
    # Let's just show it initially for the button to be visible IF the command bar itself isn't shown on top.

    # The CommandBar is designed to be the main interaction point.
    # To test it, we can call .show() directly.
    print("Showing CommandBar for test. Press Esc to hide, or type and press Enter.")
    print("Type 'exit test ui' and press Enter to quit this test.")
    command_bar.show() # Show it initially for this test run

    app_root.mainloop()
    print("Test UI finished.")
