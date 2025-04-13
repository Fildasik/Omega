import pandas as pd

# Nastav cesty k souborům – uprav dle svého prostředí
input_csv = r'C:\Users\Asus\PV\OMEGA\OmegaCars\raw_data\auta_sauto.csv'
output_csv = r'C:\Users\Asus\PV\OMEGA\OmegaCars\raw_data\auta_sauto_cleaned.csv'

# Načtení CSV souboru
df = pd.read_csv(input_csv, encoding='utf-8-sig')
print("Dataset načten, počet záznamů:", len(df))

# Zkontrolujeme, zda existuje sloupec "Objem (cm³)"
if 'Objem (cm³)' in df.columns:
    # Vytvoříme nový sloupec "Objem (l)" převodem z cm³ na litry a zaokrouhlením na 1 desetinné místo
    df['Objem (l)'] = (df['Objem (cm³)'].astype(float) / 1000).round(1)
    # Odstraníme původní sloupec "Objem (cm³)"
    df.drop(columns=['Objem (cm³)'], inplace=True)
    print("Převod byl úspěšný. Ukázka nového sloupce:")
    print(df[['Značka', 'Model', 'Objem (l)']].head())
else:
    print("Sloupec 'Objem (cm³)' nebyl nalezen. Zkontroluj název sloupce.")

# Přeuspořádáme sloupce tak, aby "Objem (l)" byl hned za "Model"
new_order = ["Značka", "Model", "Objem (l)", "Rok", "Najeté km", "Cena", "Palivo", "Převodovka", "Výkon (kW)"]
df = df[new_order]

# Uložíme aktualizovaný dataset do nového CSV souboru
df.to_csv(output_csv, index=False, encoding='utf-8-sig')
print(f"Aktualizovaný CSV soubor byl uložen jako: {output_csv}")
