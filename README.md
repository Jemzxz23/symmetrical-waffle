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

---

## Hotkeys
- **F4** — Start detection (and auto-clicking)
- **F3** — Stop detection
- **F5** — Set detection area (drag + resize the red box, press **Enter** to confirm)

---

## Requirements
### 1) Python
Python 3.9+ recommended.

### 2) Install Python packages
Open a terminal inside the project folder and run:

```bash
pip install pytesseract pillow pyautogui keyboard
