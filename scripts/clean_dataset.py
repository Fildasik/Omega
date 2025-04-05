from datetime import datetime
import pandas as pd
import unicodedata
import re

def remove_diacritics(s: str) -> str:
    """Odstraní diakritiku ze zadaného řetězce."""
    nfkd_form = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd_form if not unicodedata.combining(c))

def remove_hyphens(s: str) -> str:
    """Odstraní všechny pomlčky ze zadaného řetězce."""
    return s.replace("-", "")

def unify_brand(brand: str) -> str:
    """
    Sjednotí varianty značek podle prefixů pomocí dictionary.
    Například:
      "auDi" → "Audi"
      "BMW", "Bmw" → "BMW"
      "mercedes BeNz" → "Mercedes-Benz"
      "Skoda", "Škoda" → "Škoda"
    Pokud značka nezačíná na žádný z definovaných prefixů, vrací se značka s prvním písmenem velkým.
    """
    if pd.isna(brand):
        return None
    # Odstraň diakritiku a pomlčky, uprav na malá písmena
    b = remove_hyphens(remove_diacritics(str(brand).strip().lower()))
    prefixes = {
        "aud": "Audi",
        "bmw": "BMW",
        "cit": "Citroën",
        "dod": "Dodge",
        "for": "Ford",
        "hyu": "Hyundai",
        "jee": "Jeep",
        "kia": "Kia",
        "maz": "Mazda",
        "mer": "MercedesBenz",
        "nis": "Nissan",
        "ope": "Opel",
        "peu": "Peugeot",
        "por": "Porsche",
        "ren": "Renault",
        "sko": "Skoda",
        "toy": "Toyota",
        "volk": "Volkswagen",
        "volv": "Volvo"
    }
    for prefix, standard in prefixes.items():
        if b.startswith(prefix):
            return standard
    return str(brand).strip().title()

def unify_transmission(t: str) -> str:
    """
    Pokud text obsahuje "man" (bez ohledu na velikost), vrátí "Manuální".
    Pokud obsahuje "auto", vrátí "Automatická".
    Jinak vrátí None.
    """
    if pd.isna(t):
        return None
    text = remove_diacritics(t.strip().lower())
    if "man" in text:
        return "Manuální"
    elif "auto" in text:
        return "Automatická"
    else:
        return None

def check_palivo(p: str) -> str or None:
    """
    Pokud sloupec Palivo neobsahuje ani "benz" (Benzin), ani "naf" (Nafta),
    ani "hyb" (Hybridni), ani "ele" (Elektro) – vrátí None.
    Jinak vrátí standardizovanou hodnotu:
      - "benz" → "Benzin"
      - "naf" → "Nafta"
      - "hyb" → "Hybridni"
      - "ele" → "Elektro"
    """
    if pd.isna(p):
        return None
    text = p.strip().lower()
    if "benz" in text:
        return "Benzin"
    elif "naf" in text:
        return "Nafta"
    elif "hyb" in text:
        return "Hybridni"
    elif "ele" in text:
        return "Elektro"
    else:
        return None

def clean_dataset(file_path: str, output_path: str) -> pd.DataFrame:
    """
    Načte dataset, vyčistí ho a uloží do output_path.

    Úpravy:
      - odstraní duplicity a prázdné řádky,
      - převede číselné sloupce ("Rok", "Najeté km", "Cena", "Výkon (kW)") na numeric,
      - filtruje data: Cena mezi 30 000 a 2 500 000 a Rok mezi 1970 a 2025,
      - standardizuje sloupce "Značka", "Model", "Palivo" a "Převodovka",
      - odstraní řádky, kde Palivo neobsahuje ani "Benzin", "Nafta", "Hybridni" nebo "Elektro",
      - odstraní řádky s chybějícími kritickými hodnotami,
      - speciálně filtruje data pro BMW (odstraní řádky, kde je Značka "BMW" a Model je přesně "Rada"),
      - odstraní sloupec "Zdroj", pokud existuje,
      - přidá sloupec "Stari" = (aktuální rok - Rok) a poté odstraní sloupec "Rok",
      - odstraní diakritiku a pomlčky ze všech textových sloupců, takže výsledný CSV bude bez diakritiky a pomlček.
    """
    df = pd.read_csv(file_path, encoding="utf-8")

    # 1. Odstranění duplicit a úplně prázdných řádků
    df.drop_duplicates(inplace=True)
    df.dropna(how="all", inplace=True)

    # 2. Konverze číselných sloupců
    numeric_cols = ["Rok", "Najeté km", "Cena", "Výkon (kW)"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3. Filtrování extrémních hodnot:
    # Cena mezi 30 000 a 2 500 000 a Rok mezi 1970 a 2025
    df = df[df["Cena"].between(30000, 2500000)]
    df = df[df["Rok"].between(1970, 2025)]

    # 4. Standardizace textových sloupců pomocí sjednocovacích funkcí
    df["Značka"] = df["Značka"].apply(unify_brand)
    # Ponecháme sloupec Model beze změny zde – sjednocení modelu můžete provést samostatně nebo později
    df["Převodovka"] = df["Převodovka"].apply(unify_transmission)
    df["Palivo"] = df["Palivo"].apply(check_palivo)

    # 5. Odstranění řádků, kde některá kritická hodnota chybí
    mandatory = ["Značka", "Model", "Rok", "Cena", "Palivo", "Převodovka", "Výkon (kW)"]
    df.dropna(subset=mandatory, inplace=True)

    # 6. Speciální filtrování pro BMW (odstraní řádky, kde je Model přesně "Rada")
    df = df[~((df["Značka"] == "BMW") & (df["Model"].str.lower() == "rada"))]

    # 7. Odstranění sloupce "Zdroj", pokud existuje
    if "Zdroj" in df.columns:
        df.drop(columns=["Zdroj"], inplace=True)

    # 8. Přidání sloupce "Stari" = (aktuální rok - Rok) a odstranění sloupce "Rok"
    current_year = datetime.now().year
    df["Stari"] = current_year - df["Rok"]
    df.drop(columns=["Rok"], inplace=True)

    # 9. Odstranění diakritiky a pomlček ze všech textových sloupců
    text_columns = ["Značka", "Model", "Palivo", "Převodovka"]
    for col in text_columns:
        df[col] = df[col].apply(lambda x: remove_hyphens(remove_diacritics(x)) if isinstance(x, str) else x)

    # Uložení vyčištěného datasetu
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df

# Příklad použití:
cleaned_df = clean_dataset(
    r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\merged_auta.csv",
    r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_dataset.csv"
)
print("Čištění dokončeno.")
print(cleaned_df.head())
print(cleaned_df["Značka"].value_counts())
