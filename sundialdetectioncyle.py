import pyautogui
import pytesseract
from PIL import ImageGrab
import time
import keyboard
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from datetime import datetime
import json


class ResizableDetectionArea(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.is_adjusting = True

        # Window settings
        self.attributes('-alpha', 0.3)  # Transparency
        self.attributes('-topmost', True)  # Always on top
        self.overrideredirect(True)  # Remove window decorations
        self.configure(bg='red')

        # Default size and position
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.width = 400
        self.height = 300
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        self.geometry(f'{self.width}x{self.height}+{self.x}+{self.y}')

        # Variables for dragging/resizing
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None

        # Create main frame
        self.main_frame = tk.Frame(self, bg='red')
        self.main_frame.place(relwidth=1, relheight=1)

        # Label with instructions
        self.label = tk.Label(
            self.main_frame,
            text='DETECTION AREA\n\nDrag center to move\nDrag yellow corners to resize\n\nPress ENTER to confirm',
            bg='red',
            fg='white',
            font=('Arial', 11, 'bold'),
            justify='center'
        )
        self.label.place(relx=0.5, rely=0.5, anchor='center')

        # Bind dragging to the label only
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.on_drag)
        self.label.bind('<ButtonRelease-1>', self.stop_drag)

        # Create resize handles
        self.create_resize_handles()

        # Bind Enter and Escape keys
        self.bind('<Return>', self.confirm_area)
        self.bind('<Escape>', self.cancel_area)

        self.focus_force()

    def create_resize_handles(self):
        """Create resize handles at corners"""
        handle_size = 20

        # Top-left corner
        self.nw_handle = tk.Label(self, bg='yellow', cursor='size_nw_se', width=2, height=1)
        self.nw_handle.place(x=0, y=0, width=handle_size, height=handle_size)
        self.nw_handle.bind('<Button-1>', lambda e: self.start_resize('nw', e))
        self.nw_handle.bind('<B1-Motion>', lambda e: self.on_resize(e))
        self.nw_handle.bind('<ButtonRelease-1>', self.stop_resize)

        # Top-right corner
        self.ne_handle = tk.Label(self, bg='yellow', cursor='size_ne_sw', width=2, height=1)
        self.ne_handle.place(x=self.width-handle_size, y=0, width=handle_size, height=handle_size)
        self.ne_handle.bind('<Button-1>', lambda e: self.start_resize('ne', e))
        self.ne_handle.bind('<B1-Motion>', lambda e: self.on_resize(e))
        self.ne_handle.bind('<ButtonRelease-1>', self.stop_resize)

        # Bottom-left corner
        self.sw_handle = tk.Label(self, bg='yellow', cursor='size_ne_sw', width=2, height=1)
        self.sw_handle.place(x=0, y=self.height-handle_size, width=handle_size, height=handle_size)
        self.sw_handle.bind('<Button-1>', lambda e: self.start_resize('sw', e))
        self.sw_handle.bind('<B1-Motion>', lambda e: self.on_resize(e))
        self.sw_handle.bind('<ButtonRelease-1>', self.stop_resize)

        # Bottom-right corner
        self.se_handle = tk.Label(self, bg='yellow', cursor='size_nw_se', width=2, height=1)
        self.se_handle.place(x=self.width-handle_size, y=self.height-handle_size, width=handle_size, height=handle_size)
        self.se_handle.bind('<Button-1>', lambda e: self.start_resize('se', e))
        self.se_handle.bind('<B1-Motion>', lambda e: self.on_resize(e))
        self.se_handle.bind('<ButtonRelease-1>', self.stop_resize)

    def update_handle_positions(self):
        """Update positions of resize handles"""
        handle_size = 20
        self.ne_handle.place(x=self.width-handle_size, y=0)
        self.sw_handle.place(x=0, y=self.height-handle_size)
        self.se_handle.place(x=self.width-handle_size, y=self.height-handle_size)

    def start_drag(self, event):
        """Start dragging the window"""
        if not self.is_resizing:
            self.is_dragging = True
            self.drag_start_x = event.x_root - self.winfo_x()
            self.drag_start_y = event.y_root - self.winfo_y()

    def on_drag(self, event):
        """Handle window dragging"""
        if self.is_dragging and not self.is_resizing:
            self.x = event.x_root - self.drag_start_x
            self.y = event.y_root - self.drag_start_y
            self.geometry(f'{self.width}x{self.height}+{self.x}+{self.y}')

    def stop_drag(self, event):
        """Stop dragging"""
        self.is_dragging = False

    def start_resize(self, corner, event):
        """Start resizing from a corner"""
        self.is_resizing = True
        self.resize_corner = corner
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.resize_start_width = self.width
        self.resize_start_height = self.height
        self.resize_start_win_x = self.x
        self.resize_start_win_y = self.y

    def on_resize(self, event):
        """Handle window resizing"""
        if not self.is_resizing:
            return

        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y
        min_size = 100

        if self.resize_corner == 'se':
            new_width = max(min_size, self.resize_start_width + dx)
            new_height = max(min_size, self.resize_start_height + dy)
            self.width = new_width
            self.height = new_height

        elif self.resize_corner == 'sw':
            new_width = max(min_size, self.resize_start_width - dx)
            new_height = max(min_size, self.resize_start_height + dy)
            if new_width >= min_size:
                self.x = self.resize_start_win_x + dx
                self.width = new_width
                self.height = new_height

        elif self.resize_corner == 'ne':
            new_width = max(min_size, self.resize_start_width + dx)
            new_height = max(min_size, self.resize_start_height - dy)
            self.width = new_width
            if new_height >= min_size:
                self.y = self.resize_start_win_y + dy
                self.height = new_height

        elif self.resize_corner == 'nw':
            new_width = max(min_size, self.resize_start_width - dx)
            new_height = max(min_size, self.resize_start_height - dy)
            if new_width >= min_size:
                self.x = self.resize_start_win_x + dx
                self.width = new_width
            if new_height >= min_size:
                self.y = self.resize_start_win_y + dy
                self.height = new_height

        self.geometry(f'{self.width}x{self.height}+{self.x}+{self.y}')
        self.update_handle_positions()

    def stop_resize(self, event):
        """Stop resizing"""
        self.is_resizing = False
        self.resize_corner = None

    def confirm_area(self, event=None):
        """Confirm the selected area"""
        self.callback(self.x, self.y, self.width, self.height)
        self.is_adjusting = False
        self.destroy()

    def cancel_area(self, event=None):
        """Cancel area selection"""
        self.is_adjusting = False
        self.destroy()


class ScreenTextDetectorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Text Detector")
        self.root.geometry("550x640")

        self.running = False
        self.detection_thread = None
        self.hotkey_thread = None
        self.detection_area = None

        self.target_text = ""
        self.click_delay = 0.5
        self.debug_mode = True
        self.save_screenshots = False

        # tesseract path stored in settings
        self.tesseract_path = ""

        # Config file path
        self.config_file = "detector_settings.json"

        # Create debug folder
        self.debug_folder = "debug_screenshots"
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)

        # Load settings before creating widgets (also tries to apply saved tesseract_path)
        self.load_settings()

        # NEW: If settings didn't provide a valid path, attempt auto-find
        if not self._is_valid_tesseract_path(self.tesseract_path):
            auto = self.auto_find_tesseract()
            if auto:
                self.tesseract_path = auto
                pytesseract.pytesseract.tesseract_cmd = auto
                # Save immediately so next run is ready
                # Widgets not created yet, so call a lightweight save after create_widgets (below)
                self._pending_save_after_ui = True
            else:
                self._pending_save_after_ui = False
        else:
            self._pending_save_after_ui = False

        self.create_widgets()
        self.setup_hotkeys()
        self.apply_loaded_settings()

        # Save if auto-found before UI existed
        if self._pending_save_after_ui:
            self.save_settings()

        if self._is_valid_tesseract_path(self.tesseract_path):
            self.status_label.config(text="Status: Tesseract ready. Ready.", fg="blue")
        else:
            self.status_label.config(text="Status: Please set Tesseract (Browse...)", fg="red")

    def _is_valid_tesseract_path(self, path: str) -> bool:
        if not path:
            return False
        if not os.path.exists(path):
            return False
        return os.path.basename(path).lower() == "tesseract.exe"

    def auto_find_tesseract(self):
        """
        Try common Windows install locations for Tesseract.
        Returns full path to tesseract.exe if found, else None.
        """
        candidates = []

        # 1) Typical default install (system-wide)
        candidates.append(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        candidates.append(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe")

        # 2) User-local installs like your old hardcoded path
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            candidates.append(os.path.join(local_appdata, r"Programs\Tesseract-OCR\tesseract.exe"))

        # 3) If user has it on PATH, try calling "where"
        #    This is safe: if it fails, just ignore.
        try:
            import subprocess
            out = subprocess.check_output(["where", "tesseract"], stderr=subprocess.STDOUT, text=True)
            for line in out.splitlines():
                line = line.strip()
                if line.lower().endswith("tesseract.exe"):
                    candidates.append(line)
        except Exception:
            pass

        # Return the first existing candidate
        for p in candidates:
            if self._is_valid_tesseract_path(p):
                return p
        return None

    def load_settings(self):
        """Load settings from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)

                self.target_text = settings.get('target_text', 'colossal ethereal dragon')
                self.click_delay = settings.get('click_delay', 0.5)
                self.debug_mode = settings.get('debug_mode', True)
                self.save_screenshots = settings.get('save_screenshots', False)

                self.tesseract_path = settings.get('tesseract_path', "")

                # Try apply if valid
                if self._is_valid_tesseract_path(self.tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

                area = settings.get('detection_area', None)
                if area and len(area) == 4:
                    self.detection_area = tuple(area)

                print(f"✓ Settings loaded from {self.config_file}")
        except Exception as e:
            print(f"Could not load settings: {e}")
            self.target_text = 'colossal ethereal dragon'
            self.click_delay = 0.5
            self.debug_mode = True
            self.save_screenshots = False
            self.detection_area = None
            self.tesseract_path = ""

    def save_settings(self):
        """Save current settings to config file"""
        try:
            settings = {
                'target_text': self.text_entry.get().strip(),
                'click_delay': float(self.delay_entry.get()),
                'debug_mode': self.debug_var.get(),
                'save_screenshots': self.screenshot_var.get(),
                'detection_area': list(self.detection_area) if self.detection_area else None,
                'tesseract_path': self.tesseract_path
            }

            with open(self.config_file, 'w') as f:
                json.dump(settings, indent=4, fp=f)

            print(f"✓ Settings saved to {self.config_file}")
        except Exception as e:
            print(f"Could not save settings: {e}")

    def apply_loaded_settings(self):
        """Apply loaded settings to UI elements"""
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, self.target_text)

        self.delay_entry.delete(0, tk.END)
        self.delay_entry.insert(0, str(self.click_delay))

        self.debug_var.set(self.debug_mode)
        self.screenshot_var.set(self.save_screenshots)

        self.tess_path_var.set(self.tesseract_path)

        if self.detection_area:
            x, y, x2, y2 = self.detection_area
            width = x2 - x
            height = y2 - y
            self.area_label.config(text=f"Detection Area: x={x}, y={y}, width={width}, height={height}")
        else:
            self.area_label.config(text="Detection Area: Full Screen")

    def browse_tesseract(self):
        """Let user pick tesseract.exe using File Explorer"""
        path = filedialog.askopenfilename(
            title="Select tesseract.exe",
            filetypes=[("Tesseract executable", "tesseract.exe"), ("All files", "*.*")]
        )
        if not path:
            return

        if not self._is_valid_tesseract_path(path):
            messagebox.showerror("Invalid file", "Please select a valid tesseract.exe")
            return

        self.tesseract_path = path
        self.tess_path_var.set(path)
        pytesseract.pytesseract.tesseract_cmd = path

        self.save_settings()
        self.status_label.config(text="Status: Tesseract path set. Ready.", fg="blue")
        messagebox.showinfo("Tesseract set", f"Tesseract path saved:\n{path}")

    def create_widgets(self):
        """Create the main GUI"""
        title = tk.Label(
            self.root,
            text="Screen Text Detector & Auto-Clicker",
            font=('Arial', 16, 'bold'),
            pady=10
        )
        title.pack()

        hotkey_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        hotkey_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(
            hotkey_frame,
            text="Hotkeys:",
            font=('Arial', 11, 'bold'),
            bg='#f0f0f0'
        ).pack(anchor='w', padx=10)

        tk.Label(
            hotkey_frame,
            text="F4 - Start Detection | F3 - Stop Detection | F5 - Set Detection Area",
            font=('Arial', 9),
            bg='#f0f0f0',
            fg='#555'
        ).pack(anchor='w', padx=10)

        # Tesseract path selector
        tess_frame = tk.Frame(self.root, pady=5)
        tess_frame.pack(fill='x', padx=20)

        tk.Label(tess_frame, text="Tesseract path (tesseract.exe):", font=('Arial', 10)).pack(anchor='w')

        self.tess_path_var = tk.StringVar(value=self.tesseract_path)
        tess_entry = tk.Entry(tess_frame, textvariable=self.tess_path_var, font=('Arial', 10))
        tess_entry.pack(fill='x', pady=4)

        tk.Button(
            tess_frame,
            text="Browse tesseract.exe",
            font=('Arial', 10, 'bold'),
            command=self.browse_tesseract
        ).pack(anchor='w')

        # Target text input
        text_frame = tk.Frame(self.root, pady=10)
        text_frame.pack(fill='x', padx=20)

        tk.Label(text_frame, text="Target Text:", font=('Arial', 10)).pack(anchor='w')
        self.text_entry = tk.Entry(text_frame, font=('Arial', 11), width=50)
        self.text_entry.pack(fill='x', pady=5)

        # Click delay
        delay_frame = tk.Frame(self.root, pady=10)
        delay_frame.pack(fill='x', padx=20)

        tk.Label(delay_frame, text="Click Delay (seconds):", font=('Arial', 10)).pack(anchor='w')
        self.delay_entry = tk.Entry(delay_frame, font=('Arial', 11), width=10)
        self.delay_entry.pack(anchor='w', pady=5)

        # Debug options
        debug_frame = tk.Frame(self.root, pady=5)
        debug_frame.pack(fill='x', padx=20)

        self.debug_var = tk.BooleanVar(value=True)
        self.debug_check = tk.Checkbutton(
            debug_frame,
            text="Show detected text in console (Debug Mode)",
            variable=self.debug_var,
            font=('Arial', 9)
        )
        self.debug_check.pack(anchor='w')

        self.screenshot_var = tk.BooleanVar(value=False)
        self.screenshot_check = tk.Checkbutton(
            debug_frame,
            text="Save screenshots for debugging",
            variable=self.screenshot_var,
            font=('Arial', 9)
        )
        self.screenshot_check.pack(anchor='w')

        # Detection area button
        area_frame = tk.Frame(self.root, pady=10)
        area_frame.pack(fill='x', padx=20)

        self.area_button = tk.Button(
            area_frame,
            text="Set Detection Area (F5)",
            font=('Arial', 11, 'bold'),
            bg='#ff6b6b',
            fg='white',
            command=self.open_area_selector,
            height=2
        )
        self.area_button.pack(fill='x')

        self.area_label = tk.Label(
            area_frame,
            text="Detection Area: Full Screen",
            font=('Arial', 9),
            fg='gray'
        )
        self.area_label.pack(pady=5)

        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill='x', padx=20, pady=5)

        self.test_button = tk.Button(
            buttons_frame,
            text="TEST DETECTION",
            font=('Arial', 10),
            bg='#4dabf7',
            fg='white',
            command=self.test_detection,
            height=1
        )
        self.test_button.pack(side='left', fill='x', expand=True, padx=(0, 5))

        self.save_button = tk.Button(
            buttons_frame,
            text="SAVE SETTINGS",
            font=('Arial', 10),
            bg='#ffa94d',
            fg='white',
            command=self.manual_save_settings,
            height=1
        )
        self.save_button.pack(side='left', fill='x', expand=True, padx=(5, 0))

        self.start_button = tk.Button(
            self.root,
            text="START DETECTION (F4)",
            font=('Arial', 14, 'bold'),
            bg='#51cf66',
            fg='white',
            command=self.start_detection,
            height=2
        )
        self.start_button.pack(fill='x', padx=20, pady=10)

        self.status_label = tk.Label(
            self.root,
            text="Status: Ready",
            font=('Arial', 11, 'bold'),
            fg='blue'
        )
        self.status_label.pack()

        self.detected_frame = tk.Frame(self.root, pady=5)
        self.detected_frame.pack(fill='both', expand=True, padx=20)

        tk.Label(self.detected_frame, text="Last Detected Text:", font=('Arial', 9)).pack(anchor='w')
        self.detected_text = tk.Text(self.detected_frame, height=4, font=('Arial', 9), wrap='word')
        self.detected_text.pack(fill='both', expand=True)

    def manual_save_settings(self):
        self.save_settings()
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")

    def _ensure_tesseract_ready(self):
        if not self._is_valid_tesseract_path(self.tesseract_path):
            # One more chance: try auto-find again (maybe user installed it while app is open)
            auto = self.auto_find_tesseract()
            if auto:
                self.tesseract_path = auto
                pytesseract.pytesseract.tesseract_cmd = auto
                self.tess_path_var.set(auto)
                self.save_settings()
                self.status_label.config(text="Status: Auto-found Tesseract. Ready.", fg="blue")
                return True

            messagebox.showerror(
                "Tesseract not set",
                "Tesseract was not found automatically.\n\nClick 'Browse tesseract.exe' and select it manually."
            )
            return False
        return True

    def test_detection(self):
        if not self._ensure_tesseract_ready():
            return

        print("\n=== TESTING DETECTION ===")
        try:
            if self.detection_area:
                screenshot = ImageGrab.grab(bbox=self.detection_area)
                print(f"Captured area: {self.detection_area}")
            else:
                screenshot = ImageGrab.grab()
                print("Captured: Full Screen")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.debug_folder, f"test_{timestamp}.png")
            screenshot.save(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")

            detected_text = pytesseract.image_to_string(screenshot)

            print("\n--- DETECTED TEXT ---")
            print(detected_text)
            print("--- END ---\n")

            self.detected_text.delete(1.0, tk.END)
            self.detected_text.insert(1.0, detected_text if detected_text.strip() else "(No text detected)")

            target = self.text_entry.get().strip().lower()
            detected_lower = detected_text.lower()

            if target in detected_lower:
                result = f"✓ TARGET FOUND: '{target}' is in the detected text!"
                print(result)
                messagebox.showinfo("Test Result", result)
            else:
                result = f"✗ TARGET NOT FOUND: '{target}' is NOT in the detected text.\n\nDetected text is shown in the text box below."
                print(result)
                messagebox.showwarning("Test Result", result)

        except Exception as e:
            error_msg = f"Error during test: {e}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)

    def setup_hotkeys(self):
        self.hotkey_thread = threading.Thread(target=self.listen_hotkeys, daemon=True)
        self.hotkey_thread.start()

    def listen_hotkeys(self):
        keyboard.add_hotkey('f4', self.hotkey_start)
        keyboard.add_hotkey('f3', self.hotkey_stop)
        keyboard.add_hotkey('f5', self.hotkey_set_area)
        keyboard.wait()

    def hotkey_start(self):
        if not self.running:
            self.root.after(0, self.start_detection)

    def hotkey_stop(self):
        if self.running:
            self.root.after(0, self.stop_detection)

    def hotkey_set_area(self):
        self.root.after(0, self.open_area_selector)

    def open_area_selector(self):
        if self.running:
            messagebox.showwarning("Warning", "Stop detection before setting area!")
            return

        self.root.withdraw()
        time.sleep(0.2)

        selector = ResizableDetectionArea(self.root, self.set_detection_area)
        self.root.wait_window(selector)
        self.root.deiconify()

    def set_detection_area(self, x, y, width, height):
        self.detection_area = (x, y, x + width, y + height)
        self.area_label.config(text=f"Detection Area: x={x}, y={y}, width={width}, height={height}")
        print(f"Detection area set: {self.detection_area}")
        self.save_settings()

    def start_detection(self):
        if not self._ensure_tesseract_ready():
            return

        if self.running:
            return

        self.target_text = self.text_entry.get().strip().lower()
        if not self.target_text:
            messagebox.showerror("Error", "Please enter target text!")
            return

        try:
            self.click_delay = float(self.delay_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid click delay!")
            return

        self.debug_mode = self.debug_var.get()
        self.save_screenshots = self.screenshot_var.get()

        self.save_settings()

        self.running = True
        self.start_button.config(text="STOP DETECTION (F3)", bg='#ff6b6b')
        self.status_label.config(text="Status: Running - Clicking & Detecting...", fg='green')

        self.text_entry.config(state='disabled')
        self.delay_entry.config(state='disabled')
        self.area_button.config(state='disabled')
        self.test_button.config(state='disabled')
        self.save_button.config(state='disabled')

        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()

    def stop_detection(self):
        self.running = False
        self.start_button.config(text="START DETECTION (F4)", bg='#51cf66')
        self.status_label.config(text="Status: Stopped", fg='blue')

        self.text_entry.config(state='normal')
        self.delay_entry.config(state='normal')
        self.area_button.config(state='normal')
        self.test_button.config(state='normal')
        self.save_button.config(state='normal')

    def detection_loop(self):
        print(f"\n=== Detection Started ===")
        print(f"Looking for: '{self.target_text}'")
        print(f"Detection area: {self.detection_area if self.detection_area else 'Full Screen'}")
        print(f"Clicking center of screen every {self.click_delay} seconds until text is found...")
        print(f"Debug mode: {self.debug_mode}")
        print(f"Save screenshots: {self.save_screenshots}\n")

        screen_width, screen_height = pyautogui.size()
        center_x = screen_width // 2
        center_y = screen_height // 2
        click_count = 0

        while self.running:
            try:
                pyautogui.click(center_x, center_y)
                click_count += 1
                print(f"Click #{click_count} at center ({center_x}, {center_y})")

                time.sleep(0.1)

                if self.detection_area:
                    screenshot = ImageGrab.grab(bbox=self.detection_area)
                else:
                    screenshot = ImageGrab.grab()

                if self.save_screenshots:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    screenshot_path = os.path.join(self.debug_folder, f"scan_{click_count}_{timestamp}.png")
                    screenshot.save(screenshot_path)

                detected_text = pytesseract.image_to_string(screenshot)
                detected_lower = detected_text.lower()

                self.root.after(0, lambda: self.detected_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.detected_text.insert(
                    1.0, detected_text if detected_text.strip() else "(No text detected)"
                ))

                if self.debug_mode:
                    print(f"\n--- Detected Text (Scan #{click_count}) ---")
                    print(detected_text if detected_text.strip() else "(empty)")
                    print("--- End ---\n")

                if self.target_text in detected_lower:
                    print(f"\n✓✓✓ TEXT FOUND: '{self.target_text}' ✓✓✓")
                    print(f"Total clicks: {click_count}")
                    print("Stopping all clicks!")
                    self.root.after(0, self.on_text_found)
                    break
                else:
                    if self.debug_mode:
                        print(f"Target '{self.target_text}' not found in detected text.")

                time.sleep(self.click_delay)

            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.click_delay)

    def on_text_found(self):
        self.stop_detection()
        self.status_label.config(text="Status: Text Found! Stopped Clicking.", fg='green')
        messagebox.showinfo("Success", f"Target text '{self.target_text}' detected!\nClicking stopped.")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        self.save_settings()
        self.running = False
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        self.root.destroy()


def main():
    try:
        import pytesseract
        import pyautogui
        from PIL import ImageGrab
        import keyboard
    except ImportError:
        print("Missing required library!")
        print("\nPlease install required packages:")
        print("pip install pytesseract pillow pyautogui keyboard")
        return

    app = ScreenTextDetectorGUI()
    app.run()


if __name__ == "__main__":
    main()
