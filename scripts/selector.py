import pandas as pd

# Cesta k původnímu datasetu (uprav podle umístění tvého souboru)
input_csv = r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_dataset.csv"

# Načtení datasetu
df = pd.read_csv(input_csv, encoding="utf-8-sig")

# Nastav maximální počet záznamů na skupinu (například 50)
n = 4

# Vytvoříme vyvážený dataset:
# Pro každou kombinaci ["Značka", "Model"] vybere se min(n, počet záznamů v dané skupině)
balanced_df = df.groupby(["Značka", "Model"], group_keys=False).apply(lambda x: x.sample(min(len(x), n)))

# Uložíme nový vyvážený dataset do CSV (cestu uprav podle potřeby)
output_csv = r"C:\Users\Asus\PV\OMEGA\OmegaCars\datasets\final_balanced_dataset.csv"
balanced_df.to_csv(output_csv, index=False, encoding="utf-8-sig")

# Vytiskneme přehled, kolik záznamů má nový dataset
print("Balanced dataset shape:", balanced_df.shape)
