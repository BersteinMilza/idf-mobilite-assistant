# Changelog
Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au principe de versionnage sémantique (SemVer).

---

## [0.1.0] - 2026-06-18
### Ajouté
- Première version publique de l’intégration **IDF Mobilité Assistant**.
- Support complet des capteurs d’horaires (lignes) basés sur l’API PRIM / Navitia.
- Support complet des capteurs de messages (perturbations) par ligne.
- Interface de configuration 100% UI (aucun YAML requis).
- Recherche d’arrêt et de ligne directement dans le flux de configuration.
- Gestion propre des entités : création, suppression définitive, regroupement par type.
- Icônes dynamiques selon le mode de transport (Bus, Métro, Tram, RER, Transilien…).
- Icône dédiée pour les capteurs de messages.
- Compatibilité totale avec la Lovelace Card :
  **Ile de France Mobilité Card** (https://github.com/yyrkoon94/lovelace-idf-mobilite)
- Ajout du fichier `hacs.json` pour compatibilité HACS.
- Ajout des métadonnées nécessaires dans `manifest.json` (version, documentation, issue tracker).
- Première release GitHub.

---

## [Unreleased]
### Corrigé
- **Quota PRIM** : les capteurs interrogeaient l'API toutes les 60 secondes et par
  capteur (1 440 appels/jour), au-delà du quota de 1 000 requêtes/jour des comptes
  récents. Le rafraîchissement est désormais mutualisé dans un `DataUpdateCoordinator`
  unique par entrée, toutes les 180 secondes (≈ 480 appels/jour).
- Les appels sont dédupliqués : deux capteurs sur le même arrêt (ou la même ligne)
  ne déclenchent plus qu'une seule requête par cycle.
- Ajout du premier capteur de messages : la liste était enregistrée sous forme de
  dictionnaire, ce qui empêchait d'ajouter un second capteur et cassait la création
  des entités. Les entrées existantes sont désormais tolérées et corrigées.
- Une clé API refusée (HTTP 401/403) déclenche maintenant le flux de
  réauthentification de Home Assistant au lieu de laisser les capteurs sur un
  statut `API_KEY_ERROR`.
- Suppression de `device_class: "idf_mobilite"`, qui n'est pas une classe de
  capteur Home Assistant valide (et que la carte Lovelace n'utilise pas).
- Suppression de la vérification TLS désactivée (`ssl=False`) sur les appels PRIM.

### Modifié
- Le `ClientSession` aiohttp est remplacé par la session partagée de Home Assistant.
- Les capteurs deviennent `unavailable` lorsque l'API est réellement injoignable,
  au lieu de masquer l'erreur dans l'état.
- Suppression d'une branche morte dans l'étape `select_stop_area`.

### Ajouté
- **`OptionsFlow`** : l'intégration expose enfin un bouton **Configurer**.
  Il reprend toutes les étapes existantes (ajouter une ligne, ajouter un message,
  supprimer, mettre à jour la clé API) via les mêmes mixins que le flux de
  configuration, sans duplication de logique.
- **Intervalle de rafraîchissement réglable** (60 → 3 600 s) et **pause nocturne**
  optionnelle (aucun appel entre 01:30 et 05:30, dernier état conservé).
- Traductions complétées : les étapes `search_line`, `select_line` et
  `update_api_key` n'avaient aucun libellé et s'affichaient sous forme de clés
  brutes. Les erreurs `empty_code`, `invalid_selection` et l'abandon `no_entries`
  sont désormais traduits, en français et en anglais.
- Espace de traduction `options` (étapes, erreurs, abandons) pour le flux d'options.
- Tests de non-régression pour le réglage du rafraîchissement.

### Prévu
- Améliorations mineures et correctifs selon retours utilisateurs.
- Migration vers une arborescence `custom_components/` standard.
- Adoption de `pytest-homeassistant-custom-component` (suppression du faux
  `custom_components/` reconstitué en CI).
