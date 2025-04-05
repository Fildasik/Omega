import pandas as pd

# Načtení datasetu (uprav cestu dle potřeby)
df = pd.read_csv(r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_balanced_dataset.csv", encoding="utf-8-sig")

# Ujistíme se, že sloupec 'Cena' je numerický
df["Cena"] = pd.to_numeric(df["Cena"], errors="coerce")

# Skupina podle značky
grouped = df.groupby("Značka")

# Pro každou značku spočítáme celkový počet modelových řádků a průměrnou cenu
for brand, group in grouped:
    total_models = group["Model"].count()
    avg_price = group["Cena"].mean()
    print(f"Značka: {brand} má dohromady {total_models} záznamů a průměrná cena je {avg_price:,.0f} Kč.")
