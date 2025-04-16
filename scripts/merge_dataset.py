import pandas as pd
import os

# Základní adresář – cesta tam, kde se tento skript nachází
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cesty ke vstupním CSV souborům (v adresáři raw_data)
input_csv1 = os.path.join(base_dir, "raw_data", "auta_autoesa.csv")
input_csv2 = os.path.join(base_dir, "raw_data", "auta_sauto_cleaned.csv")

# Cesta k výstupnímu CSV souboru (v adresáři datasets)
output_csv = os.path.join(base_dir, "datasets", "merged_dataset.csv")

# Ověření existence vstupních souborů
if not os.path.exists(input_csv1):
    print("Soubor nebyl nalezen:", input_csv1)
    exit()
if not os.path.exists(input_csv2):
    print("Soubor nebyl nalezen:", input_csv2)
    exit()

# Načtení CSV souborů
df1 = pd.read_csv(input_csv1, encoding="utf-8-sig")
df2 = pd.read_csv(input_csv2, encoding="utf-8-sig")
print("Počet záznamů v prvním souboru:", len(df1))
print("Počet záznamů v druhém souboru:", len(df2))

# Přidání sloupce "Zdroj" pro identifikaci původu dat
df1["Zdroj"] = "Autoesa"
df2["Zdroj"] = "Sauto"

# Sloučení obou DataFrame
merged_df = pd.concat([df1, df2], ignore_index=True)

# Seřazení výsledného DataFrame podle sloupce "Cena"
merged_df = merged_df.sort_values(by="Cena")

# Uložení sloučeného datasetu do výstupního CSV souboru
merged_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
print("Sloučený dataset byl uložen do:", os.path.abspath(output_csv))
