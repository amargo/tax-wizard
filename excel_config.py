# Excel formátum konfigurációk
HUF_FORMAT = '#,##0 "Ft"'
NUMBER_FORMAT = '#,##0.0'

# Munkalapok oszlopformátum konfigurációi
SHEET_FORMAT_CONFIGS = {
    "Realizált PnL": {
        "number_format": [(3,), (4,), (5,)],
        "huf_format": [(6,), (7,), (8,)]
    },
    "Nyitott Pozíciók": {
        "number_format": [(3,)],
        "huf_format": [(4,)]
    },
    "Kamat": {
        "number_format": [(3,), (4,)],
        "huf_format": [(5,)]
    },
    "Osztalék": {
        "number_format": [(3,), (4,)],
        "huf_format": [(5,)]
    },
    "Összesítő": {
        "huf_format": [(2,)]
    }
}

SHEET_FORMAT_CONFIGS_REVOLUT_SAVINGS = {
    "Megtakarítás": {
        # Tegyük fel, hogy a részletes riportban a 4. és 5. oszlopok tartalmazzák az eredeti és HUF értékeket
        "number_format": [(4,)],
        "huf_format": [(5,)]
    },
    "Összesítő": {
        # Az Összesítő oldalon a 2. oszlop (Összeg eredeti devizában) esetén a number_format,
        # a 3. oszlop (Összeg HUF-ban) esetén a HUF formátum
        "number_format": [(2, 3, 4, 8, )],
        "huf_format": [(5, 6, 7, 9, )]
    }
}