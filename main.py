import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import csv
from datetime import datetime, UTC   
import style  

DB_FILENAME = "stock.db"
LOW_STOCK_THRESHOLD = 5


#Base de datos
class Database:
    def __init__(self, db_filename=DB_FILENAME):
        self.conn = sqlite3.connect(db_filename)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nombre TEXT NOT NULL,
                categoria TEXT,
                proveedor TEXT,
                precio REAL DEFAULT 0.0,
                cantidad INTEGER DEFAULT 0,
                creado_en TEXT,
                actualizado_en TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                cambio INTEGER,
                motivo TEXT,
                precio_en_movimiento REAL,
                creado_en TEXT,
                FOREIGN KEY(producto_id) REFERENCES productos(id)
            )
        ''')
        self.conn.commit()

    def add_product(self, code, name, category, provider, price, quantity):
        ahora = datetime.now(UTC).isoformat()  # ✅ corregido
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO productos (codigo, nombre, categoria, proveedor, precio, cantidad, creado_en, actualizado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, category, provider, price, quantity, ahora, ahora))
        pid = c.lastrowid
        c.execute('INSERT INTO movimientos (producto_id, cambio, motivo, precio_en_movimiento, creado_en) VALUES (?, ?, ?, ?, ?)',
                  (pid, quantity, 'Stock inicial', price, ahora))
        self.conn.commit()
        return pid

    def update_product(self, pid, code, name, category, provider, price):
        ahora = datetime.now(UTC).isoformat()  # ✅ corregido
        c = self.conn.cursor()
        c.execute('''
            UPDATE productos SET codigo=?, nombre=?, categoria=?, proveedor=?, precio=?, actualizado_en=? WHERE id=?
        ''', (code, name, category, provider, price, ahora, pid))
        self.conn.commit()

    def delete_product(self, pid):
        c = self.conn.cursor()
        c.execute('DELETE FROM movimientos WHERE producto_id=?', (pid,))
        c.execute('DELETE FROM productos WHERE id=?', (pid,))
        self.conn.commit()

    def change_quantity(self, pid, delta, reason='Ajuste manual'):
        ahora = datetime.now(UTC).isoformat()  # ✅ corregido
        c = self.conn.cursor()
        c.execute('SELECT cantidad, precio FROM productos WHERE id=?', (pid,))
        row = c.fetchone()
        if row is None:
            raise ValueError('Producto no encontrado')
        current_qty, current_price = row
        new_qty = current_qty + delta
        if new_qty < 0:
            raise ValueError('Stock insuficiente')
        c.execute('UPDATE productos SET cantidad=?, actualizado_en=? WHERE id=?', (new_qty, ahora, pid))
        c.execute('INSERT INTO movimientos (producto_id, cambio, motivo, precio_en_movimiento, creado_en) VALUES (?, ?, ?, ?, ?)',
                  (pid, delta, reason, current_price, ahora))
        self.conn.commit()
        return new_qty

    def get_all_products(self, search_text=None):
        c = self.conn.cursor()
        if search_text:
            like = f"%{search_text}%"
            c.execute('''SELECT id, codigo, nombre, categoria, proveedor, precio, cantidad FROM productos
                         WHERE nombre LIKE ? OR codigo LIKE ? OR categoria LIKE ? OR proveedor LIKE ?
                         ORDER BY nombre''', (like, like, like, like))
        else:
            c.execute('SELECT id, codigo, nombre, categoria, proveedor, precio, cantidad FROM productos ORDER BY nombre')
        return c.fetchall()

    def get_product(self, pid):
        c = self.conn.cursor()
        c.execute('SELECT id, codigo, nombre, categoria, proveedor, precio, cantidad FROM productos WHERE id=?', (pid,))
        return c.fetchone()

    def export_csv(self, filename):
        products = self.get_all_products()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Código', 'Nombre', 'Categoría', 'Proveedor', 'Precio', 'Cantidad'])
            for p in products:
                writer.writerow(p)

    def low_stock_products(self, threshold=LOW_STOCK_THRESHOLD):
        c = self.conn.cursor()
        c.execute('SELECT id, codigo, nombre, cantidad FROM productos WHERE cantidad<=? ORDER BY cantidad', (threshold,))
        return c.fetchall()

    def get_egresos(self):
        c = self.conn.cursor()
        c.execute('''
            SELECT 
                m.id, p.codigo, p.nombre, ABS(m.cambio), m.precio_en_movimiento,
                ABS(m.cambio) * m.precio_en_movimiento, m.motivo, m.creado_en
            FROM movimientos m
            JOIN productos p ON m.producto_id = p.id
            WHERE m.cambio < 0
            ORDER BY m.creado_en DESC
        ''')
        return c.fetchall()


# Fin de base de datos

# Dialogos

class ProductDialog(simpledialog.Dialog):
    def __init__(self, parent, title, product=None):
        self.product = product
        super().__init__(parent, title)

    def body(self, master):
        labels = ["Código:", "Nombre:", "Categoría:", "Proveedor:", "Precio:", "Cantidad inicial:"]
        self.entries = [tk.Entry(master) for _ in range(len(labels))]
        for i, text in enumerate(labels):
            tk.Label(master, text=text).grid(row=i, column=0, sticky='e', padx=4, pady=2)
            self.entries[i].grid(row=i, column=1, padx=4, pady=2)

        if self.product:
            _, code, name, category, provider, price, quantity = self.product
            vals = [code or '', name, category or '', provider or '', str(price), str(quantity)]
            for entry, val in zip(self.entries, vals):
                entry.insert(0, val)
            self.entries[-1].config(state='disabled')

        return self.entries[0]

    def validate(self):
        try:
            float(self.entries[4].get())
            int(self.entries[5].get())
            return True
        except ValueError:
            messagebox.showwarning('Validación', 'Precio o cantidad inválido.')
            return False

    def apply(self):
        self.result = {
            'code': self.entries[0].get().strip(),
            'name': self.entries[1].get().strip(),
            'category': self.entries[2].get().strip(),
            'provider': self.entries[3].get().strip(),
            'price': float(self.entries[4].get() or 0),
            'quantity': int(self.entries[5].get() or 0)
        }


class SaleDialog(simpledialog.Dialog):
    def __init__(self, parent, title, prod_price=0):
        self.prod_price = prod_price
        super().__init__(parent, title)

    def body(self, master):
        labels = ["Cantidad:", "Motivo:", "Recibo efect.:"]  
        self.entries = [tk.Entry(master) for _ in range(len(labels))]
        for i, text in enumerate(labels):
            tk.Label(master, text=text).grid(row=i, column=0, sticky='e', padx=4, pady=2)
            self.entries[i].grid(row=i, column=1, padx=4, pady=2)
        return self.entries[0]

    def validate(self):
        try:
            qty = int(self.entries[0].get())
            recibo = float(self.entries[2].get())
            return qty > 0 and recibo >= 0
        except ValueError:
            messagebox.showwarning('Validación', 'Campos inválidos.')
            return False

    def apply(self):
        self.result = {
            'cantidad': int(self.entries[0].get()),
            'motivo': self.entries[1].get().strip(),
            'recibo': float(self.entries[2].get())
        }



# Fin de diálogos

# Aplicación principal
class StockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Gestión de Stock - Python')
        self.attributes('-fullscreen', True)
        self.bind('<Escape>', lambda e: self.attributes('-fullscreen', False))

        self.db = Database()

        
        style.apply_styles(self)

        self.create_widgets()
        self.populate_products()
        self.check_low_stock()

    def create_widgets(self):
        # Menú 
        menubar = tk.Menu(self)
        menu_ver = tk.Menu(menubar, tearoff=0)
        menu_ver.add_command(label="Ver Egresos", command=self.show_egresos)
        menubar.add_cascade(label="Ver", menu=menu_ver)
        self.config(menu=menubar)

        #  Barra superior 
        top = tk.Frame(self, bg="#f4f6f7")
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Buscar:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.populate_products())
        e_search = tk.Entry(top, textvariable=self.search_var, width=30)
        e_search.pack(side="left", padx=4)

        btn_clear = tk.Button(top, text="Limpiar", command=self.clear_search)
        btn_export = tk.Button(top, text="Exportar CSV", command=self.export_csv)
        btn_add = tk.Button(top, text="➕ Agregar Producto", command=self.add_product)

        btn_clear.pack(side="left", padx=6)
        btn_export.pack(side="right", padx=6)
        btn_add.pack(side="right", padx=6)

        style.style_buttons(btn_clear, btn_export, btn_add)

        # Treeview
        columns = ('id', 'code', 'name', 'category', 'provider', 'price', 'quantity')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        for col, text, w in zip(columns,
                                ['ID', 'Código', 'Nombre', 'Categoría', 'Proveedor', 'Precio', 'Cantidad'],
                                [40, 80, 200, 120, 120, 80, 80]):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        style.style_treeview(self.tree)

        #  Menú contextual 
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label='Editar', command=self.edit_selected)
        self.menu.add_command(label='Eliminar', command=self.delete_selected)
        self.menu.add_separator()
        self.menu.add_command(label='Entrada de stock', command=lambda: self.adjust_stock(True))
        self.menu.add_command(label='Salida de stock', command=lambda: self.adjust_stock(False))
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<Double-1>', lambda e: self.edit_selected())

        # Barra inferior 
        status = tk.Frame(self, bg="#f4f6f7")
        status.pack(fill="x")
        self.lbl_status = tk.Label(status, text="Listo", anchor="w", bg="#f4f6f7")
        self.lbl_status.pack(fill="x", padx=10, pady=4)

        self.bind("<F2>", lambda e: self.scan_barcode())

    #  Lógica 
    def clear_search(self):
        self.search_var.set('')

    def populate_products(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        products = self.db.get_all_products(self.search_var.get().strip())
        for p in products:
            pid, code, name, category, provider, price, qty = p
            tags = ('low_stock',) if qty <= LOW_STOCK_THRESHOLD else ()
            self.tree.insert('', 'end', values=(pid, code or '', name, category or '', provider or '',
                                                f'{price:.2f}', qty), tags=tags)
        self.lbl_status.config(text=f"{len(products)} productos listados")

    def add_product(self):
        dlg = ProductDialog(self, "Agregar producto")
        if dlg.result:
            try:
                pid = self.db.add_product(dlg.result['code'], dlg.result['name'], dlg.result['category'],
                                          dlg.result['provider'], dlg.result['price'], dlg.result['quantity'])
                messagebox.showinfo("Éxito", f"Producto agregado con id {pid}")
                self.populate_products()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def scan_barcode(self):
        self.add_product()

    def get_selected_product_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Seleccione un producto.")
            return None
        return int(self.tree.item(sel[0])['values'][0])

    def edit_selected(self):
        pid = self.get_selected_product_id()
        if not pid:
            return
        prod = self.db.get_product(pid)
        dlg = ProductDialog(self, "Editar producto", product=prod)
        if dlg.result:
            self.db.update_product(pid, dlg.result['code'], dlg.result['name'], dlg.result['category'],
                                   dlg.result['provider'], dlg.result['price'])
            self.populate_products()

    def delete_selected(self):
        pid = self.get_selected_product_id()
        if pid and messagebox.askyesno("Eliminar", "¿Seguro que desea eliminar el producto?"):
            self.db.delete_product(pid)
            self.populate_products()

    def adjust_stock(self, is_entry=True):
        pid = self.get_selected_product_id()
        if not pid:
            return
        prod = self.db.get_product(pid)
        if not prod:
            return

        if is_entry:
            qty = simpledialog.askinteger("Entrada", f"Cantidad para {prod[2]}:", minvalue=1)
            if not qty:
                return
            reason = "Entrada manual"
            delta = qty
        else:
            dlg = SaleDialog(self, f"Venta de {prod[2]}", prod[5])
            if not dlg.result:
                return
            qty = dlg.result['cantidad']
            delta = -qty
            reason = dlg.result['motivo'] or "Venta"
            total = qty * prod[5]
            recibo = dlg.result['recibo']
            cambio = recibo - total
            messagebox.showinfo("Venta", f"Total: ${total:.2f}\nRecibo: ${recibo:.2f}\nCambio: ${cambio:.2f}")

        try:
            self.db.change_quantity(pid, delta, reason)
            self.populate_products()
            self.check_low_stock()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if filename:
            self.db.export_csv(filename)
            messagebox.showinfo("Exportado", f"Archivo guardado en {filename}")

    def show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.menu.tk_popup(event.x_root, event.y_root)

    def check_low_stock(self):
        lows = self.db.low_stock_products()
        if lows:
            self.lbl_status.config(text=f"⚠️ {len(lows)} productos con stock bajo")
        else:
            self.lbl_status.config(text="✔️ Todo en orden")

    def show_egresos(self):
        win = tk.Toplevel(self)
        win.title("Historial de Egresos")
        win.geometry("900x450")

        cols = ("ID", "Código", "Nombre", "Cantidad", "Precio", "Total", "Motivo", "Fecha")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        egresos = self.db.get_egresos()
        total_general = sum(e[5] or 0 for e in egresos)
        for eg in egresos:
            tree.insert("", "end", values=eg)

        tk.Label(win, text=f"💰 Total vendido: ${total_general:,.2f}",
                 font=("Arial", 11, "bold"), anchor="e").pack(fill="x", padx=10, pady=6)


if __name__ == '__main__':
    app = StockApp()
    app.mainloop()
