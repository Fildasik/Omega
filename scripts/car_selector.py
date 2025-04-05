import pandas as pd
import re

# 1) Načtení CSV datasetu – uprav cestu dle svého prostředí
df = pd.read_csv(r'/datasets/final_dataset.csv', encoding="utf-8-sig")
print("Dataset načten, počet záznamů:", len(df))
print("Sloupce datasetu:", df.columns.tolist())

# 2) Zjištění unikátních značek
brands = df['Značka'].unique()
print("Unikátní značky:", brands)

# 3) Definujeme cílový počet záznamů, který chceme získat (např. 5000 nebo 3000)
target_count = 10000  # změň na 3000, pokud chceš méně záznamů

# Určíme, kolik záznamů chceme rovnoměrně získat z každé značky
n_brand = max(1, target_count // len(brands))
print("Cílový počet záznamů na značku:", n_brand)

selected_dfs = []

# Funkce pro vyčištění ceny (odstraní vše, co není číslice) a převede na int
def clean_price_to_int(price):
    if pd.isnull(price):
        return None
    price_clean = re.sub(r"[^\d]", "", str(price))
    try:
        return int(price_clean)  # Převedeme rovnou na int
    except:
        return None

# Ujistíme se, že sloupec "Cena" je celé číslo
df["Cena"] = df["Cena"].apply(clean_price_to_int)

# 4) Pro každou značku vybereme vzorky
for brand in brands:
    # Vybereme všechny záznamy dané značky
    brand_data = df[df['Značka'] == brand].copy()

    # Pokud je pro danou značku málo záznamů, vezmeme je všechny
    if len(brand_data) <= n_brand:
        selected_dfs.append(brand_data)
        continue

    # Rozdělíme data této značky do 5 cenových kvantilů, abychom vyvážili cenové rozpětí
    try:
        brand_data['price_bin'] = pd.qcut(brand_data['Cena'], q=5, duplicates='drop')
    except Exception as e:
        print(f"Chyba při vytváření kvantilů pro značku {brand}: {e}")
        brand_data['price_bin'] = pd.cut(brand_data['Cena'], bins=5)

    bins = brand_data['price_bin'].unique()
    samples_per_bin = max(1, n_brand // len(bins))
    sampled_bins = []

    # Z každého cenového kvantilu vybereme náhodně vzorek
    for b in bins:
        bin_data = brand_data[brand_data['price_bin'] == b]
        n_to_sample = min(samples_per_bin, len(bin_data))
        sampled_bin = bin_data.sample(n=n_to_sample, random_state=42)
        sampled_bins.append(sampled_bin)

    brand_sample = pd.concat(sampled_bins)
    selected_dfs.append(brand_sample)

# Sjednotíme výběry ze všech značek
result = pd.concat(selected_dfs)

# Pokud celkový počet výsledných záznamů je menší než target_count, doplníme z celého datasetu (rovnoměrně podle ceny)
if len(result) < target_count:
    remaining = df.drop(result.index)
    remaining = remaining.sort_values('Cena', ascending=True)
    to_add = target_count - len(result)
    result = pd.concat([result, remaining.head(to_add)])

# Odstraníme pomocný sloupec s cenovými kvantily, pokud existuje
if 'price_bin' in result.columns:
    result.drop(columns=['price_bin'], inplace=True)

# Uložíme výsledný DataFrame do nového CSV
output_path = r'C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_dataset_2.csv'
result.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Hotovo! Vybraná data jsou uložena v '{output_path}'.")
print("Celkový počet vybraných záznamů:", len(result))
