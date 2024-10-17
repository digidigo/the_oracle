#!/usr/bin/python3

import sys
import os
import logging
import traceback
import signal
import time

print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"System path: {sys.path}")

# Set up logging
logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keymapper.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    # Add the directory containing the script to the Python path
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

    logging.info("Attempting to import Quartz...")
    from Quartz import (
        CGEventTapCreate, kCGEventKeyDown, kCGEventTapOptionDefault, kCGSessionEventTap,
        CGEventTapEnable, CFRunLoopAddSource, CFRunLoopRun, kCFRunLoopDefaultMode,
        CGEventCreateKeyboardEvent, CFMachPortCreateRunLoopSource, CFRunLoopGetCurrent,
        CGEventGetIntegerValueField, kCGKeyboardEventKeycode, kCGHIDEventTap
    )
    logging.info("Quartz imported successfully")
    
    logging.info("Importing ctypes...")
    import ctypes
    logging.info("ctypes imported successfully")

    logging.info("Successfully imported required modules")
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    logging.error(traceback.format_exc())
    sys.exit(1)

# Define mappings from 3-key sequences to characters
key_sequence_mapping = {
    "qqq": "1",
    "ttt": "2",
    "iii": "3",
    # Add more mappings as needed
}

# A list to keep track of the pressed keys
current_sequence = []

def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}. Exiting...")
    print("KeyMapper is shutting down...")
    sys.exit(0)

# Set up signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def key_tap_callback(proxy, event_type, event, refcon):
    global current_sequence
    logging.info(f"Callback triggered. Event type: {event_type}")

    if event_type == kCGEventKeyDown:
        keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
        logging.info(f"Key Down Event - Keycode: {keycode}")

        keymap = {
            12: "q", 13: "w", 14: "e", 15: "r", 17: "t", 16: "y", 32: "u", 34: "i", 31: "o", 35: "p",
            0: "a", 1: "s", 2: "d", 3: "f", 5: "h", 4: "g", 38: "j", 40: "k", 37: "l", 41: ";",
            6: "z", 7: "x", 8: "c", 9: "v", 11: "b", 45: "n", 46: "m", 43: ",", 47: ".", 44: "/"
        }
        
        if keycode in keymap:
            pressed_key = keymap[keycode]
            current_sequence.append(pressed_key)
            logging.info(f"Key pressed: {pressed_key}")
            logging.info(f"Current sequence: {''.join(current_sequence)}")
            
            sequence_str = "".join(current_sequence)
            for mapped_sequence, mapped_char in key_sequence_mapping.items():
                if sequence_str.endswith(mapped_sequence):
                    logging.info(f"Sequence {mapped_sequence} -> {mapped_char}")
                    new_event = CGEventCreateKeyboardEvent(None, ord(mapped_char), True)
                    current_sequence = []
                    logging.info("Returning new event")
                    return new_event
            
            if len(current_sequence) > 8:
                current_sequence = current_sequence[-8:]
        else:
            logging.info(f"Keycode {keycode} not in keymap")
        
        return 
    else:
        logging.info(f"Non-Key Down Event - Type: {event_type}")

    logging.info("Returning original event")
    return event

def main():
    logging.info("Starting main function")
    logging.info("Attempting to create event tap")
    try:
        tap = CGEventTapCreate(
            kCGHIDEventTap,
            0,  # Use 0 instead of kCGHeadInsertEventTap
            kCGEventTapOptionDefault,
            1 << kCGEventKeyDown,  # Only capture key down events
            key_tap_callback,
            None
        )

        if not tap:
            logging.error("Failed to create event tap. This might be due to insufficient permissions.")
            return

        logging.info("Event tap created successfully")

        CGEventTapEnable(tap, True)
        logging.info("Event tap enabled")

        run_loop_source = CFMachPortCreateRunLoopSource(None, tap, 0)
        run_loop = CFRunLoopGetCurrent()

        CFRunLoopAddSource(run_loop, run_loop_source, kCFRunLoopDefaultMode)

        logging.info("KeyMapper is now running. Press Ctrl+C to exit.")
        print("KeyMapper is now running. Press Ctrl+C to exit.")

        CFRunLoopRun()
    except Exception as e:
        logging.error(f"An error occurred in main: {e}")
        logging.error(traceback.format_exc())
    finally:
        logging.info("Exiting main function")
        print("KeyMapper has shut down.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        logging.error(traceback.format_exc())
    finally:
        logging.info("Script execution completed")
