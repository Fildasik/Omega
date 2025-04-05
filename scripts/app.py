import tkinter as tk
from tkinter import ttk
import pickle
import numpy as np
import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# -------------------------------------------------
# 1) Nastavení relativních cest
# -------------------------------------------------
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_path = os.path.join(base_dir, "datasets", "final_dataset.csv")
model_folder = os.path.join(base_dir, "models")

# -------------------------------------------------
# 2) Načtení datasetu a vytvoření LabelEncoderů
# -------------------------------------------------
try:
    df = pd.read_csv(dataset_path, encoding="utf-8-sig")
except Exception as e:
    print(f"Chyba při načítání datasetu: {e}")
    df = pd.DataFrame()

# Předpokládáme, že dataset obsahuje sloupce: Značka, Model, Palivo, Převodovka, Objem (l), atd.

categorical_features = ["Značka", "Model", "Palivo", "Převodovka"]
encoders = {}

for col in categorical_features:
    le = LabelEncoder()
    df[col + "_encoded"] = le.fit_transform(df[col])
    encoders[col] = le

# -------------------------------------------------
# 3) Slovníky pro dynamický výběr značky a modelu
# -------------------------------------------------
brands = sorted(df["Značka"].dropna().unique().tolist())

brand_models = {}
for brand in brands:
    filtered_models = df[df["Značka"] == brand]["Model"].dropna().unique().tolist()
    brand_models[brand] = sorted(filtered_models)

fuel_options = sorted(df["Palivo"].dropna().unique().tolist())
trans_options = sorted(df["Převodovka"].dropna().unique().tolist())


# -------------------------------------------------
# 4) Načtení předtrénovaných modelů
# -------------------------------------------------
def load_model(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Chyba při načítání modelu {filename}: {e}")
        return None


lr_model = load_model(os.path.join(model_folder, "lr_model.pkl"))
tree_model = load_model(os.path.join(model_folder, "tree_model.pkl"))
rf_model = load_model(os.path.join(model_folder, "rf_model.pkl"))
gb_model = load_model(os.path.join(model_folder, "gb_model.pkl"))

prediction_models = {
    "Lineární regrese": lr_model,
    "Decision Tree": tree_model,
    "Random Forest": rf_model,
    "Gradient Boosting": gb_model
}


# -------------------------------------------------
# 5) Funkce pro aktualizaci Modelu podle Značky
# -------------------------------------------------
def update_car_models(event):
    selected_brand = brand_var.get()
    models = brand_models.get(selected_brand, [])
    car_model_combo['values'] = models
    car_model_var.set("")
    # Vyčistíme i combobox pro objem
    volume_combo['values'] = []
    volume_var.set("")


# -------------------------------------------------
# 6) Funkce pro aktualizaci Objemu (l) podle Značka+Model
# -------------------------------------------------
def update_volumes(event):
    selected_brand = brand_var.get()
    selected_model = car_model_var.get()
    # Vybereme z dataframeu jen řádky pro danou značku a model
    subset = df[(df["Značka"] == selected_brand) & (df["Model"] == selected_model)]
    # Získáme všechny unikátní hodnoty ve sloupci "Objem (l)"
    volumes = sorted(subset["Objem (l)"].dropna().unique().tolist())

    # Combobox plníme řetězci (např. "2.0", "3.0")
    volumes_str = [str(v) for v in volumes]

    volume_combo['values'] = volumes_str
    volume_var.set("")


# -------------------------------------------------
# 7) Funkce pro predikci
# -------------------------------------------------
def predict():
    try:
        # Značka, Model, Objem (l), Palivo, Převodovka
        selected_brand = brand_var.get()
        selected_model = car_model_var.get()
        selected_volume_str = volume_var.get()
        selected_fuel = fuel_var.get()
        selected_trans = trans_var.get()

        # Kontrola, zda byly vybrány všechny kategorie
        if not all([selected_brand, selected_model, selected_volume_str, selected_fuel, selected_trans]):
            result_label.config(text="Chyba: Nevyplnili jste všechny kategorie.")
            return

        # Zakódování kategorií
        brand_encoded = encoders["Značka"].transform([selected_brand])[0]
        model_encoded = encoders["Model"].transform([selected_model])[0]
        fuel_encoded = encoders["Palivo"].transform([selected_fuel])[0]
        trans_encoded = encoders["Převodovka"].transform([selected_trans])[0]

        # Převod objemu na float
        volume_val = float(selected_volume_str)

        # Číselné vstupy: Najeté km, Výkon (kW), Stáří
        mileage_val = float(mileage_entry.get())
        power_val = float(power_entry.get())
        age_val = float(age_entry.get())

        # Ošetření záporných vstupů
        if any(x < 0 for x in [volume_val, mileage_val, power_val, age_val]):
            result_label.config(text="Chyba: Zadejte pouze nezáporné (kladné) hodnoty.")
            return

    except ValueError:
        result_label.config(text="Chyba: Zadejte platné číselné hodnoty.")
        return
    except Exception as e:
        result_label.config(text=f"Chyba: {e}")
        return

    # Sestavíme feature vector (příklad pořadí):
    # [Značka, Model, Objem (l), Najeté km, Palivo, Převodovka, Výkon (kW), Stáří]
    input_features = np.array([[brand_encoded, model_encoded, volume_val,
                                mileage_val, fuel_encoded, trans_encoded,
                                power_val, age_val]])

    selected_prediction_model = pred_model_var.get()
    model = prediction_models.get(selected_prediction_model)
    if model is None:
        result_label.config(text="Zvolený predikční model není k dispozici.")
        return

    try:
        prediction = model.predict(input_features)
        pred_price = prediction[0]
        # Pokud model vrátí zápornou cenu, ošetříme to
        if pred_price < 0:
            result_label.config(text="Chyba: Model predikoval zápornou cenu, to nedává smysl.")
        else:
            result_label.config(text=f"Predikovaná cena: {pred_price:.2f}")
    except Exception as e:
        result_label.config(text=f"Chyba při predikci: {e}")


# -------------------------------------------------
# 8) Vytvoření GUI
# -------------------------------------------------
root = tk.Tk()
root.title("Aplikace pro predikci aut")

# Nastavení okna na maximalizované (zoomed) - Windows
root.state('zoomed')

# Volitelně lze povolit/zakázat změnu velikosti:
root.resizable(True, True)

root.configure(bg='#f0f0f0')

frame = ttk.Frame(root, padding=20)
frame.pack(expand=True)

# Row 0: Značka
brand_label = ttk.Label(frame, text="Značka:")
brand_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
brand_var = tk.StringVar()
brand_combo = ttk.Combobox(frame, textvariable=brand_var, state="readonly", width=20)
brand_combo['values'] = brands
brand_combo.grid(row=0, column=1, padx=10, pady=10)
brand_combo.set("")
brand_combo.bind("<<ComboboxSelected>>", update_car_models)

# Row 1: Model
car_model_label = ttk.Label(frame, text="Model vozu:")
car_model_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
car_model_var = tk.StringVar()
car_model_combo = ttk.Combobox(frame, textvariable=car_model_var, state="readonly", width=20)
car_model_combo.grid(row=1, column=1, padx=10, pady=10)
car_model_combo.set("")
car_model_combo.bind("<<ComboboxSelected>>", update_volumes)

# Row 2: Objem (l)
volume_label = ttk.Label(frame, text="Objem (l):")
volume_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
volume_var = tk.StringVar()
volume_combo = ttk.Combobox(frame, textvariable=volume_var, state="readonly", width=20)
volume_combo.grid(row=2, column=1, padx=10, pady=10)
volume_combo.set("")

# Row 3: Najeté km
mileage_label = ttk.Label(frame, text="Najeté km:")
mileage_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
mileage_entry = ttk.Entry(frame, width=22)
mileage_entry.grid(row=3, column=1, padx=10, pady=10)

# Row 4: Palivo
fuel_label = ttk.Label(frame, text="Palivo:")
fuel_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
fuel_var = tk.StringVar()
fuel_combo = ttk.Combobox(frame, textvariable=fuel_var, state="readonly", width=20)
fuel_combo['values'] = fuel_options
fuel_combo.grid(row=4, column=1, padx=10, pady=10)
fuel_combo.set("")

# Row 5: Převodovka
trans_label = ttk.Label(frame, text="Převodovka:")
trans_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
trans_var = tk.StringVar()
trans_combo = ttk.Combobox(frame, textvariable=trans_var, state="readonly", width=20)
trans_combo['values'] = trans_options
trans_combo.grid(row=5, column=1, padx=10, pady=10)
trans_combo.set("")

# Row 6: Výkon (kW)
power_label = ttk.Label(frame, text="Výkon (kW):")
power_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")
power_entry = ttk.Entry(frame, width=22)
power_entry.grid(row=6, column=1, padx=10, pady=10)

# Row 7: Stáří (roky)
age_label = ttk.Label(frame, text="Stáří (roky):")
age_label.grid(row=7, column=0, padx=10, pady=10, sticky="w")
age_entry = ttk.Entry(frame, width=22)
age_entry.grid(row=7, column=1, padx=10, pady=10)

# Row 8: Predikční model
pred_model_label = ttk.Label(frame, text="Predikční model:")
pred_model_label.grid(row=8, column=0, padx=10, pady=10, sticky="w")
pred_model_var = tk.StringVar()
pred_model_combo = ttk.Combobox(frame, textvariable=pred_model_var, state="readonly", width=20)
pred_model_combo['values'] = list(prediction_models.keys())
pred_model_combo.grid(row=8, column=1, padx=10, pady=10)
pred_model_combo.current(0)

# Row 9: Tlačítko Predikovat
predict_button = ttk.Button(frame, text="Predikovat", command=predict)
predict_button.grid(row=9, column=0, columnspan=2, pady=20)

# Row 10: Výsledek
result_label = ttk.Label(frame, text="Výsledek predikce se zobrazí zde.", font=("Arial", 14))
result_label.grid(row=10, column=0, columnspan=2, pady=10)

# Row 11: Tlačítko Ukončit
exit_button = ttk.Button(frame, text="Ukončit", command=root.destroy)
exit_button.grid(row=11, column=0, columnspan=2, pady=10)

root.mainloop()
