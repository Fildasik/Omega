import tkinter as tk
from tkinter import ttk
import pickle
import numpy as np
import os
import pandas as pd
import unicodedata
from datetime import datetime
import logging
import joblib

# 1) Nastavení logování
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(base_dir, "app.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("Aplikace spuštěna.")

# 2) Pomocné funkce pro čištění textu
def remove_diacritics(s: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd_form if not unicodedata.combining(c))

def remove_hyphens(s: str) -> str:
    return s.replace("-", "")

# 3) Načtení datasetu
dataset_path = os.path.join(base_dir, "datasets", "final_dataset.csv")
model_folder = os.path.join(base_dir, "models")

try:
    df = pd.read_csv(dataset_path, encoding="utf-8-sig")
except Exception as e:
    logging.error(f"Chyba při načítání datasetu: {e}")
    df = pd.DataFrame()

if df.empty or "Značka" not in df.columns:
    logging.error("Dataset je prázdný nebo neobsahuje očekávané sloupce.")
    brands = []
    brand_models = {}
    fuel_options = []
    trans_options = []
else:
    brands = sorted(df["Značka"].dropna().unique().tolist())
    brand_models = {brand: sorted(df[df["Značka"] == brand]["Model"].dropna().unique().tolist()) for brand in brands}
    fuel_options = sorted(df["Palivo"].dropna().unique().tolist())
    trans_options = sorted(df["Převodovka"].dropna().unique().tolist())

# 4) Načtení modelu, scaleru a encoderů
def load_pickle_or_joblib(path):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        try:
            return joblib.load(path)
        except Exception as e:
            logging.error(f"Chyba při načítání souboru {path}: {e}")
            return None

encoders = load_pickle_or_joblib(os.path.join(model_folder, "encoders.pkl"))
scaler = load_pickle_or_joblib(os.path.join(model_folder, "scaler.pkl"))
gb_model = load_pickle_or_joblib(os.path.join(model_folder, "gb_model.pkl"))

# 5) GUI callbacky
def update_car_models(event):
    selected_brand = brand_var.get()
    models = brand_models.get(selected_brand, [])
    car_model_combo['values'] = models
    car_model_var.set("")
    volume_combo['values'] = []
    volume_var.set("")

def update_volumes(event):
    selected_brand = brand_var.get()
    selected_model = car_model_var.get()
    subset = df[(df["Značka"] == selected_brand) & (df["Model"] == selected_model)]
    volumes = sorted(subset["Objem (l)"].dropna().unique().tolist())
    volume_combo['values'] = [str(v) for v in volumes]
    volume_var.set("")

# 6) Funkce pro predikci
def predict():
    selected_brand = brand_var.get()
    selected_model = car_model_var.get()
    selected_volume_str = volume_var.get()
    selected_fuel = fuel_var.get()
    selected_trans = trans_var.get()

    if not all([selected_brand, selected_model, selected_volume_str, selected_fuel, selected_trans]):
        result_label.config(text="Chyba: Vyplňte prosím všechna pole.")
        return

    try:
        brand_encoded = encoders["Značka"].transform([selected_brand])[0]
        model_encoded = encoders["Model"].transform([selected_model])[0]
        fuel_encoded = encoders["Palivo"].transform([selected_fuel])[0]
        trans_encoded = encoders["Převodovka"].transform([selected_trans])[0]

        volume_val = float(selected_volume_str)
        mileage_val = float(mileage_entry.get())
        power_val = float(power_entry.get())
        age_val = float(age_entry.get())

        if any(x < 0 for x in [volume_val, mileage_val, power_val, age_val]):
            result_label.config(text="Chyba: Zadejte pouze nezáporné hodnoty.")
            return
        if mileage_val > 600000 or not (0.5 <= volume_val <= 8.0) or not (20 <= power_val <= 800) or age_val > 50:
            result_label.config(text="Chyba: Zkontrolujte rozsah hodnot.")
            return
    except ValueError:
        result_label.config(text="Chyba: Zadejte platné číselné hodnoty.")
        return

    input_features = np.array([[brand_encoded, model_encoded, fuel_encoded, trans_encoded,
                                volume_val, mileage_val, power_val, age_val]], dtype=float)

    logging.info(f"Vstup před škálováním: {input_features.tolist()}")

    if scaler:
        input_features[:, [4, 5, 6, 7]] = scaler.transform(input_features[:, [4, 5, 6, 7]])

    logging.info(f"Vstup po škálování: {input_features.tolist()}")

    try:
        prediction = gb_model.predict(input_features)
        pred_price = float(prediction.flatten()[0])
        if pred_price < 0:
            result_label.config(text="Chyba: Výstupní cena je záporná.")
        else:
            result_label.config(text=f"Predikovaná cena: {pred_price:,.2f} Kč")
            logging.info(f"Výstup: {pred_price:.2f} Kč")
    except Exception as e:
        result_label.config(text=f"Chyba při predikci: {e}")

# 7) GUI aplikace
root = tk.Tk()
root.title("Předpověď ceny auta (Gradient Boosting)")
root.state("zoomed")
root.configure(bg="#dbe9f4")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#f4f4f4", foreground="#222222", font=("Helvetica", 14))
style.configure("TEntry", font=("Helvetica", 14))
style.configure("TCombobox", font=("Helvetica", 14))
style.configure("TButton", font=("Helvetica", 14, "bold"), foreground="white", background="#0066cc", padding=6)
style.map("TButton", background=[("active", "#004c99")])

frame = ttk.Frame(root, padding=40, style="TFrame")
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

title_label = ttk.Label(frame, text="Předpověď ceny vozu", font=("Helvetica", 26, "bold"))
title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))

def add_row(label_text, variable, widget, row):
    ttk.Label(frame, text=label_text).grid(row=row, column=0, padx=15, pady=12, sticky="e")
    widget.grid(row=row, column=1, padx=15, pady=12, sticky="w")

add_row("Značka:", brand_var := tk.StringVar(),
        brand_combo := ttk.Combobox(frame, textvariable=brand_var, state="readonly", width=24), 1)
brand_combo['values'] = brands
brand_combo.bind("<<ComboboxSelected>>", update_car_models)

add_row("Model:", car_model_var := tk.StringVar(),
        car_model_combo := ttk.Combobox(frame, textvariable=car_model_var, state="readonly", width=24), 2)
car_model_combo.bind("<<ComboboxSelected>>", update_volumes)

add_row("Objem (l):", volume_var := tk.StringVar(),
        volume_combo := ttk.Combobox(frame, textvariable=volume_var, state="readonly", width=24), 3)

add_row("Najeté km:", tk.StringVar(),
        mileage_entry := ttk.Entry(frame, width=26), 4)

add_row("Palivo:", fuel_var := tk.StringVar(),
        fuel_combo := ttk.Combobox(frame, textvariable=fuel_var, state="readonly", width=24), 5)
fuel_combo['values'] = fuel_options

add_row("Převodovka:", trans_var := tk.StringVar(),
        trans_combo := ttk.Combobox(frame, textvariable=trans_var, state="readonly", width=24), 6)
trans_combo['values'] = trans_options

add_row("Výkon (kW):", tk.StringVar(),
        power_entry := ttk.Entry(frame, width=26), 7)

add_row("Stáří (roky):", tk.StringVar(),
        age_entry := ttk.Entry(frame, width=26), 8)

ttk.Button(frame, text="🔍 Predikovat cenu", command=predict).grid(row=9, column=0, columnspan=2, pady=(25, 15))

result_label = ttk.Label(frame, text="Výsledek predikce se zobrazí zde.", font=("Helvetica", 16, "italic"), foreground="#111111")
result_label.grid(row=10, column=0, columnspan=2, pady=(5, 25))

exit_button = ttk.Button(frame, text="❌ Ukončit", command=root.destroy)
exit_button.grid(row=11, column=0, columnspan=2, pady=(0, 15))

root.mainloop()
