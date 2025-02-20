import os
import sys
import pandas as pd
import xml.etree.ElementTree as ET

from zeep import Client, Settings
from datetime import datetime, timedelta
from excel_config import HUF_FORMAT, NUMBER_FORMAT, SHEET_FORMAT_CONFIGS

STATEMENT_PREFIX = "[statement][transactions]"
# Egyszerű cache, hogy ne kelljen ugyanazt az árfolyamot többször lekérdezni
exchange_rate_cache = {}

def get_exchange_rate(date: datetime, currency: str) -> float:
    """
    Lekéri az adott dátum (és a fallback esetén az előző nap) alapján a megadott deviza árfolyamát az MNB SOAP szolgáltatásából.
    Ha a deviza HUF, visszatér 1.0-vel.
    """
    if currency.upper() == "HUF":
        return 1.0

    settings = Settings(strict=False, xml_huge_tree=True)
    wsdl_url = "http://www.mnb.hu/arfolyamok.asmx?wsdl"
    client = Client(wsdl_url, settings=settings)

    # A start_date_str a lekérdezni kívánt nap előtti nap, az end_date_str pedig maga a lekérdezni kívánt nap
    start_date_str = (date - timedelta(days=5)).strftime("%Y-%m-%d")
    end_date_str = date.strftime("%Y-%m-%d")

    # Lekérjük a GetExchangeRatesRequestBody típust a megfelelő namespace-ben
    try:
        body_type = client.get_type("{http://www.mnb.hu/webservices/}GetExchangeRatesRequestBody")
    except Exception as e:
        print("Hiba a GetExchangeRatesRequestBody típus lekérésekor:", e)
        return None

    request_data = {
        'startDate': start_date_str,
        'endDate': end_date_str,
        'currencyNames': currency.upper()
    }

    try:
        response_xml = client.service.GetExchangeRates(**request_data)
    except Exception as e:
        print("Hiba a GetExchangeRates metódus hívásakor:", e)
        return None

    try:
        root = ET.fromstring(response_xml)
    except Exception as e:
        print(f"XML feldolgozási hiba: {e}")
        return None

    days = []
    for day in root.findall("Day"):
        day_date = day.attrib.get("date")
        try:
            parsed_date = datetime.strptime(day_date, "%Y-%m-%d")
            days.append((parsed_date, day))
        except Exception as ex:
            print(f"Hiba a dátum értelmezésekor: {day_date} -> {ex}")

    if not days:
        print("Nem található 'Day' elem a válaszban.")
        return None

    # Megpróbáljuk megtalálni a kért dátumhoz tartozó napot,
    # ha nem, akkor a legutolsó elérhető napot választjuk.
    requested_date_str = date.strftime("%Y-%m-%d")
    chosen_day = None
    for d, day in days:
        if d.strftime("%Y-%m-%d") == requested_date_str:
            chosen_day = day
            break
    if not chosen_day:
        chosen_day = max(days, key=lambda x: x[0])[1]

    for rate in chosen_day.findall("Rate"):
        if rate.attrib.get("curr", "").upper() == currency.upper():
            try:
                return float(rate.text.replace(",", "."))
            except Exception as e:
                print(f"Az árfolyam érték konvertálása sikertelen ({rate.text}): {e}")
                return None

    print(f"A {currency} árfolyam nem található a válaszban.")
    return None


def convert_to_huf(amount: float, date: datetime, currency: str) -> float:
    """
    Átváltja az adott összeget forintra a megadott dátum szerinti árfolyammal.
    """
    rate = get_exchange_rate(date, currency)
    if rate is None:
        print(f"Nincs árfolyam adat {currency} esetén {date.strftime('%Y-%m-%d')}. Az érték átváltása sikertelen.")
        return None
    return amount * rate

def process_transactions(csv_file: str):
    """
    Beolvassa a CSV fájlt, majd a következőket számolja:
      - Realizált tőkenyereség/veszteség (csak olyan ticker-ek, ahol van Sell tranzakció),
      - Nyitott pozíciók (csak Buy/Distribution tranzakciók),
      - Kamat- és osztalékjövedelmek.
      
    Minden nem HUF devizanem esetén az eladás vagy az adott tranzakció napján érvényes MNB árfolyammal kerül átváltásra.
    """
    # A dátumok formátuma: "30/12/2024 17:39:13" → dayfirst=True
    df = pd.read_csv(csv_file, parse_dates=["Date"], dayfirst=True)

    # Tisztítjuk a Type és CCY oszlopokat (fehér karakterek eltávolítása)
    df["Type"] = df["Type"].astype(str).str.strip()
    df["CCY"] = df["CCY"].astype(str).str.strip()

    # Keresünk olyan sorokat, ahol a tranzakció típusa Buy, Sell vagy Distribution és van Ticker
    trades = df[df["Type"].isin(["Buy", "Sell", "Distribution"]) & (df["Ticker"].notnull()) & (df["Ticker"] != "")]
    realized_list = []     # Realizált (eladott) pozíciók adatai
    open_positions_list = []  # Csak vásárlás (nyitott pozíciók)

    # Csoportosítás Ticker és deviza szerint
    for (ticker, ccy), group in trades.groupby(["Ticker", "CCY"]):
        # Vételi összeg: Buy és Distribution összege
        buy_sum = group[group["Type"].isin(["Buy", "Distribution"])]["Net Amt."].sum()
        # Eladási összeg: Sell tranzakciók összege
        sell_df = group[group["Type"]=="Sell"]
        sell_sum = sell_df["Net Amt."].sum()

        if sell_sum != 0:
            realized_pnl = sell_sum - buy_sum
            # Az eladás napját a legutolsó Sell dátum alapján vesszük
            sale_date = sell_df["Date"].max()
            exchange_rate = 1.0
            realized_pnl_huf = realized_pnl
            if ccy.upper() != "HUF":
                exchange_rate = get_exchange_rate(sale_date, ccy)
                if exchange_rate is None:
                    exchange_rate = 0
                realized_pnl_huf = realized_pnl * exchange_rate

            realized_list.append({
                "Ticker": ticker,
                "Currency": ccy,
                "Buy Sum": buy_sum,
                "Sell Sum": sell_sum,
                "Realized PnL": realized_pnl,
                "Sale Date": sale_date.strftime("%Y-%m-%d"),
                "Exchange Rate": exchange_rate,
                "Realized PnL (HUF)": realized_pnl_huf
            })
        else:
            # Ha nincs Sell tranzakció, akkor ez egy nyitott pozíció
            open_positions_list.append({
                "Ticker": ticker,
                "Currency": ccy,
                "Buy Sum": buy_sum
            })

    realized_df = pd.DataFrame(realized_list)
    open_df = pd.DataFrame(open_positions_list)

    # Kamat (Interest) és Dividend tranzakciók feldolgozása
    interest_df_raw = df[df["Type"]=="Interest"]
    dividend_df_raw = df[df["Type"]=="Dividend"]

    interest_rows = []
    for idx, row in interest_df_raw.iterrows():
        rate = get_exchange_rate(row["Date"], row["CCY"])
        conv_amount = row["Net Amt."] * (rate if rate is not None else 1)
        interest_rows.append({
            "Date": row["Date"].strftime("%Y-%m-%d"),
            "Currency": row["CCY"],
            "Amount": row["Net Amt."],
            "Exchange Rate": rate if rate is not None else 1,
            "Amount (HUF)": conv_amount
        })
    interest_summary = pd.DataFrame(interest_rows)

    dividend_rows = []
    for idx, row in dividend_df_raw.iterrows():
        rate = get_exchange_rate(row["Date"], row["CCY"])
        conv_amount = row["Net Amt."] * (rate if rate is not None else 1)
        dividend_rows.append({
            "Date": row["Date"].strftime("%Y-%m-%d"),
            "Currency": row["CCY"],
            "Amount": row["Net Amt."],
            "Exchange Rate": rate if rate is not None else 1,
            "Amount (HUF)": conv_amount
        })
    dividend_summary = pd.DataFrame(dividend_rows)

    return realized_df, open_df, interest_summary, dividend_summary

def generate_excel(realized_df: pd.DataFrame, open_df: pd.DataFrame, 
                  interest_df: pd.DataFrame, dividend_df: pd.DataFrame, 
                  output_file: str = "ado_bevallas.xlsx") -> None:
    """
    Generál egy Excel fájlt, amelyben külön munkalapokon szerepelnek a különböző pénzügyi adatok.

    Args:
        realized_df: Realizált nyereség/veszteség adatokat tartalmazó DataFrame
        open_df: Nyitott pozíciókat tartalmazó DataFrame
        interest_df: Kamatjövedelem adatokat tartalmazó DataFrame
        dividend_df: Osztalékjövedelem adatokat tartalmazó DataFrame
        output_file: A kimeneti Excel fájl neve

    A munkalapokon szereplő adatok:
      - Realizált nyereség/veszteség
      - Nyitott pozíciók
      - Kamatjövedelem
      - Osztalékjövedelem
      - Összesítő (forintban)
    """
    def apply_number_format(worksheet, column, start_row, format_str):
        """Adott oszlopra alkalmazza a megadott számformátumot."""
        for row in worksheet.iter_rows(min_row=start_row, min_col=column, max_col=column):
            for cell in row:
                cell.number_format = format_str

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Adatok kiírása
        dataframes = {
            "Realizált PnL": realized_df,
            "Nyitott Pozíciók": open_df,
            "Kamat": interest_df,
            "Osztalék": dividend_df
        }
        
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Összesítő számítása
        totals = {
            "Realizált PnL (HUF)": realized_df["Realized PnL (HUF)"].sum() if not realized_df.empty else 0,
            "Kamat (HUF)": interest_df["Amount (HUF)"].sum() if not interest_df.empty else 0,
            "Osztalék (HUF)": dividend_df["Amount (HUF)"].sum() if not dividend_df.empty else 0
        }
        totals["Összes bevallandó összeg (HUF)"] = sum(totals.values())
        
        summary_df = pd.DataFrame({
            "Category": list(totals.keys()),
            "Total": list(totals.values())
        })
        summary_df.to_excel(writer, sheet_name="Összesítő", index=False)

        # Formázások alkalmazása
        workbook = writer.book
        
        # Munkalapok formázása
        for sheet_name, formats in SHEET_FORMAT_CONFIGS.items():
            ws = writer.sheets[sheet_name]
            for format_type, columns in formats.items():
                format_str = HUF_FORMAT if format_type == "huf_format" else NUMBER_FORMAT
                for cols in columns:
                    for col in cols:
                        apply_number_format(ws, col, 2, format_str)
        
        # Összesítő formázása
        ws_summary = writer.sheets["Összesítő"]
        apply_number_format(ws_summary, 2, 2, HUF_FORMAT)

    print(f"Excel fájl sikeresen generálva: {output_file}")


def main(args):
    fname = args[1]
    # A CSV fájl neve, amely tartalmazza a tranzakcióidat      
    if not os.path.exists(fname):
        sys.exit(f"{STATEMENT_PREFIX} file not found: {fname}")
    realized_df, open_df, interest_df, dividend_df = process_transactions(fname)
    generate_excel(realized_df, open_df, interest_df, dividend_df)

if __name__ == "__main__":
    main(sys.argv)
