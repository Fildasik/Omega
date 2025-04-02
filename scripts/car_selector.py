import pandas as pd

# 1) Načtení CSV
df = pd.read_csv(r'C:\Users\filip\OMEGA\OmegaAuta-main\datasets\auta_cleaned.csv')

# 2) Zjištění sloupců - zkontroluj, jak se jmenuje sloupec se značkou a cenou
print(df.columns)

# 3) Zjistíme unikátní značky
brands = df['Značka'].unique()

# 4) Definujeme cílový počet
target_count = 3000

# 5) Určíme, kolik řádků vybrat z každé značky (pro začátek rovnoměrně)
n_brand = max(1, target_count // len(brands))

selected_dfs = []

for brand in brands:
    # Vytáhneme všechny záznamy dané značky
    brand_data = df[df['Značka'] == brand]
    # Seřadíme je podle ceny vzestupně
    brand_data = brand_data.sort_values('Cena', ascending=True)
    # Vezmeme n_brand "nejlevnějších" (nebo prostě prvních dle řazení)
    selected_dfs.append(brand_data.head(n_brand))

# Sjednotíme do jednoho DataFrame
result = pd.concat(selected_dfs)

# Pokud jsi vybral/a méně než 3000 (třeba když některé značky měly málo záznamů),
# doplníme do 3000 záznamů podle ceny z celého datasetu:
if len(result) < target_count:
    # Odstraníme z df řádky, které už jsou ve result
    remaining = df.drop(result.index)
    # Seřadíme zbylé řádky podle ceny
    remaining = remaining.sort_values('Cena', ascending=True)
    # Přidáme tolik, kolik chybí do 3000
    to_add = target_count - len(result)
    result = pd.concat([result, remaining.head(to_add)])

# 6) Uložíme do nového CSV
result.to_csv(r'C:\Users\filip\OMEGA\OmegaAuta-main\datasets\auta_cleaned_3000.csv', index=False)

print("Hotovo! Vybraná data jsou uložena v 'auta_cleaned_3000.csv'.")
