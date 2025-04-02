import pandas as pd
import glob
import os

# Cesta k adresáři, kde jsou uložené CSV soubory
path = r"C:\Users\filip\OMEGA\OmegaAuta-main\raw_data"

# Hledáme všechny CSV soubory, jejichž název začíná "auta_"
csv_files = glob.glob(os.path.join(path, "auta_*.csv"))

if not csv_files:
    print("Nenalezeny žádné soubory odpovídající vzoru 'auta_*.csv'. Zkontrolujte názvy souborů a cestu.")
    exit()

dfs = []
for file in csv_files:
    try:
        df = pd.read_csv(file, encoding="utf-8-sig")
    except Exception as e:
        print(f"Chyba při načítání souboru {file}: {e}")
        continue

    if "Cena" in df.columns:
        # Převedeme sloupec 'Cena' na číselný typ, pokud je to nutné
        df["Cena"] = pd.to_numeric(df["Cena"], errors="coerce")
    else:
        print(f"Soubor {file} neobsahuje sloupec 'Cena'. Přeskakuji.")
        continue

    # Přidáme informaci o zdroji na základě názvu souboru
    if "autoesa" in file.lower():
        df["Zdroj"] = "Autoesa"
    elif "sauto" in file.lower():
        df["Zdroj"] = "Sauto"
    else:
        df["Zdroj"] = "Neznámý"

    dfs.append(df)

if not dfs:
    print("Nebyly načteny žádné validní datové sady.")
    exit()

# Sloučíme všechny DataFrame
merged_df = pd.concat(dfs, ignore_index=True)

# Seřadíme výsledný DataFrame podle ceny
merged_df = merged_df.sort_values(by="Cena")

# Uložíme sloučený dataset do nového CSV souboru ve stejném adresáři
output_path = os.path.join(path, r"C:\Users\filip\OMEGA\OmegaAuta-main\datasets\merged_auta.csv")
merged_df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Sloučený dataset byl uložen do {os.path.abspath(output_path)}")
