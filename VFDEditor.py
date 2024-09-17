# VFDEditor.py
# Main logic for handling the text buffer and integrating Keyboard input for Raspberry Pi Zero W
import time
from vfd import VFD  # Import VFD display functions
from file_ops import FileOperations  # Import FileOperations module
from keyboard import KeyboardInput  # Import Keyboard input module

class VFDWordProcessor:
    """This class represents a word processor for VFD (Vacuum Fluorescent Display) technology."""

    VFD_BS = 0x08  # Backspace command for the VFD
    VFD_CR = 0x0D  # Carriage return command (start of line)
    VFD_LINEFEED = 0x0A  # Line feed (next row)

    def __init__(self, vfd):
        self.vfd = vfd
        self.keyboard_input = KeyboardInput()  # Initialize Keyboard input
        self.file_ops = FileOperations(vfd, self.keyboard_input)  # Initialize FileOperations
        self.open_filename = ""  # Opened file name
        self.buffer = bytearray(16384)  # 16KB text buffer for storing text
        self.buffer_pos = 0  # Current position in the buffer
        self.used_buffer_size = 0  # Track how much of the buffer has been used
        self.visible_start = 0  # Start of visible window in the buffer
        self.visible_end = 80  # End of visible window (40x2)
        self.cursor_pos = 0  # Current cursor position on the screen
        self.cursor_row = 0  # Row position of the cursor
        
        self.insert_mode = False  # Insert mode flag
        self.vfd.init_display()  # Initialize the VFD display
        self.vfd.clear()

        # Welcome message
        self.vfd.write("VFD Editor")
        self.update_display()
    def run(self):
        """Main loop to read USB keyboard input and update the buffer."""
        display_needs_update = False  # Flag to track whether the display should be updated

        while True:
            key = self.keyboard_input.get_key()

            # Check if Control key is pressed
            if self.keyboard_input.control_pressed:
                print(key)
                if key == "s":
                    self.save_file()  # Trigger save function
                    continue
                elif key == "o":
                    self.open_file()  # Trigger open function
                    display_needs_update = True  # File opened, update needed
                    continue
                elif key == "O":
                    self.file_ops.choose_file_from_list(self.buffer)  # Trigger open list function
                    display_needs_update = True  # File opened, update needed
                    continue
                elif key == "`":
                    self.vfd.clear()  # Clear the screen
                    self.vfd.write(f"File: {self.open_filename}")    # Display file name
                    time.sleep(2)      # Wait for 2 seconds
                    display_needs_update = True  # File opened, update needed
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
            elif key == 'KEY_ENTER':
                self.insert_char('\n')
                display_needs_update = True
            elif key == "KEY_SPACE":
                self.insert_char(' ')
                display_needs_update = True
            elif key == 'KEY_BACKSPACE':
                self.delete_char()
                display_needs_update = True
            elif key is not None and len(key) == 1:
                self.insert_char(key)  # Insert the valid character
                display_needs_update = True

            # Update display only if needed
            if display_needs_update:
                self.update_display()
                display_needs_update = False


    def insert_char(self, char):
        """Insert a character into the buffer based on the current mode (insert/overwrite)."""
        if self.insert_mode:
            # Insert mode: Shift the buffer content to the right
            if self.buffer_pos < len(self.buffer) - 1:  # Make sure not to exceed buffer size
                self.buffer[self.buffer_pos + 1:] = self.buffer[self.buffer_pos:-1]
                self.buffer[self.buffer_pos] = ord(char)
                self.buffer_pos += 1
        else:
            # Overwrite mode: Replace the current character
            if self.buffer_pos < len(self.buffer):
                self.buffer[self.buffer_pos] = ord(char)
                self.buffer_pos += 1

        self.update_cursor_position()




    def delete_char(self):
        """Delete the character at the current position."""
        if self.buffer_pos > 0:
            self.buffer[self.buffer_pos - 1] = 0
            self.buffer_pos -= 1
            self.update_cursor_position()

    def move_cursor_up(self):
        """Move the cursor up by 1 row."""
        if self.visible_start >= 40:
            self.visible_start -= 40
            self.visible_end -= 40
        elif self.visible_start < 40:
            self.buffer_pos = max(
                0, self.buffer_pos - 40
            )  # Move the cursor to the start of the buffer
            self.update_cursor_position()
        self.update_display()

    def move_cursor_down(self):
        """Move the cursor down by 1 row."""
        if self.visible_end < len(self.buffer):
            self.visible_start += 40
            self.visible_end += 40
        # TODO: it should not be possible to move the cursor or visible  past the end of the buffer
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
            self.visible_start += 40  # Move the visible window down by 40 characters (one row)
            self.visible_end += 40
            self.cursor_pos = self.buffer_pos - self.visible_start  # Adjust the cursor position

        self.vfd.set_cursor(self.cursor_pos)
        # DEBUG CODE - LEAVE HERE
        print(f"Cursor position: {self.cursor_pos}")
        print(f"Buffer position: {self.buffer_pos}")
        print(f"Visible start: {self.visible_start}")
        print(f"Visible end: {self.visible_end}"
        )


    def update_display(self):
        """Update the VFD display by replacing newline characters with '`' inline."""
        visible_text = ""

        # Loop through the visible part of the buffer
        for i in range(self.visible_start, self.visible_end):
            char = self.buffer[i]
            if char == ord('\n'):
                visible_text += "`"  # Display '`' in place of the newline character
            else:
                visible_text += chr(char) if char != 0 else " "  # Convert byte to character or space

        self.vfd.clear()
        self.vfd.write(f"{visible_text:<80}")  # Ensure the display always shows 80 characters
        self.vfd.set_cursor(self.cursor_pos)


    def save_file(self):
        """Save the buffer to a file."""
        self.open_filename = self.file_ops.save_file(self.buffer, self.open_filename)


    def open_file(self):
        """Open a file and load it into the buffer."""
        self.open_filename = self.file_ops.open_file(self.buffer)
        self.buffer_pos = self.calculate_used_buffer()  # Reset buffer position


if __name__ == "__main__":
    vfd = VFD()
    editor = VFDWordProcessor(vfd)
    editor.run()
    vfd.cleanup()
