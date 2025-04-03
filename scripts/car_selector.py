import pandas as pd

# 1) Načtení CSV
df = pd.read_csv(r'C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_dataset_2.csv', encoding="utf-8")

# 2) Zjištění sloupců – pro kontrolu
print("Sloupce datasetu:", df.columns.tolist())

# 3) Zjistíme unikátní značky
brands = df['Značka'].unique()

# 4) Definujeme cílový počet záznamů, který chceme získat (celkem)
target_count = 5000

# 5) Určíme, kolik záznamů chceme získat z každé značky (rovnoměrně)
n_brand = max(1, target_count // len(brands))

selected_dfs = []

for brand in brands:
    # Vybereme všechny záznamy dané značky
    brand_data = df[df['Značka'] == brand].copy()

    # Pokud je pro danou značku málo záznamů, vezmeme jich všechny
    if len(brand_data) <= n_brand:
        selected_dfs.append(brand_data)
        continue

    # Rozdělíme data této značky do 5 cenových kvantilů (abychom vyvážili cenové rozpětí)
    try:
        brand_data['price_bin'] = pd.qcut(brand_data['Cena'], q=5, duplicates='drop')
    except Exception as e:
        print(f"Chyba při vytváření kvantilů pro značku {brand}: {e}")
        # Pokud qcut selže, použijeme jednoduché pd.cut s 5 intervaly
        brand_data['price_bin'] = pd.cut(brand_data['Cena'], bins=5)

    bins = brand_data['price_bin'].unique()
    samples_per_bin = max(1, n_brand // len(bins))
    sampled_bins = []

    # Z každého cenového kvantilu vybereme náhodně vzorek
    for b in bins:
        bin_data = brand_data[brand_data['price_bin'] == b]
        # Pokud je v kvantilu méně záznamů, vezmeme jich všechny
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
output_path = r'C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_dataset_2.1.csv'
result.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Hotovo! Vybraná data jsou uložena v '{output_path}'.")
