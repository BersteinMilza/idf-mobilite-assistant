"""Package des fichiers utilitaires."""

from __future__ import annotations

from typing import Any


def as_record_list(value: Any) -> list[dict[str, Any]]:
    """Normaliser une valeur de config_entry en liste d’enregistrements.

    Les versions ≤ 0.1.0 pouvaient enregistrer un dict au lieu d’une liste
    lors de la création du tout premier capteur de messages. On tolère les
    deux formes afin de ne pas casser les entrées déjà existantes.
    """
    if not value:
        return []

    if isinstance(value, dict):
        return [value]

    return [item for item in value if isinstance(item, dict)]
