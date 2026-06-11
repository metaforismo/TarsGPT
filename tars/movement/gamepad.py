"""8BitDo Zero 2 gamepad mapping: manual driving alongside (or without) the AI."""
import logging
from .gaits import Gaits

log = logging.getLogger("tars.gamepad")

# evdev key codes as reported by the 8BitDo Zero 2 in keyboard mode
KEYMAP = {
    37: "l_trigger", 50: "r_trigger",
    46: "up", 32: "down", 18: "left", 33: "right",
    23: "x", 35: "y", 36: "a", 34: "b",
    49: "minus", 24: "plus",
}


GAMEPAD_NAMES = ("8bitdo", "gamepad", "controller", "joystick", "joypad")


def find_gamepad() -> str | None:
    """Scan input devices for something that looks like a game controller."""
    try:
        import evdev
    except ImportError:
        return None
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            if any(tag in dev.name.lower() for tag in GAMEPAD_NAMES):
                return path
        except (OSError, PermissionError):
            continue
    return None


def run(gaits: Gaits, device_path: str):
    """Blocking event loop; run it in its own thread."""
    try:
        from evdev import InputDevice, ecodes
    except ImportError:
        log.warning("evdev not installed - gamepad disabled")
        return
    try:
        pad = InputDevice(device_path)
    except (FileNotFoundError, PermissionError):
        found = find_gamepad()
        if found is None:
            log.warning("No gamepad at %s and none autodetected", device_path)
            return
        log.info("Gamepad autodetected at %s (configured %s was unavailable)",
                 found, device_path)
        pad = InputDevice(found)

    log.info("Gamepad connected: %s", pad.name)
    arm_direction = 1  # toggled by +/- buttons

    for event in pad.read_loop():
        if event.type != ecodes.EV_KEY or event.value != 1:
            continue
        btn = KEYMAP.get(event.code)
        if btn == "up":
            gaits.step_forward()
        elif btn == "left":
            gaits.turn_left()
        elif btn == "right":
            gaits.turn_right()
        elif btn == "down":
            gaits.pose()
        elif btn == "plus":
            arm_direction = 1
        elif btn == "minus":
            arm_direction = -1
        elif btn == "l_trigger":
            gaits.nudge_arm("port_main", arm_direction)
        elif btn == "r_trigger":
            gaits.nudge_arm("star_main", arm_direction)
        elif btn == "y":
            gaits.nudge_arm("port_forearm", arm_direction)
        elif btn == "x":
            gaits.nudge_arm("star_forearm", arm_direction)
        elif btn == "b":
            gaits.nudge_arm("port_hand", arm_direction)
        elif btn == "a":
            gaits.nudge_arm("star_hand", arm_direction)
