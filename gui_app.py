import tkinter as tk
from tkinter import ttk, messagebox
import joblib
import numpy as np

# 📂 Absolutní cesta k .pkl souborům
BASE_PATH = "C:/Users/Asus/PV/OMEGA/OmegaCars/"

# Načti model a encodery
model = joblib.load(BASE_PATH + "model.pkl")
brand_encoder = joblib.load(BASE_PATH + "brand_encoder.pkl")
model_encoder = joblib.load(BASE_PATH + "model_encoder.pkl")
fuel_dict = joblib.load(BASE_PATH + "fuel_dict.pkl")
prev_dict = joblib.load(BASE_PATH + "prev_dict.pkl")

# Dropdown hodnoty
znacky = list(brand_encoder.classes_)
modely = list(model_encoder.classes_)

# Hlavní okno
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
        messagebox.showerror("Chyba", str(e))

# GUI layout
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
ttk.Combobox(root, textvariable=palivo_var, values=list(fuel_dict.keys())).pack()

tk.Label(root, text="Převodovka").pack()
prevodovka_var = tk.StringVar()
ttk.Combobox(root, textvariable=prevodovka_var, values=list(prev_dict.keys())).pack()

tk.Label(root, text="Výkon (kW)").pack()
entry_vykon = tk.Entry(root)
entry_vykon.pack()

tk.Label(root, text="Stáří (roky)").pack()
entry_stari = tk.Entry(root)
entry_stari.pack()

tk.Button(root, text="Spočítat cenu", command=predikuj).pack(pady=20)

root.mainloop()
