import pandas as pd

# Načtení datasetu
df = pd.read_csv(r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_dataset_2.1.csv", encoding="utf-8")

# Ujistíme se, že sloupec 'Cena' je numerický
df["Cena"] = pd.to_numeric(df["Cena"], errors="coerce")

# Vyfiltrujeme záznamy s cenou mezi 30 000 a 2 000 000
df = df[(df["Cena"] >= 30000) & (df["Cena"] <= 2000000)]

# Definice hranic cenových intervalů
bins = [30000, 200000, 400000, 600000, 800000, 1000000, 1200000, 1400000, 1600000, 1800000, 2000000]
labels = [
    "30 000 - 200 000",
    "200 000 - 400 000",
    "400 000 - 600 000",
    "600 000 - 800 000",
    "800 000 - 1 000 000",
    "1 000 000 - 1 200 000",
    "1 200 000 - 1 400 000",
    "1 400 000 - 1 600 000",
    "1 600 000 - 1 800 000",
    "1 800 000 - 2 000 000"
]

# Rozřazení záznamů do definovaných intervalů
df["price_range"] = pd.cut(df["Cena"], bins=bins, labels=labels, right=False)

# Spočítání záznamů v každém intervalu
bin_counts = df["price_range"].value_counts().sort_index()

total = len(df)
print(f"Celkový počet aut: {total}\n")

# Výpis procentuálního zastoupení pro každý interval
for label in labels:
    count = bin_counts.get(label, 0)
    percentage = (count / total) * 100
    print(f"{label}: {percentage:.2f}% ({count} aut)")
