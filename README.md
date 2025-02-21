# Tax Wizard 🧙‍♂️

Adóbevallás-segítő eszköz befektetési tranzakciók feldolgozásához és Excel kimutatás generálásához. Jelenleg a Lightyear és Revolut platformok kimutatásait támogatja.

## 📋 Tartalomjegyzék
- [Követelmények](#követelmények)
- [Telepítés](#telepítés)
- [Használat](#használat)
- [Támogatott platformok](#támogatott-platformok)
- [Kimeneti Excel formátum](#kimeneti-excel-formátum)
- [Technikai részletek](#technikai-részletek)

## 🔧 Követelmények

- Python 3.8 vagy újabb verzió
- pip (Python csomagkezelő)

## 💻 Telepítés

1. Klónozd le a repository-t:
```bash
git clone https://github.com/amargo/tax-wizard.git
cd tax-wizard
```

2. Telepítsd a szükséges Python csomagokat:
```bash
pip install --no-cache-dir -r requirements.txt
```

## 🚀 Használat

1. Töltsd le a tranzakciós kimutatást a megfelelő platformról (Lightyear vagy Revolut)
2. Helyezd el a CSV fájlt a program mappájában
3. Futtasd a programot:

```bash
# Lightyear esetén:
python tax-wizard.py --mode lightyear --file LightyearStatement.csv

# Revolut esetén:
python tax-wizard.py --mode revolut --file RevolutStatement.csv
python tax-wizard.py --mode revolut_saving --file RevolutSavingsStatement.csv
```

## 🏢 Támogatott platformok

### Lightyear

```csv
[statement][transactions]
Date,Type,Status,Description,Amount,Currency,Exchange Rate,Fee,Fee Currency
2024-01-15,BUY,Completed,AAPL,-150.50,EUR,355.82,0.35,EUR
2024-02-01,SELL,Completed,AAPL,180.75,USD,356.10,0.35,USD
```

Támogatott tranzakciók:
- BUY: Részvényvásárlás
- SELL: Részvényeladás
- DIVIDEND: Osztalék kifizetés
- INTEREST: Kamat jóváírás

### Revolut

```csv
Completed Date,Description,Amount,Currency,State,Balance
2024-01-15,Savings Interest,5.50,EUR,COMPLETED,1000.50
2024-02-01,Stock Sale: AAPL,180.75,USD,COMPLETED,1181.25
```

Támogatott tranzakciók:
- Stock Purchase: Részvényvásárlás
- Stock Sale: Részvényeladás
- Savings Interest: Megtakarítási kamat
- Dividend Payment: Osztalék kifizetés

## 📊 Excel formátumok

A program platformonként különböző Excel formátumokat használ, amelyeket az `excel_config.py` fájlban konfigurálhatunk:

### 1. Lightyear formátum
#### Realizált PnL lap példa:
```
| Dátum      | Ticker | Művelet | Mennyiség | Ár (USD) | Díj (USD) | Árfolyam | HUF összeg |
|------------|--------|---------|-----------|----------|-----------|----------|------------|
| 2024-01-15 | AAPL   | BUY     | 10        | 150.50   | 0.35      | 355.82   | 535,947    |
| 2024-02-01 | AAPL   | SELL    | 10        | 180.75   | 0.35      | 356.10   | 644,281    |
```

#### Nyitott Pozíciók lap példa:
```
| Ticker | Mennyiség | Átlagár (USD) | Jelenlegi ár (USD) | HUF érték |
|--------|-----------|---------------|-------------------|-----------|
| MSFT   | 5         | 350.25        | 402.75           | 716,893   |
| GOOGL  | 2         | 140.50        | 145.80           | 103,518   |
```

#### Kamat és Osztalék lap példa:
```
| Dátum      | Típus    | Összeg (USD) | Árfolyam | HUF összeg |
|------------|----------|--------------|----------|------------|
| 2024-01-20 | DIVIDEND | 0.88         | 355.90   | 313        |
| 2024-02-15 | INTEREST | 1.25         | 356.20   | 445        |
```

### 2. Revolut formátum
#### Tranzakciók lap példa:
```csv
Completed Date,Description,Amount,Currency,State,Balance
2024-01-15,Savings Interest,5.50,EUR,COMPLETED,1000.50
2024-02-01,Stock Sale: AAPL,180.75,USD,COMPLETED,1181.25
2024-02-15,Stock Purchase: MSFT,-350.25,USD,COMPLETED,831.00
2024-03-01,Dividend Payment: GOOGL,2.50,USD,COMPLETED,833.50
```

#### Megtakarítások lap példa:
```csv
Date,Description,Value,Price per share,Quantity of shares
"Dec 31, 2024, 2:21:51 AM",Service Fee Charged GBP Class IE0002RUHW32,-£0.0276,,
"Dec 31, 2024, 2:21:51 AM",Interest PAID GBP Class R IE0002RUHW32,£0.1376,,
"Dec 30, 2024, 1:58:14 AM",Service Fee Charged GBP Class IE0002RUHW32,-£0.0276,,
"Dec 30, 2024, 1:58:14 AM",Interest PAID GBP Class R IE0002RUHW32,£0.1376,,
"Dec 29, 2024, 1:59:20 AM",Service Fee Charged GBP Class IE0002RUHW32,-£0.0276,,
"Dec 29, 2024, 1:59:20 AM",Interest PAID GBP Class R IE0002RUHW32,£0.1276,,
"Dec 28, 2024, 2:00:32 AM",Service Fee Charged GBP Class IE0002RUHW32,-£0.0276,,
"Dec 28, 2024, 2:00:32 AM",Interest PAID GBP Class R IE0002RUHW32,£0.1376,,
```

#### Összesítő lap példa:
```
| Kategória          | Összeg (eredeti) | HUF összeg |
|--------------------|------------------|------------|
| Realizált nyereség | $1,234.50       | 439,881    |
| Osztalék bevétel   | $245.75         | 87,567     |
| Kamat bevétel      | £2.15           | 966        |
| Szolgáltatási díj  | -£0.55          | -247       |
```

## 🔧 Technikai részletek

### MNB Árfolyam kezelés

Az `mnb_exchange_service.py` modul az MNB árfolyamokat kezeli:

- **Cache rendszer**: 
  - Helye: `~/exchange_rate_cache.json`
  - Formátum: `"YYYY-MM-DD|CURRENCY": rate`
  - Automatikus mentés és betöltés
- **Hibakezelés**:
  - Hétvégi árfolyamok: automatikus visszalépés az utolsó munkanapra

## 📝 Megjegyzések

- A program kezeli mindkét platform tranzakciós történetét
- Automatikus devizaváltás MNB árfolyamokkal
- Intelligens cache rendszer a gyorsabb feldolgozásért
- Részletes Excel formázás platformonként
- Tranzakciós díjak automatikus kezelése

## ⚠️ Fontos figyelmeztetés

Ez az eszköz csak segítség az adóbevallás elkészítéséhez. Az adóbevallás helyességéért mindig a felhasználó felel. Javasoljuk az eredmények ellenőrzését és szükség esetén könyvelő bevonását.
