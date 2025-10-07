import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os, re, time
import pygetwindow as gw

# ---- PDF modülü ----
try:
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    FONT_PATH = "C:\\Windows\\Fonts\\DejaVuSans.ttf"
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("DejaVuSans", FONT_PATH))
        PDF_FONT = "DejaVuSans"
    else:
        pdfmetrics.registerFont(TTFont("Arial", "C:\\Windows\\Fonts\\arial.ttf"))
        PDF_FONT = "Arial"
    CAN_PDF = True
except Exception:
    CAN_PDF = False
    PDF_FONT = "Helvetica"

# ---- Tema ----
BG = "#1b1b1b"
FG = "#f1f1f1"
ENTRY_BG = "#262626"
BUTTON_BG = "#3a86ff"
BUTTON_FG = "#ffffff"
FONT = ("Segoe UI", 10)

masaustu = os.path.join(os.path.expanduser("~"), "Desktop")
ANA_KLASOR = os.path.join(masaustu, "Udemy Notları")
os.makedirs(ANA_KLASOR, exist_ok=True)
sabit = False

# ================= Udemy başlık filtresi =================
BROWSER_SUFFIX_RE = re.compile(
    r"\s*-\s*(Opera(?:\sGX)?|Opera|Google Chrome|Microsoft Edge|Edge|Brave|Vivaldi|Firefox|Yandex)\b.*",
    re.I,
)
PREFIX_STRIP_RE = re.compile(r"^(Course|Lecture|Lesson|Kurs)\s*[:\-–—]?\s*", re.I)
UD_END_RE = re.compile(r"(?:\s[\|¦]\s*Udemy|\s[\-–—]\s*Udemy)\s*$", re.I)
UD_TAIL_RE = re.compile(r"(?:\s[\|¦]\s*Udemy|\s[\-–—]\s*Udemy)\s*$", re.I)

def extract_udemy_title(raw_title: str) -> str | None:
    if not raw_title:
        return None
    t = BROWSER_SUFFIX_RE.sub("", raw_title).strip()
    if not UD_END_RE.search(t):
        return None
    t = UD_TAIL_RE.sub("", t).strip()
    t = PREFIX_STRIP_RE.sub("", t).strip()
    return t if len(t) > 1 else None

def kurs_adi_bul() -> str | None:
    try:
        for raw in gw.getAllTitles():
            if any(bad in raw for bad in ["Udemy Note Saver", "PyCharm", "Visual Studio", "ChatGPT"]):
                continue
            t = extract_udemy_title(raw)
            if t:
                return t
    except Exception:
        pass
    return None

def otomatik_kontrol():
    """Thread yerine UI tabanlı kontrol (her 3 sn'de bir)"""
    title = kurs_adi_bul()
    if title:
        current = kurs_entry.get().strip()
        if title != current:
            kurs_entry.delete(0, tk.END)
            kurs_entry.insert(0, title)
    p.after(3000, otomatik_kontrol)

# ================= Not Kaydetme =================
def kaydet():
    kurs = (kurs_entry.get() or "").strip() or "Bilinmeyen Kurs"
    ders = (ders_entry.get() or "").strip() or "Bilinmeyen Ders"
    dakika = (dakika_entry.get() or "").strip() or "—"
    metin = (not_text.get("1.0", tk.END) or "").strip()

    if not metin:
        messagebox.showwarning("Uyarı", "Not boş olamaz!")
        return

    kurs_klasor = os.path.join(ANA_KLASOR, kurs)
    os.makedirs(kurs_klasor, exist_ok=True)
    yol = os.path.join(kurs_klasor, f"{ders}.txt")

    tarih = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    # Eğer dosya yoksa baştan oluştur
    if not os.path.exists(yol):
        blob = (
            "\n" + "─" * 60 + "\n"
            f"🎬 Kurs     : {kurs}\n"
            f"📚 Ders     : {ders}\n"
            f"🕓 Zaman    : {tarih} ({dakika})\n"
            f"📝 Not:\n"
            + "─" * 60 + "\n"
            f"{metin}\n"
            + "─" * 60 + "\n"
        )
        try:
            with open(yol, "a", encoding="utf-8") as f:
                f.write(blob)
            messagebox.showinfo("Kaydedildi", f"{ders}.txt oluşturuldu ve not eklendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydedilemedi:\n{e}")
            return
    else:
        # Dosya varsa EN ALTA ekle
        try:
            block = (
                f"🕓 {tarih} ({dakika})\n"
                f"{metin}\n"
                + "─" * 60 + "\n"
            )
            with open(yol, "a", encoding="utf-8") as f:
                f.write(block)
            messagebox.showinfo("Eklendi", f"{ders}.txt dosyasına yeni not eklendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya güncellenemedi:\n{e}")
            return

    # Alanları temizle (kurs hariç)
    ders_entry.delete(0, tk.END)
    dakika_entry.delete(0, tk.END)
    not_text.delete("1.0", tk.END)

    # Listeyi yenile
    listeyi_yenile()

# ================= Notları Gör =================
def notlari_goster():
    notebook.select(tab_notlar)
    listeyi_yenile()

def dosya_sil(kurs, dosya):
    yol = os.path.join(ANA_KLASOR, kurs, dosya)
    if messagebox.askyesno("Silme Onayı", f"'{dosya}' dosyasını silmek istiyor musun?"):
        try:
            os.remove(yol)
            messagebox.showinfo("Silindi", f"{dosya} silindi.")
            dersleri_goster(kurs)
        except Exception as e:
            messagebox.showerror("Hata", f"Silinemedi:\n{e}")

def listeyi_yenile():
    for w in tab_notlar.winfo_children():
        w.destroy()
    tk.Label(tab_notlar, text="📚 Kayıtlı Kurslar", bg=BG, fg=FG,
             font=("Segoe UI", 13, "bold")).pack(pady=10)
    kurslar = [d for d in os.listdir(ANA_KLASOR) if os.path.isdir(os.path.join(ANA_KLASOR, d))]
    if not kurslar:
        tk.Label(tab_notlar, text="Henüz kayıtlı kurs yok.", bg=BG, fg="#999").pack(pady=20)
        return
    for kurs in sorted(kurslar, key=str.lower):
        tk.Button(tab_notlar, text=f"📁 {kurs}", bg="#2d2d2d", fg=FG, bd=0,
                  relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2",
                  command=lambda k=kurs: dersleri_goster(k)).pack(pady=4, ipadx=10, fill="x", padx=60)

def dersleri_goster(kurs):
    for w in tab_notlar.winfo_children():
        w.destroy()
    tk.Label(tab_notlar, text=f"{kurs} – Ders Notları", bg=BG, fg=FG,
             font=("Segoe UI", 13, "bold")).pack(pady=10)
    klasor = os.path.join(ANA_KLASOR, kurs)
    dosyalar = [f for f in os.listdir(klasor) if f.lower().endswith(".txt")]
    if not dosyalar:
        tk.Label(tab_notlar, text="Bu kursta not yok.", bg=BG, fg="#aaa").pack(pady=15)
        return
    for dosya in sorted(dosyalar, key=str.lower):
        frame = tk.Frame(tab_notlar, bg=BG)
        frame.pack(fill="x", padx=60, pady=2)
        tk.Button(frame, text=dosya, bg="#333", fg=FG, bd=0,
                  relief="flat", font=("Segoe UI", 10),
                  command=lambda d=dosya, k=kurs: notu_ac(k, d)).pack(side="left", fill="x", expand=True)
        tk.Button(frame, text="🗑️", bg="#b30000", fg="#fff", bd=0,
                  font=("Segoe UI", 9, "bold"),
                  command=lambda d=dosya, k=kurs: dosya_sil(k, d)).pack(side="right", padx=4)
        # 🔹 PDF’e dönüştür butonu eklendi
        if CAN_PDF:
            tk.Button(tab_notlar, text="📘 PDF'e Dönüştür", bg="#0078ff", fg="#fff",
                      bd=0, font=("Segoe UI", 10, "bold"),
                      command=lambda k=kurs: kursu_pdf_yap(k)).pack(pady=12)

        # Geri dön butonu
        tk.Button(tab_notlar, text="⬅️ Geri Dön", bg="#404040", fg=FG, bd=0,
                  font=("Segoe UI", 10),
                  command=listeyi_yenile).pack(pady=(4, 14))

# ================= Not Aç / PDF =================
def notu_ac(kurs, dosya):
    yol = os.path.join(ANA_KLASOR, kurs, dosya)
    editor = tk.Toplevel(p)
    editor.title(dosya)
    editor.geometry("600x500")
    editor.config(bg=BG)
    text = tk.Text(editor, wrap="word", bg=ENTRY_BG, fg=FG,
                   insertbackground=FG, font=("Segoe UI", 10))
    text.pack(fill="both", expand=True, padx=10, pady=10)
    with open(yol, "r", encoding="utf-8") as f:
        text.insert("1.0", f.read())

    def kaydet_degisim():
        with open(yol, "w", encoding="utf-8") as f:
            f.write(text.get("1.0", tk.END))
        messagebox.showinfo("Kaydedildi", f"{dosya} güncellendi.")
        editor.destroy()

    tk.Button(editor, text="💾 Kaydet", bg=BUTTON_BG, fg=BUTTON_FG, bd=0,
              command=kaydet_degisim).pack(pady=5)

def kursu_pdf_yap(kurs):
    try:
        klasor = os.path.join(ANA_KLASOR, kurs)
        pdf_yol = os.path.join(klasor, f"{kurs}_Notlar.pdf")
        c = canvas.Canvas(pdf_yol)
        c.setFont(PDF_FONT, 10)
        y = 800
        c.drawCentredString(300, y, f"{kurs} - Notlar")
        y -= 20
        for dosya in sorted(os.listdir(klasor), key=str.lower):
            if not dosya.lower().endswith(".txt"):
                continue
            with open(os.path.join(klasor, dosya), "r", encoding="utf-8") as f:
                for satir in f:
                    if y < 60:
                        c.showPage(); c.setFont(PDF_FONT, 10); y = 800
                    c.drawString(50, y, satir.strip())
                    y -= 13
        c.save()
        messagebox.showinfo("PDF", "PDF oluşturuldu.")
        os.startfile(pdf_yol)
    except Exception as e:
        messagebox.showerror("Hata", str(e))

# ================= Sabitleme =================
def sabitle():
    global sabit
    sabit = not sabit
    p.attributes("-topmost", sabit)
    pin_butonu.config(
        text="📌 Sabitle: AÇIK" if sabit else "📌 Sabitle: KAPALI",
        bg="#0078ff" if sabit else "#3c3c3c",
    )

# ================= Arayüz =================
p = tk.Tk()
p.title("Udemy Note Saver")
p.geometry("600x640")
p.configure(bg=BG)
p.resizable(False, False)

notebook = ttk.Notebook(p)
tab_ana = tk.Frame(notebook, bg=BG)
tab_notlar = tk.Frame(notebook, bg=BG)
notebook.add(tab_ana, text="📝 Not Kaydet")
notebook.add(tab_notlar, text="📚 Notları Gör")
notebook.pack(fill="both", expand=True)

tk.Label(tab_ana, text="Udemy Not Kaydedici", font=("Segoe UI", 17, "bold"), bg=BG, fg=FG).pack(pady=10)
pin_butonu = tk.Button(tab_ana, text="📌 Sabitle: KAPALI", bg="#3c3c3c", fg=FG, bd=0,
                       font=("Segoe UI", 9), command=sabitle)
pin_butonu.pack(pady=(0, 6))

tk.Label(tab_ana, text="Kurs Adı:", bg=BG, fg=FG, font=FONT).pack(anchor="w", padx=35)
kurs_entry = tk.Entry(tab_ana, width=50, bg=ENTRY_BG, fg=FG, insertbackground=FG)
kurs_entry.pack(padx=35, pady=4, ipady=4)

tk.Label(tab_ana, text="Ders Adı:", bg=BG, fg=FG, font=FONT).pack(anchor="w", padx=35)
ders_entry = tk.Entry(tab_ana, width=50, bg=ENTRY_BG, fg=FG, insertbackground=FG)
ders_entry.pack(padx=35, pady=4, ipady=4)

tk.Label(tab_ana, text="Dakika:", bg=BG, fg=FG, font=FONT).pack(anchor="w", padx=35)
dakika_entry = tk.Entry(tab_ana, width=24, bg=ENTRY_BG, fg=FG, insertbackground=FG)
dakika_entry.pack(padx=35, pady=4, ipady=4)

tk.Label(tab_ana, text="Not:", bg=BG, fg=FG, font=FONT).pack(anchor="w", padx=35)
not_text = tk.Text(tab_ana, height=8, width=56, bg=ENTRY_BG, fg=FG,
                   insertbackground=FG, wrap="word")
not_text.pack(padx=35, pady=6)

tk.Button(tab_ana, text="💾 Notu Kaydet", bg=BUTTON_BG,
          fg=BUTTON_FG, bd=0, font=FONT, command=kaydet).pack(pady=10)
tk.Button(tab_ana, text="📚 Notları Gör", bg="#3c3c3c",
          fg=FG, bd=0, font=FONT, command=notlari_goster).pack(pady=6)

tk.Label(p, text="© 2025 Udemy Note Saver", bg=BG,
         fg="#777", font=("Segoe UI", 9)).pack(side="bottom", pady=6)

# Başlangıçta
p.after(1000, otomatik_kontrol)
listeyi_yenile()
p.mainloop()
