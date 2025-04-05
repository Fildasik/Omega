import pandas as pd

# Načtení datasetu
df = pd.read_csv(r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_balanced_dataset.csv", encoding="utf-8")

# Převedeme sloupec 'Cena' na numerický typ
df["Cena"] = pd.to_numeric(df["Cena"], errors="coerce")

# Vyfiltrujeme záznamy s cenou mezi 30 000 a 2 500 000 Kč
df = df[(df["Cena"] >= 30000) & (df["Cena"] <= 2500000)]

# Vytvoření binů:
# První interval: 30 000 - 100 000
# Poté každý interval o šířce 100 000 až do 2 500 000
bins = [30000, 100000] + list(range(200000, 2500000 + 100000, 100000))

# Vytvoření popisků pro jednotlivé intervaly
labels = []
for i in range(len(bins) - 1):
    # Formátování s mezerou jako oddělovačem tisíců
    label = f"{bins[i]:,} - {bins[i+1]:,}".replace(',', ' ')
    labels.append(label)

# Rozřazení záznamů do vytvořených intervalů
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
