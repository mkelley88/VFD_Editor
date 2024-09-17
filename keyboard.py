import evdev

class KeyboardInput:
    def __init__(self):
        # Find the input device for the keyboard
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        self.keyboard = None
        for device in devices:
            if 'keyboard' in device.name.lower():
                self.keyboard = device
                break

        if not self.keyboard:
            raise Exception("No keyboard found")
        
        self.shift_pressed = False  # Track the state of the shift key
        self.control_pressed = False  # Track the state of the control key

    def get_key(self):
        """Get input from the USB keyboard."""
        for event in self.keyboard.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                
                if key_event.keycode == "KEY_LEFTSHIFT" or key_event.keycode == "KEY_RIGHTSHIFT":
                    self.shift_pressed = event.value == 1  # Track shift key press state
                elif key_event.keycode == "KEY_LEFTCTRL" or key_event.keycode == "KEY_RIGHTCTRL":
                    self.control_pressed = event.value == 1  # Track control key press state

                if event.value == 1:  # Key press event
                    key = key_event.keycode
                    return self.modify_key(key)

    def modify_key(self, key):
        """Adjust key output based on whether the shift or control key is pressed."""
        if self.shift_pressed:
            # Handle upper-case letters or special characters when shift is pressed
            shift_map = {
                # Shifted key mappings for characters
                "KEY_A": "A", "KEY_B": "B", "KEY_C": "C", "KEY_D": "D", "KEY_E": "E",
                "KEY_F": "F", "KEY_G": "G", "KEY_H": "H", "KEY_I": "I", "KEY_J": "J",
                "KEY_K": "K", "KEY_L": "L", "KEY_M": "M", "KEY_N": "N", "KEY_O": "O",
                "KEY_P": "P", "KEY_Q": "Q", "KEY_R": "R", "KEY_S": "S", "KEY_T": "T",
                "KEY_U": "U", "KEY_V": "V", "KEY_W": "W", "KEY_X": "X", "KEY_Y": "Y",
                "KEY_Z": "Z", "KEY_1": "!", "KEY_2": "@", "KEY_3": "#", "KEY_4": "$",
                "KEY_5": "%", "KEY_6": "^", "KEY_7": "&", "KEY_8": "*", "KEY_9": "(",
                "KEY_0": ")", "KEY_MINUS": "_", "KEY_EQUAL": "+", "KEY_LEFTBRACE": "{",
                "KEY_RIGHTBRACE": "}", "KEY_SEMICOLON": ":", "KEY_APOSTROPHE": "\"",
                "KEY_GRAVE": "~", "KEY_BACKSLASH": "|", "KEY_COMMA": "<", "KEY_DOT": ">",
                "KEY_SLASH": "?"
            }
            return shift_map.get(key, key)
        else:
            # Return the unshifted or lowercase equivalent
            lower_map = {
                "KEY_A": "a", "KEY_B": "b", "KEY_C": "c", "KEY_D": "d", "KEY_E": "e",
                "KEY_F": "f", "KEY_G": "g", "KEY_H": "h", "KEY_I": "i", "KEY_J": "j",
                "KEY_K": "k", "KEY_L": "l", "KEY_M": "m", "KEY_N": "n", "KEY_O": "o",
                "KEY_P": "p", "KEY_Q": "q", "KEY_R": "r", "KEY_S": "s", "KEY_T": "t",
                "KEY_U": "u", "KEY_V": "v", "KEY_W": "w", "KEY_X": "x", "KEY_Y": "y",
                "KEY_Z": "z", "KEY_1": "1", "KEY_2": "2", "KEY_3": "3", "KEY_4": "4",
                "KEY_5": "5", "KEY_6": "6", "KEY_7": "7", "KEY_8": "8", "KEY_9": "9",
                "KEY_0": "0", "KEY_MINUS": "-", "KEY_EQUAL": "=", "KEY_LEFTBRACE": "[",
                "KEY_RIGHTBRACE": "]", "KEY_SEMICOLON": ";", "KEY_APOSTROPHE": "'",
                "KEY_GRAVE": "`", "KEY_BACKSLASH": "\\", "KEY_COMMA": ",", "KEY_DOT": ".",
                "KEY_SLASH": "/"
            }
            return lower_map.get(key, key)
