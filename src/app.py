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

# ===================================================
# 1) Nastavení logování
# ===================================================
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(base_dir, "app.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("Aplikace spuštěna.")

# ===================================================
# 2) Pomocné funkce pro čištění textu
# ===================================================
def remove_diacritics(s: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd_form if not unicodedata.combining(c))

def remove_hyphens(s: str) -> str:
    return s.replace("-", "")

# ===================================================
# 3) Načtení datasetu pro výběr hodnot v GUI
# ===================================================
dataset_path = os.path.join(base_dir, "datasets", "final_dataset.csv")
model_folder = os.path.join(base_dir, "models")

if not os.path.exists(dataset_path):
    logging.error(f"Dataset nebyl nalezen na {dataset_path}")
    df = pd.DataFrame()
else:
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
    brand_models = {}
    for brand in brands:
        models_list = df[df["Značka"] == brand]["Model"].dropna().unique().tolist()
        brand_models[brand] = sorted(models_list)
    fuel_options = sorted(df["Palivo"].dropna().unique().tolist())
    trans_options = sorted(df["Převodovka"].dropna().unique().tolist())

# ===================================================
# 4) Načtení modelů, scaleru a encoderů
# ===================================================
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

tree_model = load_pickle_or_joblib(os.path.join(model_folder, "tree_model.pkl"))
gb_model = load_pickle_or_joblib(os.path.join(model_folder, "gb_model.pkl"))
rf_model = load_pickle_or_joblib(os.path.join(model_folder, "rf_model.pkl"))

prediction_models = {}
if tree_model is not None:
    prediction_models["Decision Tree"] = tree_model
if gb_model is not None:
    prediction_models["Gradient Boosting"] = gb_model
if rf_model is not None:
    prediction_models["Random Forest"] = rf_model

# ===================================================
# 5) Reakce GUI na výběr značky a modelu
# ===================================================
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
    volumes_str = [str(v) for v in volumes]
    volume_combo['values'] = volumes_str
    volume_var.set("")

# ===================================================
# 6) Funkce pro výpočet predikce
# ===================================================
def predict():
    # Získání hodnot z GUI
    selected_brand = brand_var.get()
    selected_model = car_model_var.get()
    selected_volume_str = volume_var.get()
    selected_fuel = fuel_var.get()
    selected_trans = trans_var.get()

    # Kontrola, zda jsou všechna pole vyplněna
    if not all([selected_brand, selected_model, selected_volume_str, selected_fuel, selected_trans]):
        result_label.config(text="Chyba: Vyplňte prosím všechna pole.")
        return

    if encoders is None:
        result_label.config(text="Chyba: Encodery nejsou načteny.")
        return

    try:
        # Použití encodérů pro kategorické hodnoty
        brand_encoded = encoders["Značka"].transform([selected_brand])[0]
        model_encoded = encoders["Model"].transform([selected_model])[0]
        fuel_encoded = encoders["Palivo"].transform([selected_fuel])[0]
        trans_encoded = encoders["Převodovka"].transform([selected_trans])[0]

        # Načtení numerických hodnot
        volume_val = float(selected_volume_str)
        mileage_val = float(mileage_entry.get())
        power_val = float(power_entry.get())
        age_val = float(age_entry.get())

        # Validace vstupních čísel
        if any(x < 0 for x in [volume_val, mileage_val, power_val, age_val]):
            result_label.config(text="Chyba: Zadejte pouze nezáporné hodnoty.")
            return
        if mileage_val > 600000:
            result_label.config(text="Chyba: Najeté km nemohou přesáhnout 600 000.")
            return
        if not (0.5 <= volume_val <= 8.0):
            result_label.config(text="Chyba: Objem motoru musí být 0.5–8.0 litru.")
            return
        if not (20 <= power_val <= 800):
            result_label.config(text="Chyba: Výkon musí být 20–800 kW.")
            return
        if age_val > 50:
            result_label.config(text="Chyba: Stáří vozu nesmí přesáhnout 50 let.")
            return

    except ValueError:
        result_label.config(text="Chyba: Zadejte platné číselné hodnoty.")
        return

    # Vytvoření vstupního pole pro model predikce
    input_features = np.array([[brand_encoded, model_encoded, fuel_encoded, trans_encoded,
                                volume_val, mileage_val, power_val, age_val]], dtype=float)

    logging.info(f"Vstup před škálováním: {input_features.tolist()}")

    # Aplikování standardizace
    if scaler is not None:
        numeric_cols = [4, 5, 6, 7]
        input_features[:, numeric_cols] = scaler.transform(input_features[:, numeric_cols])

    logging.info(f"Vstup po škálování: {input_features.tolist()}")

    # Výběr modelu pro predikci
    selected_model_name = pred_model_var.get()
    if not selected_model_name:
        result_label.config(text="Chyba: Vyberte predikční model.")
        return

    model = prediction_models.get(selected_model_name)
    if model is None:
        result_label.config(text="Chyba: Model nenalezen.")
        return

    try:
        # Predikce ceny
        prediction = model.predict(input_features)
        pred_price = prediction[0]
        if pred_price < 0:
            result_label.config(text="Chyba: Výstupní cena je záporná.")
        else:
            result_label.config(text=f"Predikovaná cena: {pred_price:,.2f} Kč")
            logging.info(f"Výstup: {pred_price:.2f} Kč")
    except Exception as e:
        result_label.config(text=f"Chyba při predikci: {e}")

# ===================================================
# 7) Vytvoření GUI aplikace
# ===================================================

root = tk.Tk()
root.title("Aplikace pro predikci cen aut")
root.state("zoomed")
root.configure(bg="#dbe9f4")  # jemnější modrošedé pozadí

# Styl tlačítek, comboboxů a štítků
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#f4f4f4", foreground="#222222", font=("Helvetica", 14))
style.configure("TEntry", font=("Helvetica", 14))
style.configure("TCombobox", font=("Helvetica", 14))
style.configure("TButton",
                font=("Helvetica", 14, "bold"),
                foreground="white",
                background="#0066cc",
                padding=6)
style.map("TButton",
          background=[("active", "#004c99")])

# Rámeček
frame = ttk.Frame(root, padding=40, style="TFrame")
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

# Titulek
title_label = ttk.Label(frame, text="Předpověď ceny vozu", font=("Helvetica", 26, "bold"))
title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))

# Vstupní pole

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

add_row("Model predikce:", pred_model_var := tk.StringVar(),
        pred_model_combo := ttk.Combobox(frame, textvariable=pred_model_var, state="readonly", width=24), 9)
pred_model_combo['values'] = list(prediction_models.keys())
if prediction_models:
    pred_model_combo.current(0)

# ------------------- Akce -------------------
ttk.Button(frame, text="🔍 Predikovat cenu", command=predict).grid(row=10, column=0, columnspan=2, pady=(25, 15))

result_label = ttk.Label(frame, text="Výsledek predikce se zobrazí zde.", font=("Helvetica", 16, "italic"), foreground="#111111")
result_label.grid(row=11, column=0, columnspan=2, pady=(5, 25))

exit_button = ttk.Button(frame, text="❌ Ukončit", command=root.destroy)
exit_button.grid(row=12, column=0, columnspan=2, pady=(0, 15))

root.mainloop()
