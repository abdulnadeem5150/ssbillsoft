import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import platform
import json
import re

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ss_architect_bill_settings.json")

SAVE_MODES = [
    "Ask Every Time",
    "Auto-Save (Open PDF)",
    "Auto-Save Only",
    "Quick Print"
]

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"save_mode": SAVE_MODES[0], "save_folder": os.path.join(os.path.expanduser("~"), "Quotations")}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

class BillApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SS Architect’s Bill Software")

        self.settings = load_settings()

        # ------------------ Customer + Date + GST ------------------
        customer_frame = tk.Frame(root)
        customer_frame.pack(pady=5)

        tk.Label(customer_frame, text="Customer Name:").grid(row=0, column=0, sticky="e")
        self.customer_name = tk.Entry(customer_frame, width=30)
        self.customer_name.grid(row=0, column=1, padx=5)
        self.customer_name.bind("<KeyRelease>", lambda e: self.update_preview())

        tk.Label(customer_frame, text="Customer Address:").grid(row=1, column=0, sticky="e")
        self.customer_address = tk.Entry(customer_frame, width=30)
        self.customer_address.grid(row=1, column=1, padx=5)
        self.customer_address.bind("<KeyRelease>", lambda e: self.update_preview())

        tk.Label(customer_frame, text="Date:").grid(row=0, column=2, sticky="e")
        self.date_entry = tk.Entry(customer_frame, width=15)
        self.date_entry.grid(row=0, column=3, padx=5)
        self.date_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))
        self.date_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        tk.Label(customer_frame, text="GST % (Optional):").grid(row=1, column=2, sticky="e")
        self.gst_entry = tk.Entry(customer_frame, width=10)
        self.gst_entry.grid(row=1, column=3, padx=5)
        self.gst_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        # ------------------ Save Options ------------------
        saveopts = tk.Frame(root)
        saveopts.pack(pady=5)

        tk.Label(saveopts, text="Save Mode:").grid(row=0, column=0, sticky="e")
        self.save_mode = ttk.Combobox(saveopts, values=SAVE_MODES, state="readonly", width=20)
        self.save_mode.grid(row=0, column=1, padx=6)
        self.save_mode.set(self.settings.get("save_mode", SAVE_MODES[0]))
        self.save_mode.bind("<<ComboboxSelected>>", self._persist_save_mode)

        tk.Label(saveopts, text="Save Folder:").grid(row=0, column=2, sticky="e")
        self.save_folder_var = tk.StringVar(value=self.settings.get("save_folder", ""))
        self.save_folder_label = tk.Label(saveopts, textvariable=self.save_folder_var, width=40, anchor="w")
        self.save_folder_label.grid(row=0, column=3, padx=6)

        tk.Button(saveopts, text="Set Save Folder", command=self.choose_folder).grid(row=0, column=4, padx=6)

        # ------------------ Table ------------------
        self.headers = ["Sr", "Work Area", "Qty", "Unit", "Rate", "Amount"]
        self.tree = ttk.Treeview(root, columns=self.headers, show="headings")
        for header in self.headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, width=120)
        self.tree.pack(pady=10, fill="x")

        # ------------------ Entry fields for new item ------------------
        self.entries = {}
        entry_frame = tk.Frame(root)
        entry_frame.pack()

        for i, header in enumerate(self.headers):
            tk.Label(entry_frame, text=header).grid(row=0, column=i)
            if header == "Unit":
                combo = ttk.Combobox(entry_frame, values=["SQFT", "NOS"], state="readonly", width=12)
                combo.grid(row=1, column=i)
                self.entries[header] = combo
            else:
                entry = tk.Entry(entry_frame, width=15)
                entry.grid(row=1, column=i)
                self.entries[header] = entry

        # ------------------ Buttons ------------------
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=6)

        tk.Button(btn_frame, text="Add Item", command=self.add_item).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Duplicate Last Item", command=self.duplicate_last_item).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Remove Last Item", command=self.remove_last_item).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Clear All Items", command=self.clear_all_items).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Save as PDF", command=self.save_pdf).grid(row=0, column=4, padx=5)

        self.total_label = tk.Label(root, text="Total: 0/–", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=5)

        # ------------------ PDF Preview ------------------
        preview_frame = tk.LabelFrame(root, text="PDF Preview", padx=5, pady=5)
        preview_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.preview_text = tk.Text(preview_frame, height=15, wrap="none", font=("Courier", 10))
        self.preview_text.pack(fill="both", expand=True)

        # Scrollbars
        yscroll = tk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        yscroll.pack(side="right", fill="y")
        self.preview_text.configure(yscrollcommand=yscroll.set)

        xscroll = tk.Scrollbar(preview_frame, orient="horizontal", command=self.preview_text.xview)
        xscroll.pack(side="bottom", fill="x")
        self.preview_text.configure(xscrollcommand=xscroll.set)

        # Ensure default save folder exists
        self.ensure_save_folder()
        self.update_preview()  # Initial preview

    # ---------- Utility ----------
    def _persist_save_mode(self, _evt=None):
        self.settings["save_mode"] = self.save_mode.get()
        save_settings(self.settings)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.settings["save_folder"] = folder
            self.save_folder_var.set(folder)
            save_settings(self.settings)
            self.ensure_save_folder()

    def ensure_save_folder(self):
        folder = self.settings.get("save_folder", "")
        if folder and not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create folder:\n{folder}\n{e}")

    def sanitize_filename(self, name: str) -> str:
        name = name.strip()
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"[^\w\-\.]", "", name, flags=re.UNICODE)
        return name or "Customer"

    def auto_filename(self) -> str:
        date_txt = self.date_entry.get().strip() or datetime.today().strftime("%d/%m/%Y")
        try:
            dt = datetime.strptime(date_txt, "%d/%m/%Y")
            date_for_name = dt.strftime("%Y-%m-%d")
        except ValueError:
            date_for_name = datetime.today().strftime("%Y-%m-%d")
        cust = self.sanitize_filename(self.customer_name.get() or "Customer")[:30]
        return f"Quotation_{date_for_name}_{cust}.pdf"

    # ---------- Table Operations ----------
    def renumber_sr(self):
        for idx, child in enumerate(self.tree.get_children(), start=1):
            values = list(self.tree.item(child)["values"])
            values[0] = idx
            self.tree.item(child, values=values)

    def add_item(self):
        try:
            qty = float(self.entries["Qty"].get())
            rate = float(self.entries["Rate"].get())
            unit = self.entries["Unit"].get()
            if not unit:
                messagebox.showerror("Error", "Please select Unit (SQFT/NOS).")
                return
            qty_unit = f"{qty} {unit}"
            amount = qty * rate
            amount_str = f"{int(round(amount))}/-"

            sr_no = len(self.tree.get_children()) + 1
            values = [sr_no,
                      self.entries["Work Area"].get(),
                      qty_unit,
                      f"PER {unit}",
                      self.entries["Rate"].get(),
                      amount_str]
            self.tree.insert("", tk.END, values=values)
            self.update_total()
            self.update_preview()

            self.entries["Work Area"].delete(0, tk.END)
            self.entries["Qty"].delete(0, tk.END)
            self.entries["Rate"].delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers for Qty and Rate.")

    def duplicate_last_item(self):
        children = self.tree.get_children()
        if not children:
            messagebox.showwarning("Warning", "No item to duplicate.")
            return
        last_item = self.tree.item(children[-1])["values"]
        new_item = list(last_item)
        new_item[0] = len(children) + 1
        self.tree.insert("", tk.END, values=new_item)
        self.update_total()
        self.update_preview()

    def remove_last_item(self):
        children = self.tree.get_children()
        if not children:
            messagebox.showwarning("Warning", "No item to remove.")
            return
        self.tree.delete(children[-1])
        self.renumber_sr()
        self.update_total()
        self.update_preview()

    def clear_all_items(self):
        for child in self.tree.get_children():
            self.tree.delete(child)
        self.update_total()
        self.update_preview()

    def update_total(self):
        total = 0
        for child in self.tree.get_children():
            amt_str = self.tree.item(child)["values"][5]
            try:
                amt = int(str(amt_str).replace("/-", "").strip())
            except ValueError:
                amt = 0
            total += amt
        self.total_label.config(text=f"Total: {total}/-")

    # ---------- PDF Preview ----------
    def update_preview(self):
        self.preview_text.delete("1.0", tk.END)
        lines = []
        lines.append("SS ARCHITECT'S")
        lines.append("Ar Abdul Imran")
        lines.append(f"Date: {self.date_entry.get().strip()}")
        lines.append("="*60)
        lines.append("QUOTATION")
        lines.append("="*60)
        if self.customer_name.get().strip():
            lines.append(f"Customer: {self.customer_name.get().strip()}")
        if self.customer_address.get().strip():
            lines.append(f"Address: {self.customer_address.get().strip()}")
        lines.append("-"*60)
        lines.append(f"{'Sr':<4} {'Work Area':<20} {'Qty':<8} {'Unit':<8} {'Rate':<8} {'Amount':<8}")
        lines.append("-"*60)
        for child in self.tree.get_children():
            sr, work, qty_unit, unit, rate, amount = self.tree.item(child)["values"]
            lines.append(f"{sr:<4} {work:<20} {qty_unit:<8} {unit:<8} {rate:<8} {amount:<8}")
        lines.append("-"*60)
        subtotal = sum(int(self.tree.item(child)["values"][5].replace("/-", "")) for child in self.tree.get_children())
        lines.append(f"Subtotal: {subtotal}/-")
        gst_percent = self.gst_entry.get().strip()
        if gst_percent:
            try:
                gst_amount = (subtotal * float(gst_percent)) / 100
                grand_total = subtotal + gst_amount
                lines.append(f"GST ({gst_percent}%): {int(round(gst_amount))}/-")
                lines.append(f"Grand Total: {int(round(grand_total))}/-")
            except ValueError:
                pass
        lines.append("="*60)
        self.preview_text.insert(tk.END, "\n".join(lines))

    # ---------- PDF Generation ----------
    def draw_pdf(self, file_path):
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Header
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width/2, height - 60, "SS ARCHITECT'S")
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 80, "Ar Abdul Imran")

        c.setFont("Helvetica", 10)
        c.drawRightString(width - 50, height - 85, f"Date: {self.date_entry.get().strip()}")
        c.drawRightString(width - 50, height - 100, "Email: abdulimran9595@gmail.com")
        c.drawRightString(width - 50, height - 115, "Contact: 9595922221")

        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, height - 130, "QUOTATION")
        c.setLineWidth(0.5)
        c.line(width/2 - 40, height - 135, width/2 + 40, height - 135)

        y = height - 155
        c.setFont("Helvetica", 10)
        if self.customer_name.get().strip():
            c.drawString(50, y, f"Customer Name: {self.customer_name.get().strip()}")
            y -= 15
        if self.customer_address.get().strip():
            c.drawString(50, y, f"Address: {self.customer_address.get().strip()}")
            y -= 20

        c.setFont("Helvetica-Bold", 10)
        col_positions = [50, 90, 300, 360, 420, 480]
        for i, header in enumerate(self.headers):
            c.drawString(col_positions[i], y, header)
        c.line(50, y - 2, 550, y - 2)

        y -= 20
        c.setFont("Helvetica", 9)
        for child in self.tree.get_children():
            row = self.tree.item(child)["values"]
            for i, val in enumerate(row):
                c.drawString(col_positions[i], y, str(val))
                c.line(50, y - 2, 550, y - 2)
            y -= 15

        subtotal = sum(int(self.tree.item(child)["values"][5].replace("/-", "")) for child in self.tree.get_children())
        gst_percent = self.gst_entry.get().strip()
        gst_amount = 0
        grand_total = subtotal

        y -= 10
        c.setFont("Helvetica-Bold", 14)
        c.drawString(400, y, f"Subtotal: {int(round(subtotal))}/-")

        if gst_percent:
            try:
                gst_amount = (subtotal * float(gst_percent)) / 100
                grand_total = subtotal + gst_amount
                y -= 15
                c.drawString(400, y, f"GST ({gst_percent}%): {int(round(gst_amount))}/-")
                y -= 15
                c.drawString(400, y, f"Grand Total: {int(round(grand_total))}/-")
            except ValueError:
                pass

        y -= 40
        c.setFont("Helvetica", 10)
        c.drawString(50, y, "SS ARCHITECT’S")
        c.drawString(50, y - 15, "Ar Abdul Imran")
        c.save()

    def save_pdf(self):
        mode = self.save_mode.get()
        filename = self.auto_filename()

        if mode == "Ask Every Time":
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=filename,
                                                     filetypes=[("PDF files", "*.pdf")])
            if not file_path:
                return
        else:
            folder = self.settings.get("save_folder", "")
            if not folder:
                messagebox.showerror("Save Folder", "Please set a Save Folder first.")
                return
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, filename)

        gst_txt = self.gst_entry.get().strip()
        if gst_txt:
            try:
                float(gst_txt)
            except ValueError:
                messagebox.showerror("GST %", "Invalid GST value. Please enter a number or leave blank.")
                return

        self.draw_pdf(file_path)

        if mode == "Auto-Save (Open PDF)":
            self.open_pdf(file_path)
            messagebox.showinfo("Saved", f"PDF saved and opened:\n{file_path}")
        elif mode == "Auto-Save Only":
            messagebox.showinfo("Saved", f"PDF saved:\n{file_path}")
        elif mode == "Quick Print":
            self.quick_print(file_path)
            messagebox.showinfo("Quick Print", f"PDF sent to printer:\n{file_path}")
        else:
            self.open_pdf(file_path)
            messagebox.showinfo("Saved", f"PDF saved and opened:\n{file_path}")

    def open_pdf(self, path):
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                os.system(f"open '{path}'")
            else:
                os.system(f"xdg-open '{path}'")
        except Exception as e:
            messagebox.showwarning("Open PDF", f"PDF saved but could not auto-open.\n{e}")

    def quick_print(self, path):
        try:
            if platform.system() == "Windows":
                os.startfile(path, "print")
            else:
                os.system(f"lp '{path}'")
        except Exception as e:
            messagebox.showwarning("Quick Print", f"Sent to printer may have failed.\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BillApp(root)
    root.mainloop()
