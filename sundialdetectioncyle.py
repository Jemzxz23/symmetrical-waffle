import pyautogui
import pytesseract
from PIL import ImageGrab, Image
import numpy as np
import cv2
import time
import keyboard
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from datetime import datetime
import json
import requests
import subprocess


class ResizableDetectionArea(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.is_adjusting = True
        
        self.attributes('-alpha', 0.3)
        self.attributes('-topmost', True)
        self.overrideredirect(True)
        self.configure(bg='red')
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.width = 400
        self.height = 300
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        self.geometry(f'{self.width}x{self.height}+{self.x}+{self.y}')
        
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None
        
        self.main_frame = tk.Frame(self, bg='red')
        self.main_frame.place(relwidth=1, relheight=1)
        
        self.label = tk.Label(
            self.main_frame,
            text='DETECTION AREA\n\nDrag center to move\nDrag yellow corners to resize\n\nPress ENTER to confirm',
            bg='red',
            fg='white',
            font=('Arial', 11, 'bold'),
            justify='center'
        )
        self.label.place(relx=0.5, rely=0.5, anchor='center')
        
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.on_drag)
        self.label.bind('<ButtonRelease-1>', self.stop_drag)
        
        self.create_resize_handles()
        
        self.bind('<Return>', self.confirm_area)
        self.bind('<Escape>', self.cancel_area)
        self.focus_force()

    def create_resize_handles(self):
        handle_size = 20
        
        self.nw_handle = tk.Label(self, bg='yellow', cursor='size_nw_se', width=2, height=1)
        self.nw_handle.place(x=0, y=0, width=handle_size, height=handle_size)
        self.nw_handle.bind('<Button-1>', lambda e: self.start_resize('nw', e))
        self.nw_handle.bind('<B1-Motion>', lambda e: self.on_resize(e))
        self.nw_handle.bind('<ButtonRelease-1>', self.stop_resize)
        
        self.ne_handle = tk.Label(self, bg='yellow', cursor='size_ne_sw', width=2, height=1)
        self.ne_handle.place(x=self.width - handle_size, y=0, width=handle_size, height=handle_size)
        self.ne_handle.bind('<Button-1>', lambda e: self.start_resize('ne', e))
        self.ne_handle.bind('<B1-Motion>', lambda e: self.on_resize(e))
        self.ne_handle.bind('<ButtonRelease-1>', self.stop_resize)
        
        self.sw_handle = tk.Label(self, bg='yellow', cursor='size_ne_sw', width=2, height=1)
        self.sw_handle.place(x=0, y=self.height - handle_size, width=handle_size, height=handle_size)
        self.sw_handle.bind('<Button-1>', lambda e: self.start_resize('sw', e))
        self.sw_handle.bind('<B1-Motion>', lambda e: self.on_resize(e))
        self.sw_handle.bind('<ButtonRelease-1>', self.stop_resize)
        
        self.se_handle = tk.Label(self, bg='yellow', cursor='size_nw_se', width=2, height=1)
        self.se_handle.place(x=self.width - handle_size, y=self.height - handle_size, width=handle_size, height=handle_size)
        self.se_handle.bind('<Button-1>', lambda e: self.start_resize('se', e))
        self.se_handle.bind('<B1-Motion>', lambda e: self.on_resize(e))
        self.se_handle.bind('<ButtonRelease-1>', self.stop_resize)

    def update_handle_positions(self):
        handle_size = 20
        self.ne_handle.place(x=self.width - handle_size, y=0)
        self.sw_handle.place(x=0, y=self.height - handle_size)
        self.se_handle.place(x=self.width - handle_size, y=self.height - handle_size)

    def start_drag(self, event):
        if not self.is_resizing:
            self.is_dragging = True
            self.drag_start_x = event.x_root - self.winfo_x()
            self.drag_start_y = event.y_root - self.winfo_y()

    def on_drag(self, event):
        if self.is_dragging and not self.is_resizing:
            self.x = event.x_root - self.drag_start_x
            self.y = event.y_root - self.drag_start_y
            self.geometry(f'{self.width}x{self.height}+{self.x}+{self.y}')

    def stop_drag(self, event):
        self.is_dragging = False

    def start_resize(self, corner, event):
        self.is_resizing = True
        self.resize_corner = corner
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.resize_start_width = self.width
        self.resize_start_height = self.height
        self.resize_start_win_x = self.x
        self.resize_start_win_y = self.y

    def on_resize(self, event):
        if not self.is_resizing:
            return
        
        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y
        min_size = 100
        
        if self.resize_corner == 'se':
            self.width = max(min_size, self.resize_start_width + dx)
            self.height = max(min_size, self.resize_start_height + dy)
        
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
        self.is_resizing = False
        self.resize_corner = None

    def confirm_area(self, event=None):
        self.callback(self.x, self.y, self.width, self.height)
        self.is_adjusting = False
        self.destroy()

    def cancel_area(self, event=None):
        self.is_adjusting = False
        self.destroy()


class ScreenTextDetectorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Text Detector")
        self.root.geometry("400x550")
        self.root.minsize(380, 500)
        
        self.running = False
        self.detection_thread = None
        self.hotkey_thread = None
        self.detection_area = None
        
        self.target_text = ""
        self.click_delay = 0.5
        self.debug_mode = True
        self.save_screenshots = False
        
        self.tesseract_path = ""
        self.discord_webhook_url = ""
        
        # Color filter settings
        self.use_color_filter = False
        self.saturation_threshold = 110
        
        self.theme_mode = "dark"
        
        self.config_file = "detector_settings.json"
        
        self.debug_folder = "debug_screenshots"
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)
        
        self.style = ttk.Style(self.root)
        
        self.load_settings()
        
        if not self._is_valid_tesseract_path(self.tesseract_path):
            found = self.auto_find_tesseract()
            if found:
                self.tesseract_path = found
                pytesseract.pytesseract.tesseract_cmd = found
        
        self.create_widgets()
        self.apply_loaded_settings()
        self.apply_theme(self.theme_mode)
        
        self.setup_hotkeys()

    # ---------- Color Filtering ----------
    def apply_color_filter(self, image_pil):
        """Apply saturation-based color filtering to detect colorful text"""
        if not self.use_color_filter:
            return image_pil
        
        img_np = np.array(image_pil)
        img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
        
        lower = np.array([0, self.saturation_threshold, 50])
        upper = np.array([180, 255, 255])
        mask = cv2.inRange(img_hsv, lower, upper)
        
        result = cv2.bitwise_and(img_np, img_np, mask=mask)
        result_gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
        _, result_binary = cv2.threshold(result_gray, 1, 255, cv2.THRESH_BINARY)
        
        return Image.fromarray(result_binary)

    def preview_color_filter(self):
        """Show preview window with color filtering applied"""
        if not self._ensure_tesseract_ready():
            return
        
        try:
            if self.detection_area:
                screenshot = ImageGrab.grab(bbox=self.detection_area)
            else:
                screenshot = ImageGrab.grab()
            
            filtered = self.apply_color_filter(screenshot)
            
            preview_win = tk.Toplevel(self.root)
            preview_win.title("Color Filter Preview")
            preview_win.geometry("700x500")
            
            display_img = filtered.copy()
            display_img.thumbnail((680, 400), Image.Resampling.LANCZOS)
            
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(display_img)
            
            label = tk.Label(preview_win, image=photo)
            label.image = photo
            label.pack(pady=10)
            
            detected = pytesseract.image_to_string(filtered)
            text_box = tk.Text(preview_win, height=4, wrap='word')
            text_box.pack(fill='x', padx=10, pady=5)
            text_box.insert(1.0, detected if detected.strip() else "(No text detected)")
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error: {e}")

    def toggle_color_controls(self):
        """Show/hide color filter controls"""
        if self.color_filter_var.get():
            self.color_filter_frame.pack(fill="x", pady=(4, 6))
        else:
            self.color_filter_frame.pack_forget()

    # ---------- Theme ----------
    def apply_theme(self, mode: str):
        mode = "dark" if mode == "dark" else "light"
        self.theme_mode = mode
        
        try:
            themes = self.style.theme_names()
            if "clam" in themes:
                self.style.theme_use("clam")
        except Exception:
            pass
        
        if mode == "dark":
            bg = "#1e1f22"
            fg = "#e6e6e6"
            entry_bg = "#2b2d31"
            entry_fg = "#e6e6e6"
            box_bg = "#2b2d31"
        else:
            bg = "#f5f5f5"
            fg = "#111111"
            entry_bg = "#ffffff"
            entry_fg = "#111111"
            box_bg = "#ffffff"
        
        self.root.configure(bg=bg)
        self.canvas.configure(bg=bg)
        self.scrollable_frame.configure(bg=bg)
        
        for w in self.theme_labels:
            try:
                w.configure(bg=bg, fg=fg)
            except:
                pass
        
        for e in self.theme_entries:
            e.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        
        self.detected_text.configure(bg=box_bg, fg=entry_fg, insertbackground=entry_fg)
        self.status_label.configure(bg=bg)
        
        self.save_settings(silent=True)

    def toggle_theme(self):
        self.apply_theme("light" if self.theme_mode == "dark" else "dark")

    # ---------- Discord webhook ----------
    def send_discord_webhook(self, message: str):
        url = (self.discord_webhook_url or "").strip()
        if not url:
            return
        payload = {"content": message}
        try:
            r = requests.post(url, json=payload, timeout=10)
            if not (200 <= r.status_code < 300):
                print("Webhook failed:", r.status_code, r.text)
        except Exception as e:
            print("Webhook error:", e)

    # ---------- Tesseract helpers ----------
    def _is_valid_tesseract_path(self, path: str) -> bool:
        if not path:
            return False
        if not os.path.exists(path):
            return False
        return os.path.basename(path).lower() == "tesseract.exe"

    def auto_find_tesseract(self):
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            candidates.append(os.path.join(local_appdata, r"Programs\Tesseract-OCR\tesseract.exe"))
        
        try:
            out = subprocess.check_output(["where", "tesseract"], stderr=subprocess.STDOUT, text=True)
            for line in out.splitlines():
                line = line.strip()
                if line.lower().endswith("tesseract.exe"):
                    candidates.append(line)
        except Exception:
            pass
        
        for p in candidates:
            if self._is_valid_tesseract_path(p):
                return p
        return None

    def browse_tesseract(self):
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
        pytesseract.pytesseract.tesseract_cmd = path
        self.tess_path_var.set(path)
        self.save_settings(silent=True)
        messagebox.showinfo("Tesseract set", "Tesseract path saved!")

    def _ensure_tesseract_ready(self):
        if self._is_valid_tesseract_path(self.tesseract_path):
            return True
        
        found = self.auto_find_tesseract()
        if found:
            self.tesseract_path = found
            pytesseract.pytesseract.tesseract_cmd = found
            self.tess_path_var.set(found)
            self.save_settings(silent=True)
            return True
        
        messagebox.showerror(
            "Tesseract not set",
            "Tesseract was not found.\nClick 'Browse' and select tesseract.exe."
        )
        return False

    # ---------- Settings ----------
    def load_settings(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                
                self.target_text = settings.get('target_text', '')
                self.click_delay = settings.get('click_delay', 0.5)
                self.debug_mode = settings.get('debug_mode', True)
                self.save_screenshots = settings.get('save_screenshots', False)
                
                self.tesseract_path = settings.get('tesseract_path', "")
                self.discord_webhook_url = settings.get('discord_webhook_url', "")
                self.theme_mode = settings.get('theme_mode', "dark")
                
                self.use_color_filter = settings.get('use_color_filter', False)
                self.saturation_threshold = settings.get('saturation_threshold', 110)
                
                if self._is_valid_tesseract_path(self.tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
                
                area = settings.get('detection_area', None)
                if area and len(area) == 4:
                    self.detection_area = tuple(area)
        except Exception as e:
            print(f"Could not load settings: {e}")

    def save_settings(self, silent=False):
        try:
            if hasattr(self, 'saturation_slider'):
                self.saturation_threshold = self.saturation_slider.get()
            
            settings = {
                'target_text': self.text_entry.get().strip() if hasattr(self, "text_entry") else self.target_text,
                'click_delay': float(self.delay_entry.get()) if hasattr(self, "delay_entry") else self.click_delay,
                'debug_mode': self.debug_var.get() if hasattr(self, "debug_var") else self.debug_mode,
                'save_screenshots': self.screenshot_var.get() if hasattr(self, "screenshot_var") else self.save_screenshots,
                'detection_area': list(self.detection_area) if self.detection_area else None,
                'tesseract_path': self.tesseract_path,
                'discord_webhook_url': self.webhook_entry.get().strip() if hasattr(self, "webhook_entry") else self.discord_webhook_url,
                'theme_mode': self.theme_mode,
                'use_color_filter': self.color_filter_var.get() if hasattr(self, 'color_filter_var') else self.use_color_filter,
                'saturation_threshold': self.saturation_threshold,
            }
            with open(self.config_file, 'w') as f:
                json.dump(settings, indent=4, fp=f)
            if not silent:
                print(f"✓ Settings saved to {self.config_file}")
        except Exception as e:
            if not silent:
                print(f"Could not save settings: {e}")

    def apply_loaded_settings(self):
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, self.target_text)
        
        self.delay_entry.delete(0, tk.END)
        self.delay_entry.insert(0, str(self.click_delay))
        
        self.debug_var.set(self.debug_mode)
        self.screenshot_var.set(self.save_screenshots)
        
        self.tess_path_var.set(self.tesseract_path)
        
        self.webhook_entry.delete(0, tk.END)
        self.webhook_entry.insert(0, self.discord_webhook_url)
        
        self.color_filter_var.set(self.use_color_filter)
        self.saturation_slider.set(self.saturation_threshold)
        self.toggle_color_controls()
        
        if self.detection_area:
            x, y, x2, y2 = self.detection_area
            width = x2 - x
            height = y2 - y
            self.area_label.config(text=f"x={x}, y={y}, w={width}, h={height}")
        else:
            self.area_label.config(text="Full Screen")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # ---------- UI ----------
    def create_widgets(self):
        # Main container with scrollbar
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar
        container = tk.Frame(self.root)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Bind mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.theme_labels = []
        self.theme_entries = []
        
        # Content frame with padding
        content = tk.Frame(self.scrollable_frame)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header = tk.Frame(content)
        header.pack(fill="x", pady=(0, 8))
        
        title = tk.Label(header, text="Screen Text Detector", font=('Arial', 12, 'bold'))
        title.pack(side="left")
        self.theme_labels.append(title)
        
        theme_btn = ttk.Button(header, text="Theme", command=self.toggle_theme, width=8)
        theme_btn.pack(side="right")
        
        hotkeys = tk.Label(content, text="F4: Start | F3: Stop | F5: Area", font=('Arial', 8))
        hotkeys.pack(anchor="w")
        self.theme_labels.append(hotkeys)
        
        ttk.Separator(content, orient='horizontal').pack(fill='x', pady=8)
        
        # Tesseract (compact)
        tess_frame = tk.Frame(content)
        tess_frame.pack(fill="x", pady=2)
        
        tk.Label(tess_frame, text="Tesseract:", font=('Arial', 9)).pack(side="left")
        self.theme_labels.append(tess_frame.winfo_children()[-1])
        
        ttk.Button(tess_frame, text="Browse", command=self.browse_tesseract, width=10).pack(side="right")
        
        self.tess_path_var = tk.StringVar(value=self.tesseract_path)
        self.tess_entry = tk.Entry(content, textvariable=self.tess_path_var, font=('Arial', 8))
        self.tess_entry.pack(fill="x", pady=(2, 6))
        self.theme_entries.append(self.tess_entry)
        
        # Webhook (compact)
        tk.Label(content, text="Discord Webhook:", font=('Arial', 9)).pack(anchor="w")
        self.theme_labels.append(content.winfo_children()[-1])
        
        self.webhook_entry = tk.Entry(content, font=('Arial', 8))
        self.webhook_entry.pack(fill="x", pady=(2, 6))
        self.theme_entries.append(self.webhook_entry)
        
        # Target text
        tk.Label(content, text="Target Text:", font=('Arial', 9, 'bold')).pack(anchor="w")
        self.theme_labels.append(content.winfo_children()[-1])
        
        self.text_entry = tk.Entry(content, font=('Arial', 10))
        self.text_entry.pack(fill="x", pady=(2, 6))
        self.theme_entries.append(self.text_entry)
        
        # Delay (inline)
        delay_frame = tk.Frame(content)
        delay_frame.pack(fill="x", pady=2)
        
        tk.Label(delay_frame, text="Delay (s):", font=('Arial', 9)).pack(side="left")
        self.theme_labels.append(delay_frame.winfo_children()[-1])
        
        self.delay_entry = tk.Entry(delay_frame, width=8)
        self.delay_entry.pack(side="left", padx=(5, 0))
        self.theme_entries.append(self.delay_entry)
        
        # Checkboxes (compact)
        self.debug_var = tk.BooleanVar(value=True)
        self.screenshot_var = tk.BooleanVar(value=False)
        
        self.debug_check = tk.Checkbutton(content, text="Debug mode", variable=self.debug_var, font=('Arial', 8))
        self.debug_check.pack(anchor="w")
        self.theme_labels.append(self.debug_check)
        
        self.screenshot_check = tk.Checkbutton(content, text="Save screenshots", variable=self.screenshot_var, font=('Arial', 8))
        self.screenshot_check.pack(anchor="w", pady=(0, 6))
        self.theme_labels.append(self.screenshot_check)
        
        # Color filter
        self.color_filter_var = tk.BooleanVar(value=False)
        color_check = tk.Checkbutton(
            content,
            text="Color Filter (for rarity text)",
            variable=self.color_filter_var,
            command=self.toggle_color_controls,
            font=('Arial', 9, 'bold')
        )
        color_check.pack(anchor="w")
        self.theme_labels.append(color_check)
        
        # Color filter controls (compact) - USE PACK NOT GRID
        self.color_filter_frame = tk.Frame(content)
        # Don't pack it yet, let toggle_color_controls handle it
        
        tk.Label(self.color_filter_frame, text="Intensity:", font=('Arial', 8)).pack(anchor="w")
        self.theme_labels.append(self.color_filter_frame.winfo_children()[-1])
        
        self.saturation_slider = tk.Scale(
            self.color_filter_frame,
            from_=50,
            to=200,
            orient='horizontal',
            length=250,
            showvalue=True
        )
        self.saturation_slider.set(110)
        self.saturation_slider.pack(fill="x", pady=2)
        
        tk.Label(
            self.color_filter_frame,
            text="50-80: Light • 110: Standard • 150+: Vivid",
            font=('Arial', 7)
        ).pack(anchor="w")
        self.theme_labels.append(self.color_filter_frame.winfo_children()[-1])
        
        ttk.Button(self.color_filter_frame, text="Preview Filter", command=self.preview_color_filter).pack(fill="x", pady=(4, 0))
        
        ttk.Separator(content, orient='horizontal').pack(fill='x', pady=6)
        
        # Area
        ttk.Button(content, text="Set Detection Area (F5)", command=self.open_area_selector).pack(fill="x", pady=2)
        
        self.area_label = tk.Label(content, text="Full Screen", font=('Arial', 8))
        self.area_label.pack(anchor="w", pady=(2, 6))
        self.theme_labels.append(self.area_label)
        
        # Action buttons (compact row)
        btn_frame = tk.Frame(content)
        btn_frame.pack(fill="x", pady=4)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Button(btn_frame, text="Test", command=self.test_detection).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(btn_frame, text="Save", command=self.manual_save_settings).grid(row=0, column=1, sticky="ew", padx=(3, 0))
        
        # Start button
        self.start_button = ttk.Button(content, text="Start Detection (F4)", command=self.start_detection)
        self.start_button.pack(fill="x", pady=(6, 4))
        
        # Status
        self.status_label = tk.Label(content, text="Ready", font=('Arial', 9, 'bold'), fg="blue")
        self.status_label.pack(anchor="w", pady=(4, 2))
        self.theme_labels.append(self.status_label)
        
        # Detected text (compact)
        tk.Label(content, text="Detected:", font=('Arial', 8)).pack(anchor="w")
        self.theme_labels.append(content.winfo_children()[-1])
        
        self.detected_text = tk.Text(content, height=4, font=('Arial', 8), wrap='word')
        self.detected_text.pack(fill="x", pady=(2, 0))

    # ---------- Actions ----------
    def manual_save_settings(self):
        self.discord_webhook_url = self.webhook_entry.get().strip()
        self.use_color_filter = self.color_filter_var.get()
        self.save_settings(silent=False)
        messagebox.showinfo("Saved", "Settings saved successfully!")

    def test_detection(self):
        if not self._ensure_tesseract_ready():
            return
        
        try:
            if self.detection_area:
                screenshot = ImageGrab.grab(bbox=self.detection_area)
            else:
                screenshot = ImageGrab.grab()
            
            processed = self.apply_color_filter(screenshot)
            detected_text = pytesseract.image_to_string(processed)
            
            self.detected_text.delete(1.0, tk.END)
            self.detected_text.insert(1.0, detected_text if detected_text.strip() else "(No text)")
            
            target = self.text_entry.get().strip().lower()
            if target and target in detected_text.lower():
                messagebox.showinfo("Test", f"✓ FOUND: '{target}'")
            else:
                messagebox.showwarning("Test", "Target not found")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")

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
            messagebox.showwarning("Warning", "Stop detection first!")
            return
        
        self.root.withdraw()
        time.sleep(0.2)
        
        selector = ResizableDetectionArea(self.root, self.set_detection_area)
        self.root.wait_window(selector)
        self.root.deiconify()

    def set_detection_area(self, x, y, width, height):
        self.detection_area = (x, y, x + width, y + height)
        self.area_label.config(text=f"x={x}, y={y}, w={width}, h={height}")
        self.save_settings(silent=True)

    def start_detection(self):
        if self.running:
            return
        if not self._ensure_tesseract_ready():
            return
        
        self.target_text = self.text_entry.get().strip().lower()
        if not self.target_text:
            messagebox.showerror("Error", "Enter target text!")
            return
        
        try:
            self.click_delay = float(self.delay_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid delay!")
            return
        
        self.debug_mode = self.debug_var.get()
        self.save_screenshots = self.screenshot_var.get()
        self.discord_webhook_url = self.webhook_entry.get().strip()
        self.use_color_filter = self.color_filter_var.get()
        
        self.save_settings(silent=True)
        
        self.running = True
        self.start_button.config(text="Stop (F3)")
        self.status_label.config(text="Running...", fg="green")
        
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()

    def stop_detection(self):
        self.running = False
        self.start_button.config(text="Start Detection (F4)")
        self.status_label.config(text="Stopped", fg="blue")

    def detection_loop(self):
        screen_width, screen_height = pyautogui.size()
        center_x = screen_width // 2
        center_y = screen_height // 2
        click_count = 0
        
        while self.running:
            try:
                pyautogui.click(center_x, center_y)
                click_count += 1
                
                time.sleep(0.1)
                
                if self.detection_area:
                    screenshot = ImageGrab.grab(bbox=self.detection_area)
                else:
                    screenshot = ImageGrab.grab()
                
                processed = self.apply_color_filter(screenshot)
                
                if self.save_screenshots:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    os.makedirs("debug_screenshots", exist_ok=True)
                    screenshot_path = os.path.join("debug_screenshots", f"scan_{click_count}_{timestamp}.png")
                    processed.save(screenshot_path)
                
                detected_text = pytesseract.image_to_string(processed)
                detected_lower = detected_text.lower()
                
                self.root.after(0, lambda: self.detected_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.detected_text.insert(
                    1.0, detected_text if detected_text.strip() else "(No text)"
                ))
                
                if self.target_text in detected_lower:
                    self.root.after(0, self.on_text_found)
                    break
                
                time.sleep(self.click_delay)
                
            except Exception as e:
                if self.debug_mode:
                    print("Error:", e)
                time.sleep(self.click_delay)

    def on_text_found(self):
        self.stop_detection()
        self.status_label.config(text="Text Found!", fg="green")
        self.send_discord_webhook(f"✅ Target found: '{self.target_text}'")
        messagebox.showinfo("Success", f"'{self.target_text}' detected!\nClicking stopped.")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        self.save_settings(silent=True)
        self.running = False
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        self.root.destroy()


def main():
    app = ScreenTextDetectorGUI()
    app.run()


if __name__ == "__main__":
    main()
