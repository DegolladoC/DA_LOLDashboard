#!/usr/bin/env python3
import sys
from getpass import getpass
from pathlib import Path

import httpx
from dotenv import set_key

ENV_PATH = Path(__file__).parent / ".env"
VALIDATION_URL = "https://la1.api.riotgames.com/lol/platform/v3/champion-rotations"


def validate_key(key: str) -> bool | None:
    """True si Riot acepta la key, False si la rechaza, None si no se pudo verificar (ej. sin internet)."""
    try:
        response = httpx.get(VALIDATION_URL, headers={"X-Riot-Token": key}, timeout=5.0)
    except httpx.HTTPError:
        return None
    if response.status_code == 200:
        return True
    if response.status_code in (401, 403):
        return False
    return None


def main() -> None:
    key = getpass("Pega tu nueva RIOT_API_KEY (no se mostrará en pantalla): ").strip()

    if not key:
        print("No se ingresó ninguna key, cancelado.")
        sys.exit(1)

    if not key.startswith("RGAPI-"):
        print("Advertencia: las Development API Keys de Riot normalmente empiezan con 'RGAPI-'.")

    print("Validando contra la Riot API...")
    is_valid = validate_key(key)

    if is_valid is False:
        print("Riot rechazó la key (401/403) — probablemente esté mal copiada o ya caducada. No se guardó.")
        sys.exit(1)
    if is_valid is None:
        print("No se pudo verificar contra Riot (¿sin internet?) — se guarda sin validar.")
    else:
        print("Key válida.")

    ENV_PATH.touch(exist_ok=True)
    set_key(str(ENV_PATH), "RIOT_API_KEY", key)
    masked = f"{key[:9]}...{key[-4:]}" if len(key) > 13 else "***"
    print(f"Guardada en {ENV_PATH} ({masked})")


if __name__ == "__main__":
    main()
