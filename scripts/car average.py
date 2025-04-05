import pandas as pd
import re

# Načtení datasetu – uprav cestu k souboru podle potřeby
df = pd.read_csv(r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_dataset.csv", encoding="utf-8-sig")

# Funkce pro vyčištění ceny, odstranění textu a převod na číslo
def clean_price(price):
    if pd.isnull(price):
        return None
    # Odstraní vše, co není číslice (např. Kč, mezery, oddělovače)
    price_clean = re.sub(r"[^\d]", "", str(price))
    try:
        return float(price_clean)
    except:
        return None

# Vyčistíme sloupec "Cena" a uložíme do nového sloupce "Cena_clean"
df["Cena_clean"] = df["Cena"].apply(clean_price)

# Skupinujeme podle značky
grouped = df.groupby("Značka")

# Pro každou značku vypíšeme počet unikátních modelů a průměrnou cenu
for brand, group in grouped:
    unique_models = group["Model"].nunique()
    avg_price = group["Cena_clean"].mean()
    print(f"Značka: {brand} má {unique_models} unikátních modelů a průměrná cena je {avg_price:,.0f} Kč.")
