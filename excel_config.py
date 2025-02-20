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
    }
}
