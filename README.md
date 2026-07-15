# Gesture AI (GestureVision)

Control your computer with hand gestures. A Python backend uses your webcam and
MediaPipe to detect hand landmarks and classify gestures in real time, then maps
each gesture to a system action (media controls, mouse, app launching, etc.).
A React + Electron frontend shows a small always-on-top overlay with the live
camera feed, current gesture, and a settings panel to customize gesture ->
action mappings and sensitivity.

## How it works

- **Backend** (`backend/`): a Python WebSocket server (`main.py`, port `8765`)
  that captures webcam frames, runs MediaPipe hand landmark detection
  (`detector.py`), classifies the hand shape into a named gesture
  (`classifier.py`), executes the mapped OS-level action (`automation.py`, via
  `pyautogui`), and stores gesture mappings / history in a local SQLite
  database (`database.py`, `gestures.db`).
- **Frontend** (`frontend/`): a React + Vite UI (`src/App.jsx`) that connects
  to the backend over WebSocket, rendered inside a frameless, transparent,
  always-on-top Electron window (`main.cjs`).

Default gesture -> action mappings (editable from the app's settings panel):

| Gesture | Action |
|---|---|
| Open Palm | No action |
| Closed Fist | Play / Pause |
| Pointing Finger | Move cursor |
| Pinch | Left click |
| Victory Sign | Next slide |
| Thumbs Up | Volume up |
| Thumbs Down | Volume down |
| Three Fingers | Open Chrome |
| Rock Sign | Mute |

## Requirements

- **Windows** (the launcher script and Electron backend path are Windows-specific)
- [Node.js](https://nodejs.org/) 18+ and npm
- [Python](https://www.python.org/) 3.10–3.11 (recommended for MediaPipe compatibility)
- A webcam

## 1. Set up the backend (Python)

```powershell
cd Gesture-AI/backend

# Create a virtual environment named "venv" (required — the Electron app
# looks for backend/venv/Scripts/python.exe)
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install opencv-python mediapipe websockets pyautogui
```

> There is no `requirements.txt` in this project. The commands above install
> every third-party package actually imported by the backend code
> (`cv2`, `mediapipe`, `websockets`, `pyautogui`). If you'd like, I can
> generate a `requirements.txt` from these so future installs are a single
> `pip install -r requirements.txt`.

`hand_landmarker.task` (the MediaPipe hand-landmark model) is already included
in `backend/`, so no separate model download is needed.

## 2. Set up the frontend (Node)

```powershell
cd Gesture-AI/frontend
npm install
```

## 3. Run the app

### Option A — one-click launcher (recommended)

From the project root, in PowerShell:

```powershell
cd Gesture-AI
./start.ps1
```

This clears anything already running on ports `8765` (backend) and `5173`
(Vite dev server), then starts the Electron app, which in turn launches the
Python backend from `backend/venv` and opens the overlay window.

> If PowerShell blocks the script with an execution-policy error, run:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first, then
> re-run `./start.ps1`.

### Option B — run everything manually

**Terminal 1 — backend:**

```powershell
cd Gesture-AI/backend
venv\Scripts\activate
python main.py
```

You should see `[GestureApp] WebSocket server running on ws://localhost:8765`.

**Terminal 2 — frontend (Electron + Vite together):**

```powershell
cd Gesture-AI/frontend
npm run electron:dev
```

This runs `vite` (dev server on `http://localhost:5173`) and, once it's
ready, launches the Electron shell pointed at it.

### Option C — browser only, no Electron

If you just want the UI in a normal browser tab instead of the overlay
window (backend must already be running per Terminal 1 above):

```powershell
cd Gesture-AI/frontend
npm run dev
```

Then open the printed local URL (`http://localhost:5173`) in your browser.

## Other useful frontend commands

```powershell
npm run build      # Production build of the React app (outputs to frontend/dist)
npm run preview    # Preview the production build
npm run lint        # Lint with oxlint
```

## Notes

- The app connects to the backend at `ws://localhost:8765` — make sure the
  backend is running before (or shortly after) opening the frontend.
- Gesture history and mappings persist in `backend/gestures.db` (SQLite),
  which is created automatically on first run. Note that the current
  `database.py` drops and recreates the `gestures` table on every backend
  start, so custom mappings reset to the defaults each run.
- Closing the Electron window also terminates the spawned Python backend
  process.
