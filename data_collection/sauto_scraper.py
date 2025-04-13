import os
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

pd.set_option('display.max_colwidth', None)

# Načtení konfigurace z .env souboru
load_dotenv()


def validate_config(BRAND, NUM_LISTINGS, MAX_PAGES, MAX_WORKERS, MIN_PRICE, MAX_PRICE):
    errors = []
    if MIN_PRICE is not None and MIN_PRICE < 0:
        errors.append("MIN_PRICE nesmí být záporná.")
    if NUM_LISTINGS <= 0:
        errors.append("NUM_LISTINGS musí být kladné číslo.")
    if MAX_PAGES <= 0:
        errors.append("MAX_PAGES musí být kladné číslo.")
    if MAX_WORKERS <= 0:
        errors.append("MAX_WORKERS musí být kladné číslo.")
    if MIN_PRICE is not None and MAX_PRICE is not None and MIN_PRICE >= MAX_PRICE:
        errors.append("MIN_PRICE musí být menší než MAX_PRICE.")
    if errors:
        raise ValueError(" ".join(errors))


# Načtení konfiguračních proměnných z .env
BRAND = os.getenv("BRAND")
NUM_LISTINGS = int(os.getenv("NUM_LISTINGS", 50))
MAX_PAGES = int(os.getenv("MAX_PAGES", 5))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 10))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./raw_data")
MIN_PRICE = os.getenv("MIN_PRICE")
MAX_PRICE = os.getenv("MAX_PRICE")

MIN_PRICE = int(MIN_PRICE) if MIN_PRICE is not None else None
MAX_PRICE = int(MAX_PRICE) if MAX_PRICE is not None else None

try:
    validate_config(BRAND, NUM_LISTINGS, MAX_PAGES, MAX_WORKERS, MIN_PRICE, MAX_PRICE)
except ValueError as ve:
    print("Konfigurační chyba:", ve)
    exit(1)

# Sestavení základní URL
base_url = "https://www.sauto.cz/inzerce/osobni"
if BRAND:
    base_url += f"/{BRAND.lower()}"
base_url += "?stav=nove%2Cojete"
if MIN_PRICE is not None:
    base_url += f"&cena-od={MIN_PRICE}"
if MAX_PRICE is not None:
    base_url += f"&cena-do={MAX_PRICE}"


# Fallback mechanismus: ověří, zda URL pro zadanou značku vrací očekávaný obsah; pokud ne, použije základní URL
def get_validated_url(base_url, brand):
    test_url = f"{base_url}/{brand}?stav=nove%2Cojete"
    try:
        response = requests.get(test_url, timeout=10)
        response.raise_for_status()
        if "inzerát" not in response.text.lower():
            print(f"Zadaná značka '{brand}' nevrací očekávaný obsah, používá se fallback URL.")
            return base_url
        return test_url
    except Exception as e:
        print(f"Chyba při ověřování URL pro značku '{brand}': {e}")
        return base_url


validated_url = get_validated_url("https://www.sauto.cz/inzerce/osobni", BRAND)
if validated_url != base_url:
    base_url = validated_url

# Globální session pro Sauto
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def get_listing_links(page_url: str) -> list:
    """Získá odkazy na detail inzerátů z jedné stránky Sauto."""
    try:
        resp = session.get(page_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Chyba při načítání listingu {page_url}: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()
    items = soup.find_all("a", class_="sds-surface sds-surface--clickable sds-surface--00 c-item__link")
    for a in items:
        href = a.get("href")
        if href:
            full_url = href if href.startswith("http") else "https://www.sauto.cz" + href
            links.add(full_url)
    return list(links)


def fallback_brand_model(url: str) -> tuple:
    """Z fallbacku URL získá značku a model."""
    try:
        after = url.split("/detail/")[1]
        parts = after.split("/")
        if len(parts) >= 2:
            raw_brand = parts[0]
            raw_model = parts[1]
            brand = raw_brand.replace("-", " ").title()
            model = raw_model.replace("-", " ").title()
            return brand, model
        return ("Nezjištěno", "Nezjištěno")
    except:
        return ("Nezjištěno", "Nezjištěno")


def parse_sauto_detail(url: str) -> dict or None:
    """
    Načte detail inzerátu ze Sauto a extrahuje data.
    Extrahuje: Značka, Model, Objem (cm³), Rok, Najeté km, Cena, Palivo, Převodovka, Výkon (kW).
    """
    fb_brand, fb_model = fallback_brand_model(url)
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"Chyba při načítání detailu {url}: {e}")
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    brand = fb_brand
    model = fb_model
    year_val = "Nezjištěno"
    mileage_val = "Nezjištěno"
    price_val = "Nezjištěno"
    fuel_val = "Nezjištěno"
    gearbox_val = "Nezjištěno"
    power_kw = "Nezjištěno"
    engine_volume = "Nezjištěno"

    subinfo = soup.find("span", class_="c-a-basic-info__subtitle-info")
    if subinfo:
        txt = subinfo.get_text(" ", strip=True)
        txt = txt.replace("Ojeté", "").replace("Nové", "").strip()
        parts = txt.split(",")
        for part in parts:
            p_clean = part.strip()
            if "/" in p_clean and year_val == "Nezjištěno":
                splitted = p_clean.split("/")
                if len(splitted) == 2:
                    try:
                        rok = int(splitted[1])
                        if 1900 < rok < 2100:
                            year_val = str(rok)
                    except:
                        pass
            elif p_clean.isdigit() and year_val == "Nezjištěno":
                val = int(p_clean)
                if 1900 < val < 2100:
                    year_val = str(val)
            elif "km" in p_clean.lower() and mileage_val == "Nezjištěno":
                digits = re.sub(r"[^\d]", "", p_clean)
                if digits:
                    mileage_val = digits
    c_div = soup.find("div", class_="c-a-basic-info__price")
    if c_div:
        pr_txt = c_div.get_text(strip=True)
        pr_txt = pr_txt.replace("Kč", "").replace("\xa0", "").replace(" ", "").strip()
        if pr_txt:
            price_val = pr_txt
    else:
        c_span = soup.find("span", class_="c-basic-info__price")
        if c_span:
            pr_txt2 = c_span.get_text(strip=True)
            pr_txt2 = pr_txt2.replace("Kč", "").replace("\xa0", "").replace(" ", "").strip()
            if pr_txt2:
                price_val = pr_txt2
    li_elems = soup.find_all("li", class_=re.compile("c-car-properties__tile|c-car-otherProperties__tile"))
    for li in li_elems:
        lbl_div = li.find("div", class_=re.compile("tile-label"))
        val_div = li.find("div", class_=re.compile("tile-value"))
        if not lbl_div or not val_div:
            continue
        lbl = lbl_div.get_text(strip=True)
        val = val_div.get_text(strip=True)
        if lbl == "Palivo":
            fuel_val = val
        elif lbl == "Převodovka":
            gearbox_val = val
        elif lbl == "Výkon":
            digits = re.sub(r"[^\d]", "", val)
            if digits:
                power_kw = digits
        elif lbl == "Objem":
            match = re.search(r'(\d[\d\s]*)(?=\s*ccm)', val.replace('\xa0', ' '))
            if match:
                digits = re.sub(r'\s+', '', match.group(1))
                try:
                    volume_cm3 = int(digits)
                    engine_volume = volume_cm3
                except:
                    engine_volume = "Nezjištěno"
            else:
                engine_volume = "Nezjištěno"
    mandatory = [brand, model, year_val, mileage_val, price_val, fuel_val, gearbox_val, power_kw, engine_volume]
    if any(x == "Nezjištěno" for x in mandatory):
        return None
    return {
        "URL": url,
        "Značka": brand,
        "Model": model,
        "Objem (cm³)": engine_volume,
        "Rok": year_val,
        "Najeté km": mileage_val,
        "Cena": price_val,
        "Palivo": fuel_val,
        "Převodovka": gearbox_val,
        "Výkon (kW)": power_kw
    }


def scrape_sauto_one_page(page_url: str, max_workers: int = 10, seen_set=None):
    if seen_set is None:
        seen_set = set()
    links = get_listing_links(page_url)
    print(f"Na stránce '{page_url}' nalezeno {len(links)} inzerátů.")
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(parse_sauto_detail, ln) for ln in links]
        for link, future in zip(links, futures):
            try:
                data = future.result()
                if not data:
                    continue
                dedup_key = (
                    data["Značka"],
                    data["Model"],
                    data["Objem (cm³)"],
                    data["Rok"],
                    data["Najeté km"],
                    data["Cena"],
                    data["Palivo"],
                    data["Převodovka"],
                    data["Výkon (kW)"]
                )
                if dedup_key in seen_set:
                    continue
                seen_set.add(dedup_key)
                results.append(data)
                print("-" * 60)
                print(f"URL:        {data['URL']}")
                print(f"Značka:     {data['Značka']}")
                print(f"Model:      {data['Model']}")
                print(f"Objem (cm³):  {data['Objem (cm³)']}")
                print(f"Rok:        {data['Rok']}")
                print(f"Najeté km:  {data['Najeté km']}")
                print(f"Cena:       {data['Cena']}")
                print(f"Palivo:     {data['Palivo']}")
                print(f"Převodovka: {data['Převodovka']}")
                print(f"Výkon (kW): {data['Výkon (kW)']}")
            except Exception as e:
                print(f"Chyba při zpracování detailu {link}: {e}")
    return results, seen_set


def scrape_sauto_min_inzeraty(base_url: str, min_inzeraty: int = 50, max_pages: int = 5, max_workers: int = 10):
    all_data = []
    seen_set = set()
    page = 1
    while page <= max_pages:
        if page == 1:
            page_url = base_url
        else:
            sep = "&" if "?" in base_url else "?"
            page_url = f"{base_url}{sep}strana={page}"
        print(f"\nSCRAPUJI STRÁNKU č.{page}: {page_url}")
        page_results, seen_set = scrape_sauto_one_page(page_url, max_workers=max_workers, seen_set=seen_set)
        if not page_results:
            print("Žádné inzeráty splňující podmínky => končím.")
            break
        all_data.extend(page_results)
        print(f"Aktuálně nasbíráno {len(all_data)} záznamů (po deduplikaci).\n")
        if len(all_data) >= min_inzeraty:
            print(f"Dosaženo {min_inzeraty} záznamů => končím.")
            break
        page += 1
        time.sleep(2)
    df = pd.DataFrame(all_data)
    if "URL" in df.columns:
        df.drop(columns=["URL"], inplace=True)
    output_path = os.path.join(OUTPUT_DIR, r"C:\Users\Asus\PV\OMEGA\OmegaCars\raw_data\auta_sauto2.csv")
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path)
            combined_df = pd.concat([existing_df, df]).drop_duplicates().reset_index(drop=True)
            combined_df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(
                f"Hotovo! Přidáno {len(combined_df) - len(existing_df)} nových záznamů. Celkem {len(combined_df)} záznamů uložených do {output_path}.")
        except Exception as e:
            print(f"Chyba při načítání nebo ukládání existujícího souboru: {e}")
    else:
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Hotovo! Uloženo {len(df)} záznamů do {output_path}.")
    return df


if __name__ == "__main__":
    df = scrape_sauto_min_inzeraty(
        base_url=base_url,
        min_inzeraty=NUM_LISTINGS,
        max_pages=MAX_PAGES,
        max_workers=MAX_WORKERS
    )
    print("\nNáhled do CSV (prvních 5 řádků):")
    print(df.head())
