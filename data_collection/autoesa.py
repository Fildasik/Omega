import os
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

pd.set_option('display.max_colwidth', None)

# Vytvoříme session s hlavičkami
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "cs-CZ,cs;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connaection": "keep-alive"
})


def parse_brand_model(title: str) -> tuple[str, str]:
    """
    Rozdělí titulek (např. "Volkswagen Passat 2.0TDi") na značku a model.
    Značka je první token (i když obsahuje pomlčku, např. "Mercedes-Benz")
    a model je pouze druhý token.
    """
    tokens = title.split()
    if len(tokens) < 2:
        return (title, "Nezjištěno")
    brand = tokens[0]
    model = tokens[1]
    return (brand, model)


def get_listing_links(page_url: str) -> list[str]:
    """
    Na stránce Auto ESA (např. https://www.autoesa.cz/vsechna-auta?stranka=...)
    najde odkazy na jednotlivé inzeráty. Odkazy se předpokládají v <a class="car_item">.
    """
    try:
        resp = session.get(page_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Chyba při načítání listingu {page_url}: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", class_="car_item"):
        href = a_tag.get("href")
        if href:
            full_url = href if href.startswith("http") else "https://www.autoesa.cz" + href
            links.add(full_url)
    return list(links)


def parse_esa_detail(url: str) -> dict | None:
    """
    Načte detail inzerátu z Auto ESA a extrahuje:
      Značka, Model, Rok, Najeté km, Cena, Palivo, Převodovka, Výkon (kW)
    """
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"Chyba při načítání detailu {url}: {e}")
        return None
    soup = BeautifulSoup(r.text, "html.parser")

    # Značka a model – element: <div class="car_detail2__h1"><h1>Volkswagen Passat 2.0TDi</h1></div>
    h1_div = soup.find("div", class_="car_detail2__h1")
    if not h1_div:
        print(f"Nelze najít element pro značku/model na {url}")
        return None
    h1_tag = h1_div.find("h1")
    if not h1_tag:
        print(f"Nelze najít <h1> uvnitř car_detail2__h1 na {url}")
        return None
    title_text = h1_tag.get_text(strip=True)
    brand, model = parse_brand_model(title_text)

    # Rok – hledáme <li data-toggle="popover"> s <strong>Rok</strong> a potom <span>2018</span>
    li_year = None
    for li in soup.find_all("li", attrs={"data-toggle": "popover"}):
        strong = li.find("strong")
        if strong and strong.get_text(strip=True).lower() == "rok":
            li_year = li
            break
    if not li_year:
        print(f"Nelze najít li s 'Rok' na {url}")
        return None
    span_year = li_year.find("span")
    if not span_year:
        print(f"Nelze najít span s 'Rok' na {url}")
        return None
    year_val = span_year.get_text(strip=True)

    # Najeté km – hledáme <li data-toggle="popover"> s <strong>Stav tachometru</strong>
    li_mileage = None
    for li in soup.find_all("li", attrs={"data-toggle": "popover"}):
        strong = li.find("strong")
        if strong and strong.get_text(strip=True).lower() == "stav tachometru":
            li_mileage = li
            break
    if not li_mileage:
        print(f"Nelze najít li se 'Stav tachometru' na {url}")
        return None
    span_mileage = li_mileage.find("span")
    if not span_mileage:
        print(f"Nelze najít span pro tachometr na {url}")
        return None
    mileage_text = span_mileage.get_text(strip=True)
    mileage_digits = re.sub(r"[^\d]", "", mileage_text)

    # Cena – hledáme <div class="show-more-price-right-right"> a v něm <strong>439 000 Kč</strong>
    price_div = soup.find("div", class_="show-more-price-right-right")
    if not price_div:
        print(f"Nelze najít div pro cenu na {url}")
        return None
    strong_price = price_div.find("strong")
    if not strong_price:
        print(f"Nelze najít strong pro cenu na {url}")
        return None
    price_text = strong_price.get_text(strip=True)
    price_digits = re.sub(r"[^\d]", "", price_text)
    price_val = price_digits

    # Palivo – hledáme <li data-toggle="popover"> s <strong>Palivo</strong>
    li_fuel = None
    for li in soup.find_all("li", attrs={"data-toggle": "popover"}):
        strong = li.find("strong")
        if strong and strong.get_text(strip=True).lower() == "palivo":
            li_fuel = li
            break
    if not li_fuel:
        print(f"Nelze najít li s 'Palivo' na {url}")
        return None
    span_fuel = li_fuel.find("span")
    if not span_fuel:
        print(f"Nelze najít span s 'Palivo' na {url}")
        return None
    fuel_val = span_fuel.get_text(strip=True)

    # Převodovka – hledáme <li data-toggle="popover"> s <strong>Převodovka</strong> a bereme první část před lomítkem
    li_trans = None
    for li in soup.find_all("li", attrs={"data-toggle": "popover"}):
        strong = li.find("strong")
        if strong and strong.get_text(strip=True).lower() == "převodovka":
            li_trans = li
            break
    if not li_trans:
        print(f"Nelze najít li s 'Převodovka' na {url}")
        return None
    span_trans = li_trans.find("span")
    if not span_trans:
        print(f"Nelze najít span s 'Převodovka' na {url}")
        return None
    transmission_text = span_trans.get_text(strip=True)
    transmission_main = transmission_text.split("/")[0].strip()

    # Výkon (kW) – hledáme <li> s <strong>Výkon</strong> a potom <span>140 kW</span>
    li_power = None
    for li in soup.find_all("li"):
        strong = li.find("strong")
        if strong and strong.get_text(strip=True).lower() == "výkon":
            li_power = li
            break
    if not li_power:
        print(f"Nelze najít li s 'Výkon' na {url}")
        return None
    span_power = li_power.find("span")
    if not span_power:
        print(f"Nelze najít span s 'Výkon' na {url}")
        return None
    power_text = span_power.get_text(strip=True)
    match_power = re.search(r"(\d+)\s*kW", power_text)
    if not match_power:
        print(f"Nelze extrahovat výkon na {url}")
        return None
    power_val = match_power.group(1)

    mandatory = [brand, model, year_val, mileage_digits, price_val, fuel_val, transmission_main, power_val]
    if any(x == "" for x in mandatory):
        print(f"Chybí nějaká povinná hodnota na {url}")
        return None

    return {
        "URL": url,
        "Značka": brand,
        "Model": model,
        "Rok": year_val,
        "Najeté km": mileage_digits,
        "Cena": price_val,
        "Palivo": fuel_val,
        "Převodovka": transmission_main,
        "Výkon (kW)": power_val
    }


def scrape_esa_one_page(page_url: str, max_workers: int = 10, seen_set=None):
    if seen_set is None:
        seen_set = set()

    links = get_listing_links(page_url)
    print(f"Na stránce '{page_url}' nalezeno {len(links)} inzerátů.")
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(parse_esa_detail, ln) for ln in links]
        for link, future in zip(links, futures):
            try:
                data = future.result()
                if not data:
                    continue
                dedup_key = (
                    data["Značka"],
                    data["Model"],
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
                print(f"URL:          {data['URL']}")
                print(f"Značka:       {data['Značka']}")
                print(f"Model:        {data['Model']}")
                print(f"Rok:          {data['Rok']}")
                print(f"Najeté km:    {data['Najeté km']}")
                print(f"Cena:         {data['Cena']}")
                print(f"Palivo:       {data['Palivo']}")
                print(f"Převodovka:   {data['Převodovka']}")
                print(f"Výkon (kW):   {data['Výkon (kW)']}")
            except Exception as e:
                print(f"Chyba při detailu {link}: {e}")
    return results, seen_set


def scrape_esa_min_inzeraty(base_url: str, min_inzeraty: int = 50, max_pages: int = 5, max_workers: int = 10):
    all_data = []
    seen_set = set()
    page = 1
    while page <= max_pages:
        if page == 1:
            page_url = base_url
        else:
            sep = "&" if "?" in base_url else "?"
            page_url = f"{base_url}{sep}stranka={page}"
        print(f"\nSCRAPUJI STRÁNKU č.{page}: {page_url}")
        page_results, seen_set = scrape_esa_one_page(page_url, max_workers=max_workers, seen_set=seen_set)
        if not page_results:
            print("Žádné inzeráty => končím.")
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
    output_dir = r"C:\Users\filip\OMEGA\OmegaAuta-main\raw_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, "auta_autoesa.csv")

    # Pokud soubor existuje, načteme ho a přidáme nové záznamy
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
    df = scrape_esa_min_inzeraty(
        base_url="https://www.autoesa.cz/vsechna-auta?cena_od=400000&cena_do=600000",
        min_inzeraty=550,
        max_pages=272,
        max_workers=12
    )
    print("\nNáhled do CSV (prvních 5 řádků):")
    print(df.head())
