# Test Report

**Tester:** Václav Vondráček 
**,Datum testování:** 16. dubna 2025   

---

## 🎯 Cíl testování

- Zadání kompletních validních údajů
- Vynechání jednoho nebo více vstupních polí
- Zadání nesmyslných hodnot (např. záporný nájezd km)

---

## ✅ Testované scénáře

| Test Case ID | Název testu                                 | Typ         | Výsledek  | Popis výsledku                                             |
|--------------|----------------------------------------------|-------------|-----------|-------------------------------------------------------------|
| `App_01`     | Predikce ceny s platnými údaji               | Funkční     | ✅ PASS   | Zobrazila se správná cena ve správném formátu              |
| `App_02`     | Chybějící vstupní hodnota (např. výkon)      | Negativní   | ✅ PASS   | Zobrazilo se chybové hlášení, výpočet neproběhl             |
| `App_03`     | Zadání záporné hodnoty (např. -20 000 km)    | Negativní   | ✅ PASS   | Aplikace zabránila výpočtu a zobrazila chybu               |

---

## 🧾 Shrnutí

- **Počet testů:** 3  
- **Úspěšných testů:** 3  
- **Selhání:** 0  

Aplikace reagovala ve všech případech podle očekávání.
