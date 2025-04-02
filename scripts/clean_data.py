import pandas as pd
import numpy as np

# 1. Načtení dat
df = pd.read_csv(r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\merged_auta.csv", encoding="utf-8")

# 2. Odebrání sloupce 'Zdroj' (pokud existuje)
if 'Zdroj' in df.columns:
    df.drop(columns=['Zdroj'], inplace=True)

# 3. Výběr vybraných sloupců (pokud reálně existují)
desired_columns = ["Značka", "Model", "Rok", "Najeté km", "Cena", "Palivo", "Převodovka", "Výkon (kW)"]
existing_desired_columns = [c for c in desired_columns if c in df.columns]
df = df[existing_desired_columns]

# 4. Odstranění duplicit a prázdných řádků
df.drop_duplicates(inplace=True)
df.dropna(how="all", inplace=True)

# 5. Cenový filtr (30 000 - 2 000 000)
if "Cena" in df.columns:
    df["Cena"] = pd.to_numeric(df["Cena"], errors="coerce")
    df = df[(df["Cena"] >= 30000) & (df["Cena"] <= 2000000)]

# 6. Standardizace paliva
def standardize_fuel(fuel):
    """
    Tato funkce se aplikuje POUZE na sloupec "Palivo".
    Pokud text obsahuje:
      • 'benz', 'gasol'  → Benzín
      • 'dies', 'naf'    → Nafta
      • 'hybr'           → Hybridní
      • 'elek'           → Elektro
    Jinak None (řádek se pak odstraní).
    """
    if pd.isna(fuel):
        return None
    text = str(fuel).strip().lower()

    if ("benz" in text) or ("gasol" in text):
        return "Benzín"
    elif ("dies" in text) or ("naf" in text):
        return "Nafta"
    elif "hybr" in text:
        return "Hybridní"
    elif "elek" in text:
        return "Elektro"
    else:
        return None

if "Palivo" in df.columns:
    df["Palivo"] = df["Palivo"].apply(standardize_fuel)

# 7. Standardizace převodovky
def standardize_transmission(t):
    """
    Tato funkce se aplikuje POUZE na sloupec "Převodovka".
    Pokud text obsahuje:
      • 'manu' → Manuální
      • 'auto' → Automatická
    Jinak None (řádek se pak odstraní).
    """
    if pd.isna(t):
        return None
    text = str(t).strip().lower()

    if "manu" in text:
        return "Manuální"
    elif "auto" in text:
        return "Automatická"
    else:
        return None

if "Převodovka" in df.columns:
    df["Převodovka"] = df["Převodovka"].apply(standardize_transmission)

# 8. Striktní standardizace značky
def standardize_brand(brand):
    """
    Tato funkce se aplikuje POUZE na sloupec "Značka".
    Povolené značky jsou uvedené v brand_mapping.
    Vše ostatní → None (řádek se pak odstraní).
    """
    if pd.isna(brand):
        return None
    original = str(brand).strip().lower()

    brand_mapping = {
        "alfa": "Alfa Romeo",
        "alfa romeo": "Alfa Romeo",
        "audi": "Audi",
        "bmw": "BMW",
        "chevrolet": "Chevrolet",
        "citroen": "Citroën",
        "citroën": "Citroën",
        "cupra": "Cupra",
        "dacia": "Dacia",
        "dodge": "Dodge",
        "fiat": "Fiat",
        "ford": "Ford",
        "honda": "Honda",
        "hyundai": "Hyundai",
        "jaguar": "Jaguar",
        "jeep": "Jeep",
        "kia": "Kia",
        "land rover": "Land Rover",
        "land-rover": "Land Rover",
        "landrover": "Land Rover",
        "lexus": "Lexus",
        "mg": "MG",
        "mazda": "Mazda",
        "mercedes": "Mercedes-Benz",
        "mercedes-benz": "Mercedes-Benz",
        "mercedes benz": "Mercedes-Benz",
        "mini": "Mini",
        "nissan": "Nissan",
        "opel": "Opel",
        "peugeot": "Peugeot",
        "porsche": "Porsche",
        "renault": "Renault",
        "seat": "Seat",
        "subaru": "Subaru",
        "tesla": "Tesla",
        "toyota": "Toyota",
        "vw": "Volkswagen",
        "volkswagen": "Volkswagen",
        "volvo": "Volvo",
        "skoda": "Škoda",
        "škoda": "Škoda"
    }
    return brand_mapping.get(original, None)

if "Značka" in df.columns:
    df["Značka"] = df["Značka"].apply(standardize_brand)

# 9. Standardizace modelu
def standardize_model(m):
    """
    Tato funkce se aplikuje POUZE na sloupec "Model".
    Když se objeví 'rada' / 'Rada' (v jakékoli velikosti) samotně nebo v textu,
    přemapujeme to na 'Řada'. Jinak necháváme text, jak je.

    Příklad:
      'Rada' → 'Řada'
      'Rada 3' → 'Řada 3'
      'BMW Rada' → 'BMW Řada'
    """
    if pd.isna(m):
        return None
    text = str(m).strip()
    lower_text = text.lower()

    # Pokud obsahuje řetězec 'rada', nahradíme ho (bez ohledu na velká/malá písmena)
    if "rada" in lower_text:
        # Nahrazujeme case-insensitive, takže si pomůžeme metodou replace() nad lower:
        # Lepší je konstruovat nový řetězec, ale pro jednoduchost můžeme zkusit:
        text = text.replace("rada", "Řada")
        text = text.replace("Rada", "Řada")
        text = text.replace("RADA", "Řada")
        # a tak dále... aby se to nahradilo ve všech případech.
    return text

if "Model" in df.columns:
    df["Model"] = df["Model"].apply(standardize_model)

# 10. Odstranění řádků, kde jsou v klíčových sloupcích prázdné hodnoty
required_for_nonempty = ["Značka", "Palivo", "Převodovka", "Cena"]
df.dropna(subset=required_for_nonempty, inplace=True)

# 11. Vyfiltrování značek, které mají aspoň 25 výskytů
if "Značka" in df.columns:
    brand_counts = df["Značka"].value_counts()
    valid_brands = brand_counts[brand_counts >= 25].index.tolist()
    df = df[df["Značka"].isin(valid_brands)]

# 12. Limit počtu záznamů na max 500 pro každou značku
if "Značka" in df.columns:
    df = (
        df.groupby("Značka", group_keys=False)
        .apply(lambda grp: grp.sample(n=500, random_state=42) if len(grp) > 500 else grp)
        .reset_index(drop=True)
    )

# 13. Odstranění řádků obsahujících nežádoucí hodnoty
undesired_terms = ["ostatni", "nezjisteno"]

def contains_undesired(row):
    for cell in row:
        if pd.isna(cell):
            continue
        cell_str = str(cell).strip().lower()
        if any(term in cell_str for term in undesired_terms):
            return True
    return False

df = df[~df.apply(contains_undesired, axis=1)]

# 14. Speciální pravidlo pro BMW:
#     Pokud Značka = "BMW" a Model obsahuje "Řada" (libovolná velkost písmen),
#     ale NEobsahuje číslo (3,4,5...) za tím slovem, tak řádek smazat.
if "Značka" in df.columns and "Model" in df.columns:
    # Filtr: Značka je BMW, v Modelu je 'Řada', ale neobsahuje žádnou číslici.
    # Pro jistotu budeme ignorovat velikost písmen (case-insensitive),
    # a jako "není číslice" použijeme pattern negující jakékoli \d (0-9).
    condition_bmw = df["Značka"] == "BMW"
    condition_rada = df["Model"].str.contains("řada", case=False, na=False)
    condition_no_number = ~df["Model"].str.contains(r"\d", regex=True, na=False)
    df = df[~(condition_bmw & condition_rada & condition_no_number)]

# 15. Uložení do CSV
output_path = r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\auta_cleaned.csv"
df.to_csv(output_path, index=False)

print("Data úspěšně vyčištěna a uložena do 'auta_cleaned.csv'.")
print(f"Po čištění zůstalo {df.shape[0]} řádků.")
print("• Sloupec 'Zdroj' odebrán,")
print("• Palivo => Benzín/Nafta/Hybridní/Elektro (dle obsahu textu), vše ostatní smazáno,")
print("• Převodovka => Automatická/Manuální (dle obsahu textu), vše ostatní smazáno,")
print("• Značky jen vyjmenované v brand_mapping, jinak smazáno,")
print("• Model: 'rada' → 'Řada', pokud je BMW a Model obsahuje 'Řada' bez čísla, smazáno,")
print("• Minimum 25 výskytů značky, maximum 500,")
print("• Odstraněny řádky obsahující 'ostatni' nebo 'nezjisteno',")
print("• Zůstávají sloupce:", ", ".join(df.columns))
