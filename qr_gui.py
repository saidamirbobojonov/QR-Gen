import tkinter as tk
from tkinter import messagebox

import qrcode
from PIL import Image, ImageTk
import io

# Function to generate and display QR code
def generate_qr():
    url = url_entry.get()
    name = name_entry.get().strip()
    if not url:
        messagebox.showwarning("Input Error", "Please enter a URL.")
        return
    if not name:
        messagebox.showwarning("Input Error", "Please enter a name for the QR code image.")
        return
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # Save to a bytes buffer
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    # Display in Tkinter
    tk_img = ImageTk.PhotoImage(Image.open(buf))
    qr_label.config(image=tk_img)
    qr_label.image = tk_img
    # Save the image with the given name
    filename = f"{name}.png"
    img.save(filename)
    status_label.config(text=f"QR code saved as {filename}")

# Set up the main window
root = tk.Tk()
root.title("QR Code Generator")
root.geometry("400x550")

# URL entry
url_label = tk.Label(root, text="Enter URL:")
url_label.pack(pady=10)
url_entry = tk.Entry(root, width=40)
url_entry.pack(pady=5)

# Name entry
name_label = tk.Label(root, text="Enter name for QR image (without .png):")
name_label.pack(pady=10)
name_entry = tk.Entry(root, width=40)
name_entry.pack(pady=5)

# Generate button
gen_btn = tk.Button(root, text="Generate QR Code", command=generate_qr)
gen_btn.pack(pady=10)

# QR code display
qr_label = tk.Label(root)
qr_label.pack(pady=20)

# Status label
status_label = tk.Label(root, text="")
status_label.pack(pady=10)

root.mainloop() 