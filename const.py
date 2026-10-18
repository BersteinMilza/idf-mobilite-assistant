"""Constantes globales pour l’intégration IDF Mobilité Assistant.

Ce module regroupe les clés de configuration, les actions de menu,
ainsi que les mappings d’icônes et de libellés utilisés dans l’interface
et les flux de configuration.
"""

from datetime import time

DOMAIN = "idf_mobilite_assistant"

# Endpoints de l’API PRIM
PRIM_STOP_MONITORING_URL = (
    "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring"
)
PRIM_LINE_REPORTS_URL = (
    "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"
    "/line_reports/lines/{line_id}/line_reports"
)

# Intervalle de rafraîchissement par défaut, en secondes.
# 180 s ≈ 480 appels/jour/arrêt, compatible avec le quota PRIM
# de 1 000 requêtes/jour des comptes récents (60 s dépassait le quota).
DEFAULT_SCAN_INTERVAL = 180

# Bornes acceptées pour l’intervalle de rafraîchissement, en secondes
MIN_SCAN_INTERVAL = 60
MAX_SCAN_INTERVAL = 3600

# Fenêtre de pause nocturne (heure locale) : aucun appel PRIM entre les deux,
# le réseau étant interrompu. Les capteurs conservent leur dernier état.
NIGHT_PAUSE_START = time(1, 30)
NIGHT_PAUSE_END = time(5, 30)

# Délai maximal d’une requête vers PRIM, en secondes
REQUEST_TIMEOUT = 30

# Clés de configuration
CONF_API_KEY = "api_key"
CONF_MONITORING_REF = "monitoring_ref"
CONF_NAME = "name"
CONF_STOP_ID = "stop_id"

# Clés d’options
CONF_SCAN_INTERVAL = "scan_interval"
CONF_NIGHT_PAUSE = "night_pause"

# Actions du menu principal
MENU_ADD_LIGNE = "add_ligne"
MENU_ADD_MESSAGE = "add_message"
MENU_DELETE = "delete"
MENU_REFRESH = "refresh_settings"
MENU_UPDATE_API = "update_api"
MENU_EXIT = "exit"

# Icônes associées aux modes de transport
ICON_MAP = {
    "bus": "🚍",
    "metro": "🚇",
    "subway": "🚇",
    "tramway": "🚊",
    "tram": "🚊",
    "rail": "🚆",
    "transilien": "🚆",
    "ter": "🚆",
    "rer": "🚆",
    "cableway": "🚡",
    "rapidtransit": "🚆",
    "train": "🚈",
    "night_bus": "🌙",
    "multimodal": "🚆🚇🚍",
    "other": "❓",
}

# Libellés affichés dans les menus de sélection
MODE_LABELS = {
    "all": "🔍 Localisation (ex: Gare du Nord, Créteil)",
    "bus": "🚍 Bus",
    "metro": "🚇 Métro",
    "rer": "🚆 RER",
    "tram": "🚊 Tramway",
    "cableway": "🚡 Téléphérique",
    "transilien": "🚈 Transilien",
    "ter": "🚈 TER / Intercités",
    "noctilien": "🌙 Noctilien",
}

# Placeholders affichés dans les champs de recherche
PLACEHOLDERS = {
    "all": "Ex: Gare du Nord, Créteil",
    "bus": "Ex: 206, 210, 317",
    "metro": "Ex: 1, 7, 14",
    "rer": "Ex: A, B, C",
    "tram": "Ex: T1, T2, T3b",
    "transilien": "Ex: J, L, P",
    "noctilien": "Ex: N34, N130",
}
