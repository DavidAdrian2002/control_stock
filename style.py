import tkinter as tk
from tkinter import ttk

# 🎨 Paleta de colores base
PRIMARY_COLOR = "#4CAF50"     # Verde principal
SECONDARY_COLOR = "#388E3C"   # Verde más oscuro
BACKGROUND = "#F5F5F5"        # Fondo claro
TEXT_COLOR = "#212121"        # Texto principal
WARNING_COLOR = "#FF7043"     # Naranja para advertencias
LOW_STOCK_COLOR = "#E53935"   # Rojo para bajo stock

# 🧩---------------------------------------------
def apply_styles(root):
    """Aplica estilos generales a toda la interfaz."""
    root.configure(bg=BACKGROUND)
    root.option_add("*Font", ("Segoe UI", 11))
    root.option_add("*Label.Background", BACKGROUND)
    root.option_add("*Label.Foreground", TEXT_COLOR)
    root.option_add("*Entry.Background", "white")
    root.option_add("*Entry.Foreground", TEXT_COLOR)
    root.option_add("*Button.Foreground", TEXT_COLOR)

    style = ttk.Style(root)
    style.theme_use("clam")

    # --- Treeview base ---
    style.configure(
        "Treeview",
        background="white",
        foreground=TEXT_COLOR,
        rowheight=25,
        fieldbackground="white",
        font=("Segoe UI", 10)
    )
    style.map("Treeview",
              background=[("selected", PRIMARY_COLOR)],
              foreground=[("selected", "white")])

    # --- Encabezados de tabla ---
    style.configure(
        "Treeview.Heading",
        background=PRIMARY_COLOR,
        foreground="white",
        font=("Segoe UI", 10, "bold")
    )

    # --- Scrollbar ---
    style.configure(
        "Vertical.TScrollbar",
        gripcount=0,
        background=SECONDARY_COLOR,
        troughcolor=BACKGROUND,
        bordercolor=BACKGROUND,
        arrowcolor="white"
    )

    # --- Botones ttk ---
    style.configure(
        "TButton",
        background=PRIMARY_COLOR,
        foreground="white",
        borderwidth=0,
        focusthickness=3,
        focuscolor="none",
        padding=6
    )
    style.map("TButton",
              background=[("active", SECONDARY_COLOR)],
              relief=[("pressed", "flat")])

# 🧩---------------------------------------------
def style_buttons(*buttons):
    """Aplica estilo uniforme a los botones (tk.Button)."""
    for btn in buttons:
        btn.configure(
            bg=PRIMARY_COLOR,
            fg="white",
            activebackground=SECONDARY_COLOR,
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=4,
            cursor="hand2",
            borderwidth=0
        )

# 🧩---------------------------------------------
def style_treeview(tree):
    """Aplica estilo visual adicional a Treeview (colores de filas alternadas y stock bajo)."""
    # Alternar colores de filas
    tree.tag_configure("evenrow", background="#F9F9F9")
    tree.tag_configure("oddrow", background="#FFFFFF")
    tree.tag_configure("lowstock", background=LOW_STOCK_COLOR, foreground="white")
