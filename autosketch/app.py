import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk
from pynput import keyboard

from autosketch.drawing.plan import (
    build_color_plan,
    build_contour_plan,
    build_pixel_plan,
    distinct_color_count,
)
from autosketch.executor import execute_plan
from autosketch.screen.calibration import capture_points, capture_points_until_enter
from autosketch.screen.mouse import MouseController
from autosketch.screen.palette import build_palette
from autosketch.screen.presets import SITE_NAMES, load_site_preset, save_site_preset
from autosketch.settings import detail_to_epsilon_ratio, detail_to_grid_cols
from autosketch.vision.loader import get_image_info, load_image, load_image_from_url

IMAGE_FILETYPES = [("Images", "*.png *.jpg *.jpeg *.bmp"), ("Tous les fichiers", "*.*")]
PREVIEW_SIZE = (260, 260)

BG = "#1f2430"
PANEL = "#262b3a"
ACCENT = "#4f8cff"
TEXT = "#e6e9f0"
MUTED = "#8b93a7"
OK_COLOR = "#5fd08a"
WARN_COLOR = "#f0a35e"

MODES = [
    ("Couleur", "color"),
    ("Contours", "contour"),
    ("Pixels", "pixel"),
]


class App:
    def __init__(self, root):
        self.root = root
        self.image = None
        self.image_name = None
        self._preview_photo = None
        self._busy = False
        self._exit_event = threading.Event()

        root.title("AutoSketch AI")
        root.geometry("880x600")
        root.minsize(820, 560)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_style()
        self._build_layout()
        self._refresh_calibration_status()

        self._key_listener = keyboard.Listener(on_press=self._on_key_press)
        self._key_listener.start()

    # -- interface --

    def _build_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=BG, foreground=TEXT, fieldbackground=PANEL)
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabelframe", background=BG, foreground=TEXT, bordercolor=MUTED)
        style.configure("TLabelframe.Label", background=BG, foreground=ACCENT,
                        font=("Segoe UI", 9, "bold"))
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Ok.TLabel", background=BG, foreground=OK_COLOR, font=("Segoe UI", 9, "bold"))
        style.configure("Warn.TLabel", background=BG, foreground=WARN_COLOR, font=("Segoe UI", 9, "bold"))
        style.configure("Status.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9), padding=5)
        style.configure("Draw.TButton", font=("Segoe UI", 12, "bold"), padding=12)
        style.configure("TCheckbutton", background=BG, foreground=TEXT, font=("Segoe UI", 9))
        style.configure("TRadiobutton", background=BG, foreground=TEXT, font=("Segoe UI", 9))
        style.configure("Horizontal.TProgressbar", background=ACCENT)

    def _build_layout(self):
        header = ttk.Frame(self.root, padding=(16, 12, 16, 6))
        header.pack(fill="x")
        ttk.Label(header, text="AutoSketch AI", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Dessine une image d'internet sur Skribbl.io, Gartic Phone ou Paint.",
                  style="Sub.TLabel").pack(anchor="w")

        body = ttk.Frame(self.root, padding=(16, 0, 16, 8))
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", padx=(0, 14))
        self._build_preview(left)
        self._build_log(left)

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        self._build_steps(right)

        self._build_status_bar()

    def _build_preview(self, parent):
        frame = ttk.Labelframe(parent, text="Apercu", padding=8)
        frame.pack(fill="x")
        self.preview_canvas = tk.Canvas(frame, width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1],
                                        bg=PANEL, highlightthickness=0)
        self.preview_canvas.pack()
        self.image_label = ttk.Label(frame, text="Aucune image", style="Sub.TLabel")
        self.image_label.pack(pady=(6, 0))

    def _build_log(self, parent):
        frame = ttk.Labelframe(parent, text="Journal", padding=6)
        frame.pack(fill="both", expand=True, pady=(10, 0))

        self.log_box = tk.Text(frame, width=34, height=8, bg=PANEL, fg=TEXT, insertbackground=TEXT,
                               relief="flat", font=("Consolas", 8), state="disabled", wrap="word")
        scrollbar = ttk.Scrollbar(frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _build_steps(self, parent):
        self.buttons = []

        # 1. Image
        step1 = ttk.Labelframe(parent, text="1 - Quelle image ?", padding=10)
        step1.pack(fill="x")
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(step1, textvariable=self.url_var)
        url_entry.pack(fill="x")
        url_entry.bind("<Return>", lambda _e: self._start(self._load_url))
        ttk.Label(step1, text="Colle l'adresse d'une image trouvee sur internet.",
                  style="Sub.TLabel").pack(anchor="w", pady=(3, 6))

        row = ttk.Frame(step1)
        row.pack(fill="x")
        self._add_button(row, "Charger l'URL", lambda: self._start(self._load_url), side="left")
        self._add_button(row, "Ou un fichier...", self._pick_file, side="left", padx=(6, 0))

        # 2. Cible
        step2 = ttk.Labelframe(parent, text="2 - Ou dessiner ?", padding=10)
        step2.pack(fill="x", pady=(10, 0))

        row = ttk.Frame(step2)
        row.pack(fill="x")
        self.site_var = tk.StringVar(value=SITE_NAMES[0])
        site_box = ttk.Combobox(row, textvariable=self.site_var, state="readonly", values=SITE_NAMES)
        site_box.pack(side="left", fill="x", expand=True)
        site_box.bind("<<ComboboxSelected>>", lambda _e: self._refresh_calibration_status())
        self._add_button(row, "Calibrer", lambda: self._start(self._calibrate), side="left", padx=(6, 0))

        self.calibration_label = ttk.Label(step2, text="", style="Warn.TLabel")
        self.calibration_label.pack(anchor="w", pady=(6, 0))

        # 3. Rendu
        step3 = ttk.Labelframe(parent, text="3 - Comment dessiner ?", padding=10)
        step3.pack(fill="x", pady=(10, 0))

        row = ttk.Frame(step3)
        row.pack(fill="x")
        self.mode_var = tk.StringVar(value=MODES[0][1])
        for label, value in MODES:
            ttk.Radiobutton(row, text=label, value=value, variable=self.mode_var).pack(side="left", padx=(0, 12))

        self.speed_var = tk.DoubleVar(value=600)
        self.detail_var = tk.DoubleVar(value=5)
        self._add_scale(step3, "Vitesse", self.speed_var, 100, 1500, "{:.0f} px/s")
        self._add_scale(step3, "Detail", self.detail_var, 1, 10, "{:.0f}/10")

        self.dither_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(step3, text="Dither (rend les degrades plus fideles)",
                        variable=self.dither_var).pack(anchor="w", pady=(6, 0))

        # Action
        self.draw_button = ttk.Button(parent, text="DESSINER", style="Draw.TButton",
                                      command=lambda: self._start(self._draw))
        self.draw_button.pack(fill="x", pady=(14, 0))
        self.buttons.append(self.draw_button)
        ttk.Label(parent, text="Appuie sur ECHAP a tout moment pour tout arreter.",
                  style="Sub.TLabel").pack(anchor="center", pady=(6, 0))

    def _add_button(self, parent, text, command, side="top", padx=0):
        button = ttk.Button(parent, text=text, command=command)
        button.pack(side=side, padx=padx)
        self.buttons.append(button)
        return button

    def _add_scale(self, parent, label, variable, from_, to_, fmt):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(8, 0))
        ttk.Label(row, text=label, width=8).pack(side="left")
        value_label = ttk.Label(row, text=fmt.format(variable.get()), width=9, anchor="e")
        value_label.pack(side="right")
        scale = ttk.Scale(row, from_=from_, to=to_, variable=variable, orient="horizontal",
                          command=lambda _v: value_label.configure(text=fmt.format(variable.get())))
        scale.pack(side="left", fill="x", expand=True, padx=8)

    def _build_status_bar(self):
        bar = ttk.Frame(self.root, style="Panel.TFrame", padding=(12, 6))
        bar.pack(fill="x", side="bottom")
        self.status_label = ttk.Label(bar, text="Pret", style="Status.TLabel")
        self.status_label.pack(side="left")
        self.progress = ttk.Progressbar(bar, mode="indeterminate", length=140)
        self.progress.pack(side="right")

    # -- plomberie --

    def _on_key_press(self, key):
        if key == keyboard.Key.esc:
            self._exit_event.set()

    def _on_close(self):
        if self._busy and not messagebox.askyesno(
            "AutoSketch AI",
            "Une action est en cours. Fermer maintenant peut laisser le bouton de la souris "
            "enfonce dans ton logiciel de dessin. Fermer quand meme ?",
            parent=self.root,
        ):
            return
        self._exit_event.set()
        self._key_listener.stop()
        self.root.destroy()

    def log(self, message):
        def append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.root.after(0, append)

    def _set_busy(self, busy, status):
        def apply():
            self.status_label.configure(text=status)
            state = "disabled" if busy else "normal"
            for button in self.buttons:
                button.configure(state=state)
            if busy:
                self.progress.start(12)
            else:
                self.progress.stop()
        self.root.after(0, apply)

    def _start(self, action):
        if self._busy:
            return
        self._busy = True
        self._exit_event.clear()
        self._set_busy(True, "En cours... (ECHAP pour arreter)")

        def worker():
            try:
                action()
            except Exception as e:
                self.log(f"Erreur : {e}")
            finally:
                self._busy = False
                self._set_busy(False, "Pret")

        threading.Thread(target=worker, daemon=True).start()

    def _interrupted(self):
        if self._exit_event.is_set():
            self.log("Interrompu (ECHAP).")
            return True
        return False

    def _countdown(self, seconds):
        self.log(f"Dessin dans {seconds} secondes... (ne touche plus a la souris)")
        for _ in range(seconds * 10):
            if self._exit_event.is_set():
                return False
            time.sleep(0.1)
        return True

    # -- etape 1 : image --

    def _set_image(self, image, name):
        self.image = image
        self.image_name = os.path.basename(name) or name
        info = get_image_info(image)

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb)
        pil_image.thumbnail(PREVIEW_SIZE, Image.LANCZOS)

        def apply():
            self._preview_photo = ImageTk.PhotoImage(pil_image)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(PREVIEW_SIZE[0] // 2, PREVIEW_SIZE[1] // 2,
                                             image=self._preview_photo)
            self.image_label.configure(text=f"{self.image_name}  -  {info['width']}x{info['height']} px")
        self.root.after(0, apply)
        self.log(f"Image chargee : {info['width']}x{info['height']} px")

    def _load_url(self):
        url = self.url_var.get().strip()
        if not url:
            self.log("Colle d'abord l'adresse d'une image.")
            return
        try:
            image = load_image_from_url(url)
        except Exception as e:
            self.log(f"Impossible de charger cette image : {e}")
            return
        self._set_image(image, url)

    def _pick_file(self):
        path = filedialog.askopenfilename(title="Choisir une image", filetypes=IMAGE_FILETYPES,
                                          parent=self.root)
        if not path:
            return
        try:
            self._set_image(load_image(path), path)
        except Exception as e:
            self.log(f"Impossible de charger ce fichier : {e}")

    # -- etape 2 : calibration --

    def _refresh_calibration_status(self):
        preset = load_site_preset(self.site_var.get())
        if preset is None:
            text, style = "Pas encore calibre - clique sur Calibrer.", "Warn.TLabel"
        else:
            palette, zone = preset
            (x1, y1), (x2, y2) = zone
            text = f"Calibre : zone {abs(x2 - x1)}x{abs(y2 - y1)} px, {len(palette)} couleur(s)."
            style = "Ok.TLabel"
        self.calibration_label.configure(text=text, style=style)

    def _calibrate(self):
        site = self.site_var.get()
        self.log(f"--- Calibration de {site} ---")
        self.log("1/3 Clique sur le COIN HAUT-GAUCHE de la zone de dessin.")
        top_left = capture_points(1)[0]
        if self._interrupted():
            return

        self.log("2/3 Clique sur le COIN BAS-DROITE de la zone de dessin.")
        bottom_right = capture_points(1)[0]
        if self._interrupted():
            return
        if top_left[0] == bottom_right[0] or top_left[1] == bottom_right[1]:
            self.log("Zone invalide : les deux coins sont alignes. Recommence.")
            return

        self.log("3/3 Clique sur chaque couleur de la palette, puis appuie sur ENTREE.")
        positions = capture_points_until_enter()
        if not positions:
            self.log("Aucune couleur cliquee : la selection de couleur sera desactivee.")
        palette = build_palette(positions)

        zone = (top_left, bottom_right)
        save_site_preset(site, palette, zone)
        self.root.after(0, self._refresh_calibration_status)
        self.log(f"{site} calibre : zone {abs(bottom_right[0] - top_left[0])}x"
                 f"{abs(bottom_right[1] - top_left[1])} px, {len(palette)} couleur(s). "
                 f"C'est enregistre, tu n'auras plus a le refaire.")

    # -- etape 3 : dessin --

    def _build_plan(self, palette):
        mode = self.mode_var.get()
        detail = self.detail_var.get()
        colors = palette.colors_rgb() if len(palette) else None

        if mode == "contour":
            return build_contour_plan(self.image, epsilon_ratio=detail_to_epsilon_ratio(detail))
        if mode == "pixel":
            return build_pixel_plan(self.image, cols=detail_to_grid_cols(detail),
                                    palette_colors_rgb=colors, dither=self.dither_var.get())
        return build_color_plan(self.image, palette_colors_rgb=colors,
                                dither=self.dither_var.get(),
                                epsilon_ratio=detail_to_epsilon_ratio(detail))

    def _explain_empty_plan(self, palette):
        """Dire ce qui s'est reellement passe : le curseur Detail n'y peut rien,
        c'est presque toujours la palette qui aplatit l'image."""
        if self.mode_var.get() == "contour":
            self.log("Rien a dessiner : aucun contour trouve. Cette image est probablement "
                     "trop uniforme ou trop floue.")
            return

        colors = palette.colors_rgb() if len(palette) else None
        distinct = distinct_color_count(self.image, palette_colors_rgb=colors,
                                        dither=self.dither_var.get())
        if distinct <= 1:
            if colors:
                self.log(f"Rien a dessiner : avec les {len(colors)} couleur(s) calibrees, "
                         f"toute l'image se ramene a une seule couleur. Recalibre la palette "
                         f"du site (etape 2) en cliquant des couleurs bien differentes.")
            else:
                self.log("Rien a dessiner : cette image est unie. Essaie une autre image.")
        else:
            self.log(f"Rien a dessiner alors que l'image compte {distinct} couleurs. "
                     f"Essaie le rendu Contours.")

    def _draw(self):
        if self.image is None:
            self.log("Charge d'abord une image (etape 1).")
            return

        site = self.site_var.get()
        preset = load_site_preset(site)
        if preset is None:
            self.log(f"{site} n'est pas encore calibre (etape 2).")
            return
        palette, zone = preset

        self.log(f"Preparation du trace ({self.mode_var.get()})...")
        plan = self._build_plan(palette)
        if plan.path_count() == 0:
            self._explain_empty_plan(palette)
            return
        self.log(f"{plan.path_count()} trait(s) sur {len(plan.groups)} couleur(s).")

        if not self._countdown(3):
            return self._interrupted()

        drawn = execute_plan(plan, MouseController(), zone, speed=self.speed_var.get(),
                             palette=palette if len(palette) else None,
                             exit_event=self._exit_event, on_event=self.log)

        if not self._interrupted():
            self.log(f"Termine : {drawn} trait(s) dessine(s).")


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()
