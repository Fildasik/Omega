import pandas as pd

# Načtení datasetu
df = pd.read_csv(r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_dataset.csv", encoding="utf-8-sig")

# Celkový počet aut
total = len(df)
print("Celkový počet aut:", total)

# Definice cenových intervalů (bins) a jejich popisků (labels)
bins = [30000, 100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000,
        1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000, 1700000, 1800000,
        1900000, 2000000, 2100000, 2200000, 2300000, 2400000, 2500000]

labels = [
    "30 000 - 100 000",
    "100 000 - 200 000",
    "200 000 - 300 000",
    "300 000 - 400 000",
    "400 000 - 500 000",
    "500 000 - 600 000",
    "600 000 - 700 000",
    "700 000 - 800 000",
    "800 000 - 900 000",
    "900 000 - 1 000 000",
    "1 000 000 - 1 100 000",
    "1 100 000 - 1 200 000",
    "1 200 000 - 1 300 000",
    "1 300 000 - 1 400 000",
    "1 400 000 - 1 500 000",
    "1 500 000 - 1 600 000",
    "1 600 000 - 1 700 000",
    "1 700 000 - 1 800 000",
    "1 800 000 - 1 900 000",
    "1 900 000 - 2 000 000",
    "2 000 000 - 2 100 000",
    "2 100 000 - 2 200 000",
    "2 200 000 - 2 300 000",
    "2 300 000 - 2 400 000",
    "2 400 000 - 2 500 000"
]

# Rozřazení záznamů do cenových intervalů (pro účely rebalance)
df["price_range"] = pd.cut(df["Cena"], bins=bins, labels=labels, right=False)

# Cílový počet záznamů pro každý interval = 7 % z celkového počtu aut
target_count = int(total * 0.07)
print("Cílový počet záznamů na interval (7%):", target_count)

# Přebalancování datasetu: pro každý interval, pokud je počet záznamů větší než target_count, provedeme undersampling
balanced_groups = []
for interval, group in df.groupby("price_range"):
    print(f"Interval {interval}: původně {len(group)} záznamů")
    if len(group) > target_count:
        balanced_group = group.sample(n=target_count, random_state=42)
        print(f"  - Oříznuto na {target_count} záznamů")
    else:
        balanced_group = group
        print("  - Zachováno, počet záznamů je pod cílovou hodnotou")
    balanced_groups.append(balanced_group)

# Sjednocení všech vyvážených skupin
balanced_df = pd.concat(balanced_groups)
print("Nový celkový počet záznamů po vyvážení:", len(balanced_df))

# (Volitelné) Zobrazení nové distribuce podle intervalů
new_distribution = balanced_df["price_range"].value_counts(sort=False)
print("\nNová distribuce záznamů podle cenových intervalů:")
print(new_distribution)

# Odstranění pomocného sloupce 'price_range'
balanced_df = balanced_df.drop(columns=["price_range"])

# Uložení vyváženého datasetu do CSV souboru
output_csv = r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_balanced_dataset.csv"
balanced_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
print(f"Vyvážený dataset byl uložen do souboru: {output_csv}")
