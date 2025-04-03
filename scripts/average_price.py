import pandas as pd

# Nastav cestu k souboru, případně uprav dle umístění
csv_path = r"/datasets/final_dataset_2.csv"

# Načtení datasetu
df = pd.read_csv(csv_path, encoding="utf-8")

# Zkontrolujeme, zda sloupec "Cena" existuje a obsahuje čísla
if "Cena" in df.columns:
    # Převedeme sloupec Cena na numerický typ, pokud již není
    df["Cena"] = pd.to_numeric(df["Cena"], errors="coerce")

    # Spočítáme průměrnou cenu aut
    average_price = df["Cena"].mean()

    # Vypíšeme výsledky
    print("Průměrná cena aut:", average_price)

    # Pro zajímavost i další statistiky:
    print("\nZákladní statistiky ceny aut:")
    print(df["Cena"].describe())
else:
    print("Sloupec 'Cena' nebyl nalezen v datasetu.")
