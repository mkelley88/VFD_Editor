''' Main logic for handling buffer and integrating Keyboard input for Raspberry Pi Zero W '''
import time
from vfd import VFD  # Import VFD display functions
from file_ops import FileOperations  # Import FileOperations module
from keyboard import KeyboardInput  # Import Keyboard input module


# The `VFDWordProcessor` class represents a word processor for VFD (Vacuum Fluorescent Display)
# technology with features for text editing and display control.
class VFDWordProcessor:
    """This class represents a word processor for VFD (Vacuum Fluorescent Display) technology."""

    VFD_BS = 0x08  # Backspace command for the VFD
    VFD_CR = 0x0D  # Carriage return command (start of line)
    VFD_LINEFEED = 0x0A  # Line feed (next row)

    def __init__(self, vfd_instance):
        self.vfd = vfd_instance
        self.keyboard_input = KeyboardInput()  # Initialize Keyboard input
        self.file_ops = FileOperations(
            self.vfd, self.keyboard_input
        )  # Initialize FileOperations
        self.open_filename = ""  # Opened file name
        self.buffer = bytearray(16384)  # 16KB text buffer for storing text
        self.buffer_pos = 0  # Current position in the buffer
        self.used_buffer_size = 0  # Track how much of the buffer has been used
        self.visible_start = 0  # Start of visible window in the buffer
        self.visible_end = 80  # End of visible window (40x2)
        self.cursor_pos = 0  # Current cursor position on the screen
        self.buffer_altered = False  # Flag to track if buffer has been altered
        self.insert_mode = False  # Insert mode flag
        self.vfd.init_display()  # Initialize the VFD display
        self.vfd.clear()

        # Welcome message
        self.vfd.write("VFD Editor")
        self.update_display()

    def run(self):
        """
        The function `run` handles keyboard input for a text editor, allowing for file operations, text
        editing, and display updates.
        """
        display_needs_update = (
            False  # Flag to track whether the display should be updated
        )

        while True:
            key = self.keyboard_input.get_key()

            # Check if Control-Q is pressed for quitting
            if self.keyboard_input.control_pressed and key == "q":
                if self.buffer_altered:
                    self.vfd.write("Unsaved changes. Save before quitting? (y/n)")
                    response = self.keyboard_input.get_key()
                    if response == "y":
                        self.save_file()  # Save the buffer if user says yes
                    elif response == "n":
                        break  # Exit without saving
                break  # Quit the program gracefully
            elif self.keyboard_input.control_pressed and key == "s":
                self.save_file()  # Trigger save function
                self.buffer_altered = False  # Reset buffer_altered after saving
                continue
            elif self.keyboard_input.control_pressed and key == "o":
                self.open_file()  # Trigger open function
                display_needs_update = True  # File opened, update needed
                self.buffer_altered = False  # Reset buffer_altered after opening a file
                continue
            elif self.keyboard_input.control_pressed and key == "O":
                self.file_ops.choose_file_from_list(
                    self.buffer
                )  # Trigger file chooser function
                display_needs_update = True  # File opened, update needed
                self.buffer_altered = False  # Reset buffer_altered after opening a file
                continue

            # Regular input handling
            if key == "KEY_INSERT":
                self.insert_mode = not self.insert_mode
                self.vfd.write(f"Insert Mode: {'ON' if self.insert_mode else 'OFF'}")
                display_needs_update = True
            elif key == "KEY_UP":
                self.move_cursor_up()
                display_needs_update = True
            elif key == "KEY_DOWN":
                self.move_cursor_down()
                display_needs_update = True
            elif key == "KEY_LEFT":
                self.move_cursor_left()
                display_needs_update = True
            elif key == "KEY_RIGHT":
                self.move_cursor_right()
                display_needs_update = True
            elif key == "KEY_ENTER":
                self.insert_char("\n")
                self.buffer_altered = True  # Mark buffer as altered
                display_needs_update = True
            elif key == "KEY_SPACE":
                self.insert_char(" ")
                self.buffer_altered = True  # Mark buffer as altered
                display_needs_update = True
            elif key == "KEY_BACKSPACE":
                self.delete_char()
                self.buffer_altered = True  # Mark buffer as altered
                display_needs_update = True
            elif key is not None and len(key) == 1:
                self.insert_char(key)  # Insert the valid character
                self.buffer_altered = True  # Mark buffer as altered
                display_needs_update = True

            # Update display only if needed
            if display_needs_update:
                self.update_display()
                display_needs_update = False

        self.cleanup()  # Cleanup GPIO before exiting

    def insert_char(self, char):
        """
        The `insert_char` function inserts a character into a buffer based on the current mode
        (insert/overwrite) in a Python class.
        
        :param char: The `char` parameter in the `insert_char` method represents the character that you want
        to insert into the buffer at the current position. This character will be either inserted into the
        buffer or used to overwrite an existing character based on the current mode (insert/overwrite) of
        the buffer
        """
        if self.insert_mode:
            # Insert mode: Shift the buffer content to the right
            if (
                self.buffer_pos < len(self.buffer) - 1
            ):  # Make sure not to exceed buffer size
                self.buffer[self.buffer_pos + 1 :] = self.buffer[self.buffer_pos : -1]
                self.buffer[self.buffer_pos] = ord(char)
                self.buffer_pos += 1
        # Overwrite mode: Overwrite the current character
        elif self.buffer_pos < len(self.buffer):
            self.buffer[self.buffer_pos] = ord(char)
            self.buffer_pos += 1
        self.update_cursor_position()

    def delete_char(self):
        """
        The code snippet contains methods to delete a character at the current position and move the cursor
        up by one row in a Python class.
        """
        if self.buffer_pos > 0:
            self.buffer[self.buffer_pos - 1] = 0
            self.buffer_pos -= 1
            self.update_cursor_position()

    def move_cursor_up(self):
        """Move the cursor up by 1 row."""
        if self.visible_start >= 40:
            self.visible_start -= 40
            self.visible_end -= 40
        else:
            self.buffer_pos = max(
                0, self.buffer_pos - 40
            )  # Move the cursor to the start of the buffer
            self.update_cursor_position()
        self.update_display()

    def move_cursor_down(self):
        """Move the cursor down by 1 row."""
        buffer_size = self.calculate_used_buffer()  # Get the size of the used portion of the buffer

        if self.visible_end + 40 <= buffer_size:  # Check if we can safely move down
            self.visible_start += 40
            self.visible_end += 40
        elif self.visible_end < buffer_size:  # If we're near the end but can't do a full row move
            # Adjust to the maximum valid visible window
            self.visible_start = max(0, buffer_size - 40)
            self.visible_end = buffer_size
        else:
            return  # Do nothing if we're already at the end of the buffer

        self.buffer_pos = min(buffer_size, self.buffer_pos + 40)  # Move the cursor down
        self.update_cursor_position()
        self.update_display()


    def move_cursor_left(self):
        """Move the cursor left by 1 column."""
        if self.buffer_pos > 0:
            self.buffer_pos -= 1
            self.update_cursor_position()

    def move_cursor_right(self):
        """Move the cursor right by 1 column."""
        if self.buffer_pos < len(self.buffer):
            self.buffer_pos += 1
            self.update_cursor_position()

    def calculate_used_buffer(self):
        """Calculate the amount of the buffer that is currently used."""
        return sum(byte != 0 for byte in self.buffer)

    def update_cursor_position(self):
        """Update the cursor position."""
        self.cursor_pos = self.buffer_pos - self.visible_start
        if self.cursor_pos < 0:
            self.cursor_pos = 0  # Cursor position cannot be negative
        elif self.cursor_pos > 79:  # Cursor position cannot exceed 79
            self.visible_start += (
                40  # Move the visible window down by 40 characters (one row)
            )
            self.visible_end += 40
            self.cursor_pos = (
                self.buffer_pos - self.visible_start
            )  # Adjust the cursor position

        self.vfd.set_cursor(self.cursor_pos)

    def update_display(self):
        """Update the VFD display by replacing newline characters with '`' inline."""
        visible_text = ""

        # Loop through the visible part of the buffer, but ensure we don't go out of bounds
        buffer_size = self.calculate_used_buffer()  # Calculate the used part of the buffer
        for i in range(self.visible_start, min(self.visible_end, buffer_size)):
            char = self.buffer[i]
            if char == ord("\n"):
                visible_text += "`"  # Display '`' in place of the newline character
            else:
                visible_text += chr(char) if char != 0 else " "  # Convert byte to character or space

        # If the visible_text is shorter than 80 characters, pad it with spaces
        visible_text = f"{visible_text:<80}"

        self.vfd.clear()
        self.vfd.write(visible_text)
        self.vfd.set_cursor(self.cursor_pos)


    def save_file(self):
        """Save the buffer to a file."""
        self.open_filename = self.file_ops.save_file(self.buffer, self.open_filename)
        self.buffer_altered = False  # Reset buffer_altered flag after saving
        time.sleep(2)
        self.update_display()

    def open_file(self):
        """Open a file and load it into the buffer."""
        self.open_filename = self.file_ops.open_file(self.buffer)
        self.buffer_pos = self.calculate_used_buffer()  # Reset buffer position
        self.buffer_altered = False  # Reset buffer_altered after opening a file
        time.sleep(2)
        self.update_display()

    def cleanup(self):
        """Cleanup resources before quitting."""
        self.vfd.cleanup()  # Ensure GPIO is cleaned up properly


if __name__ == "__main__":
    vfd_instance = VFD()
    editor = VFDWordProcessor(vfd_instance)
    editor.run()
