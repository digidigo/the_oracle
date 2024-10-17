#!/usr/bin/python3

import sys
import os
import logging
import traceback
import signal

print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
print(f"Working directory: {os.getcwd()}")

# Set up logging
logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keymapper.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    # Add the directory containing the script to the Python path
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

    from Quartz import (
        CGEventTapCreate, kCGEventKeyDown, kCGEventTapOptionDefault, kCGHIDEventTap,
        CGEventTapEnable, CFRunLoopAddSource, CFRunLoopRun, kCFRunLoopDefaultMode,
        CGEventCreateKeyboardEvent
    )
    from Quartz import CFRunLoopGetCurrent, CFRunLoopSourceInvalidate
    import ctypes

    logging.info("Successfully imported required modules")
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    sys.exit(1)

# Define mappings from 3-key sequences to characters
key_sequence_mapping = {
    "qweasdzx": "1",
    "tyuhjkbm": "2",
    "iopkl;,.": "3",
    # Add more mappings as needed
}

# A list to keep track of the pressed keys
current_sequence = []

def signal_handler(signum, frame):
    logging.error(f"Received signal {signum}")
    sys.exit(1)

# Add this line before the main() function
signal.signal(signal.SIGTERM, signal_handler)

def key_tap_callback(proxy, event_type, event, refcon):
    try:
        global current_sequence

        if event_type == kCGEventKeyDown:
            keycode = ctypes.c_uint64()
            ctypes.memmove(ctypes.addressof(keycode), event, ctypes.sizeof(keycode))
            
            keymap = {
                12: "q", 13: "w", 14: "e", 15: "r", 17: "t", 16: "y", 32: "u", 34: "i", 31: "o", 35: "p",
                0: "a", 1: "s", 2: "d", 3: "f", 5: "h", 4: "g", 38: "j", 40: "k", 37: "l", 41: ";",
                6: "z", 7: "x", 8: "c", 9: "v", 11: "b", 45: "n", 46: "m", 43: ",", 47: ".", 44: "/"
            }
            
            if keycode.value in keymap:
                current_sequence.append(keymap[keycode.value])
                logging.info(f"Current sequence: {''.join(current_sequence)}")
                
                sequence_str = "".join(current_sequence)
                for mapped_sequence, mapped_char in key_sequence_mapping.items():
                    if sequence_str.endswith(mapped_sequence):
                        logging.info(f"Sequence {mapped_sequence} -> {mapped_char}")
                        new_event = CGEventCreateKeyboardEvent(None, ord(mapped_char), True)
                        current_sequence = []
                        return new_event
                
                if len(current_sequence) > 8:
                    current_sequence = current_sequence[-8:]

        return event
    except Exception as e:
        logging.error(f"An error occurred in key_tap_callback: {e}")
        logging.error(traceback.format_exc())
        return event

def main():
    logging.info("Starting main function")
    logging.info("Attempting to create event tap")
    try:
        tap = CGEventTapCreate(
            kCGHIDEventTap,
            0,
            kCGEventTapOptionDefault,
            kCGEventKeyDown,
            key_tap_callback,
            None
        )

        if not tap:
            logging.error("Failed to create event tap. This might be due to insufficient permissions.")
            return

        logging.info("Event tap created successfully")

        CGEventTapEnable(tap, True)

        run_loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(
            run_loop,
            CFRunLoopSourceInvalidate(tap),
            kCFRunLoopDefaultMode
        )

        logging.info("Starting run loop")
        CFRunLoopRun()
    except Exception as e:
        logging.error(f"An error occurred in main: {e}")
        logging.error(traceback.format_exc())
    finally:
        logging.info("Exiting main function")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)
