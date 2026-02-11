# Screen Text Detector + Auto Clicker (OCR)

A small desktop tool that uses **Tesseract OCR** to read text on your screen and automatically clicks until your target text appears.  
You can select a detection area, test OCR results, and run it with simple hotkeys.

> Not affiliated with any game or app. Use responsibly.

---

## What it does
- You type a **target text** (a word/phrase you expect to appear on screen).
- The app takes screenshots of either:
  - the full screen, or
  - a region you select
- It runs OCR on that screenshot.
- It keeps clicking the screen center every X seconds until the target text is found.
- Runs through your screen and with forgiving color detecton enchancer for Text that has a lot of colors higly hue colors that mostly OCR detection will ignore

---

## Hotkeys
- **F4** — Start detection (and auto-clicking)
- **F3** — Stop detection
- **F5** — Set detection area (drag + resize the red box, press **Enter** to confirm)

---

## Limitation
- Due to Tesseract OCR having a hard time detecting small letters with high color values, I highly recommend to Zoom In / Enlarge the the Letters if possible

---
## Requirements
### 1) Python
Python 3.9+ recommended.

### 2) Install Python packages
Open a terminal inside the project folder and run:

```bash
pip install pyautogui pytesseract pillow numpy opencv-python keyboard requests
