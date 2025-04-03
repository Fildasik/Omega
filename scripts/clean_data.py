import pandas as pd
import unicodedata
import re


def remove_diacritics(s: str) -> str:
    """Odstraní diakritiku ze zadaného řetězce."""
    nfkd_form = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd_form if not unicodedata.combining(c))


def unify_brand(brand: str) -> str:
    """
    Sjednotí varianty značek podle prefixů.
    Například:
      "auDi" → "Audi"
      "BMW", "Bmw" → "BMW"
      "mercedes BeNz" → "Mercedes-Benz"
      "Skoda", "Škoda" → "Škoda"
    """
    if pd.isna(brand):
        return None
    b = remove_diacritics(str(brand).strip().lower())

    if b.startswith("aud"):
        standard = "Audi"
    elif b.startswith("bmw"):
        standard = "BMW"
    elif b.startswith("cit"):
        standard = "Citroën"
    elif b.startswith("dod"):
        standard = "Dodge"
    elif b.startswith("for"):
        standard = "Ford"
    elif b.startswith("hyu"):
        standard = "Hyundai"
    elif b.startswith("jee"):
        standard = "Jeep"
    elif b.startswith("kia"):
        standard = "Kia"
    elif b.startswith("maz"):
        standard = "Mazda"
    elif b.startswith("mer"):
        standard = "Mercedes-Benz"
    elif b.startswith("nis"):
        standard = "Nissan"
    elif b.startswith("ope"):
        standard = "Opel"
    elif b.startswith("peu"):
        standard = "Peugeot"
    elif b.startswith("por"):
        standard = "Porsche"
    elif b.startswith("ren"):
        standard = "Renault"
    elif b.startswith("sko"):
        standard = "Škoda"
    elif b.startswith("toy"):
        standard = "Toyota"
    elif b.startswith("volk"):
        standard = "Volkswagen"
    elif b.startswith("volv"):
        standard = "Volvo"
    else:
        standard = str(brand).strip().title()

    # Ověříme, že standard obsahuje jen písmena (bez diakritiky a mezer)
    b_clean = remove_diacritics(standard).replace(" ", "").lower()
    if not re.fullmatch(r"[a-z]+", b_clean):
        return None
    return standard


def unify_model(model: str) -> str:
    """
    Sjednotí model.
    Pokud model obsahuje "rada" (v jakékoli podobě: RADA, Řada, rada), vrátí "Rada".
    Jinak převede na title case.
    """
    if pd.isna(model):
        return None
    m = remove_diacritics(model.strip().lower())
    if m == "rada":
        return "Rada"
    return model.strip().title()


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
    ani "hyb" (Hybridni), ani "ele" (Elektro) – v libovolné podobě,
    vrátí None (řádek se odstraní).
    Pokud obsahuje:
      - "benz" → vrátí "Benzin"
      - "naf" → vrátí "Nafta"
      - "hyb" → vrátí "Hybridni"
      - "ele" → vrátí "Elektro"
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
      - filtruje data: Cena mezi 30 000 a 8 000 000, Rok mezi 1970 a 2025,
      - standardizuje sloupce "Značka", "Model", "Palivo" a "Převodovka",
      - odstraní řádky, kde Palivo neobsahuje ani "Benzin", "Nafta", "Hybridni" nebo "Elektro",
      - odstraní řádky s chybějícími kritickými hodnotami,
      - speciálně filtruje data pro BMW (odstraní řádky, kde je Značka "BMW" a Model je přesně "Rada"),
      - smaže sloupec "Zdroj", pokud existuje,
      - přidá sloupec "Stari" jako (2025 - Rok) a poté odstraní sloupec "Rok",
      - nakonec odstraní diakritiku ze všech textových sloupců, takže výsledný CSV bude bez diakritiky.
    """
    df = pd.read_csv(file_path, encoding="utf-8")

    # 1. Odstranění duplicit a úplně prázdných řádků
    df.drop_duplicates(inplace=True)
    df.dropna(how="all", inplace=True)

    # 2. Konverze číselných sloupců
    numeric_cols = ["Rok", "Najeté km", "Cena", "Výkon (kW)"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3. Filtrování extrémních hodnot: Cena 30k-8M, Rok 1970-2025
    df = df[df["Cena"].between(10000, 4000000)]
    df = df[df["Rok"].between(1970, 2025)]

    # 4. Standardizace textových sloupců
    df["Značka"] = df["Značka"].apply(unify_brand)
    df["Model"] = df["Model"].apply(unify_model)
    df["Převodovka"] = df["Převodovka"].apply(unify_transmission)
    df["Palivo"] = df["Palivo"].apply(check_palivo)

    # 5. Odstranění řádků, kde některá kritická hodnota chybí
    mandatory = ["Značka", "Model", "Rok", "Cena", "Palivo", "Převodovka", "Výkon (kW)"]
    df.dropna(subset=mandatory, inplace=True)

    # 6. Speciální filtr pro BMW: Pokud je Značka "BMW" a Model je přesně "Rada", řádek smažeme
    df = df[~((df["Značka"] == "BMW") & (df["Model"].str.fullmatch(r"Rada", case=False)))]

    # 7. Odstranění sloupce "Zdroj", pokud existuje
    if "Zdroj" in df.columns:
        df.drop(columns=["Zdroj"], inplace=True)

    # 8. Přidání sloupce "Stari" = 2025 - Rok a odstranění sloupce "Rok"
    current_year = 2025
    df["Stari"] = current_year - df["Rok"]
    df.drop(columns=["Rok"], inplace=True)

    # 9. Odstranění diakritiky ze všech textových sloupců (výstup bude čistě bez diakritiky)
    text_columns = ["Značka", "Model", "Palivo", "Převodovka"]
    for col in text_columns:
        df[col] = df[col].apply(lambda x: remove_diacritics(x) if isinstance(x, str) else x)

    # Uložení vyčištěného datasetu
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df


# Příklad použití:
cleaned_df = clean_dataset(
    r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\merged_auta_2.csv",
    r"/datasets/final_dataset_2.csv"
)
print("Čištění dokončeno.")
print(cleaned_df.head())
print(cleaned_df["Značka"].value_counts())
