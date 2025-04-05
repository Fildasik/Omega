import tkinter as tk
from tkinter import ttk, messagebox
import joblib
import numpy as np
import os
import sys

# 🔧 Určení cesty pro PyInstaller (--add-data)
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS  # cesta do dočasné složky kde jsou data rozbalená
else:
    BASE_PATH = os.path.dirname(__file__)

def load_pickle(filename):
    return joblib.load(os.path.join(BASE_PATH, filename))

# Načti model a encodery
model = load_pickle("model.pkl")
brand_encoder = load_pickle("brand_encoder.pkl")
model_encoder = load_pickle("model_encoder.pkl")
fuel_dict = load_pickle("fuel_dict.pkl")
prev_dict = load_pickle("prev_dict.pkl")

# Dropdown hodnoty
znacky = list(brand_encoder.classes_)
modely = list(model_encoder.classes_)
paliva = list(fuel_dict.keys())
prevodovky = list(prev_dict.keys())

# GUI
root = tk.Tk()
root.title("Predikce ceny auta")
root.geometry("400x500")

def predikuj():
    try:
        znacka = brand_var.get()
        model_auta = model_var.get()
        km = int(entry_km.get())
        palivo = fuel_dict[palivo_var.get()]
        prevod = prev_dict[prevodovka_var.get()]
        vykon = int(entry_vykon.get())
        stari = int(entry_stari.get())

        znacka_encoded = brand_encoder.transform([znacka])[0]
        model_encoded = model_encoder.transform([model_auta])[0]

        vstup = np.array([[znacka_encoded, model_encoded, km, palivo, prevod, vykon, stari]])
        cena = model.predict(vstup)[0]

        messagebox.showinfo("Výsledek", f"Odhadovaná cena vozu: {int(cena):,} Kč")
    except Exception as e:
        messagebox.showerror("Chyba", f"Nastala chyba: {str(e)}")

tk.Label(root, text="Značka").pack()
brand_var = tk.StringVar()
ttk.Combobox(root, textvariable=brand_var, values=znacky).pack()

tk.Label(root, text="Model").pack()
model_var = tk.StringVar()
ttk.Combobox(root, textvariable=model_var, values=modely).pack()

tk.Label(root, text="Najeté km").pack()
entry_km = tk.Entry(root)
entry_km.pack()

tk.Label(root, text="Palivo").pack()
palivo_var = tk.StringVar()
ttk.Combobox(root, textvariable=palivo_var, values=paliva).pack()

tk.Label(root, text="Převodovka").pack()
prevodovka_var = tk.StringVar()
ttk.Combobox(root, textvariable=prevodovka_var, values=prevodovky).pack()

tk.Label(root, text="Výkon (kW)").pack()
entry_vykon = tk.Entry(root)
entry_vykon.pack()

tk.Label(root, text="Stáří (roky)").pack()
entry_stari = tk.Entry(root)
entry_stari.pack()

tk.Button(root, text="Spočítat cenu", command=predikuj).pack(pady=20)

root.mainloop()
    