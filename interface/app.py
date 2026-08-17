import math
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import cv2
from PIL import Image, ImageTk
from pynput import keyboard

from ai_engine.style_learning import apply_style, extract_style, record_drawing
from ai_engine.trajectory_optimizer import refine_with_two_opt
from automation.mouse_controller import MouseController
from core.calibration import capture_points, capture_points_until_enter, map_points
from drawing_engine.grid_runs import extract_color_runs
from drawing_engine.path_builder import contours_to_paths, smooth_path
from drawing_engine.path_optimizer import optimize_path_order, total_travel_distance
from drawing_engine.shapes import (
    draw_circle,
    draw_ellipse,
    draw_filled_rect,
    draw_line,
    draw_path_with_speed,
    draw_polyline,
    draw_rectangle,
)
from plugins.palette import calibrate_palette, load_palette, save_palette, select_color
from vision.color_segmentation import color_masks, quantize_colors, quantize_to_palette
from vision.contour_detection import (
    detect_edges,
    find_contours,
    find_contours_from_mask,
    is_background_like,
)
from vision.image_loader import get_image_info, load_image
from vision.pixel_grid import image_to_grid

IMAGE_FILETYPES = [("Images", "*.png *.jpg *.jpeg *.bmp"), ("Tous les fichiers", "*.*")]
PREVIEW_SIZE = (280, 280)

BG = "#1f2430"
PANEL = "#262b3a"
ACCENT = "#4f8cff"
TEXT = "#e6e9f0"
MUTED = "#8b93a7"


class App:
    def __init__(self, root):
        self.root = root
        self.buttons = []
        self._busy = False
        self._preview_photo = None
        self.current_image = None
        self.current_image_name = None
        self.color_palette = None
        self._exit_event = threading.Event()

        root.title("AutoSketch AI")
        root.geometry("880x620")
        root.minsize(760, 560)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_style()
        self._build_menu()
        self._build_layout()

        self._key_listener = keyboard.Listener(on_press=self._on_key_press)
        self._key_listener.start()

    def _on_key_press(self, key):
        if key == keyboard.Key.esc:
            self._exit_event.set()

    # -- construction --

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
        style.configure("TLabelframe.Label", background=BG, foreground=MUTED, font=("Segoe UI", 9, "bold"))
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9), padding=6)
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), padding=6)
        style.configure("TCheckbutton", background=BG, foreground=TEXT, font=("Segoe UI", 9))
        style.configure("Horizontal.TProgressbar", background=ACCENT)

    def _build_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Charger une palette...", command=self._load_palette)
        file_menu.add_command(label="Enregistrer la palette...", command=self._save_palette)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.destroy)
        menu_bar.add_cascade(label="Fichier", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="A propos", command=self._show_about)
        menu_bar.add_cascade(label="Aide", menu=help_menu)

        self.root.config(menu=menu_bar)

    def _show_about(self):
        messagebox.showinfo(
            "A propos",
            "AutoSketch AI\n\n"
            "Reproduction automatique de dessins par pilotage de la souris.\n"
            "Vision par ordinateur + optimisation de trajectoires + apprentissage de style.",
        )

    def _build_layout(self):
        header = ttk.Frame(self.root, padding=(16, 14, 16, 8))
        header.pack(fill="x")
        ttk.Label(header, text="AutoSketch AI", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Ouvre ton logiciel de dessin avant de lancer une action.",
                  style="Sub.TLabel").pack(anchor="w")

        body = ttk.Frame(self.root, padding=(16, 0, 16, 8))
        body.pack(fill="both", expand=True)

        sidebar = ttk.Frame(body)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        self._build_sidebar(sidebar)

        main = ttk.Frame(body)
        main.pack(side="left", fill="both", expand=True)
        self._build_main_panel(main)

        self._build_status_bar()

    def _build_sidebar(self, parent):
        groups = [
            ("Formes", [
                ("Ligne", self._run_line),
                ("Rectangle", self._run_rectangle),
                ("Cercle", self._run_circle),
                ("Ellipse", self._run_ellipse),
                ("Polyligne libre", self._run_polyline),
            ]),
            ("Image", [
                ("Importer une image", self._run_import_image),
                ("Detecter les contours", self._run_detect_contours),
            ]),
            ("Reproduction", [
                ("Reproduire (N&B)", self._run_reproduce_image),
                ("Reproduire (couleur)", self._run_reproduce_color_image),
                ("Reproduire (matrice de pixels)", self._run_pixel_grid),
            ]),
            ("Intelligence artificielle", [
                ("Mode d'apprentissage", self._run_learning_mode),
            ]),
        ]

        for title, actions in groups:
            frame = ttk.Labelframe(parent, text=title, padding=8)
            frame.pack(fill="x", pady=(0, 10))
            for label, action in actions:
                button = ttk.Button(frame, text=label, width=26, command=lambda a=action: self._start(a))
                button.pack(fill="x", pady=2)
                self.buttons.append(button)

    def _build_main_panel(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="both", expand=True)

        preview_frame = ttk.Labelframe(top, text="Apercu", padding=8)
        preview_frame.pack(side="left", fill="y", padx=(0, 10))
        self.preview_canvas = tk.Canvas(preview_frame, width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1],
                                         bg=PANEL, highlightthickness=0)
        self.preview_canvas.pack()
        self.image_name_label = ttk.Label(preview_frame, text="Aucune image chargee", style="Sub.TLabel")
        self.image_name_label.pack(pady=(6, 0))

        params_frame = ttk.Labelframe(top, text="Parametres", padding=10)
        params_frame.pack(side="left", fill="both", expand=True)
        self._build_params(params_frame)

        log_frame = ttk.Labelframe(parent, text="Journal", padding=6)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.log_box = tk.Text(log_frame, height=10, bg=PANEL, fg=TEXT, insertbackground=TEXT,
                                relief="flat", font=("Consolas", 9), state="disabled", wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _build_params(self, parent):
        self.speed_var = tk.DoubleVar(value=400)
        self.precision_var = tk.DoubleVar(value=1.0)
        self.colors_var = tk.IntVar(value=6)
        self.grid_cols_var = tk.IntVar(value=24)
        self.fill_lines_var = tk.IntVar(value=4)
        self.smooth_var = tk.BooleanVar(value=True)
        self.skip_background_var = tk.BooleanVar(value=True)
        self.dither_var = tk.BooleanVar(value=False)

        self._add_scale(parent, 0, "Vitesse de trace (px/s)", self.speed_var, 100, 1200, "{:.0f}")
        self._add_scale(parent, 1, "Simplification des contours (%)", self.precision_var, 0.2, 3.0, "{:.1f}")
        self._add_scale(parent, 2, "Nombre de couleurs", self.colors_var, 2, 16, "{:.0f}")
        self._add_scale(parent, 3, "Colonnes de la grille (matrice)", self.grid_cols_var, 4, 64, "{:.0f}")
        self._add_scale(parent, 4, "Lignes de remplissage par cellule", self.fill_lines_var, 1, 8, "{:.0f}")

        ttk.Checkbutton(parent, text="Lisser les courbes", variable=self.smooth_var).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(8, 2))
        ttk.Checkbutton(parent, text="Ignorer le fond (contours > 90% de l'image)",
                         variable=self.skip_background_var).grid(row=6, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(parent, text="Dither (avec une palette chargee/calibree)",
                         variable=self.dither_var).grid(row=7, column=0, columnspan=2, sticky="w")

        parent.columnconfigure(1, weight=1)

    def _add_scale(self, parent, row, label, variable, from_, to_, fmt):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        value_label = ttk.Label(parent, text=fmt.format(variable.get()), width=6, anchor="e")
        value_label.grid(row=row, column=2, sticky="e", padx=(6, 0))

        def _on_change(_evt=None):
            value_label.configure(text=fmt.format(variable.get()))

        scale = ttk.Scale(parent, from_=from_, to=to_, variable=variable, orient="horizontal",
                           command=_on_change)
        scale.grid(row=row, column=1, sticky="ew", padx=8)

    def _build_status_bar(self):
        bar = ttk.Frame(self.root, style="Panel.TFrame", padding=(12, 6))
        bar.pack(fill="x", side="bottom")
        self.status_label = ttk.Label(bar, text="Pret", style="Status.TLabel")
        self.status_label.pack(side="left")
        self.progress = ttk.Progressbar(bar, mode="indeterminate", length=140)
        self.progress.pack(side="right")

    # -- infrastructure GUI / threading --

    def _on_close(self):
        if self._busy:
            if not messagebox.askyesno(
                "AutoSketch AI",
                "Un dessin est en cours. Fermer maintenant peut laisser le bouton de la souris "
                "bloque dans ton logiciel de dessin. Fermer quand meme ?",
                parent=self.root,
            ):
                return
        self._key_listener.stop()
        self.root.destroy()

    def log(self, message):
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.root.after(0, _append)

    def _set_status(self, text, busy):
        def _apply():
            self.status_label.configure(text=text)
            if busy:
                self.progress.start(12)
            else:
                self.progress.stop()
        self.root.after(0, _apply)

    def _set_buttons_enabled(self, enabled):
        def _apply():
            state = "normal" if enabled else "disabled"
            for button in self.buttons:
                button.configure(state=state)
        self.root.after(0, _apply)

    def _start(self, action):
        if self._busy:
            return
        self._busy = True
        self._exit_event.clear()
        self._set_buttons_enabled(False)
        self._set_status("En cours... (ECHAP pour interrompre)", busy=True)

        def wrapper():
            try:
                action()
            except Exception as e:
                self.log(f"Erreur : {e}")
            finally:
                self._busy = False
                self._set_buttons_enabled(True)
                self._set_status("Pret", busy=False)

        threading.Thread(target=wrapper, daemon=True).start()

    def _finish_log(self):
        if self._exit_event.is_set():
            self.log("Interrompu (ECHAP).")
        else:
            self.log("Termine.")

    def _load_palette(self):
        path = filedialog.askopenfilename(
            title="Charger une palette", filetypes=[("Palette JSON", "*.json"), ("Tous les fichiers", "*.*")],
            parent=self.root)
        if not path:
            return
        try:
            self.color_palette = load_palette(path)
        except Exception as e:
            messagebox.showerror("AutoSketch AI", f"Impossible de charger la palette : {e}", parent=self.root)
            return
        self.log(f"Palette chargee : {len(self.color_palette.swatches)} couleur(s) depuis {os.path.basename(path)}")

    def _save_palette(self):
        if self.color_palette is None:
            messagebox.showinfo("AutoSketch AI", "Aucune palette calibree ou chargee pour le moment.",
                                 parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            title="Enregistrer la palette", defaultextension=".json",
            filetypes=[("Palette JSON", "*.json")], parent=self.root)
        if not path:
            return
        save_palette(self.color_palette, path)
        self.log(f"Palette enregistree dans {os.path.basename(path)}")

    def ask_text(self, prompt, initial=""):
        result = queue.Queue()
        self.root.after(0, lambda: result.put(
            simpledialog.askstring("AutoSketch AI", prompt, initialvalue=initial, parent=self.root)))
        return result.get()

    def ask_file(self):
        result = queue.Queue()
        self.root.after(0, lambda: result.put(
            filedialog.askopenfilename(title="Choisir une image", filetypes=IMAGE_FILETYPES, parent=self.root)))
        return result.get()

    def ask_yesno(self, prompt):
        result = queue.Queue()
        self.root.after(0, lambda: result.put(messagebox.askyesno("AutoSketch AI", prompt, parent=self.root)))
        return result.get()

    def show_preview(self, image_bgr):
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb)
        pil_image.thumbnail(PREVIEW_SIZE, Image.LANCZOS)

        def _apply():
            self._preview_photo = ImageTk.PhotoImage(pil_image)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                PREVIEW_SIZE[0] // 2, PREVIEW_SIZE[1] // 2, image=self._preview_photo)
        self.root.after(0, _apply)

    # -- parametres --

    def get_speed(self):
        return max(float(self.speed_var.get()), 10.0)

    def get_epsilon_ratio(self):
        return max(float(self.precision_var.get()), 0.05) / 100.0

    def get_color_count(self):
        return max(int(self.colors_var.get()), 2)

    def get_grid_cols(self):
        return max(int(self.grid_cols_var.get()), 2)

    def get_fill_lines(self):
        return max(int(self.fill_lines_var.get()), 1)

    # -- image courante (evite de re-importer a chaque action) --

    def _ensure_image(self):
        if self.current_image is not None:
            return self.current_image

        path = self.ask_file()
        if not path:
            return None
        image = load_image(path)
        self._set_current_image(image, path)
        return image

    def _set_current_image(self, image, path):
        self.current_image = image
        self.current_image_name = os.path.basename(path)
        self.show_preview(image)

        def _apply():
            self.image_name_label.configure(text=f"Image : {self.current_image_name}")
        self.root.after(0, _apply)

    # -- helpers communs --

    def _calibrate_zone(self):
        self.log("Clique sur le COIN HAUT-GAUCHE de la zone de dessin...")
        zone_top_left = capture_points(1)[0]
        self.log("Clique sur le COIN BAS-DROITE de la zone de dessin...")
        zone_bottom_right = capture_points(1)[0]

        if zone_top_left[0] == zone_bottom_right[0] or zone_top_left[1] == zone_bottom_right[1]:
            raise ValueError("La zone de dessin est degeneree (les deux coins cliques sont alignes).")

        return zone_top_left, zone_bottom_right

    def _build_drawable_paths(self, contours):
        epsilon_ratio = self.get_epsilon_ratio()
        paths = contours_to_paths(contours, epsilon_ratio=epsilon_ratio)
        if self.smooth_var.get():
            paths = [smooth_path(p) for p in paths]
        return paths

    # -- actions : formes --

    def _run_line(self):
        self.log("Clique sur le POINT DE DEPART...")
        start = capture_points(1)[0]
        self.log("Clique sur le POINT D'ARRIVEE...")
        end = capture_points(1)[0]
        self.log("Dessin dans 2 secondes... (ne touche pas la souris)")
        time.sleep(2)
        if self._exit_event.is_set():
            return self._finish_log()
        draw_line(MouseController(), start, end, speed=self.get_speed(), exit_event=self._exit_event)
        self._finish_log()

    def _run_rectangle(self):
        self.log("Clique sur le COIN HAUT-GAUCHE du rectangle...")
        top_left = capture_points(1)[0]
        self.log("Clique sur le COIN BAS-DROITE du rectangle...")
        bottom_right = capture_points(1)[0]
        self.log("Dessin dans 2 secondes... (ne touche pas la souris)")
        time.sleep(2)
        if self._exit_event.is_set():
            return self._finish_log()
        draw_rectangle(MouseController(), top_left, bottom_right, speed=self.get_speed(), exit_event=self._exit_event)
        self._finish_log()

    def _run_circle(self):
        self.log("Clique sur le CENTRE du cercle...")
        center = capture_points(1)[0]
        self.log("Clique sur un POINT DU BORD du cercle...")
        edge = capture_points(1)[0]
        radius = round(math.hypot(edge[0] - center[0], edge[1] - center[1]))
        self.log(f"Rayon : {radius}")
        self.log("Dessin dans 2 secondes... (ne touche pas la souris)")
        time.sleep(2)
        if self._exit_event.is_set():
            return self._finish_log()
        draw_circle(MouseController(), center, radius, speed=self.get_speed(), exit_event=self._exit_event)
        self._finish_log()

    def _run_ellipse(self):
        self.log("Clique sur le COIN HAUT-GAUCHE de la boite englobante de l'ellipse...")
        top_left = capture_points(1)[0]
        self.log("Clique sur le COIN BAS-DROITE de la boite englobante de l'ellipse...")
        bottom_right = capture_points(1)[0]
        self.log("Dessin dans 2 secondes... (ne touche pas la souris)")
        time.sleep(2)
        if self._exit_event.is_set():
            return self._finish_log()
        draw_ellipse(MouseController(), top_left, bottom_right, speed=self.get_speed(), exit_event=self._exit_event)
        self._finish_log()

    def _run_polyline(self):
        self.log("Clique sur chaque point de la forme libre, puis appuie sur ENTREE pour terminer.")
        points = capture_points_until_enter()
        if len(points) < 2:
            self.log("Pas assez de points pour tracer une forme.")
            return
        closed = self.ask_yesno("Fermer la forme (revenir au premier point) ?")
        self.log(f"{len(points)} point(s) captures. Dessin dans 2 secondes...")
        time.sleep(2)
        if self._exit_event.is_set():
            return self._finish_log()
        draw_polyline(MouseController(), points, closed=closed, speed=self.get_speed(), exit_event=self._exit_event)
        self._finish_log()

    # -- actions : image --

    def _run_import_image(self):
        path = self.ask_file()
        if not path:
            self.log("Annule.")
            return
        image = load_image(path)
        self._set_current_image(image, path)
        info = get_image_info(image)
        self.log(f"Image chargee : {info['width']}x{info['height']} px, {info['channels']} canal(aux) "
                  f"(reutilisee pour les prochaines actions)")

    def _run_detect_contours(self):
        image = self._ensure_image()
        if image is None:
            self.log("Annule.")
            return
        edges = detect_edges(image)
        contours = find_contours(edges)
        self.log(f"{len(contours)} contour(s) detecte(s)")

        preview = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(preview, contours, -1, (0, 0, 255), 1)
        self.show_preview(preview)

    # -- actions : reproduction --

    def _run_reproduce_image(self):
        image = self._ensure_image()
        if image is None:
            self.log("Annule.")
            return

        edges = detect_edges(image)
        contours = find_contours(edges)
        paths = self._build_drawable_paths(contours)
        self.log(f"{len(paths)} trait(s) a dessiner (apres simplification)")
        if not paths:
            self.log("Aucun contour exploitable dans cette image.")
            return

        before = total_travel_distance(paths)
        paths = optimize_path_order(paths)
        after_greedy = total_travel_distance(paths)
        paths = refine_with_two_opt(paths)
        after = total_travel_distance(paths)
        self.log(f"Trajectoires optimisees : {before:.0f}px -> {after_greedy:.0f}px (glouton) -> {after:.0f}px (IA/2-opt)")

        zone_top_left, zone_bottom_right = self._calibrate_zone()

        mouse = MouseController()
        speed = self.get_speed()
        self.log(f"Dessin de {len(paths)} trait(s) dans 3 secondes... (ne touche pas la souris)")
        time.sleep(3)

        for path_points in paths:
            if self._exit_event.is_set():
                break
            screen_points = map_points(path_points, image.shape, zone_top_left, zone_bottom_right)
            draw_path_with_speed(mouse, screen_points, speed=speed, exit_event=self._exit_event)

        self._finish_log()

    def _run_reproduce_color_image(self):
        image = self._ensure_image()
        if image is None:
            self.log("Annule.")
            return

        palette = self._maybe_calibrate_palette(self.get_color_count())
        if palette is not None:
            quantized, centers = quantize_to_palette(image, palette.colors_rgb(), dither=self.dither_var.get())
            self.log(f"Quantification sur la palette chargee ({len(centers)} couleur(s)), "
                     f"dither={'oui' if self.dither_var.get() else 'non'}")
        else:
            quantized, centers = quantize_colors(image, k=self.get_color_count())
        masks = color_masks(quantized, centers)
        skip_background = self.skip_background_var.get()

        color_paths = []
        skipped_background = 0
        for color_bgr, mask in masks:
            contours = find_contours_from_mask(mask)
            if skip_background:
                kept = [c for c in contours if not is_background_like(c, image.shape)]
                skipped_background += len(contours) - len(kept)
                contours = kept
            paths = self._build_drawable_paths(contours)
            if paths:
                paths = refine_with_two_opt(optimize_path_order(paths))
                color_paths.append((color_bgr, paths))

        total = sum(len(p) for _, p in color_paths)
        self.log(f"{len(color_paths)} couleur(s), {total} trait(s) au total")
        if skip_background and skipped_background:
            self.log(f"{skipped_background} contour(s) de type 'fond' ignore(s).")
        if not color_paths:
            self.log("Aucune zone exploitable dans cette image.")
            return

        zone_top_left, zone_bottom_right = self._calibrate_zone()

        mouse = MouseController()
        speed = self.get_speed()
        for color_bgr, paths in color_paths:
            if self._exit_event.is_set():
                break
            b, g, r = color_bgr
            target_rgb = (r, g, b)
            self._apply_color_for_group(mouse, palette, target_rgb, f"{len(paths)} trait(s)")
            for path_points in paths:
                if self._exit_event.is_set():
                    break
                screen_points = map_points(path_points, image.shape, zone_top_left, zone_bottom_right)
                draw_path_with_speed(mouse, screen_points, speed=speed, exit_event=self._exit_event)

        self._finish_log()

    def _run_pixel_grid(self):
        image = self._ensure_image()
        if image is None:
            self.log("Annule.")
            return

        cols = self.get_grid_cols()
        grid = image_to_grid(image, cols)
        self.show_preview(grid)

        palette = self._maybe_calibrate_palette(self.get_color_count())
        if palette is not None:
            quantized_grid, _ = quantize_to_palette(grid, palette.colors_rgb(), dither=self.dither_var.get())
        else:
            quantized_grid, _ = quantize_colors(grid, k=self.get_color_count())
        rows, cols = quantized_grid.shape[:2]

        color_runs = extract_color_runs(quantized_grid)
        nb_cells = rows * cols
        nb_runs = sum(len(runs) for runs in color_runs.values())
        self.log(f"Grille {cols}x{rows} ({nb_cells} cellule(s)), {len(color_runs)} couleur(s), "
                 f"{nb_runs} trait(s) apres fusion des cellules adjacentes")

        zone_top_left, zone_bottom_right = self._calibrate_zone()
        zx1, zy1 = zone_top_left
        zx2, zy2 = zone_bottom_right
        cell_w = (zx2 - zx1) / cols
        cell_h = (zy2 - zy1) / rows
        lines = self.get_fill_lines()

        mouse = MouseController()
        speed = self.get_speed()
        for color_bgr, runs in color_runs.items():
            if self._exit_event.is_set():
                break
            b, g, r = color_bgr
            target_rgb = (r, g, b)

            fill_paths = []
            for row_start, col_start, row_end, col_end in runs:
                x1 = zx1 + col_start * cell_w
                y1 = zy1 + row_start * cell_h
                x2 = zx1 + (col_end + 1) * cell_w
                y2 = zy1 + (row_end + 1) * cell_h
                fill_paths.append([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
            fill_paths = refine_with_two_opt(optimize_path_order(fill_paths))

            self._apply_color_for_group(mouse, palette, target_rgb, f"{len(runs)} trait(s)")
            for corners in fill_paths:
                if self._exit_event.is_set():
                    break
                draw_filled_rect(mouse, corners[0], corners[2], lines=lines, speed=speed, exit_event=self._exit_event)

        self._finish_log()

    # -- helpers : couleur/palette --

    def _maybe_calibrate_palette(self, default_count):
        if self.color_palette is not None:
            if self.ask_yesno(f"Reutiliser la palette chargee ({len(self.color_palette.swatches)} couleur(s)) ?"):
                return self.color_palette
        if not self.ask_yesno("Calibrer une palette pour la selection automatique de couleur ?"):
            return None
        self.log("Clique successivement sur chaque couleur visible dans la palette de ton logiciel.")
        n_input = self.ask_text("Combien de couleurs dans la palette", initial=str(default_count))
        n_swatches = max(int(n_input), 1) if n_input and n_input.strip() else default_count
        self.color_palette = calibrate_palette(n_swatches)
        return self.color_palette

    def _apply_color_for_group(self, mouse, palette, target_rgb, count_label):
        if palette is not None:
            swatch = select_color(mouse, palette, target_rgb)
            if swatch is None:
                self.log(f"Couleur RGB{target_rgb} : palette vide, selection ignoree.")
            else:
                position, matched = swatch
                self.log(f"Couleur RGB{target_rgb} -> swatch le plus proche RGB{matched} a {position}")
        else:
            self.log(f"Couleur suivante : RGB{target_rgb} - {count_label}")
            self.ask_text("Selectionne cette couleur dans ton logiciel puis valide", initial="ok")

        self.log("Dessin dans 2 secondes... (ne touche pas la souris)")
        time.sleep(2)

    # -- actions : IA --

    def _run_learning_mode(self):
        self.log("Dessine librement dans ton logiciel. Appuie sur ECHAP pour arreter l'enregistrement.")
        strokes = record_drawing()
        self._exit_event.clear()  # l'ECHAP ci-dessus arrete l'enregistrement, pas la reproduction qui suit
        if not strokes:
            self.log("Aucun trait enregistre.")
            return

        style = extract_style(strokes)
        self.log(f"Style appris : ~{style['speed']:.0f} px/s, pause moyenne ~{style['avg_pause']:.2f}s "
                  f"({len(strokes)} trait(s) analyse(s))")

        image = self._ensure_image()
        if image is None:
            self.log("Annule.")
            return

        edges = detect_edges(image)
        contours = find_contours(edges)
        paths = refine_with_two_opt(optimize_path_order(self._build_drawable_paths(contours)))
        self.log(f"{len(paths)} trait(s) a dessiner avec le style appris")
        if not paths:
            self.log("Aucun contour exploitable dans cette image.")
            return

        zone_top_left, zone_bottom_right = self._calibrate_zone()

        mouse = MouseController()
        self.log("Dessin dans 3 secondes... (ne touche pas la souris)")
        time.sleep(3)
        if self._exit_event.is_set():
            return self._finish_log()
        screen_paths = [map_points(p, image.shape, zone_top_left, zone_bottom_right) for p in paths]
        apply_style(mouse, screen_paths, style, exit_event=self._exit_event)
        self._finish_log()


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()
