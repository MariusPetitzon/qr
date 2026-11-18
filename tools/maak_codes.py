"""
Leest de map media/ en maakt daaruit:
  - codes.js : welke QR-code naar welke pagina gaat (media + lokcodes)
  - media.js : per mediabestand: soort, bron, naam, label

Regels voor media/:
  - Eerste niveau = activiteit (Koken, Carting, ...). Dieper mag (Koken/Groentekaart_win/...).
  - Elk bestand krijgt een EIGEN QR-code: foto/gif, audio, video, of een link (.url / .txt met alleen een link).
  - YouTube-links worden op de pagina getoond, GIPHY-links als GIF.
  - X.txt naast X.jpg (zelfde naam) = tekst onder die afbeelding (geen eigen QR-code).
  - LEESMIJ.txt wordt genegeerd.
  - Bestaande codes veranderen nooit, zolang je een bestand niet hernoemt of verplaatst.

Gebruik:  python3 maak_codes.py
"""
import json
import re
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT if (ROOT / "index.html").exists() else ROOT / "site"
MEDIA = SITE / "media"
CODES_JS = SITE / "codes.js"
MEDIA_JS = SITE / "media.js"
AANTALLEN = ROOT / "tools" / "aantallen.json"
ALFABET = "abcdefghjkmnpqrstuvwxyz23456789"   # zonder i, l, o, 0, 1

BEELD = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
AUDIO = {".mp3", ".m4a", ".wav", ".ogg", ".aac"}
VIDEO = {".mp4", ".webm", ".mov", ".m4v"}
LINK = {".url", ".txt"}
NEGEER = {"leesmij.txt", "desktop.ini", "thumbs.db", ".ds_store"}


def lees_js(pad: Path) -> dict:
    if not pad.exists():
        return {}
    t = pad.read_text(encoding="utf-8")
    return json.loads(t[t.index("{"): t.rindex("}") + 1])


def schrijf_js(pad: Path, naam: str, data: dict):
    pad.write_text(f"// AUTOMATISCH GEMAAKT door tools/maak_codes.py. Niet met de hand aanpassen.\n"
                   f"const {naam} = {json.dumps(data, ensure_ascii=False, indent=2)};\n", encoding="utf-8")


def lees_link(pad: Path):
    t = pad.read_text(encoding="utf-8", errors="ignore")
    if pad.suffix.lower() == ".url":
        m = re.search(r"^URL=(\S+)", t, re.M)
        return m.group(1) if m else None
    regels = [r.strip() for r in t.splitlines() if r.strip()]
    return regels[0] if len(regels) == 1 and re.match(r"https?://", regels[0]) else None


def nette_naam(stam: str) -> str:
    for staart in [" - YouTube", " - Find & Share on GIPHY"]:
        if stam.endswith(staart):
            stam = stam[: -len(staart)]
    return stam.strip()


def beschrijf(pad: Path):
    """Geeft (soort, gegevens) of None als het geen mediabestand is."""
    ext = pad.suffix.lower()
    rel = pad.relative_to(SITE).as_posix()
    if ext in BEELD:
        return {"soort": "beeld", "src": rel}
    if ext in AUDIO:
        return {"soort": "audio", "src": rel}
    if ext in VIDEO:
        return {"soort": "video", "src": rel}
    if ext in LINK:
        url = lees_link(pad)
        if not url:
            return None
        yt = re.search(r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([\w-]{11})", url)
        if yt:
            return {"soort": "youtube", "id": yt.group(1), "link": url}
        gp = re.search(r"giphy\.com/(?:gifs|media|embed)/(?:[\w-]*-)?(\w+)", url)
        if gp:
            gid = gp.group(1)
            return {"soort": "giphy", "src": f"https://media.giphy.com/media/{gid}/giphy.gif", "link": url}
        return {"soort": "link", "link": url}
    return None


def scan_media():
    items, overgeslagen = {}, []
    if not MEDIA.exists():
        return items, overgeslagen
    alle = sorted(p for p in MEDIA.rglob("*") if p.is_file())
    stammen = {(p.parent, p.stem.lower()) for p in alle if p.suffix.lower() in BEELD | AUDIO | VIDEO}
    for p in alle:
        if p.name.lower() in NEGEER or p.name.startswith("."):
            continue
        ext = p.suffix.lower()
        # X.txt naast X.jpg = tekst bij die afbeelding
        if ext == ".txt" and (p.parent, p.stem.lower()) in stammen and not lees_link(p):
            continue
        # .mpeg/.mpg: overslaan als er een .mp3/.mp4 met dezelfde naam naast staat
        if ext in {".mpeg", ".mpg"}:
            if any((p.parent, p.stem.lower()) == s for s in stammen):
                continue
            overgeslagen.append((p, "niet afspeelbaar op gsm; zet om naar .mp3 of .mp4"))
            continue
        info = beschrijf(p)
        if info is None:
            overgeslagen.append((p, "onbekend bestandstype of geen link gevonden"))
            continue
        rel = p.relative_to(MEDIA)
        delen = list(rel.parts)
        info["map"] = delen[0] if len(delen) > 1 else ""
        info["groep"] = " - ".join(delen[1:-1])
        info["naam"] = nette_naam(p.stem)
        info["label"] = " - ".join(x for x in [info["map"], info["groep"], info["naam"]] if x)
        tekst = p.with_suffix(".txt")
        if ext != ".txt" and tekst.exists() and not lees_link(tekst):
            info["tekst"] = tekst.read_text(encoding="utf-8", errors="ignore").strip()
        items[rel.as_posix()] = info
    return items, overgeslagen


def nieuwe_code(bestaand) -> str:
    while True:
        c = "".join(secrets.choice(ALFABET) for _ in range(4))
        if c not in bestaand:
            return c


def main():
    cfg = json.loads(AANTALLEN.read_text(encoding="utf-8"))
    oud = lees_js(CODES_JS)
    items, overgeslagen = scan_media()

    codes, nieuw, weg = {}, 0, 0
    # 1. media: bestaande code behouden, anders een nieuwe
    per_pad = {v[len("media:"):]: k for k, v in oud.items() if v.startswith("media:")}
    for rel in items:
        code = per_pad.get(rel) or nieuwe_code(set(oud) | set(codes))
        nieuw += rel not in per_pad
        codes[code] = f"media:{rel}"
    weg = sum(1 for rel in per_pad if rel not in items)
    # 2. lokcodes: bestaande behouden, aanvullen tot het gevraagde aantal
    for soort, aantal in cfg["lok"].items():
        bestaand = [k for k, v in oud.items() if v == soort]
        for k in bestaand:
            codes[k] = soort
        for _ in range(max(0, aantal - len(bestaand))):
            codes[nieuwe_code(set(oud) | set(codes))] = soort

    schrijf_js(CODES_JS, "CODES", codes)
    schrijf_js(MEDIA_JS, "MEDIA", items)

    print(f"{len(items)} mediabestanden ({nieuw} nieuw), "
          f"{sum(1 for v in codes.values() if not v.startswith('media:'))} lokcodes.")
    if weg:
        print(f"LET OP: {weg} code(s) van verdwenen of hernoemde bestanden zijn vervallen.")
    for p, reden in overgeslagen:
        print(f"  overgeslagen: {p.relative_to(MEDIA)}  ({reden})")


if __name__ == "__main__":
    main()
