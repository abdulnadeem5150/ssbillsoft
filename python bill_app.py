import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

class BillApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bill Entry Software")

        # Table headers
        headers = ["Sr", "Work Area", "Qty", "Unit", "Rate", "Amount"]
        self.tree = ttk.Treeview(root, columns=headers, show="headings")
        for header in headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, width=100)
        self.tree.pack(pady=10)

        # Entry fields
        self.entries = {}
        entry_frame = tk.Frame(root)
        entry_frame.pack(pady=5)

        for i, header in enumerate(headers):
            tk.Label(entry_frame, text=header).grid(row=0, column=i)
            entry = tk.Entry(entry_frame)
            entry.grid(row=1, column=i)
            self.entries[header] = entry

        # Buttons
        tk.Button(root, text="Add Item", command=self.add_item).pack(pady=5)
        tk.Button(root, text="Calculate Total", command=self.calculate_total).pack(pady=5)
        tk.Button(root, text="Save as PDF", command=self.save_pdf).pack(pady=5)

        self.total_label = tk.Label(root, text="Total: 0")
        self.total_label.pack(pady=5)

    def add_item(self):
        try:
            qty = float(self.entries["Qty"].get())
            rate = float(self.entries["Rate"].get())
            amount = qty * rate
            self.entries["Amount"].delete(0, tk.END)
            self.entries["Amount"].insert(0, f"{amount:.2f}")
            values = [self.entries[h].get() for h in self.entries]
            self.tree.insert("", tk.END, values=values)
            for entry in self.entries.values():
                entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for Qty and Rate.")

    def calculate_total(self):
        total = 0
        for child in self.tree.get_children():
            total += float(self.tree.item(child)["values"][5])
        self.total_label.config(text=f"Total: {total:.2f}")

    def save_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                 filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        # Create PDF
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "SS ARCHITECT’S - QUOTATION")

        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "Date: __________________")
        c.drawString(350, height - 70, "Contact: 9595922221")
        c.drawString(50, height - 85, "Email: abdulimran9595@gmail.com")

        # Table header
        y = height - 120
        c.setFont("Helvetica-Bold", 10)
        headers = ["Sr", "Work Area", "Qty", "Unit", "Rate", "Amount"]
        x_positions = [50, 90, 300, 360, 420, 480]
        for i, header in enumerate(headers):
            c.drawString(x_positions[i], y, header)
        c.line(50, y - 2, 550, y - 2)

        # Table rows
        y -= 20
        c.setFont("Helvetica", 9)
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            for i, val in enumerate(values):
                c.drawString(x_positions[i], y, str(val))
            y -= 15

        # Total
        y -= 10
        total = sum(float(self.tree.item(child)["values"][5]) for child in self.tree.get_children())
        c.setFont("Helvetica-Bold", 10)
        c.drawString(400, y, f"Total: {total:.2f}")

        c.save()
        messagebox.showinfo("Success", f"PDF saved at {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BillApp(root)
    root.mainloop()
