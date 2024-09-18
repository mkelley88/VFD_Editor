""" Main logic for handling buffer and integrating Keyboard input for Raspberry Pi Zero W """

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
        self.visible_text = (" " * 80)  # Visible text in the buffer
        self.visible_old = (" " * 80)  # Old visible text in the buffer
        self.cursor_pos = 0  # Current cursor position on the screen
        self.buffer_altered = False  # Flag to track if buffer has been altered
        self.insert_mode = False  # Insert mode flag
        self.vfd.init_display()  # Initialize the VFD display

        # Welcome message
        self.vfd.write("VFD Editor")
        time.sleep(2)
        self.vfd.clear()
        self.update_display()

    def run(self):
        """
        The function `run` handles keyboard input for a text editor, allowing for file operations, text
        editing, and display updates.
        """
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
                self.buffer_altered = False  # Reset buffer_altered after opening a file
                continue
            elif self.keyboard_input.control_pressed and key == "O":
                self.file_ops.choose_file_from_list(
                    self.buffer
                )  # Trigger file chooser function
                self.buffer_altered = False  # Reset buffer_altered after opening a file
                continue
            elif self.keyboard_input.control_pressed and key == "w":
                self.vfd.clear()
                word_count = self.count_words_in_buffer()  # Trigger word count function
                self.vfd.write(f"Word Count: {word_count}")  # Display word count
                self.return_to_main_screen()
                continue
            elif self.keyboard_input.control_pressed and key == "j":
                self.journal_entry()  # Trigger journal entry function
                continue

            # Regular input handling
            if key == "KEY_INSERT":
                self.insert_mode = not self.insert_mode
                self.vfd.write(f"Insert Mode: {'ON' if self.insert_mode else 'OFF'}")
                time.sleep(1)
            elif key == "KEY_UP":
                self.move_cursor_up()
            elif key == "KEY_DOWN":
                self.move_cursor_down()
            elif key == "KEY_LEFT":
                self.move_cursor_left()
            elif key == "KEY_RIGHT":
                self.move_cursor_right()
            elif key == "KEY_ENTER":
                self.insert_char("\n")
                self.buffer_altered = True  # Mark buffer as altered
            elif key == "KEY_SPACE":
                self.insert_char(" ")
                self.buffer_altered = True  # Mark buffer as altered
            elif key == "KEY_BACKSPACE":
                self.delete_char()
                self.buffer_altered = True  # Mark buffer as altered
            elif key is not None and len(key) == 1:
                self.insert_char(key)  # Insert the valid character
                self.buffer_altered = True  # Mark buffer as altered

            self.update_display()

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
        if self.buffer_pos < len(self.buffer) - 1:  # Ensure the buffer doesn't overflow
            if self.insert_mode:
                # Insert mode: Shift the buffer content to the right
                self.buffer[self.buffer_pos + 1:] = self.buffer[self.buffer_pos:-1]
            # Insert or overwrite the character
            self.buffer[self.buffer_pos] = ord(char)
            self.buffer_pos += 1
        
        self.update_cursor_position()

    def delete_char(self):
        """Delete the character at the current buffer position and update the cursor."""
        if self.buffer_pos > 0:
            self.buffer_pos -= 1
            self.buffer[self.buffer_pos] = 0  # Clear the character
            self.update_cursor_position()

    def move_cursor_up(self):
        """Move the cursor up by 1 row."""
        if self.visible_start >= 40:
            self.visible_start -= 40
            self.visible_end -= 40
        else:
            self.buffer_pos = max(0, self.buffer_pos - 40)  # Move the cursor to the start of the buffer
            self.update_cursor_position()
        self.update_display()

    def move_cursor_down(self):
        """Move the cursor down by 1 row, ensuring it stays within the bounds of the buffer."""
        buffer_size = self.calculate_used_buffer()  # Get the size of the used portion of the buffer

        # If there's room to scroll down by a full row (40 characters)
        if self.visible_end + 40 <= buffer_size:
            self.visible_start += 40
            self.visible_end += 40
        # If near the end of the buffer, adjust to show the last visible row
        elif self.visible_end < buffer_size:
            self.visible_start = max(0, buffer_size - 40)
            self.visible_end = buffer_size
        else:
            return  # Reached the end of the buffer, no further movement

        # Ensure buffer_pos does not exceed the actual buffer content
        self.buffer_pos = min(buffer_size, self.buffer_pos + 40)
        
        # Adjust cursor and display
        self.update_cursor_position()
        self.update_display()


    def move_cursor_left(self):
        """Move the cursor left by one position in the buffer if not at the start."""
        if self.buffer_pos > 0:
            self.buffer_pos -= 1  # Move the cursor one position left
            self.update_cursor_position()


    def move_cursor_right(self):
        """Move the cursor right by one position in the buffer if not at the end."""
        if self.buffer_pos < len(self.buffer) - 1:
            self.buffer_pos += 1  # Move the cursor one position right
            self.update_cursor_position()


    def calculate_used_buffer(self):
        """Calculate the amount of the buffer that is currently used."""
        return sum(byte != 0 for byte in self.buffer)

    def update_cursor_position(self):
        """Update the cursor position, ensuring it stays within the buffer bounds."""
        buffer_size = self.calculate_used_buffer()

        if self.buffer_pos > buffer_size:  # Ensure cursor doesn't go beyond used buffer
            self.buffer_pos = buffer_size

        self.cursor_pos = self.buffer_pos - self.visible_start

        if self.cursor_pos < 0:
            self.cursor_pos = 0
        elif self.cursor_pos > 79:  # Move the visible window when cursor exceeds 79
            self.visible_start += 40
            self.visible_end += 40
            self.cursor_pos = self.buffer_pos - self.visible_start

        self.vfd.set_cursor(self.cursor_pos)


    def update_display(self):
        """Update the VFD display by replacing newline characters with '`' inline and reducing flicker."""
        buffer_size = self.calculate_used_buffer()  # Calculate the used part of the buffer
        self.visible_text = ""

        # Build the visible_text by iterating over the visible buffer range
        for i in range(self.visible_start, min(self.visible_end, buffer_size)):
            char = self.buffer[i]
            self.visible_text += "`" if char == ord("\n") else (chr(char) if char != 0 else " ")

        # Ensure visible_text is exactly 80 characters long
        self.visible_text = f"{self.visible_text:<80}"

        # Compare the new visible_text with the old one and update only changed characters
        for i, char in enumerate(self.visible_text):
            if i >= len(self.visible_old) or self.visible_old[i] != char:
                self.vfd.set_cursor(i)  # Move the cursor to the position of the difference
                self.vfd.write(char)  # Write only the changed character

        # Update visible_old to reflect the current state
        self.visible_old = self.visible_text

        # Set cursor position to the current cursor_pos
        self.vfd.set_cursor(self.cursor_pos)
    
    def count_words_in_buffer(self):
        """Return the count of words in the used portion of the buffer."""
        # Decode the used buffer portion and split by whitespace to count words
        used_buffer = self.buffer[:self.calculate_used_buffer()].decode("ascii", "ignore")
        return len(used_buffer.split())

    def journal_entry(self):
        """Clear the buffer and screen, then save a new journal entry with a timestamped filename."""
        # Clear the buffer and reset the position
        self.buffer = bytearray(16384)
        self.buffer_pos = 0
        self.vfd.clear()

        # Create the filename using the current timestamp
        filename = time.strftime("%Y%m%dT%H%M%S") + ".txt"

        # Save the buffer as a new journal entry
        self.open_filename = self.file_ops.save_file(self.buffer, filename)
        self.buffer_altered = False

        # Inform the user about the new journal entry
        self.vfd.clear()
        self.vfd.write("New journal entry saved as:")
        self.vfd.set_cursor(40)
        self.vfd.write(f"{filename}")
        
        # Return to the main screen
        self.return_to_main_screen()


    def save_file(self):
        """Save the buffer to a file."""
        self.open_filename = self.file_ops.save_file(self.buffer, self.open_filename)
        self.buffer_altered = False  # Reset buffer_altered flag after saving
        self.return_to_main_screen()

    def open_file(self):
        """Open a file and load its contents into the buffer."""
        self.open_filename = self.file_ops.open_file(self.buffer)
        self.buffer_pos = self.calculate_used_buffer()  # Reset buffer position to match the file size
        self.buffer_altered = False  # The buffer is now synchronized with the file
        self.return_to_main_screen()


    def return_to_main_screen(self, delay=2):
        """Clear the screen and return to the main editor after a short delay."""
        time.sleep(delay)
        self.vfd.clear()
        self.vfd.write(self.visible_text)
        self.update_display()

    def cleanup(self):
        """Cleanup resources before quitting."""
        self.vfd.cleanup()  # Ensure GPIO is cleaned up properly


if __name__ == "__main__":
    vfd_instance = VFD()
    editor = VFDWordProcessor(vfd_instance)
    editor.run()
