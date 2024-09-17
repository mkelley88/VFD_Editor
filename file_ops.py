import os

class FileOperations:
    def __init__(self, vfd, keyboard):
        self.vfd = vfd
        self.keyboard_input = keyboard  # Add keyboard input reference
        self.base_dir = os.path.join(os.path.expanduser("~"), "VFDEditorFiles")  # Correctly set the base directory for files
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)  # Create the directory if it doesn't exist

    def get_filename_from_user(self, prompt):
        """Prompt the user for a file name using the keyboard."""
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
            self.vfd.write(f"\r{prompt}{filename}")  # Update VFD display with current input

        filename = filename.strip()
        if filename:
            return os.path.join(self.base_dir, filename)  # Return full path with base directory
        return None

    def save_file(self, buffer):
        """Save the buffer to a file."""
        self.vfd.clear()
        filename = self.get_filename_from_user("Save file as: ")
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(buffer.decode('ascii'))
                self.vfd.write(f"File saved as {os.path.basename(filename)}.")
                return filename
            except (IOError, OSError) as e:
                self.vfd.write(f"Error saving file: {str(e)}")
        return None

    def open_file(self, buffer, filename=None):
        """Open a file and load its contents into the buffer."""
        self.vfd.clear()
        filename = self.get_filename_from_user("Open file: ")
        if filename and self.file_exists(filename):
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                buffer[:] = bytearray(content.encode('ascii'))
                self.vfd.write(f"Loaded {os.path.basename(filename)}.")
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
        files = [f for f in os.listdir(self.base_dir) if os.path.isfile(os.path.join(self.base_dir, f))]
        
        if not files:
            self.vfd.write("No files available.")
            return None

        index = 0  # Start with the first file selected
        total_files = len(files)

        while True:
            # Display the current file selection
            self.vfd.clear()
            for i, file in enumerate(files):
                if i == index:
                    self.vfd.write(f"> {file}\n")  # Highlight selected file
                else:
                    self.vfd.write(f"  {file}\n")
            
            key = self.keyboard_input.get_key()

            if key == "KEY_ENTER":  # Confirm selection
                selected_file = os.path.join(self.base_dir, files[index])
                self.vfd.clear()
                self.vfd.write(f"Selected: {files[index]}")
                self.open_file(buffer, selected_file)
            elif key == "KEY_UP":  # Move selection up
                index = (index - 1) % total_files  # Wrap around if at the top
            elif key == "KEY_DOWN":  # Move selection down
                index = (index + 1) % total_files  # Wrap around if at the bottom
            elif key == "KEY_ESC":  # Cancel selection
                self.vfd.write("Selection cancelled.")
                return None
