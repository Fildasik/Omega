import pandas as pd
import os

# Cesty ke vstupním CSV souborům
input_csv1 = r"C:\Users\Asus\PV\OMEGA\OmegaCars\raw_data\auta_autoesa.csv"
input_csv2 = r"C:\Users\Asus\PV\OMEGA\OmegaCars\raw_data\auta_sauto_cleaned.csv"

# Cesta k výstupnímu CSV souboru
output_csv = r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\merged_auta.csv"

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
