"""
Zorgt dat site/codes.js genoeg codes bevat voor de aantallen in tools/aantallen.json.

- Bestaande codes worden NOOIT gewijzigd of verwijderd (ze kunnen al geprint zijn).
- Ontbrekende codes worden toegevoegd met een willekeurige, unieke code van 4 tekens.

Gebruik:  python3 maak_codes.py
"""
import json
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT if (ROOT / "index.html").exists() else ROOT / "site"
CODES_JS = SITE / "codes.js"
AANTALLEN = ROOT / "tools" / "aantallen.json"
PREFIX = "// AUTOMATISCH GEMAAKT door tools/maak_codes.py. Niet met de hand aanpassen.\nconst CODES = "
ALFABET = "abcdefghjkmnpqrstuvwxyz23456789"   # zonder i, l, o, 0, 1


def lees_codes() -> dict:
    if not CODES_JS.exists():
        return {}
    tekst = CODES_JS.read_text(encoding="utf-8")
    return json.loads(tekst[tekst.index("{"): tekst.rindex("}") + 1])


def schrijf_codes(codes: dict):
    regels = ",\n".join(f'  "{k}": "{v}"' for k, v in codes.items())
    CODES_JS.write_text(PREFIX + "{\n" + regels + "\n};\n", encoding="utf-8")


def nieuwe_code(bestaand) -> str:
    while True:
        c = "".join(secrets.choice(ALFABET) for _ in range(4))
        if c not in bestaand:
            return c


def main():
    cfg = json.loads(AANTALLEN.read_text(encoding="utf-8"))
    codes = lees_codes()
    toegevoegd = 0

    aanwezig = {v for v in codes.values()}
    for n in range(1, cfg["activiteiten"] + 1):
        doel = f"activiteit:{n}"
        if doel not in aanwezig:
            codes[nieuwe_code(codes)] = doel
            toegevoegd += 1

    for soort, aantal in cfg["lok"].items():
        huidig = sum(1 for v in codes.values() if v == soort)
        for _ in range(max(0, aantal - huidig)):
            codes[nieuwe_code(codes)] = soort
            toegevoegd += 1

    schrijf_codes(codes)
    print(f"{toegevoegd} codes toegevoegd, {len(codes)} in totaal.")


if __name__ == "__main__":
    main()
