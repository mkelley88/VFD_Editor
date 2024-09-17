''' File operations for the VFD Editor. '''
import os
class FileOperations:
    """
    File operations for the VFD Editor.
    """
    def __init__(self, vfd, keyboard):
        """
        Initializes the FileOperations instance.

        :param vfd: The VFD display instance
        :param keyboard: The keyboard input instance
        """
        self.vfd = vfd
        self.keyboard_input = keyboard  # Add keyboard input reference
        self.base_dir = os.path.join(
            os.path.expanduser("~"), "VFDEditorFiles"
        )  # Correctly set the base directory for files
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)  # Create the directory if it doesn't exist

    def get_filename_from_user(self, prompt):
        """
        Get a filename from the user by displaying a prompt and allowing them to
        enter text.

        :param prompt: The prompt to display to the user
        :return: The full path to the file, or None if the user didn't enter a filename
        """
        self.vfd.write(prompt)
        filename = ""
        while True:
            key = self.keyboard_input.get_key()
            if key == "KEY_ENTER":  # End filename input on ENTER
                break
            elif key == "KEY_BACKSPACE":  # Handle backspace for editing
                filename = filename[:-1]
            elif len(key) == 1:  # Append characters to filename
                filename += key
            self.vfd.write(
                f"\r{prompt}{filename}"
            )  # Update VFD display with current input

        filename = filename.strip()
        return os.path.join(self.base_dir, filename) if filename else None

    def save_file(self, buffer, filename=None):
        """Save the used part of the buffer to a file and display the number of bytes written."""
        self.vfd.clear()

        # Calculate the used portion of the buffer
        used_buffer = buffer[
            : buffer.find(0)
        ]  # Find the first zero byte and slice up to that point

        if not filename:
            filename = self.get_filename_from_user("Save file as: ")

        if filename:
            try:
                with open(filename, "w", encoding="UTF-8") as f:
                    bytes_written = f.write(
                        used_buffer.decode("ascii")
                    )  # Write only the used part
                self.vfd.write(f"File saved as {os.path.basename(filename)}.")
                self.vfd.set_cursor(40)
                self.vfd.write(f"{bytes_written} bytes written")
                return filename
            except (IOError, OSError) as e:
                self.vfd.write(f"Error saving file: {str(e)}")
        return None

    def open_file(self, buffer, filename=None):
        """Open a file and load its contents into the buffer."""
        self.vfd.clear()
        if not filename:
            filename = self.get_filename_from_user("Open file: ")

        if filename and self.file_exists(filename):
            try:
                with open(filename, "r", encoding="UTF-8") as f:
                    content = f.read()
                buffer[:] = bytearray(content.encode("ascii"))
                self.vfd.clear()
                self.vfd.write(f"Loaded {os.path.basename(filename)}")
                return filename
            except (IOError, OSError) as e:
                self.vfd.write(f"Error loading file: {str(e)}")
        else:
            self.vfd.write("File not found.")
        return None

    def file_exists(self, filename):
        """Check if a file exists."""
        return os.path.isfile(filename)

    def choose_file_from_list(self, buffer):
        """Display a list of files in the base directory and allow the user to choose one."""
        self.vfd.clear()

        # Get the list of files in the base directory
        files = [
            f
            for f in os.listdir(self.base_dir)
            if os.path.isfile(os.path.join(self.base_dir, f))
        ]

        if not files:
            self.vfd.write("No files available.")
            return None

        index = 0  # Start with the first file selected
        total_files = len(files)

        while True:
            # Display the current file selection (one file per line)
            self.vfd.clear()

            # Only display the selected file on the screen
            selected_file = files[index]
            self.vfd.write(f"> {selected_file:<40}")  # Display the selected file

            key = self.keyboard_input.get_key()

            if key == "KEY_ENTER":  # Confirm selection
                selected_file_path = os.path.join(self.base_dir, selected_file)
                self.vfd.clear()
                self.vfd.write(f"Selected: {selected_file}")
                return self.open_file(buffer, selected_file_path)  # Open the selected file
            elif key == "KEY_UP":  # Move selection up
                index = (index - 1) % total_files  # Wrap around if at the top
            elif key == "KEY_DOWN":  # Move selection down
                index = (index + 1) % total_files  # Wrap around if at the bottom
            elif key == "KEY_ESC":  # Cancel selection
                self.vfd.write("Selection cancelled.")
                return None
