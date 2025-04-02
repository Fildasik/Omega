import pandas as pd

# Načtení vyčištěného datasetu
df = pd.read_csv(r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\auta_cleaned.csv", encoding="utf-8")

# Přejmenování sloupce "Značka" na "znacka", pokud existuje
if "Značka" in df.columns:
    df.rename(columns={"Značka": "znacka"}, inplace=True)

# Ověření, že sloupec 'znacka' existuje a výpis počtu aut podle značky
if 'znacka' in df.columns:
    # Skupinování podle značky a spočítání počtu záznamů
    brand_counts = df.groupby('znacka').size().reset_index(name='pocet')

    # Seřazení podle názvu značky
    brand_counts.sort_values(by='znacka', inplace=True)

    # Výpis výsledků
    print("Značka auta a počet aut:")
    for _, row in brand_counts.iterrows():
        print(f"{row['znacka']}: {row['pocet']}")
else:
    print("Sloupec 'znacka' (nebo 'Značka') nebyl nalezen v datasetu.")
