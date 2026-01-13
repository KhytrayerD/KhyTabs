import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from tkinter import messagebox, simpledialog
import pygetwindow as gw
import keyboard
import os
import ctypes
import json
import time
import copy
import sys
import webbrowser
import urllib.request
import io
import threading

try:
    import psutil
except ImportError:
    psutil = None

from PIL import Image, ImageTk, ImageFilter

# --- CLASES Y DATOS ---
CLASS_ID_MAP = {
    1: "Feca", 2: "Osamodas", 3: "Anutrof", 4: "Sram", 5: "Xelor",
    6: "Zurkarak", 7: "Aniripsa", 8: "Yopuka", 9: "Ocra", 10: "Sadida",
    11: "Sacrogrito", 12: "Pandawa", 13: "Tymador", 14: "Zobal",
    15: "Steamer", 16: "Selotrop", 17: "Hipermago", 18: "Uginak",
    19: "Forjalanza"
}
CLASES_NAMES_LOWER = {v.lower(): k for k, v in CLASS_ID_MAP.items()}

# --- CONFIGURACIÓN DEFAULT ---
DEFAULT_CONFIG = {
    "slots": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"],
    "key_next": "pagedown",
    "key_prev": "pageup",
    "text_mode": "always",
    "ui_scale": "medium",
    "orientation": "vertical",
    "window_x": 10,
    "window_y": 100,
    "opacity": 1.0,
    "locked": False,
    "smart_hide": False,
    "profiles": {}
}

UI_SIZES = {
    "small":  {"icon": 24, "canvas": 28, "font_max": 7, "pad": 1, "header_font": 7, "header_txt": "Khy"},
    "medium": {"icon": 32, "canvas": 38, "font_max": 9, "pad": 2, "header_font": 8, "header_txt": "Khy"},
    "large":  {"icon": 48, "canvas": 54, "font_max": 11, "pad": 4, "header_font": 10, "header_txt": "KhyDofus"}
}

# --- COLORES ---
COLOR_DOFUS_BG = '#c3bca3'
COLOR_DOFUS_BORDER = '#544a3b'
COLOR_HEADER_BG = '#40382d'
COLOR_HEADER_FG = '#ffbd2e'
COLOR_TEXTO = '#3d372a'
COLOR_ACTIVO_BG = '#2ecc71'
COLOR_ACTIVO_BORDER = '#1e8449'
COLOR_BUTTON_INACTIVE = '#bdaea0'
COLOR_LINK = '#2b6cb0'
COLOR_PANEL_BG = '#d0c8b0'

# COLORES PARA EL DRAG & DROP
COLOR_ROW_NORMAL = '#e0dccc'
COLOR_ROW_DRAGGING = '#d4ae80'
COLOR_ROW_TARGET = '#9c9280'

RGB_DOFUS_BG = (195, 188, 163)
RGB_ACTIVE_GLOW = (46, 204, 113)
COLOR_CHROMA_KEY = '#ff00ff'
LINK_YOUTUBE = "https://www.youtube.com/@KhytrayerDofus"

LEGAL_TEXT = """
KhyDofus Tabs - Herramienta de Organización Visual

Esta aplicación es una herramienta de terceros gratuita y sin ánimo de lucro.
NO modifica los archivos del juego.
NO automatiza acciones (no es un bot).
NO intercepta paquetes de red.

Simplemente ayuda a cambiar entre ventanas usando atajos de teclado estándar de Windows.

AVISO DE COPYRIGHT:
Dofus y Ankama son marcas registradas de Ankama Games.
Todas las imágenes, logotipos y nombres de clases son propiedad exclusiva de Ankama Games.
Esta aplicación no está afiliada, respaldada ni patrocinada por Ankama Games.
"""

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
# Debugging flags
DEBUG_TAB = True

class ToolTip:
    _active = None

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def motion(self, event=None):
        pass

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(200, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            try: self.widget.after_cancel(id)
            except: pass

    def showtip(self):
        if not self.text: return
        try:
            if ToolTip._active and ToolTip._active is not self:
                ToolTip._active.hidetip()
        except: pass
        if self.tip_window:
            return
        try:
            bbox = None
            try:
                bbox = self.widget.bbox("insert")
            except: bbox = None
            if bbox:
                x, y, cx, cy = bbox
                x = x + self.widget.winfo_rootx() + 35
                y = y + self.widget.winfo_rooty() + 10
            else:
                x = self.widget.winfo_rootx() + 12
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        try: tw.attributes('-topmost', True)
        except: pass

        frame = tk.Frame(tw, bg=COLOR_DOFUS_BG, bd=1, relief='solid')
        frame.pack(fill='both', expand=True)
        label = tk.Label(frame, text=self.text, justify='left',
                         background=COLOR_PANEL_BG, fg=COLOR_TEXTO,
                         font=("Segoe UI", 9), bd=0, padx=6, pady=4, wraplength=280)
        label.pack()
        ToolTip._active = self

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            try: tw.destroy()
            except: pass
        try:
            if ToolTip._active is self:
                ToolTip._active = None
        except: pass

# --- APP PRINCIPAL ---
class DofusOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("KhyTrayer Tabs")
        
        if os.path.exists("icono.ico"):
            try: self.root.iconbitmap("icono.ico")
            except: pass

        self.config = self.load_config()
        self.active_config = self.config 
        
        self.dofus_windows = [] 
        self.image_cache = {} 
        self.raw_icon_cache = {} 

        self.almanax_item_id = None
        self.dolmanax_icon = None
        
        self.is_visible_globally = True
        self.manual_hidden = False
        self.smart_hide_active = False 
        self._drag_data = {"x": 0, "y": 0}
        self._last_active_title = "" 

        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.wm_attributes("-transparentcolor", COLOR_CHROMA_KEY)
        self.root.attributes('-alpha', self.config.get('opacity', 1.0))
        self.root.configure(bg=COLOR_CHROMA_KEY)
        self.root.geometry(f"+{self.config['window_x']}+{self.config['window_y']}")

        # MENÚ CONTEXTUAL
        self.context_menu = tk.Menu(root, tearoff=0, bg=COLOR_DOFUS_BG, fg=COLOR_TEXTO)
        self.context_menu.add_command(label="⚙ Configuración", command=self.open_settings)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="⚖ Aviso Legal", command=self.show_legal)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="↻ Refrescar", command=self.scan_windows)
        self.context_menu.add_command(label="✕ Cerrar App", command=self.close_app)

        self.main_canvas = tk.Canvas(self.root, bg=COLOR_CHROMA_KEY, highlightthickness=0, bd=0)
        self.main_canvas.pack(fill='both', expand=True)
        
        self.inner_frame = tk.Frame(self.main_canvas, bg=COLOR_DOFUS_BG, bd=0, highlightthickness=0)

        for w in [self.main_canvas, self.inner_frame]:
            w.bind("<Button-1>", self.start_move_window)
            w.bind("<B1-Motion>", self.do_move_window)
            w.bind("<Button-3>", self.show_context_menu)

        # Hotkeys: registrar una vez y luego solo actualizar los dinámicos
        self._hotkey_ids = {}
        try:
            self._hotkey_ids['toggle_visibility'] = keyboard.add_hotkey("ctrl+shift+h", self.toggle_interface_phantom)
        except:
            self._hotkey_ids['toggle_visibility'] = None

        self.scan_windows()
        self.check_active_window_loop()

    # --- CORE ---
    def toggle_interface_phantom(self):
        try:
            if self.is_visible_globally:
                self.root.withdraw()
                self.is_visible_globally = False
                self.manual_hidden = True
            else:
                self.root.deiconify()
                self.is_visible_globally = True
                self.manual_hidden = False
                self.smart_hide_active = False
                self.force_focus_self()
        except:
            pass

    def show_legal(self):
        messagebox.showinfo("Aviso Legal", LEGAL_TEXT)

    def force_focus_self(self):
        try:
            self.root.lift()
            self.root.attributes('-topmost', True)
        except: pass

    def load_config(self):
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    loaded = json.load(f)
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(loaded)
                    if "profiles" not in merged: merged["profiles"] = {}
                    return merged
            except: return DEFAULT_CONFIG
        return DEFAULT_CONFIG

    def save_config(self):
        self.config["window_x"] = self.root.winfo_x()
        self.config["window_y"] = self.root.winfo_y()
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)

    def get_current_ui_params(self):
        scale = self.active_config.get("ui_scale", "medium")
        return UI_SIZES.get(scale, UI_SIZES["medium"])

    def start_move_window(self, event):
        if self.active_config.get('locked', False): return
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_move_window(self, event):
        if self.active_config.get('locked', False): return
        x = self.root.winfo_x() + (event.x - self._drag_data["x"])
        y = self.root.winfo_y() + (event.y - self._drag_data["y"])
        self.root.geometry(f"+{x}+{y}")

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    # --- UI DRAWING ---
    def draw_rounded_container(self, width, height, radius=12, border_width=3):
        # Draw border as filled shapes (ovals + rects) using integer coordinates
        self.main_canvas.delete("bg_shape")
        self.main_canvas.delete("bg_fill")
        tags_shape = "bg_shape"
        tags_fill = "bg_fill"

        bw = int(max(1, border_width))
        r = int(max(0, radius))
        w = int(width)
        h = int(height)

        bc = COLOR_DOFUS_BORDER
        # define canvas rect coordinates and radii
        left, top, right, bottom = 0, 0, w, h
        outer_r = r
        inner_r = max(0, outer_r - bw)
        # draw border using filled rectangles + corner ovals for crisp edges
        try:
            self.main_canvas.create_rectangle(left+outer_r, top, right-outer_r, bottom, fill=bc, outline=bc, tags=tags_shape)
            self.main_canvas.create_rectangle(left, top+outer_r, right, bottom-outer_r, fill=bc, outline=bc, tags=tags_shape)
            self.main_canvas.create_oval(left, top, left+2*outer_r, top+2*outer_r, fill=bc, outline=bc, tags=tags_shape)
            self.main_canvas.create_oval(right-2*outer_r, top, right, top+2*outer_r, fill=bc, outline=bc, tags=tags_shape)
            self.main_canvas.create_oval(left, bottom-2*outer_r, left+2*outer_r, bottom, fill=bc, outline=bc, tags=tags_shape)
            self.main_canvas.create_oval(right-2*outer_r, bottom-2*outer_r, right, bottom, fill=bc, outline=bc, tags=tags_shape)
        except: pass
        bg = COLOR_DOFUS_BG
        # fill center area with rectangles + corner ovals to create inner rounded rect
        try:
            self.main_canvas.create_rectangle(left+inner_r, top, right-inner_r, bottom, fill=bg, outline=bg, tags=tags_fill)
            self.main_canvas.create_rectangle(left, top+inner_r, right, bottom-inner_r, fill=bg, outline=bg, tags=tags_fill)
            self.main_canvas.create_oval(left, top, left+2*inner_r, top+2*inner_r, fill=bg, outline=bg, tags=tags_fill)
            self.main_canvas.create_oval(right-2*inner_r, top, right, top+2*inner_r, fill=bg, outline=bg, tags=tags_fill)
            self.main_canvas.create_oval(left, bottom-2*inner_r, left+2*inner_r, bottom, fill=bg, outline=bg, tags=tags_fill)
            self.main_canvas.create_oval(right-2*inner_r, bottom-2*outer_r, right, bottom, fill=bg, outline=bg, tags=tags_fill)
        except: pass

        self.main_canvas.tag_lower(tags_fill)
        self.main_canvas.tag_lower(tags_shape)

    def update_layout(self):
        self.inner_frame.update_idletasks()
        req_w = self.inner_frame.winfo_reqwidth()
        req_h = self.inner_frame.winfo_reqheight()
        pad_x, pad_y = 10, 10
        final_w = req_w + pad_x
        final_h = req_h + pad_y
        self.main_canvas.config(width=final_w, height=final_h)
        self.draw_rounded_container(final_w, final_h)
        self.main_canvas.delete("frame_win")
        self.main_canvas.create_window(final_w/2, final_h/2, window=self.inner_frame, tags="frame_win", anchor="center")
        self.root.geometry(f"{final_w}x{final_h}")

    # --- Animations / helpers ---
    def _hex_to_rgb(self, hexcol):
        c = hexcol.lstrip('#')
        if len(c) == 3:
            c = ''.join([ch*2 for ch in c])
        return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _animate_color_transition(self, widget, start_hex, end_hex, steps=6, delay=30):
        # Cancel existing animation
        if hasattr(widget, '_anim_id') and widget._anim_id:
            try: widget.after_cancel(widget._anim_id)
            except: pass
        try:
            start = self._hex_to_rgb(start_hex)
            end = self._hex_to_rgb(end_hex)
        except:
            widget._anim_id = None
            widget.config(bg=end_hex)
            return

        def step(i):
            t = i/steps
            cur = (int(start[0] + (end[0]-start[0])*t),
                   int(start[1] + (end[1]-start[1])*t),
                   int(start[2] + (end[2]-start[2])*t))
            hexc = self._rgb_to_hex(cur)
            widget.config(bg=hexc)
            # adjust fg for readability
            try:
                lum = 0.299*cur[0] + 0.587*cur[1] + 0.114*cur[2]
                widget.config(fg='black' if lum > 186 else 'white')
            except: pass
            if i < steps:
                widget._anim_id = widget.after(delay, lambda: step(i+1))
            else:
                widget._anim_id = None

        step(0)

    def fade_in_window(self, win, duration=220):
        try:
            steps = max(6, int(duration/30))
            target = self.config.get('opacity', 1.0)
            try: win.attributes('-alpha', 0.0)
            except: pass
            def s(i):
                a = (i/steps) * target
                try: win.attributes('-alpha', a)
                except: pass
                if i < steps:
                    win.after(int(duration/steps), lambda: s(i+1))
            s(0)
        except: pass

    def styled_button(self, parent, text, command, primary=False, width=None, primary_color=None, secondary_color=None):
        bg_primary = COLOR_ACTIVO_BG
        fg_primary = "white"
        bg_secondary = COLOR_BUTTON_INACTIVE
        fg_secondary = COLOR_TEXTO
        # Determine background
        if primary:
            btn_bg = primary_color if primary_color else bg_primary
        else:
            btn_bg = secondary_color if secondary_color else bg_secondary

        def readable_fg(hexcol):
            try:
                r, g, b = self._hex_to_rgb(hexcol)
                lum = 0.299*r + 0.587*g + 0.114*b
                return 'black' if lum > 186 else 'white'
            except:
                return fg_primary if primary else fg_secondary

        btn_fg = readable_fg(btn_bg)
        font = ("Segoe UI", 10, "bold") if primary else ("Segoe UI", 10)
        btn = tk.Button(parent, text=text, command=command, bg=btn_bg, fg=btn_fg,
                        activebackground=btn_bg, activeforeground=btn_fg,
                        bd=0, relief="flat", font=font, cursor="hand2", padx=10, pady=6, width=width)

        # compute hover color
        def darken(hexcol, factor=0.88):
            try:
                r, g, b = self._hex_to_rgb(hexcol)
                return self._rgb_to_hex((max(0,int(r*factor)), max(0,int(g*factor)), max(0,int(b*factor))))
            except: return hexcol

        hover_bg = darken(btn_bg, 0.88)

        def on_enter(e):
            try:
                cur = btn.cget('bg')
                self._animate_color_transition(btn, cur, hover_bg)
            except: btn.config(bg=hover_bg)

        def on_leave(e):
            try:
                cur = btn.cget('bg')
                self._animate_color_transition(btn, cur, btn_bg)
            except: btn.config(bg=btn_bg)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def fetch_icon_data(self, class_name):
        class_id = CLASES_NAMES_LOWER.get(class_name.lower())
        if not class_id: return None
        if class_id in self.raw_icon_cache: return self.raw_icon_cache[class_id]
        
        url = f"https://api.dofusdb.fr/img/breeds/symbol_{class_id}.png"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read()
                self.raw_icon_cache[class_id] = data
                return data
        except Exception: return None

    def get_almanax_data(self):
        try:
            day = time.strftime("%Y-%m-%d")
            url = f"https://api.dofusdu.de/dofus3/v1/es/almanax/{day}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6) as response:
                payload = response.read().decode('utf-8')
            data = json.loads(payload)

            try:
                self.almanax_item_id = data.get('tribute', {}).get('item', {}).get('image_urls', {}).get('icon')
            except:
                self.almanax_item_id = None

            offer = ""
            bonus = ""
            try:
                offer = str(data.get('tribute', {}).get('quantity')) + "x " + data.get('tribute', {}).get('item', {}).get('name') or ''
            except:
                offer = ""
            try:
                bonus = data.get('bonus', {}).get('description') or ''
            except:
                bonus = ""

            offer = offer.replace('🥖', '').strip()
            bonus = bonus.strip()
            if not offer: offer = "(Sin datos de ofrenda)"
            if not bonus: bonus = "(Sin datos de bonus)"
            return offer, bonus
        except:
            try:
                self.almanax_item_id = None
            except:
                pass
            return "(Error cargando Almanax)", ""

    def get_dolmanax_icon(self, size=44):
        try:
            icon_src = getattr(self, 'almanax_item_id', None)
            if not icon_src:
                return None
            if isinstance(icon_src, str) and icon_src.startswith('http'):
                url = icon_src
            else:
                url = f"https://api.dofusdu.de/dofus3/v1/img/item/{icon_src}-64.png"

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6) as response:
                raw = response.read()
            img = Image.open(io.BytesIO(raw)).convert('RGBA')
            img = img.resize((int(size), int(size)), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except:
            return None

    # --- PROCESADO DE IMAGENES (ESTILO CLÁSICO) ---
    def get_processed_images(self, class_name):
        scale_key = f"{class_name}_{self.active_config.get('ui_scale')}"
        if scale_key in self.image_cache: return self.image_cache[scale_key]
        data = self.fetch_icon_data(class_name)
        if not data: return None
        try:
            params = self.get_current_ui_params()
            sz_icon = params["icon"]
            sz_canvas = params["canvas"]
            icon_src = Image.open(io.BytesIO(data)).convert("RGBA")
            icon_resized = icon_src.resize((sz_icon, sz_icon), Image.Resampling.LANCZOS)
            base_bg = Image.new("RGBA", (sz_canvas, sz_canvas), RGB_DOFUS_BG + (255,))
            paste_pos = ((sz_canvas - sz_icon) // 2, (sz_canvas - sz_icon) // 2)
            
            # Imagen Normal
            img_normal_pil = base_bg.copy()
            img_normal_pil.paste(icon_resized, paste_pos, icon_resized)
            
            # Imagen Contour (Reseguido Verde)
            alpha = icon_resized.getchannel('A')
            mask = alpha.point(lambda p: 255 if p > 50 else 0)
            dilated_mask = mask.filter(ImageFilter.MaxFilter(3))
            green_solid = Image.new("RGBA", (sz_icon, sz_icon), RGB_ACTIVE_GLOW + (255,))
            
            img_contour_pil = base_bg.copy()
            img_contour_pil.paste(green_solid, paste_pos, dilated_mask)
            img_contour_pil.paste(icon_resized, paste_pos, icon_resized)

            res = {"normal": ImageTk.PhotoImage(img_normal_pil), "contour": ImageTk.PhotoImage(img_contour_pil)}
            self.image_cache[scale_key] = res
            return res
        except: return None

    def fit_text_font(self, text, max_width, max_font_size):
        size = max_font_size
        current_font = tkfont.Font(family="Consolas", size=size, weight="bold")
        while size > 6:
            if current_font.measure(text) <= max_width: return size
            size -= 1
            current_font.configure(size=size)
        return 6

    def render_ui(self):
        for w in self.inner_frame.winfo_children(): w.destroy()
        # No usar unhook_all(): puede desregistrar Ctrl+Shift+H y dejarlo inconsistente.
        # Solo limpiamos hotkeys dinámicos (next/prev/slots).
        try:
            for k in ('key_next', 'key_prev'):
                hk_id = self._hotkey_ids.get(k)
                if hk_id:
                    try: keyboard.remove_hotkey(hk_id)
                    except: pass
                    self._hotkey_ids[k] = None
        except:
            pass
        try:
            slot_ids = self._hotkey_ids.get('slots')
            if isinstance(slot_ids, list):
                for hk_id in slot_ids:
                    try: keyboard.remove_hotkey(hk_id)
                    except: pass
            self._hotkey_ids['slots'] = []
        except:
            self._hotkey_ids['slots'] = []
        
        if self.active_config.get("key_next"):
            try:
                self._hotkey_ids['key_next'] = keyboard.add_hotkey(self.active_config["key_next"], lambda: self.cycle_windows(1))
            except:
                self._hotkey_ids['key_next'] = None
        if self.active_config.get("key_prev"):
            try:
                self._hotkey_ids['key_prev'] = keyboard.add_hotkey(self.active_config["key_prev"], lambda: self.cycle_windows(-1))
            except:
                self._hotkey_ids['key_prev'] = None
        
        try: self.root.attributes('-alpha', float(self.active_config.get('opacity', 1.0)))
        except: pass

        orientation = self.active_config.get("orientation", "vertical")
        params = self.get_current_ui_params()
        text_mode = self.active_config.get('text_mode', 'always')
        show_text_inline = (text_mode == 'always')

        header_text = params["header_txt"]
        header_frame = tk.Frame(self.inner_frame, bg=COLOR_HEADER_BG)
        lbl_header = tk.Label(header_frame, text=header_text, bg=COLOR_HEADER_BG, fg=COLOR_HEADER_FG, 
                              font=("Segoe UI", params["header_font"], "bold"))

        if orientation == "vertical":
            header_frame.pack(fill='x', pady=(0, 2), side='top')
            lbl_header.pack(pady=2, padx=1) 
        else:
            header_frame.pack(fill='y', padx=(0, 2), side='left')
            if len(header_text) > 3: lbl_header.config(text="K\nH\nY") 
            lbl_header.pack(padx=2, pady=5)
            
        for w in [header_frame, lbl_header]:
            w.bind("<Button-1>", self.start_move_window)
            w.bind("<B1-Motion>", self.do_move_window)
            w.bind("<Button-3>", self.show_context_menu)

        for idx, item in enumerate(self.dofus_windows):
            title = item["window_title"]
            clase = item["class_name"]
            char_name = item["char_name"]
            hotkey = self.active_config['slots'][idx] if idx < len(self.active_config['slots']) else None
            
            # Si hay texto, usamos borde en el contenedor. Si no, borde 0 (lo hace la imagen).
            hl_thick = 2 if show_text_inline else 0
            
            container = tk.Frame(self.inner_frame, bg=COLOR_DOFUS_BG, 
                                 highlightthickness=hl_thick, 
                                 highlightbackground=COLOR_DOFUS_BG, 
                                 highlightcolor=COLOR_DOFUS_BG, bd=0)
            
            if orientation == "vertical":
                container.pack(fill='x', pady=1, side='top', anchor='center')
            else:
                container.pack(fill='y', padx=1, side='left', anchor='center')

            item['row_widget'] = container 
            item['last_state'] = None 
            
            click_cmd = lambda e, t=title: self.force_focus(t)
            container.bind("<Button-1>", click_cmd)
            container.bind("<Button-3>", self.show_context_menu)

            if text_mode == 'hover':
                tt_text = f"{char_name} [{hotkey}]" if hotkey else char_name
                ToolTip(container, tt_text)

            if hotkey: 
                try:
                    hk_id = keyboard.add_hotkey(hotkey, lambda t=title: self.conditional_activate(t))
                    try:
                        self._hotkey_ids.setdefault('slots', []).append(hk_id)
                    except:
                        self._hotkey_ids['slots'] = [hk_id]
                except:
                    pass

            imgs = self.get_processed_images(clase)
            content_box = tk.Frame(container, bg=COLOR_DOFUS_BG, bd=0)
            content_box.pack(expand=True, fill='both') 
            content_box.bind("<Button-1>", click_cmd)
            content_box.bind("<Button-3>", self.show_context_menu)
            if text_mode == 'hover': ToolTip(content_box, tt_text)

            lbl = None
            if imgs:
                lbl = tk.Label(content_box, image=imgs["normal"], bg=COLOR_DOFUS_BG, bd=0)
                pack_side = 'left' if orientation == 'vertical' and show_text_inline else 'top'
                if not show_text_inline: pack_side = 'top'
                lbl.pack(side=pack_side, padx=params['pad'], pady=params['pad'], anchor='center')
                lbl.bind("<Button-1>", click_cmd)
                lbl.bind("<Button-3>", self.show_context_menu)
                if text_mode == 'hover': ToolTip(lbl, tt_text)
                item['img_widget'] = lbl

            if show_text_inline:
                txt_str = f"{char_name}\n{hotkey}" if hotkey else f"{char_name}"
                max_w = 60 if orientation == "vertical" else 80
                final_font_size = self.fit_text_font(char_name, max_w, params['font_max'])
                lbl_txt = tk.Label(content_box, text=txt_str, bg=COLOR_DOFUS_BG, fg=COLOR_TEXTO,
                                 font=("Consolas", final_font_size, "bold"), bd=0)
                pack_side = 'left' if orientation == 'vertical' else 'top'
                lbl_txt.pack(side=pack_side, padx=(0, 2), expand=True, anchor='center')
                lbl_txt.bind("<Button-1>", click_cmd)
                lbl_txt.bind("<Button-3>", self.show_context_menu)
                item['txt_widget'] = lbl_txt

        self.update_layout()
        self._last_active_title = "" 
        self.check_active_window_logic()

    # --- SCANNER ---
    def get_window_creation_time(self, title):
        if not psutil: return 0
        try:
            wins = gw.getWindowsWithTitle(title)
            if not wins: return 0
            hwnd = wins[0]._hWnd
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return psutil.Process(pid.value).create_time()
        except: return 0

    def parse_window_title(self, title):
        parts = title.split(' - ')
        if len(parts) < 2: return None, None
        detected_class = None
        detected_name = None
        for i, part in enumerate(parts):
            clean_part = part.strip().lower()
            if clean_part in CLASES_NAMES_LOWER:
                detected_class = CLASS_ID_MAP[CLASES_NAMES_LOWER[clean_part]]
                detected_name = " - ".join(parts[:i]).strip()
                break
        return detected_name, detected_class

    def scan_windows(self):
        all_titles = gw.getAllTitles()
        found_data = []
        for title in all_titles:
            if " - " not in title: continue
            char_name, detected_class = self.parse_window_title(title)
            if char_name and detected_class:
                found_data.append({
                    "window_title": title,
                    "class_name": detected_class,
                    "char_name": char_name,
                    "time": self.get_window_creation_time(title),
                    "row_widget": None, "img_widget": None, "txt_widget": None, "last_state": None
                })
        found_data.sort(key=lambda x: x["time"])
        self.dofus_windows = found_data
        self.render_ui()

    def check_active_window_loop(self):
        self.check_active_window_logic()
        self.root.after(150, self.check_active_window_loop)

    def check_active_window_logic(self):
        try:
            active = gw.getActiveWindow()
            curr = active.title if active else ""

            # Si el usuario ha ocultado manualmente, no aplicar Smart Hide automáticamente.
            try:
                if self.manual_hidden:
                    return
            except:
                pass

            # Smart Hide Logic
            if self.is_visible_globally and self.active_config.get('smart_hide', False):
                is_dofus = any(item['window_title'] == curr for item in self.dofus_windows)
                is_me = "KhyDofus" in curr or "Configuración" in curr or "Organizador" in curr
                if is_dofus or is_me:
                    if self.smart_hide_active:
                        self.root.deiconify()
                        self.root.attributes('-topmost', True)
                        self.smart_hide_active = False
                else:
                    if not self.smart_hide_active:
                        self.root.withdraw()
                        self.smart_hide_active = True

            if not self.is_visible_globally or self.smart_hide_active: return
            if curr == self._last_active_title: return
            self._last_active_title = curr
            
            try:
                text_mode = self.active_config.get('text_mode', 'always')
            except:
                text_mode = 'always'
            show_text = (text_mode == 'always')

            for item in self.dofus_windows:
                is_active = item['window_title'] == curr
                # Force refresh if status changed
                if item.get('last_state') == is_active: continue
                item['last_state'] = is_active

                row = item['row_widget']
                img = item['img_widget']
                txt = item['txt_widget']
                clase = item['class_name']
                imgs = self.get_processed_images(clase)

                if row and row.winfo_exists():
                    
                    if show_text:
                        # MODO TEXTO: Highlight en Fondo + Borde del Contenedor
                        bg_color = COLOR_ACTIVO_BG if is_active else COLOR_DOFUS_BG
                        bd_color = COLOR_ACTIVO_BORDER if is_active else COLOR_DOFUS_BG
                        
                        row.configure(bg=bg_color, highlightbackground=bd_color, highlightcolor=bd_color)
                        for child in row.winfo_children():
                            child.configure(bg=bg_color)
                            for grand_child in child.winfo_children():
                                grand_child.configure(bg=bg_color)
                        
                        # Imagen siempre normal en modo texto
                        if img and imgs: img.configure(image=imgs["normal"])

                    else:
                        # MODO ICONO: Highlight en la IMAGEN (Reseguido/Contour)
                        # Contenedor siempre color base
                        row.configure(bg=COLOR_DOFUS_BG, highlightthickness=0)
                        for child in row.winfo_children():
                            child.configure(bg=COLOR_DOFUS_BG)
                            for grand_child in child.winfo_children():
                                grand_child.configure(bg=COLOR_DOFUS_BG)
                        
                        if img and imgs:
                            target_img = imgs["contour"] if is_active else imgs["normal"]
                            img.configure(image=target_img, bg=COLOR_DOFUS_BG)

        except: pass

    # --- CONFIGURACIÓN ---
    def open_settings(self):
        top = tk.Toplevel(self.root)
        top.title("Configuración KhyDofus")
        top.configure(bg=COLOR_DOFUS_BG)
        top.geometry("600x630") 
        try: top.attributes('-alpha', 0.0)
        except: pass
        top.resizable(True, True)
        top.attributes('-topmost', True)
        
        if os.path.exists("icono.ico"):
            try: top.iconbitmap("icono.ico")
            except: pass

        header_conf = tk.Frame(top, bg=COLOR_HEADER_BG, height=40)
        header_conf.pack(fill='x', side='top')
        tk.Label(header_conf, text="KHYDOFUS TABS - CONFIGURACIÓN", bg=COLOR_HEADER_BG, fg=COLOR_HEADER_FG, 
                 font=("Segoe UI", 12, "bold")).pack()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=COLOR_DOFUS_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR_PANEL_BG, foreground=COLOR_TEXTO, padding=[10, 5], font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", "#d4ae80")], foreground=[("selected", "black")])
        style.configure("TFrame", background=COLOR_DOFUS_BG)

        # Scrollbar temática
        try:
            style.configure(
                "Dofus.Vertical.TScrollbar",
                gripcount=0,
                background=COLOR_BUTTON_INACTIVE,
                darkcolor=COLOR_DOFUS_BORDER,
                lightcolor=COLOR_PANEL_BG,
                troughcolor=COLOR_DOFUS_BG,
                bordercolor=COLOR_DOFUS_BORDER,
                arrowcolor=COLOR_TEXTO
            )
        except:
            pass

        # Contenido scrolleable (para pantallas pequeñas o contenido grande)
        content_wrap = tk.Frame(top, bg=COLOR_DOFUS_BG)
        content_wrap.pack(side='top', fill='both', expand=True)

        scroll_canvas = tk.Canvas(content_wrap, bg=COLOR_DOFUS_BG, highlightthickness=0, bd=0)
        scroll_canvas.pack(side='left', fill='both', expand=True)

        v_scroll = ttk.Scrollbar(content_wrap, orient='vertical', command=scroll_canvas.yview, style="Dofus.Vertical.TScrollbar")
        v_scroll.pack(side='right', fill='y')
        scroll_canvas.configure(yscrollcommand=v_scroll.set)

        scroll_inner = tk.Frame(scroll_canvas, bg=COLOR_DOFUS_BG)
        scroll_win = scroll_canvas.create_window((0, 0), window=scroll_inner, anchor='nw')

        def _sync_scroll_region(e=None):
            try:
                scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all'))
            except:
                pass

        def _sync_inner_width(e=None):
            try:
                scroll_canvas.itemconfigure(scroll_win, width=scroll_canvas.winfo_width())
            except:
                pass

        scroll_inner.bind('<Configure>', _sync_scroll_region)
        scroll_canvas.bind('<Configure>', _sync_inner_width)

        def _on_mousewheel(event):
            try:
                # Windows: event.delta suele ser múltiplo de 120
                scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
                return 'break'
            except:
                return

        try:
            # Bind global en esta ventana
            top.bind_all('<MouseWheel>', _on_mousewheel)
        except:
            pass

        notebook = ttk.Notebook(scroll_inner)
        notebook.pack(side='top', fill='both', expand=True, padx=10, pady=10)

        # When the user changes tabs, avoid focusing the first input (removes dotted focus outline).
        try:
            notebook.bind("<<NotebookTabChanged>>", lambda e, t=top: t.focus_set())
        except: pass

        tab_general = ttk.Frame(notebook)
        tab_hotkeys = ttk.Frame(notebook)
        tab_profiles = ttk.Frame(notebook)
        
        notebook.add(tab_general, text="General & Apariencia")
        notebook.add(tab_hotkeys, text="Atajos de Teclado")
        notebook.add(tab_profiles, text="Perfiles & Orden")

        temp_config = copy.deepcopy(self.config)
        self.active_config = temp_config
        temp_dofus_list = self.dofus_windows[:] 

        # animate window in
        try: self.fade_in_window(top, duration=240)
        except: pass

        def create_modern_selector(parent, label, options, key):
            f = tk.Frame(parent, bg=COLOR_DOFUS_BG)
            f.pack(fill='x', padx=10, pady=5)
            tk.Label(f, text=label, bg=COLOR_DOFUS_BG, font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=(0,2))
            btn_frame = tk.Frame(f, bg=COLOR_DOFUS_BG)
            btn_frame.pack(fill='x')
            buttons = []
            def on_click(val):
                temp_config[key] = val
                update_buttons()
                self.image_cache = {} 
                self.render_ui()
            def update_buttons():
                current = temp_config.get(key)
                for b_val, b_obj in buttons:
                    if b_val == current:
                        b_obj.config(bg="#d4ae80", fg="black", relief="sunken")
                    else:
                        b_obj.config(bg=COLOR_BUTTON_INACTIVE, fg=COLOR_TEXTO, relief="flat")
            for val, text in options:
                btn = tk.Button(btn_frame, text=text, font=("Segoe UI", 8), bd=0, padx=5, pady=4,
                                command=lambda v=val: on_click(v))
                btn.pack(side='left', fill='x', expand=True, padx=1)
                buttons.append((val, btn))
            update_buttons()

        # TAB 1
        gen_frame = tk.Frame(tab_general, bg=COLOR_DOFUS_BG)
        gen_frame.pack(fill='both', expand=True, padx=10, pady=10)
        create_modern_selector(gen_frame, "Tamaño de Interfaz", [("small", "Pequeño"), ("medium", "Medio"), ("large", "Grande")], "ui_scale")
        create_modern_selector(gen_frame, "Orientación", [("vertical", "Vertical"), ("horizontal", "Horizontal")], "orientation")
        create_modern_selector(gen_frame, "Modo de Texto", [("always", "Siempre"), ("hover", "Tooltip"), ("never", "Nunca")], "text_mode")

        tk.Label(gen_frame, text="Opacidad", bg=COLOR_DOFUS_BG, font=("Segoe UI", 9, "bold")).pack(anchor='w', padx=10, pady=(10,0))
        scale_op = tk.Scale(gen_frame, from_=0.2, to=1.0, resolution=0.1, orient='horizontal', bg=COLOR_DOFUS_BG, highlightthickness=0,
                            command=lambda v: self.root.attributes('-alpha', float(v)))
        scale_op.set(temp_config.get('opacity', 1.0))
        scale_op.pack(fill='x', padx=10)
        scale_op.bind("<ButtonRelease-1>", lambda e: temp_config.update({"opacity": scale_op.get()}))

        chk_frame = tk.Frame(gen_frame, bg=COLOR_DOFUS_BG)
        chk_frame.pack(fill='x', padx=10, pady=15)
        var_lock = tk.BooleanVar(value=temp_config.get('locked', False))
        var_smart = tk.BooleanVar(value=temp_config.get('smart_hide', False))
        def update_bools():
            temp_config['locked'] = var_lock.get()
            temp_config['smart_hide'] = var_smart.get()
            self.active_config['locked'] = temp_config['locked'] 
        tk.Checkbutton(chk_frame, text="🔒 Bloquear Movimiento", variable=var_lock, bg=COLOR_DOFUS_BG, command=update_bools).pack(anchor='w')
        tk.Checkbutton(chk_frame, text="👁 Smart Hide (Ocultar Display): Ctrl + Shift + H", variable=var_smart, bg=COLOR_DOFUS_BG, command=update_bools).pack(anchor='w')

        try:
            almanax_outer = tk.Frame(gen_frame, bg=COLOR_DOFUS_BG)
            almanax_outer.pack(fill='x', padx=10, pady=(0, 10))

            almanax_inner = tk.Frame(almanax_outer, bg=COLOR_PANEL_BG, bd=1, relief='solid')
            almanax_inner.pack(fill='x')

            almanax_header = tk.Frame(almanax_inner, bg=COLOR_HEADER_BG)
            almanax_header.pack(fill='x')
            tk.Label(
                almanax_header,
                text="ALMANAX",
                bg=COLOR_HEADER_BG,
                fg=COLOR_HEADER_FG,
                font=("Segoe UI", 10, "bold")
            ).pack(padx=8, pady=6)

            almanax_body = tk.Frame(almanax_inner, bg=COLOR_PANEL_BG)
            almanax_body.pack(fill='x', padx=10, pady=10)

            lbl_almanax_ico = tk.Label(almanax_body, bg=COLOR_PANEL_BG)
            lbl_almanax_ico.pack(anchor='center', pady=(0, 6))

            lbl_almanax_offer = tk.Label(
                almanax_body,
                text="Cargando Almanax...",
                bg=COLOR_PANEL_BG,
                fg=COLOR_TEXTO,
                font=("Segoe UI", 9, "bold"),
                justify='center'
            )
            lbl_almanax_offer.pack(fill='x', pady=(0, 6))

            lbl_almanax_bonus = tk.Label(
                almanax_body,
                text="",
                bg=COLOR_PANEL_BG,
                fg=COLOR_TEXTO,
                font=("Segoe UI", 9),
                justify='center'
            )
            lbl_almanax_bonus.pack(fill='x')

            def _update_almanax_wrap(e=None):
                try:
                    w = almanax_body.winfo_width()
                    # margen para que no se pegue a los bordes
                    wrap = max(260, int(w - 20))
                    lbl_almanax_offer.config(wraplength=wrap)
                    lbl_almanax_bonus.config(wraplength=wrap)
                except:
                    pass

            try:
                almanax_body.bind('<Configure>', _update_almanax_wrap)
                self.root.after(0, _update_almanax_wrap)
            except:
                pass

            def _apply_almanax_to_ui(offer, bonus):
                try:
                    lbl_almanax_offer.config(text=offer)
                    lbl_almanax_bonus.config(text=bonus)
                except:
                    pass
                try:
                    ico = self.get_dolmanax_icon(size=46)
                    self.dolmanax_icon = ico
                    if ico:
                        lbl_almanax_ico.config(image=ico)
                    else:
                        lbl_almanax_ico.config(image='')
                except:
                    pass

            def _load_almanax_bg():
                try:
                    offer, bonus = self.get_almanax_data()
                except:
                    offer, bonus = "(Error cargando Almanax)", ""
                try:
                    self.root.after(0, lambda: _apply_almanax_to_ui(offer, bonus))
                except:
                    pass

            threading.Thread(target=_load_almanax_bg, daemon=True).start()
        except:
            pass

        # TAB 2
        key_frame = tk.Frame(tab_hotkeys, bg=COLOR_DOFUS_BG)
        key_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        def capture_key(event, var, key_name=None):
            k = event.keysym.lower()
            map_keys = {"prior": "pageup", "next": "pagedown", "return": "enter"}
            final_key = map_keys.get(k, k)
            var.set(final_key)
            if key_name: temp_config[key_name] = final_key
            return "break"
        def create_key_entry(parent, label_text, var, key_map_name=None):
            fr = tk.Frame(parent, bg=COLOR_DOFUS_BG)
            fr.pack(fill='x', pady=1)
            tk.Label(fr, text=label_text, bg=COLOR_DOFUS_BG, width=15, anchor='w', font=("Segoe UI", 9)).pack(side='left')
            ent = tk.Entry(fr, textvariable=var, bg="#e0dccc", justify='center', relief="flat", bd=1, highlightthickness=0)
            ent.pack(side='right', expand=True, fill='x')
            ent.bind("<KeyPress>", lambda e: capture_key(e, var, key_map_name))

        tk.Label(key_frame, text="Navegación", bg=COLOR_DOFUS_BG, font=("Segoe UI", 9, "bold")).pack(pady=5)
        var_next = tk.StringVar(value=temp_config.get("key_next", "pagedown"))
        var_prev = tk.StringVar(value=temp_config.get("key_prev", "pageup"))
        create_key_entry(key_frame, "Siguiente >>", var_next, "key_next")
        create_key_entry(key_frame, "Anterior <<", var_prev, "key_prev")
        tk.Label(key_frame, text="Slots Personajes", bg=COLOR_DOFUS_BG, font=("Segoe UI", 9, "bold")).pack(pady=5)
        vars_slots = []
        for i in range(8):
            val = temp_config['slots'][i] if i < len(temp_config['slots']) else ""
            v = tk.StringVar(value=val)
            vars_slots.append(v)
            create_key_entry(key_frame, f"Personaje {i+1}", v)

        # TAB 3
        prof_frame = tk.Frame(tab_profiles, bg=COLOR_DOFUS_BG)
        prof_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Button(prof_frame, text="↕️REORDENAR VENTANAS", 
                 command=lambda: self.open_organizer_popup(top, temp_dofus_list), 
                 bg="#d4ae80", font=("Segoe UI", 9, "bold")).pack(fill='x', pady=5)

        tk.Label(prof_frame, text="Gestión de Perfiles (Teams)", bg=COLOR_DOFUS_BG, font=("Segoe UI", 9, "bold")).pack(pady=(15, 5))
        lb_profiles = tk.Listbox(prof_frame, bg="#e0dccc", height=5)
        lb_profiles.pack(fill='x', padx=5)
        
        def refresh_profiles():
            lb_profiles.delete(0, tk.END)
            for p_name in temp_config.get('profiles', {}):
                lb_profiles.insert(tk.END, p_name)
        refresh_profiles()

        def save_profile():
            name = simpledialog.askstring("Guardar Perfil", "Nombre del Team (ej: PvM):", parent=top)
            if name:
                order_names = [w['char_name'] for w in temp_dofus_list]
                temp_config['profiles'][name] = order_names
                refresh_profiles()

        def load_profile():
            nonlocal temp_dofus_list
            sel = lb_profiles.curselection()
            if not sel: return
            p_name = lb_profiles.get(sel[0])
            saved_order = temp_config['profiles'].get(p_name, [])
            current_pool = temp_dofus_list[:]
            new_list = []
            for saved_char in saved_order:
                found = next((w for w in current_pool if w['char_name'] == saved_char), None)
                if found:
                    new_list.append(found)
                    current_pool.remove(found)
            new_list.extend(current_pool)
            temp_dofus_list[:] = new_list 
            self.dofus_windows = temp_dofus_list
            self.render_ui()
            messagebox.showinfo("Cargado", f"Perfil '{p_name}' aplicado.", parent=top)

        btn_box = tk.Frame(prof_frame, bg=COLOR_DOFUS_BG)
        btn_box.pack(fill='x', pady=5)
        self.styled_button(btn_box, "💾 Guardar", save_profile, primary=True, primary_color=COLOR_HEADER_FG).pack(side='left', expand=True, fill='x', padx=2)
        self.styled_button(btn_box, "📂 Cargar", load_profile, primary=False, secondary_color=COLOR_PANEL_BG).pack(side='left', expand=True, fill='x', padx=2)

        # FOOTER CON YOUTUBE
        footer_frame = tk.Frame(top, bg=COLOR_DOFUS_BG)
        footer_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        lbl_yt = tk.Label(footer_frame, text="YouTube: @KhytrayerDofus", bg=COLOR_DOFUS_BG, fg=COLOR_LINK, font=("Segoe UI", 9, "underline"), cursor="hand2")
        lbl_yt.pack(side='left')
        lbl_yt.bind("<Button-1>", lambda e: webbrowser.open(LINK_YOUTUBE))
        
        def save():
            temp_config['slots'] = [x.get() for x in vars_slots]
            self.config = temp_config
            self.active_config = self.config
            self.dofus_windows = temp_dofus_list
            self.save_config()
            self.render_ui()
            top.destroy()
        
        def cancel():
            self.active_config = self.config 
            self.root.attributes('-alpha', self.config.get('opacity', 1.0))
            self.scan_windows()
            top.destroy()

        self.styled_button(footer_frame, "Guardar", save, primary=True, primary_color=COLOR_HEADER_FG).pack(side='right', padx=5)
        self.styled_button(footer_frame, "Cancelar", cancel, primary=False, secondary_color=COLOR_DOFUS_BORDER).pack(side='right', padx=5)
        top.protocol("WM_DELETE_WINDOW", cancel)

        # Ajustar alto inicial razonable
        try:
            top.update_idletasks()
            screen_h = top.winfo_screenheight()
            top.minsize(600, min(520, int(screen_h * 0.9)))
        except:
            pass

        def _cleanup_scroll_binds():
            try:
                top.unbind_all('<MouseWheel>')
            except:
                pass

        try:
            top.bind('<Destroy>', lambda e: _cleanup_scroll_binds())
        except:
            pass

    # --- ORGANIZADOR POPUP (REAL-TIME UPDATE + DOFUS COLORS) ---
    def open_organizer_popup(self, parent, target_list):
        org_win = tk.Toplevel(parent)
        org_win.title("Organizador")
        org_win.configure(bg=COLOR_DOFUS_BG)
        # compact default size; will expand based on content
        preferred_h = min(60 + len(target_list) * 44, 420)
        org_win.geometry(f"420x{preferred_h}")
        try: org_win.attributes('-alpha', 0.0)
        except: pass
        if os.path.exists("icono.ico"):
            try: org_win.iconbitmap("icono.ico")
            except: pass
        org_win.transient(parent)
        org_win.attributes('-topmost', True)
        try: self.fade_in_window(org_win, duration=180)
        except: pass

        # Header with accent
        hdr = tk.Frame(org_win, bg=COLOR_HEADER_BG)
        hdr.pack(fill='x')
        tk.Label(hdr, text="Organizador de Ventanas", bg=COLOR_HEADER_BG, fg=COLOR_HEADER_FG, font=("Segoe UI", 10, "bold")) .pack(side='left', padx=10, pady=8)

        # toggle mostrar iniciativa (discreto)
        show_initiative = tk.BooleanVar(value=False)
        chk_init = tk.Checkbutton(hdr, text='Mostrar iniciativa', variable=show_initiative,
                      bg=COLOR_HEADER_BG, fg=COLOR_HEADER_FG, selectcolor=COLOR_HEADER_BG,
                      activebackground=COLOR_HEADER_BG, bd=0, highlightthickness=0,
                      font=("Segoe UI", 8), command=lambda: refresh_list_ui())
        chk_init.pack(side='right', padx=8, pady=6)

        info = tk.Label(org_win, text="Arrastra para reordenar — suelta para aplicar", bg=COLOR_DOFUS_BG, fg=COLOR_TEXTO, font=("Segoe UI", 9))
        info.pack(fill='x', padx=10, pady=(6,4))

        frame_container = tk.Frame(org_win, bg=COLOR_DOFUS_BG)
        frame_container.pack(fill='both', expand=True, padx=10, pady=6)

        inner_list = tk.Frame(frame_container, bg=COLOR_DOFUS_BG)
        inner_list.pack(fill='both', expand=True)

        row_widgets = []
        init_entries = []

        def focus_next_init(idx):
            try:
                for j in range(idx+1, len(init_entries)):
                    w = init_entries[j]
                    if w and str(w) != '' and w.winfo_exists():
                        try:
                            w.focus_set()
                            w.selection_range(0, 'end')
                        except: pass
                        return
            except: pass

        def focus_prev_init(idx):
            try:
                for j in range(idx-1, -1, -1):
                    w = init_entries[j]
                    if w and str(w) != '' and w.winfo_exists():
                        try:
                            w.focus_set()
                            w.selection_range(0, 'end')
                        except: pass
                        return
            except: pass

        def _global_key_handler(e):
            try:
                if e.keysym != 'Tab':
                    return
                focused = org_win.focus_get()
                if not focused:
                    return
                if DEBUG_TAB:
                    try:
                        print("[DEBUG_TAB] global handler keysym=", e.keysym)
                        print("[DEBUG_TAB] focused=", focused, "type=", type(focused))
                        try:
                            print("[DEBUG_TAB] tk_focusNext=", focused.tk_focusNext())
                        except Exception:
                            print("[DEBUG_TAB] tk_focusNext() unavailable")
                        print("[DEBUG_TAB] row_widgets count=", len(row_widgets), "init_entries=", len(init_entries))
                    except: pass
                shift = (e.state & 0x0001) != 0

                # try to find the row index by climbing parents from the focused widget
                row_idx = None
                try:
                    w = focused
                    while w is not None:
                        if w in row_widgets:
                            row_idx = row_widgets.index(w)
                            break
                        w = getattr(w, 'master', None)
                except: row_idx = None

                # if we couldn't find a row, maybe the focused widget is the entry itself
                if row_idx is None:
                    try:
                        for i, ent in enumerate(init_entries):
                            if ent is focused:
                                row_idx = i
                                break
                    except: row_idx = None

                if row_idx is None:
                    return

                next_idx = row_idx - 1 if shift else row_idx + 1
                # move to next/prev existing initiative entry in that direction
                while 0 <= next_idx < len(init_entries):
                    try:
                        cand = init_entries[next_idx]
                        if cand and cand.winfo_exists():
                            try:
                                cand.focus_set()
                                cand.selection_range(0, 'end')
                                return 'break'
                            except: pass
                    except: pass
                    next_idx = next_idx - 1 if shift else next_idx + 1
                return 'break'
            except:
                return

        def save_initiative(idx, var):
            try:
                val = int(var.get())
            except:
                val = 0
                try: var.set('0')
                except: pass
            if 0 <= idx < len(target_list):
                target_list[idx]['initiative'] = val

        def sort_by_initiative():
            try:
                target_list.sort(key=lambda it: int(it.get('initiative', 0)), reverse=True)
            except:
                # fallback robust numeric sort
                def _safe(it):
                    try: return int(it.get('initiative', 0))
                    except: return 0
                target_list.sort(key=_safe, reverse=True)
            self.dofus_windows = target_list[:]
            try: self.render_ui()
            except: pass
            refresh_list_ui()

        # footer area (kept empty; sorting happens automatically when iniciativa is edited)
        footer = tk.Frame(org_win, bg=COLOR_DOFUS_BG)
        footer.pack(fill='x', padx=10, pady=(6,8))

        def refresh_list_ui():
            nonlocal row_widgets, init_entries
            row_widgets = []
            init_entries = []
            row_to_entry = []
            for w in inner_list.winfo_children(): w.destroy()

            for idx, item in enumerate(target_list):
                char_name = item.get("char_name", "")
                clase = item.get("class_name", "")

                row = tk.Frame(inner_list, bg=COLOR_ROW_NORMAL, bd=0, relief='flat')
                row.pack(fill='x', pady=4, padx=2)
                row_widgets.append(row)

                # icon area
                imgs = self.get_processed_images(item.get('class_name',''))
                if imgs:
                    ico = tk.Label(row, image=imgs['normal'], bg=COLOR_ROW_NORMAL)
                    ico.image = imgs['normal']
                    ico.pack(side='left', padx=(8,6), pady=6)
                else:
                    ico = tk.Label(row, text='?', bg=COLOR_ROW_NORMAL, width=3)
                    ico.pack(side='left', padx=(8,6), pady=6)

                lbl = tk.Label(row, text=f"{idx+1}. {clase} - {char_name}", bg=COLOR_ROW_NORMAL, fg=COLOR_TEXTO, font=("Segoe UI", 9))
                lbl.pack(side='left', fill='x', expand=True, padx=6, pady=8)

                # iniciativa entry (numeric) - shown only if toggle activo
                init_var = tk.StringVar(value=str(item.get('initiative', 0)))
                if show_initiative.get():
                    # attempt to load initiative icon into cache
                    try:
                        if 'initiative_icon' not in self.image_cache:
                            url = 'https://dofusdb.fr/icons/effects/initiative.png'
                            try:
                                raw = urllib.request.urlopen(url, timeout=2).read()
                                img = Image.open(io.BytesIO(raw)).convert('RGBA')
                                img = img.resize((18, 18), Image.LANCZOS)
                                tkimg = ImageTk.PhotoImage(img)
                                self.image_cache['initiative_icon'] = tkimg
                            except:
                                self.image_cache['initiative_icon'] = None
                    except:
                        pass

                    img_lbl = None
                    try:
                        ic = self.image_cache.get('initiative_icon')
                        if ic:
                            img_lbl = tk.Label(row, image=ic, bg=COLOR_ROW_NORMAL)
                            img_lbl.image = ic
                            img_lbl.pack(side='right', padx=(6,2), pady=8)
                    except: img_lbl = None

                    ent_init = tk.Entry(row, textvariable=init_var, width=6, justify='center', bd=1, takefocus=1)
                    ent_init.pack(side='right', padx=(2,4), pady=8)
                    # add to list for tab-navigation and map to row
                    ent_init._row_widget = row
                    init_entries.append(ent_init)
                    row_to_entry.append(ent_init)
                    def _on_focus_out(e, i=idx, v=init_var):
                        save_initiative(i, v)
                        try:
                            sort_by_initiative()
                        except: pass
                        try: refresh_list_ui()
                        except: pass
                    def _on_return(e, i=idx, v=init_var):
                        save_initiative(i, v)
                        try: sort_by_initiative()
                        except: pass
                        try: refresh_list_ui()
                        except: pass

                    def _tab_move(e, reverse=False):
                        try:
                            # find the row index of the current entry by its attached row
                            cur_row = getattr(e.widget, '_row_widget', None)
                            if cur_row is None:
                                # fallback: climb parents
                                w = e.widget
                                while w is not None and w not in row_widgets:
                                    w = getattr(w, 'master', None)
                                cur_row = w
                            if cur_row is None:
                                return 'break'
                            try:
                                idx_row = row_widgets.index(cur_row)
                            except ValueError:
                                return 'break'
                            next_idx = idx_row - 1 if reverse else idx_row + 1
                            # find next row with an entry
                            while 0 <= next_idx < len(row_widgets):
                                try:
                                    cand = row_to_entry[next_idx]
                                    if cand and cand.winfo_exists():
                                        try:
                                            cand.focus_set()
                                            cand.selection_range(0, 'end')
                                            return 'break'
                                        except: pass
                                except: pass
                                next_idx = next_idx - 1 if reverse else next_idx + 1
                        except: pass
                        return 'break'

                    ent_init.bind('<FocusOut>', _on_focus_out)
                    ent_init.bind('<Return>', _on_return)
                    ent_init.bind('<Tab>', lambda e: _tab_move(e, reverse=False))
                    ent_init.bind('<Shift-Tab>', lambda e: _tab_move(e, reverse=True))
                    ent_init.bind('<Down>', lambda e: _tab_move(e, reverse=False))
                    ent_init.bind('<Up>', lambda e: _tab_move(e, reverse=True))
                    ent_init.bind('<Control-Down>', lambda e: _tab_move(e, reverse=False))
                    ent_init.bind('<Control-Up>', lambda e: _tab_move(e, reverse=True))

                # drag handle
                handle = tk.Label(row, text='☰', bg=COLOR_ROW_NORMAL, fg=COLOR_TEXTO, font=("Segoe UI", 11))
                handle.pack(side='right', padx=8)

                # bind drag events (accept missing event arg)
                for w in (row, lbl, ico, handle):
                    try:
                        w.bind('<Button-1>', lambda e=None, i=idx: on_start(e, i))
                        w.bind('<B1-Motion>', on_move)
                        w.bind('<ButtonRelease-1>', on_release)
                    except: pass

            # ensure any global KeyPress binding is removed to avoid conflicts
            # build an explicit focus chain for initiative entries to avoid
            # relying on platform-specific tk_focusNext behavior
            try:
                if init_entries:
                    for i, ent in enumerate(init_entries):
                        try:
                            ent.configure(takefocus=1)
                        except: pass
                        # compute next/prev (no wrap-around by default)
                        nxt = init_entries[i+1] if i+1 < len(init_entries) else None
                        prev = init_entries[i-1] if i-1 >= 0 else None

                        def _make_goto(target):
                            def _h(ev, target=target):
                                try:
                                    if target and target.winfo_exists():
                                        target.focus_set()
                                        try: target.selection_range(0, 'end')
                                        except: pass
                                        return 'break'
                                except: pass
                                return 'break'
                            return _h

                        try:
                            ent.unbind('<Tab>')
                            ent.unbind('<Shift-Tab>')
                        except: pass
                        try:
                            ent.bind('<Tab>', _make_goto(nxt))
                            ent.bind('<Shift-Tab>', _make_goto(prev))
                            # additional event names (platforms differ)
                            ent.bind('<ISO_Left_Tab>', _make_goto(prev))
                            ent.bind('<KeyPress-Tab>', _make_goto(nxt))
                        except: pass
            except: pass

            try:
                try: org_win.unbind_all('<KeyPress>')
                except: pass
            except: pass

            # Resize window height to fit content using real widget heights
            try:
                org_win.update_idletasks()
                inner_req = inner_list.winfo_reqheight()
                hdr_h = hdr.winfo_reqheight() if 'hdr' in locals() or 'hdr' in globals() else 60
                info_h = info.winfo_reqheight() if 'info' in locals() or 'info' in globals() else 24
                # add some padding for margins and potential footer area
                bottom_pad = 32
                desired_h = hdr_h + info_h + inner_req + bottom_pad
                screen_h = org_win.winfo_screenheight()
                max_h = min(520, screen_h - 120)
                desired_h = max(160, min(desired_h, max_h))
                # keep width consistent
                org_win.geometry(f"420x{desired_h}")
            except: pass

        drag_data = {"idx": None, "active": False}

        def on_start(event, idx):
            drag_data["idx"] = idx
            drag_data["active"] = True
            org_win.config(cursor="fleur")
            # highlight source
            if 0 <= idx < len(row_widgets):
                w_row = row_widgets[idx]
                w_row.config(bg=COLOR_ROW_DRAGGING)
                for child in w_row.winfo_children():
                    try: child.config(bg=COLOR_ROW_DRAGGING)
                    except: pass

        def on_move(event):
            if not drag_data["active"]: return
            # compute target index using widget centers for accuracy
            y_rel = event.y_root - inner_list.winfo_rooty()
            ins = 0
            centers = []
            for w in row_widgets:
                centers.append(w.winfo_rooty() - inner_list.winfo_rooty() + w.winfo_height()/2)
            for i, c in enumerate(centers):
                if y_rel > c:
                    ins = i+1

            # visual feedback
            for i, rw in enumerate(row_widgets):
                try:
                    rw.config(bg=COLOR_ROW_NORMAL)
                    for ch in rw.winfo_children(): ch.config(bg=COLOR_ROW_NORMAL)
                except: pass
            # sorting is automatic on iniciativa edit; no manual sort button

            src_idx = drag_data.get('idx')
            if 0 <= src_idx < len(row_widgets):
                try:
                    rw_src = row_widgets[src_idx]
                    rw_src.config(bg=COLOR_ROW_DRAGGING)
                    for child in rw_src.winfo_children(): child.config(bg=COLOR_ROW_DRAGGING)
                except: pass

            if 0 <= ins < len(row_widgets):
                try:
                    rw_tgt = row_widgets[ins]
                    rw_tgt.config(bg=COLOR_ROW_TARGET)
                    for child in rw_tgt.winfo_children(): child.config(bg=COLOR_ROW_TARGET)
                except: pass

        def on_release(event):
            org_win.config(cursor="arrow")
            if not drag_data["active"]: return
            y_rel = event.y_root - inner_list.winfo_rooty()
            ins = 0
            centers = []
            for w in row_widgets:
                centers.append(w.winfo_rooty() - inner_list.winfo_rooty() + w.winfo_height()/2)
            for i, c in enumerate(centers):
                if y_rel > c:
                    ins = i+1

            src = drag_data["idx"]
            if src is None:
                drag_data["active"] = False
                return
            if src != ins:
                item = target_list.pop(src)
                if ins > src:
                    ins -= 1
                target_list.insert(int(ins), item)
                self.dofus_windows = target_list[:]
                self.render_ui()

            drag_data["active"] = False
            refresh_list_ui()

        refresh_list_ui()

    # --- SYSTEM ---
    def close_app(self):
        self.save_config()
        try:
            keyboard.unhook_all()
        except:
            pass
        self.root.quit()

    def cycle_windows(self, direction):
        if not self.dofus_windows: return
        if not self.is_safe_context(): return
        active = gw.getActiveWindow()
        curr_t = active.title if active else ""
        curr_idx = -1
        for i, item in enumerate(self.dofus_windows):
            if item['window_title'] == curr_t:
                curr_idx = i
                break
        if curr_idx == -1: next_idx = 0
        else: next_idx = (curr_idx + direction) % len(self.dofus_windows)
        self.force_focus(self.dofus_windows[next_idx]['window_title'])

    def conditional_activate(self, target):
        if self.is_safe_context():
            self.force_focus(target)

    def is_safe_context(self):
        try:
            active = gw.getActiveWindow()
            if not active: return False
            if any(item['window_title'] == active.title for item in self.dofus_windows): return True
            if "KhyDofus" in active.title: return True
            return False
        except: return False

    def force_focus(self, window_title):
        try:
            windows = gw.getWindowsWithTitle(window_title)
            if not windows: return
            t_win = windows[0]
            hwnd_t = t_win._hWnd 
            hwnd_a = user32.GetForegroundWindow()
            tid_a = user32.GetWindowThreadProcessId(hwnd_a, None)
            tid_t = user32.GetWindowThreadProcessId(hwnd_t, None)
            tid_c = kernel32.GetCurrentThreadId()
            if hwnd_t == hwnd_a: return
            if tid_a != tid_c: user32.AttachThreadInput(tid_c, tid_a, True)
            if tid_t != tid_c: user32.AttachThreadInput(tid_c, tid_t, True)
            if user32.IsIconic(hwnd_t): user32.ShowWindow(hwnd_t, 9)
            else: user32.ShowWindow(hwnd_t, 5)
            user32.SetForegroundWindow(hwnd_t)
            user32.SetFocus(hwnd_t)
            if tid_a != tid_c: user32.AttachThreadInput(tid_c, tid_a, False)
            if tid_t != tid_c: user32.AttachThreadInput(tid_c, tid_t, False)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = DofusOrganizer(root)
    root.mainloop()