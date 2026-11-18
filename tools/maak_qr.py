"""
Maakt alle QR-codes en twee printbare A4-PDF's (3 x 4 per pagina, met de naam boven elke code).

Gebruik:
    python3 maak_qr.py --basis https://mariuspetitzon.github.io/qr/
    (foto in het midden: heidigom.jpg in de hoofdmap wordt automatisch gebruikt, of --foto pad)

Leest codes.js en media.js (eerst tools/maak_codes.py draaien). Schrijft naar output/:
    qr/<label>_<code>.png      losse QR-codes, met naam erboven
    kaarten_media.pdf          alle media-codes (gesorteerd per map) + spiekbriefje
    kaarten_lokcodes.pdf       alle lokcodes (door elkaar gehusseld)
"""
import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import segno
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

HIER = Path(__file__).resolve().parent
ROOT = HIER.parent
SITE = ROOT if (ROOT / "index.html").exists() else ROOT / "site"
KOLOMMEN, RIJEN = 3, 4
CEL_CM, QR_CM = 6.6, 5.7          # kaartje en QR-code (incl. witte rand)
LABEL_CM = 0.55                   # band boven de QR-code voor de naam


def lees_js(naam):
    t = (SITE / naam).read_text(encoding="utf-8")
    return json.loads(t[t.index("{"): t.rindex("}") + 1])


def ronde_foto(pad: Path, diameter: int, rand: int) -> Image.Image:
    foto = ImageOps.exif_transpose(Image.open(pad)).convert("RGB")
    foto = ImageOps.fit(foto, (diameter, diameter), Image.LANCZOS)
    masker = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(masker).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    totaal = diameter + 2 * rand
    uit = Image.new("RGBA", (totaal, totaal), (0, 0, 0, 0))
    ImageDraw.Draw(uit).ellipse((0, 0, totaal - 1, totaal - 1), fill=(255, 255, 255, 255))
    uit.paste(foto, (rand, rand), masker)
    return uit


def maak_qr(url: str, foto_rond, schaal: int):
    qr = segno.make(url, error="h", boost_error=False)
    tmp = HIER / "_tmp_qr.png"
    qr.save(tmp, scale=schaal, border=4)
    img = Image.open(tmp).convert("RGBA")
    tmp.unlink()
    if foto_rond is not None:
        x = (img.width - foto_rond.width) // 2
        img.alpha_composite(foto_rond, (x, x))
    return img.convert("RGB"), qr.version, qr.symbol_size(scale=1, border=0)[0]


def leesbaar(img: Image.Image, url: str, det) -> bool:
    """Leest de code terug: groot, klein (~ telefoon op afstand) en klein + wazig."""
    for breedte, blur in [(1000, 0), (300, 0), (300, 1.0)]:
        t = img.resize((breedte, breedte), Image.LANCZOS)
        if blur:
            t = t.filter(ImageFilter.GaussianBlur(blur))
        data, _, _ = det.detectAndDecode(cv2.cvtColor(np.array(t), cv2.COLOR_RGB2BGR))
        if data != url:
            return False
    return True


def met_label(img: Image.Image, label: str) -> Image.Image:
    """PNG met een witte band en de naam erboven."""
    band = int(img.width * 0.09)
    uit = Image.new("RGB", (img.width, img.height + band), "white")
    uit.paste(img, (0, band))
    d = ImageDraw.Draw(uit)
    font = ImageFont.load_default(size=int(band * 0.55))
    tekst = label
    while d.textlength(tekst, font=font) > img.width * 0.94 and len(tekst) > 4:
        tekst = tekst[:-2].rstrip("…").rstrip() + "…"
    d.text((img.width / 2, band * 0.6), tekst, font=font, fill="black", anchor="mm")
    return uit


def past(c, tekst, font, grootte, breedte):
    while c.stringWidth(tekst, font, grootte) > breedte and len(tekst) > 4:
        tekst = tekst[:-2].rstrip("…").rstrip() + "…"
    return tekst


def raster(c, kaarten):
    """Tekent kaarten (img, label) 3 x 4 per pagina. Geeft (pagina, rij, kolom) per kaart terug."""
    W, H = A4
    k, q, band = CEL_CM * cm, QR_CM * cm, LABEL_CM * cm
    mx, my = (W - KOLOMMEN * k) / 2, (H - RIJEN * k) / 2
    per = KOLOMMEN * RIJEN
    pos = []
    for i, (img, label) in enumerate(kaarten):
        if i and i % per == 0:
            c.showPage()
        j = i % per
        kol, rij = j % KOLOMMEN, j // KOLOMMEN
        x0, y0 = mx + kol * k, H - my - (rij + 1) * k
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setDash(2, 3)
        c.setLineWidth(0.4)
        c.rect(x0, y0, k, k)
        onder = (k - band - q) / 2
        c.drawImage(ImageReader(img), x0 + (k - q) / 2, y0 + onder, q, q)
        if label:
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 8)
            c.drawCentredString(x0 + k / 2, y0 + onder + q + band * 0.35,
                                past(c, label, "Helvetica", 8, k - 0.4 * cm))
        pos.append((i // per + 1, rij + 1, kol + 1))
    return pos


def veilig(tekst: str) -> str:
    return re.sub(r"[^\w\-]+", "_", tekst).strip("_")[:60]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--basis", required=True, help="bv. https://mariuspetitzon.github.io/qr/")
    p.add_argument("--foto", type=Path, help="foto voor in het midden (standaard: heidigom.jpg als die bestaat)")
    p.add_argument("--fractie", type=float, default=0.27, help="fotodiameter als deel van de codebreedte")
    p.add_argument("--schaal", type=int, default=20, help="pixels per module in de PNG's")
    args = p.parse_args()

    basis = args.basis if args.basis.endswith("/") else args.basis + "/"
    codes = lees_js("codes.js")
    media = lees_js("media.js")
    uitmap = ROOT / "output" / "qr"
    uitmap.mkdir(parents=True, exist_ok=True)
    for oud in uitmap.glob("*.png"):
        oud.unlink()

    foto = args.foto
    if foto is None:
        for kandidaat in [SITE / "heidigom.jpg", ROOT / "heidigom.jpg", SITE / "heidigom.png"]:
            if kandidaat.exists():
                foto = kandidaat
                break
    foto_rond = None
    if foto:
        _, _, modules = maak_qr(basis + "?xxxx", None, args.schaal)
        foto_rond = ronde_foto(foto, int(modules * args.schaal * args.fractie), rand=int(args.schaal * 0.6))

    det = cv2.QRCodeDetector()
    media_kaarten, lok, fouten, versies = [], [], [], Counter()
    for code, doel in codes.items():
        url = f"{basis}?{code}"
        img, versie, _ = maak_qr(url, foto_rond, args.schaal)
        versies[versie] += 1
        if not leesbaar(img, url, det):
            fouten.append(url)
        if doel.startswith("media:"):
            rel = doel[6:]
            label = media.get(rel, {}).get("label", rel)
            media_kaarten.append((rel, code, img, label))
        else:
            label = f"lokcode: {doel}"
            lok.append((doel, code, img, label))
        met_label(img, label).save(uitmap / f"{veilig(label)}_{code}.png")

    media_kaarten.sort(key=lambda a: a[0].lower())
    random.Random(42).shuffle(lok)      # soorten door elkaar, maar elke keer dezelfde volgorde

    # --- PDF 1: media + spiekbriefje ---
    W, H = A4
    c = canvas.Canvas(str(ROOT / "output" / "kaarten_media.pdf"), pagesize=A4)
    pos = raster(c, [(img, label) for _, _, img, label in media_kaarten])
    c.showPage()
    c.setDash()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, H - 2 * cm, "Spiekbriefje - media")
    c.setFont("Helvetica", 9)
    y = H - 3 * cm
    for (rel, code, img, label), (pag, rij, kol) in zip(media_kaarten, pos):
        c.setFillColorRGB(0, 0, 0)
        c.drawString(2 * cm, y, past(c, label, "Helvetica", 9, W - 9 * cm))
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(W - 6.5 * cm, y, f"p{pag} r{rij} k{kol}   ?{code}")
        y -= 0.55 * cm
        if y < 2 * cm:
            c.showPage()
            c.setFont("Helvetica", 9)
            y = H - 2 * cm
    c.setFillColorRGB(0, 0, 0)
    c.drawString(2 * cm, y - 0.4 * cm, "Lokcodes (andere PDF, onderling verwisselbaar): " +
                 ", ".join(f"{s} {n}" for s, n in Counter(s for s, _, _, _ in lok).items()))
    c.save()

    # --- PDF 1b: alleen de nieuwe media-codes van de laatste maak_codes.py ---
    nieuw_pad = ROOT / "tools" / "laatste_nieuw.json"
    nieuw = set(json.loads(nieuw_pad.read_text(encoding="utf-8"))) if nieuw_pad.exists() else set()
    nieuwe_kaarten = [(img, label) for _, code, img, label in media_kaarten if code in nieuw]
    if nieuwe_kaarten:
        c = canvas.Canvas(str(ROOT / "output" / "kaarten_nieuw.pdf"), pagesize=A4)
        raster(c, nieuwe_kaarten)
        c.save()
        print(f"{len(nieuwe_kaarten)} nieuwe kaarten apart in kaarten_nieuw.pdf")

    # --- PDF 2: lokcodes ---
    c = canvas.Canvas(str(ROOT / "output" / "kaarten_lokcodes.pdf"), pagesize=A4)
    raster(c, [(img, label) for _, _, img, label in lok])
    c.save()

    per = KOLOMMEN * RIJEN
    print(f"{len(media_kaarten)} media-codes ({-(-len(media_kaarten) // per)} pagina's), "
          f"{len(lok)} lokcodes ({-(-len(lok) // per)} pagina's). QR-versie(s): {dict(versies)}. "
          f"Foto: {foto.name if foto else 'geen'}")
    print("Alles leesbaar." if not fouten else f"LET OP, niet betrouwbaar leesbaar: {fouten}")


if __name__ == "__main__":
    main()
