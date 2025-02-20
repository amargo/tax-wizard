# Tax Wizard 🧙‍♂️

Adóbevallás-segítő eszköz befektetési tranzakciók feldolgozásához és Excel kimutatás generálásához. Jelenleg a Lightyear befektetési platform kimutatásait támogatja.

## 📋 Tartalomjegyzék
- [Követelmények](#követelmények)
- [Telepítés](#telepítés)
- [Használat](#használat)
- [Bemeneti CSV formátum](#bemeneti-csv-formátum)
- [Kimeneti Excel formátum](#kimeneti-excel-formátum)

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

1. Töltsd le a tranzakciós kimutatást a Lightyear platformról CSV formátumban
2. Helyezd el a CSV fájlt a program mappájában
3. Futtasd a programot:
```bash
python tax-wizard.py LightyearStatement.csv
```

4. A program létrehoz egy `ado_bevallas.xlsx` fájlt az aktuális mappában

## 📥 Bemeneti CSV formátum

A program a Lightyear platformról letöltött tranzakciós kimutatásokat tudja feldolgozni. Példa a CSV formátumra:

```csv
[statement][transactions]
Date,Type,Status,Description,Amount,Currency,Exchange Rate,Fee,Fee Currency
2024-01-15,BUY,Completed,AAPL,-150.50,USD,355.82,0.35,USD
2024-02-01,SELL,Completed,AAPL,180.75,USD,356.10,0.35,USD
2024-01-20,DIVIDEND,Completed,MSFT Dividend,1.50,USD,355.82,0.00,USD
2024-02-05,INTEREST,Completed,Cash Interest,5.50,USD,355.82,0.00,USD
```

A program automatikusan felismeri és feldolgozza a következő tranzakció típusokat:
- BUY: Részvényvásárlás
- SELL: Részvényeladás
- DIVIDEND: Osztalék kifizetés
- INTEREST: Kamat jóváírás

## 📊 Kimeneti Excel formátum

Az Excel fájl a következő munkalapokat tartalmazza:

### 1. Realizált PnL
| Ticker | Currency | Buy Sum | Sell Sum | Realized PnL | Sale Date | Exchange Rate | Realized PnL (HUF) |
|--------|----------|---------|-----------|-------------|-----------|--------------|------------------|
| AAPL   | EUR      | 150.50  | 180.75    | 30.25       | 2024-02-01| 356.10       | 10,772 Ft        |
| TSLA   | USD      | 220.30  | 280.45    | 60.15       | 2024-02-15| 357.25       | 21,489 Ft        |

### 2. Nyitott Pozíciók
| Ticker | Currency | Buy Sum |
|--------|----------|---------|
| MSFT   | EUR      | 285.50  |
| GOOGL  | USD      | 2450.75 |

### 3. Kamat
| Date       | Currency | Amount | Exchange Rate | Amount (HUF) |
|------------|----------|--------|---------------|--------------|
| 2024-02-05 | EUR      | 5.50   | 355.82        | 1,957 Ft     |
| 2024-03-10 | USD      | 3.75   | 356.50        | 1,337 Ft     |

### 4. Osztalék
| Date       | Currency | Amount | Exchange Rate | Amount (HUF) |
|------------|----------|--------|---------------|--------------|
| 2024-01-20 | USD      | 1.50   | 355.82        | 534 Ft       |
| 2024-03-15 | EUR      | 2.25   | 357.30        | 804 Ft       |

### 5. Összesítő
| Category                       | Total      |
|--------------------------------|------------|
| Realizált PnL (HUF)            | 32,261 Ft  |
| Kamat (HUF)                    | 3,294 Ft   |
| Osztalék (HUF)                 | 1,338 Ft   |
| Összes bevallandó összeg (HUF) | 36,893 Ft  |

## 📝 Megjegyzések

- A program automatikusan kezeli a Lightyear tranzakciós történetet
- Az összegek automatikusan forintra váltódnak a megfelelő árfolyamon
- A program kezeli a különböző devizákat
- Az Excel fájlban minden összeg megfelelően formázva jelenik meg
- A nyitott pozíciók nem számítanak bele az adózandó összegbe
- A program figyelembe veszi és levonja a tranzakciós díjakat

## ⚠️ Fontos figyelmeztetés

Ez az eszköz csak segítség az adóbevallás elkészítéséhez. Az adóbevallás helyességéért mindig a felhasználó felel. Javasoljuk az eredmények ellenőrzését és szükség esetén könyvelő bevonását.
