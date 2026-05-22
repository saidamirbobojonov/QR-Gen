import tkinter as tk
from tkinter import messagebox
import qrcode
from PIL import Image, ImageTk
import io
import datetime

def build_vcard(name, phone, address, website):
    # Собираем vCard (VERSION:3.0). Добавляем только непустые поля.
    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    if name:
        # FN — полное имя
        lines.append(f"FN:{escape_vcard(name)}")
    if phone:
        # TEL — телефон (тип CELL)
        lines.append(f"TEL;TYPE=CELL:{escape_vcard(phone)}")
    if address:
        # ADR — адрес; vCard ADR имеет формат: PO Box;Extended;Street;City;Region;PostalCode;Country
        # Упростим и поместим весь адрес в поле Street (третья позиция)
        # Формируем: ;;Street;;;; чтобы остальное осталось пустым
        addr_escaped = escape_vcard(address)
        lines.append(f"ADR:;;{addr_escaped};;;;")
    if website:
        lines.append(f"URL:{escape_vcard(website)}")
    lines.append("END:VCARD")
    return "\n".join(lines)

def escape_vcard(text: str) -> str:
    # Экранируем точки с запятой, запятые и переводы строк, которые важны для vCard
    return text.replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")

def generate_qr():
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()
    address = address_entry.get().strip()
    website = website_entry.get().strip()
    file_name = filename_entry.get().strip()

    if not file_name:
        messagebox.showwarning("Input Error", "Please enter a name for the QR code image (without .png).")
        return

    # Если у пользователя нет ни одного поля, предупреждаем
    if not (name or phone or address or website):
        messagebox.showwarning("Input Error", "Please enter at least one field (name, phone, address or website).")
        return

    # Собираем vCard
    vcard_text = build_vcard(name, phone, address, website)

    # Генерируем QR
    qr = qrcode.QRCode(
        version=None,  # авто-подбор
        error_correction=qrcode.constants.ERROR_CORRECT_Q,  # высокий уровень коррекции
        box_size=10,
        border=4,
    )
    qr.add_data(vcard_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Сохраняем в файл
    filename = f"{file_name}.png"
    try:
        img.save(filename)
    except Exception as e:
        messagebox.showerror("Save Error", f"Failed to save image: {e}")
        return

    # Отображаем в Tkinter
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    tk_img = ImageTk.PhotoImage(Image.open(buf))
    qr_label.config(image=tk_img)
    qr_label.image = tk_img

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_label.config(text=f"Saved as {filename} ({timestamp})")

# --- GUI ---
root = tk.Tk()
root.title("QR Code (vCard) Generator")
root.geometry("420x640")
root.resizable(False, False)
pad_y = 6

frame = tk.Frame(root)
frame.pack(padx=12, pady=12, fill="both", expand=True)

tk.Label(frame, text="Full name (Имя / Название):").pack(anchor="w", pady=(0,2))
name_entry = tk.Entry(frame, width=48)
name_entry.pack(pady=pad_y)

tk.Label(frame, text="Phone (Телефон):").pack(anchor="w", pady=(8,2))
phone_entry = tk.Entry(frame, width=48)
phone_entry.pack(pady=pad_y)

tk.Label(frame, text="Address (Адрес):").pack(anchor="w", pady=(8,2))
address_entry = tk.Entry(frame, width=48)
address_entry.pack(pady=pad_y)

tk.Label(frame, text="Website (Сайт, включая https://):").pack(anchor="w", pady=(8,2))
website_entry = tk.Entry(frame, width=48)
website_entry.pack(pady=pad_y)

tk.Label(frame, text="Filename for QR image (без .png):").pack(anchor="w", pady=(8,2))
filename_entry = tk.Entry(frame, width=48)
filename_entry.pack(pady=pad_y)

gen_btn = tk.Button(frame, text="Generate QR Code", command=generate_qr, width=20)
gen_btn.pack(pady=14)

qr_label = tk.Label(frame, bd=2, relief="sunken", width=300, height=300)
qr_label.pack(pady=8)

status_label = tk.Label(frame, text="", anchor="w")
status_label.pack(fill="x", pady=(6,0))

root.mainloop()