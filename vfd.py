import time
import RPi.GPIO as GPIO
# VFD Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
GPIO.setwarnings(False)

# VFD Data Commands
VFD_BS = 0x08  # DC1 or DC2 Mode: The cursor position is shifted to the left by one character position.
VFD_HT = 0x09  # DC1 Mode: The cursor position is shifted to the right by one character position.
VFD_CR = 0x0D  # DC1 or DC2 Mode: The cursor is positioned on the leftmost position of the same line.
VFD_LF = 0x0A  # Line Feed (LF) - Moves the cursor position to the same column in the other row.
VFD_FF = 0x0C  # Form Feed (FF) - Unknown if working on this model
VFD_RS = 0x50  # Clears the display, cursor position to 0,0
VFD_DC1 = 0x11  # DC1 – Normal display mode.
VFD_DC2 = 0x12  # DC2 – Vertical scroll mode.
VFD_DC3 = 0x13  # Underline cursor.
VFD_DC4 = 0x14  # Block cursor.
VFD_DC5 = 0x15  # Cursor off.
VFD_DC6 = 0x16  # Blinking mode.

class VFD:
    def __init__(self):
        '''Initializes the hardware for the VFD display'''
        # GPIO pin setup (BCM numbering)
        self.data_pins = [9, 10, 22, 27, 17, 4, 3, 2]
        self.wr = 11  # Write pin
        self.ad = 5  # AD pin
        self.rd = 6  # Read pin 
        self.cs = 13  # Chip Select pin
        
        # Set pins as output
        for pin in self.data_pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.wr, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.ad, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.rd, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.cs, GPIO.OUT, initial=GPIO.LOW)
    
    def init_display(self):
        '''Initializes the VFD display screen'''
        self.send_command(VFD_RS) # Reset display
        time.sleep(0.2)          # Wait for reset
        self.send_data(VFD_DC1) # Normal display mode
        time.sleep(0.2)          # Wait for reset
        self.send_data(VFD_DC6) # Blinking mode
        
    def clear(self):
        '''
        Clears the VFD display and moves the cursor to the home position.
        
        This method writes 80 spaces to the VFD and then moves the cursor to the
        home position (0,0).
        '''
        
        self.write(" " * 80)  # Clear all 80 positions of the VFD
        self.set_cursor(0)       # Set cursor position to 0
    
    def send_command(self, cmd):
        """
        Sends a single byte command to the VFD display.

        :param cmd: The byte command to send
        """
        self.send_byte(cmd, is_command=True)
    
    def send_data(self, data):
        """
        Sends a single byte of data to the VFD display.

        :param data: The byte of data to send
        """
        self.send_byte(data, is_command=False)
    
    def send_byte(self, byte, is_command):
        """
        Sends a single byte to the VFD display.

        :param byte: The byte to send
        :param is_command: True if the byte is a command, False if it is data
        """
        GPIO.output(self.ad, is_command)
        GPIO.output(self.wr, 0)
        for i in range(8):
            GPIO.output(self.data_pins[i], (byte >> i) & 0x01)
        time.sleep(0.00005)  # 50us delay
        GPIO.output(self.wr, 1)

    def reset(self):
        '''Resets the VFD display. The display is reset to its power-on state, and the cursor is set to the home position.'''
        self.send_command(VFD_RS)
        time.sleep(0.005)
        self.clear()
    
    def set_cursor(self, pos):
        """
        Sets the cursor position on the VFD display.

        :param pos: The position to set the cursor to (0-79)
        """
        self.send_command(pos)
    
    def write(self, text):
        """
        Writes a string of text to the VFD display.

        :param text: The string of text to write
        """
        for char in text:
            self.send_data(ord(char))

    def set_brightness(self, level):
        """
        Sets the brightness of the VFD display.

        :param level: The brightness level to set (0-15)
        """
        self.send_command(VFD_SUB)
        self.send_data(level)

    def get_byte(self, is_command):
        """
        Reads a byte from the VFD display.

        :param is_command: True if the byte to be read is a command, False if it is data
        :return: The read byte
        """
        
        GPIO.output(self.ad, is_command)
        GPIO.output(self.rd, 0)  # Enable read

        # Set pins to input mode
        for pin in self.data_pins:
            GPIO.setup(pin, GPIO.IN)

        time.sleep(0.00005)  # 50us delay
        
        # Read the byte from data pins
        byte = 0
        for i in range(8):
            byte |= GPIO.input(self.data_pins[i]) << i

        GPIO.output(self.rd, 1)  # Disable read

        # Set pins back to output mode
        for pin in self.data_pins:
            GPIO.setup(pin, GPIO.OUT)

        return byte

    def cleanup(self):
        """
        Clean up GPIO allocation.
        """
        GPIO.cleanup()
