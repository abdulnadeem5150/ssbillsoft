import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import platform

class BillApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SS Architect’s Bill Software")

        # Customer Details Section
        customer_frame = tk.Frame(root)
        customer_frame.pack(pady=5)

        tk.Label(customer_frame, text="Customer Name:").grid(row=0, column=0, sticky="e")
        self.customer_name = tk.Entry(customer_frame, width=30)
        self.customer_name.grid(row=0, column=1, padx=5)

        tk.Label(customer_frame, text="Customer Address:").grid(row=1, column=0, sticky="e")
        self.customer_address = tk.Entry(customer_frame, width=30)
        self.customer_address.grid(row=1, column=1, padx=5)

        tk.Label(customer_frame, text="Date:").grid(row=0, column=2, sticky="e")
        self.date_entry = tk.Entry(customer_frame, width=15)
        self.date_entry.grid(row=0, column=3, padx=5)
        self.date_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))

        self.headers = ["Sr", "Work Area", "Qty", "Unit", "Rate", "Amount"]
        self.tree = ttk.Treeview(root, columns=self.headers, show="headings")
        for header in self.headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, width=120)
        self.tree.pack(pady=10)

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

        # Buttons Frame
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add Item", command=self.add_item).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Duplicate Last Item", command=self.duplicate_last_item).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Remove Last Item", command=self.remove_last_item).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Clear All Items", command=self.clear_all_items).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Save as PDF", command=self.save_pdf).grid(row=0, column=4, padx=5)

        self.total_label = tk.Label(root, text="Total: 0/–", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=5)

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
            qty_unit = f"{int(qty)} {unit}"
            amount = qty * rate
            amount_str = f"{int(amount)}/-"

            self.entries["Amount"].delete(0, tk.END)
            self.entries["Amount"].insert(0, amount_str)

            sr_no = len(self.tree.get_children()) + 1
            values = [sr_no,
                      self.entries["Work Area"].get(),
                      qty_unit,
                      f"PER {unit}",
                      self.entries["Rate"].get(),
                      amount_str]
            self.tree.insert("", tk.END, values=values)
            self.update_total()

            self.entries["Work Area"].delete(0, tk.END)
            self.entries["Qty"].delete(0, tk.END)
            self.entries["Rate"].delete(0, tk.END)
            self.entries["Amount"].delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers for Qty and Rate.")

    def duplicate_last_item(self):
        children = self.tree.get_children()
        if not children:
            messagebox.showwarning("Warning", "No item to duplicate.")
            return
        last_item = self.tree.item(children[-1])["values"]
        new_item = list(last_item)
        self.tree.insert("", tk.END, values=new_item)
        self.renumber_sr()
        self.update_total()

    def remove_last_item(self):
        children = self.tree.get_children()
        if not children:
            messagebox.showwarning("Warning", "No item to remove.")
            return
        self.tree.delete(children[-1])
        self.renumber_sr()
        self.update_total()

    def clear_all_items(self):
        for child in self.tree.get_children():
            self.tree.delete(child)
        self.update_total()

    def update_total(self):
        total = 0
        for child in self.tree.get_children():
            amt_str = self.tree.item(child)["values"][5]
            amt = int(amt_str.replace("/-", ""))
            total += amt
        self.total_label.config(text=f"Total: {total}/-")

    def save_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                 filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 50, "SS ARCHITECT’S")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Date: {self.date_entry.get()}")
        c.drawString(400, height - 70, "Contact: 9595922221")
        c.drawString(50, height - 85, "Email: abdulimran9595@gmail.com")
        c.drawString(50, height - 100, "QUOTATION")

        # Customer details
        y = height - 120
        c.setFont("Helvetica", 10)
        if self.customer_name.get():
            c.drawString(50, y, f"Customer Name: {self.customer_name.get()}")
            y -= 15
        if self.customer_address.get():
            c.drawString(50, y, f"Address: {self.customer_address.get()}")
            y -= 20

        # Table Header
        c.setFont("Helvetica-Bold", 10)
        col_positions = [50, 90, 300, 360, 420, 480]
        for i, header in enumerate(self.headers):
            c.drawString(col_positions[i], y, header)
        c.line(50, y - 2, 550, y - 2)

        # Table Rows
        y -= 20
        c.setFont("Helvetica", 9)
        for child in self.tree.get_children():
            row = self.tree.item(child)["values"]
            for i, val in enumerate(row):
                c.drawString(col_positions[i], y, str(val))
            y -= 15

        # Total
        total = self.total_label.cget("text").replace("Total: ", "")
        y -= 10
        c.setFont("Helvetica-Bold", 10)
        c.drawString(400, y, f"TOTAL {total}")

        # Footer
        y -= 40
        c.setFont("Helvetica", 10)
        c.drawString(50, y, "SS ARCHITECT’S")
        c.drawString(50, y - 15, "Ar Abdul Imran")

        c.save()

        # Auto-open PDF after saving
        self.open_pdf(file_path)
        messagebox.showinfo("Saved", f"PDF saved and opened: {file_path}")

    def open_pdf(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open '{path}'")
        else:  # Linux
            os.system(f"xdg-open '{path}'")

if __name__ == "__main__":
    root = tk.Tk()
    app = BillApp(root)
    root.mainloop()
