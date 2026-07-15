import pyautogui
import subprocess
import sys
import time
import os

# Disable pyautogui failsafe
pyautogui.FAILSAFE = False

# Action labels for display in UI
ACTION_LABELS = {
    'none':          'No Action',
    'cursor_move':   '🖱️ Move Cursor',
    'left_click':    '🖱️ Left Click',
    'right_click':   '🖱️ Right Click',
    'play_pause':    '⏯️ Play / Pause',
    'volume_up':     '🔊 Volume Up',
    'volume_down':   '🔉 Volume Down',
    'mute':          '🔇 Mute',
    'next_track':    '⏭️ Next Track',
    'prev_track':    '⏮️ Prev Track',
    'next_slide':    '▶️ Next Slide',
    'prev_slide':    '◀️ Prev Slide',
    'scroll_up':     '⬆️ Scroll Up',
    'scroll_down':   '⬇️ Scroll Down',
    'open_chrome':   '🌐 Open Chrome',
    'open_explorer': '📁 Open File Explorer',
    'open_calc':     '🔢 Open Calculator',
    'open_vscode':   '💻 Open VS Code',
    'open_spotify':  '🎵 Open Spotify',
    'open_terminal': '🖥️ Open Terminal',
    'alt_tab':       '🔄 Alt + Tab',
    'win_key':       '🪟 Windows Key',
    'close_window':  '❌ Close Window',
    'copy':          '📋 Copy',
    'paste':         '📋 Paste',
    'undo':          '↩️ Undo',
    'custom_shortcut': '⌨️ Custom Shortcut',
}


class AutomationEngine:
    MIN_SENSITIVITY = 500
    MAX_SENSITIVITY = 8000
    DEFAULT_SENSITIVITY = 2800

    def __init__(self, db):
        self.db = db
        self.mappings = self.db.get_mappings()

        self.last_gesture_time = 0
        self.cooldown = 1.2  # seconds between discrete actions

        # Relative cursor tracking
        self.prev_index_x = None
        self.prev_index_y = None

        # Cursor sensitivity is persisted so it survives restarts
        stored = self.db.get_setting('cursor_sensitivity', self.DEFAULT_SENSITIVITY)
        self.sensitivity = self._clamp_sensitivity(stored)

        self.last_action_label = 'Idle'

    def _clamp_sensitivity(self, value):
        try:
            value = int(float(value))
        except (TypeError, ValueError):
            value = self.DEFAULT_SENSITIVITY
        return max(self.MIN_SENSITIVITY, min(self.MAX_SENSITIVITY, value))

    def get_sensitivity(self):
        return self.sensitivity

    def set_sensitivity(self, value):
        self.sensitivity = self._clamp_sensitivity(value)
        self.db.set_setting('cursor_sensitivity', self.sensitivity)
        return self.sensitivity

    def _launch_app(self, windows, macos, linux, windows_shell=False):
        """
        Launches an application using the right command for the current OS.
        `windows`, `macos`, `linux` are each a subprocess.Popen argv list.
        Failures are caught and logged rather than crashing the detection loop
        (e.g. the app isn't installed, or isn't on PATH).
        """
        platform = sys.platform
        try:
            if platform.startswith('win'):
                subprocess.Popen(windows, shell=windows_shell)
            elif platform == 'darwin':
                subprocess.Popen(macos)
            else:
                subprocess.Popen(linux)
        except Exception as e:
            print(f"[AutomationEngine] Could not launch app on {platform}: {e}")

    def execute(self, gesture, hand_landmarks):
        # Refresh mappings
        self.mappings = self.db.get_mappings()

        config = self.mappings.get(gesture, {'action': 'none'})
        action = config.get('action', 'none')
        shortcut = config.get('shortcut', '')

        # --- Continuous: Cursor movement ---
        if action == 'cursor_move':
            index_tip = hand_landmarks.landmark[8]

            if self.prev_index_x is not None and self.prev_index_y is not None:
                dx = index_tip.x - self.prev_index_x
                dy = index_tip.y - self.prev_index_y

                move_x = int(dx * self.sensitivity)
                move_y = int(dy * self.sensitivity)

                if abs(move_x) > 1 or abs(move_y) > 1:
                    pyautogui.move(move_x, move_y, _pause=False)

            self.prev_index_x = index_tip.x
            self.prev_index_y = index_tip.y
            self.last_action_label = ACTION_LABELS['cursor_move']
            return self.last_action_label
        else:
            self.prev_index_x = None
            self.prev_index_y = None

        # --- Discrete actions with cooldown ---
        if action == 'none':
            return 'Idle'

        current_time = time.time()
        if (current_time - self.last_gesture_time) < self.cooldown:
            return self.last_action_label

        self.last_gesture_time = current_time
        label = ACTION_LABELS.get(action, action)

        try:
            if action == 'left_click':
                pyautogui.click()

            elif action == 'right_click':
                pyautogui.click(button='right')

            elif action == 'play_pause':
                pyautogui.press('playpause')

            elif action == 'volume_up':
                for _ in range(5):
                    pyautogui.press('volumeup')

            elif action == 'volume_down':
                for _ in range(5):
                    pyautogui.press('volumedown')

            elif action == 'mute':
                pyautogui.press('volumemute')

            elif action == 'next_track':
                pyautogui.press('nexttrack')

            elif action == 'prev_track':
                pyautogui.press('prevtrack')

            elif action == 'next_slide':
                pyautogui.press('right')

            elif action == 'prev_slide':
                pyautogui.press('left')

            elif action == 'scroll_up':
                pyautogui.scroll(300)

            elif action == 'scroll_down':
                pyautogui.scroll(-300)

            elif action == 'alt_tab':
                pyautogui.hotkey('alt', 'tab')

            elif action == 'win_key':
                pyautogui.press('win')

            elif action == 'close_window':
                pyautogui.hotkey('alt', 'f4')

            elif action == 'copy':
                pyautogui.hotkey('ctrl', 'c')

            elif action == 'paste':
                pyautogui.hotkey('ctrl', 'v')

            elif action == 'undo':
                pyautogui.hotkey('ctrl', 'z')

            elif action == 'open_chrome':
                self._launch_app(
                    windows=['start', 'chrome'],
                    macos=['open', '-a', 'Google Chrome'],
                    linux=['google-chrome'],
                    windows_shell=True,
                )

            elif action == 'open_explorer':
                self._launch_app(
                    windows=['explorer'],
                    macos=['open', os.path.expanduser('~')],
                    linux=['xdg-open', os.path.expanduser('~')],
                    windows_shell=True,
                )

            elif action == 'open_calc':
                self._launch_app(
                    windows=['calc'],
                    macos=['open', '-a', 'Calculator'],
                    linux=['gnome-calculator'],
                    windows_shell=True,
                )

            elif action == 'open_vscode':
                self._launch_app(
                    windows=['code'],
                    macos=['open', '-a', 'Visual Studio Code'],
                    linux=['code'],
                    windows_shell=True,
                )

            elif action == 'open_spotify':
                self._launch_app(
                    windows=['start', 'spotify'],
                    macos=['open', '-a', 'Spotify'],
                    linux=['spotify'],
                    windows_shell=True,
                )

            elif action == 'open_terminal':
                self._launch_app(
                    windows=['start', 'cmd'],
                    macos=['open', '-a', 'Terminal'],
                    linux=['x-terminal-emulator'],
                    windows_shell=True,
                )

            elif action == 'custom_shortcut' and shortcut:
                keys = [k.strip().lower() for k in shortcut.split('+')]
                pyautogui.hotkey(*keys)

        except Exception as e:
            print(f"[AutomationEngine] Error executing {action}: {e}")

        self.db.log_history(gesture, action)
        self.last_action_label = label
        return label
