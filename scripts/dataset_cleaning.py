from datetime import datetime
import os
import pandas as pd
import unicodedata
import re

def remove_diacritics(s: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd_form if not unicodedata.combining(c))

def remove_hyphens_spaces(s: str) -> str:
    return s.replace("-", "").replace(" ", "")

def unify_text(s: str) -> str:
    if pd.isna(s):
        return None
    s_clean = remove_diacritics(s).lower()
    s_clean = remove_hyphens_spaces(s_clean)
    return s_clean.title()  # sjednocené finálně na např. "Troc", "Cmax", "Xtrail"

def unify_brand(brand: str) -> str:
    if pd.isna(brand):
        return None
    b = remove_hyphens_spaces(remove_diacritics(str(brand).strip().lower()))
    prefixes = {
        "aud": "Audi", "bmw": "BMW", "cit": "Citroën", "dod": "Dodge",
        "for": "Ford", "hyu": "Hyundai", "jee": "Jeep", "kia": "Kia",
        "maz": "Mazda", "mer": "MercedesBenz", "nis": "Nissan", "ope": "Opel",
        "peu": "Peugeot", "por": "Porsche", "ren": "Renault", "sko": "Skoda",
        "toy": "Toyota", "volk": "Volkswagen", "volv": "Volvo"
    }
    for prefix, standard in prefixes.items():
        if b.startswith(prefix):
            return standard
    return str(brand).strip().title()

def unify_transmission(t: str) -> str:
    if pd.isna(t):
        return None
    text = remove_diacritics(t.strip().lower())
    if "man" in text:
        return "Manuální"
    elif "auto" in text:
        return "Automatická"
    return None

def check_palivo(p: str) -> str or None:
    if pd.isna(p):
        return None
    text = p.strip().lower()
    if "benz" in text or "gasol" in text:
        return "Benzin"
    elif "naf" in text or "diesel" in text:
        return "Nafta"
    elif "hyb" in text:
        return "Hybridni"
    elif "ele" in text:
        return "Elektro"
    return None

def clean_dataset(file_path: str, output_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, encoding="utf-8")

    df.drop_duplicates(inplace=True)
    df.dropna(how="all", inplace=True)

    numeric_cols = ["Rok", "Najeté km", "Cena", "Výkon (kW)", "Objem (l)"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Filtrování extrémních hodnot
    df = df[df["Cena"].between(30000, 2500000)]
    df = df[df["Rok"].between(1970, 2025)]
    df = df[df["Najeté km"] <= 600000]
    df = df[df["Objem (l)"].between(0.5, 8.0)]
    df = df[df["Výkon (kW)"].between(20, 800)]

    df["Značka"] = df["Značka"].apply(unify_brand)
    df["Model"] = df["Model"].apply(unify_text)
    df["Převodovka"] = df["Převodovka"].apply(unify_transmission)
    df["Palivo"] = df["Palivo"].apply(check_palivo)

    mandatory = ["Značka", "Model", "Rok", "Cena", "Palivo", "Převodovka", "Výkon (kW)", "Objem (l)"]
    df.dropna(subset=mandatory, inplace=True)

    df = df[~((df["Značka"] == "BMW") & (df["Model"].str.lower() == "rada"))]

    if "Zdroj" in df.columns:
        df.drop(columns=["Zdroj"], inplace=True)

    current_year = datetime.now().year
    df["Stari"] = current_year - df["Rok"]
    df.drop(columns=["Rok"], inplace=True)

    text_columns = ["Značka", "Model", "Palivo", "Převodovka"]
    for col in text_columns:
        df[col] = df[col].apply(lambda x: unify_text(x) if isinstance(x, str) else x)

    invalid_values = {"ostatni", "nezjisteno"}
    for col in text_columns:
        df = df[~df[col].str.lower().isin(invalid_values)]

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_path = os.path.join(base_dir, "datasets", "merged_dataset.csv")
output_path = os.path.join(base_dir, "datasets", "final_dataset.csv")

# Použití funkce pro vyčištění datasetu
cleaned_df = clean_dataset(input_path, output_path)
print("Čištění dokončeno.")
print(cleaned_df.head())
print(cleaned_df["Model"].value_counts().head(20))
