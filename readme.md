# Projekt: Předpověď cen automobilů – pomocí regrese

Autor: Filip Novotný  
Kontakt: filipnovotny0902@gmail.com  
Datum: 5. dubna 2025

## Popis

Tato školní aplikace predikuje cenu ojetého automobilu na základě dat získaných pomocí web scrapingu. Uživatel zadává parametry jako značka, model, objem, najeté km, palivo, převodovka, výkon a stáří vozu. Výstupem je předpokládaná cena vozu.

Aplikace využívá modely strojového učení (Decision Tree, Gradient Boosting, Random Forest), obsahuje grafické uživatelské rozhraní (`Tkinter`) a nástroje pro zpracování dat.

## Instalace a spuštění

1. Stáhněte a rozbalte projekt.
2. Otevřete terminál v hlavní složce.
3. Spusťte instalaci knihoven: pip install -r requirements.txt
4. Upravte `.env` soubor (pokud používáte scraper): BRAND=Skoda NUM_LISTINGS=200 MAX_PAGES=20 ...
5. Spusťte aplikaci: python src/app.py


## Struktura projektu

- `/datasets` – datové soubory
- `/models` – trénované modely
- `/src` – zdrojové kódy (včetně `app.py`)
- `requirements.txt` – potřebné knihovny
- `.env` – konfigurace pro scraping
- `README.md` – popis projektu

## Požadavky

- Python 3.8+
- pandas, numpy, scikit-learn, joblib, tkinter, requests, beautifulsoup4








