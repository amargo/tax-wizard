import os
import json
import xml.etree.ElementTree as ET

from datetime import datetime, timedelta
from zeep import Client, Settings

# A cache fájl elérési útja: a felhasználó otthoni könyvtárában lesz
CACHE_FILE = os.path.join(os.path.expanduser("~"), "exchange_rate_cache.json")

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Hiba a cache fájl betöltésekor:", e)
            return {}
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Hiba a cache fájl mentésekor:", e)

# A cache értékeket először a fájlból töltjük be, ha létezik
exchange_rate_cache = load_cache()


class MNBExchangeService:
    """Az MNB árfolyam szolgáltatásával kapcsolatos műveletek, cache-eléssel."""
    def __init__(self, wsdl_url="http://www.mnb.hu/arfolyamok.asmx?wsdl", strict=False):
        settings = Settings(strict=strict, xml_huge_tree=True)
        self.client = Client(wsdl_url, settings=settings)

    def get_exchange_rate(self, date, currency: str) -> float:
        """Lekéri az adott dátum (fallback esetén az előző nap) alapján a deviza árfolyamát.
        Ha a deviza HUF, visszatér 1.0-vel. A lekérdezést cache-eli egy JSON fájlban.
        """

        # Ha a date string, próbáljuk meg datetime objektummá konvertálni.
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                try:
                    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    print(f"Hibás dátum formátum: {date} -> {e}")
                    return None

        # A cache kulcsa: "YYYY-MM-DD|CURRENCY"
        key = f"{date.strftime('%Y-%m-%d')}|{currency.upper()}"
        if key in exchange_rate_cache:
            return exchange_rate_cache[key]
        if currency.upper() == "HUF":
            exchange_rate_cache[key] = 1.0
            save_cache(exchange_rate_cache)
            return 1.0

        start_date_str = (date - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date_str = date.strftime("%Y-%m-%d")
        request_data = {
            'startDate': start_date_str,
            'endDate': end_date_str,
            'currencyNames': currency.upper()
        }
        try:
            response_xml = self.client.service.GetExchangeRates(**request_data)
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

        requested_date_str = date.strftime("%Y-%m-%d")
        # Megpróbáljuk megtalálni a kért dátumhoz tartozó napot,
        # ha nem, akkor a legutolsó elérhető napot választjuk.
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
                    value = float(rate.text.replace(",", "."))
                    exchange_rate_cache[key] = value
                    save_cache(exchange_rate_cache)
                    return value
                except Exception as e:
                    print(f"Az árfolyam érték konvertálása sikertelen ({rate.text}): {e}")
                    return None

        print(f"A {currency} árfolyam nem található a válaszban.")
        return None

    def convert_to_huf(self, amount: float, date: datetime, currency: str) -> float:
        """Átváltja az adott összeget forintra a lekérdezett árfolyammal."""
        rate = self.get_exchange_rate(date, currency)
        if rate is None:
            print(f"Nincs árfolyam adat {currency} esetén {date.strftime('%Y-%m-%d')}.")
            return None
        return amount * rate
