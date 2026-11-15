"""
Maakt alle QR-codes (met foto in het midden) en twee printbare A4-PDF's (3 x 4 per pagina).

Gebruik:
    python3 maak_qr.py --basis https://mariuspetitzon.github.io/qr/ --foto foto.jpg

Leest site/codes.js (welke code naar welke pagina) en site/inhoud.js (titels).
Schrijft naar output/:
    qr/<soort>_<code>.png        losse QR-codes
    kaarten_activiteiten.pdf     de echte activiteiten + spiekbriefje
    kaarten_lokcodes.pdf         alle lokcodes (door elkaar gehusseld)
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
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

HIER = Path(__file__).resolve().parent
ROOT = HIER.parent
SITE = ROOT if (ROOT / "index.html").exists() else ROOT / "site"
KOLOMMEN, RIJEN = 3, 4
CEL_CM, QR_CM = 6.6, 6.0          # kaartje en QR-code (incl. witte rand)


def lees_codes():
    t = (SITE / "codes.js").read_text(encoding="utf-8")
    return json.loads(t[t.index("{"): t.rindex("}") + 1])


def lees_titels():
    t = (SITE / "inhoud.js").read_text(encoding="utf-8")
    t = t[t.index("const ACTIVITEITEN"): t.index("const LOKPAGINAS")]
    return {int(n): titel for n, titel in re.findall(r'nummer:\s*(\d+),\s*titel:\s*"([^"]*)"', t)}


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


def raster(c, kaarten):
    """Tekent kaarten 3 x 4 per pagina. Geeft (pagina, rij, kolom) per kaart terug."""
    W, H = A4
    k, q = CEL_CM * cm, QR_CM * cm
    mx, my = (W - KOLOMMEN * k) / 2, (H - RIJEN * k) / 2
    per = KOLOMMEN * RIJEN
    pos = []
    for i, img in enumerate(kaarten):
        if i and i % per == 0:
            c.showPage()
        j = i % per
        kol, rij = j % KOLOMMEN, j // KOLOMMEN
        x0, y0 = mx + kol * k, H - my - (rij + 1) * k
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setDash(2, 3)
        c.setLineWidth(0.4)
        c.rect(x0, y0, k, k)
        c.drawImage(ImageReader(img), x0 + (k - q) / 2, y0 + (k - q) / 2, q, q)
        pos.append((i // per + 1, rij + 1, kol + 1))
    return pos


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--basis", required=True, help="bv. https://mariuspetitzon.github.io/qr/")
    p.add_argument("--foto", type=Path, help="foto voor in het midden (optioneel)")
    p.add_argument("--fractie", type=float, default=0.27, help="fotodiameter als deel van de codebreedte")
    p.add_argument("--schaal", type=int, default=20, help="pixels per module in de PNG's")
    args = p.parse_args()

    basis = args.basis if args.basis.endswith("/") else args.basis + "/"
    codes = lees_codes()
    titels = lees_titels()
    uitmap = ROOT / "output" / "qr"
    uitmap.mkdir(parents=True, exist_ok=True)
    for oud in uitmap.glob("*.png"):
        oud.unlink()

    # foto één keer voorbereiden (alle codes hebben dezelfde grootte)
    _, _, modules = maak_qr(basis + "?xxxx", None, args.schaal)
    foto_rond = None
    if args.foto:
        diameter = int(modules * args.schaal * args.fractie)
        foto_rond = ronde_foto(args.foto, diameter, rand=int(args.schaal * 0.6))

    det = cv2.QRCodeDetector()
    acts, lok, fouten, versies = [], [], [], Counter()
    for code, doel in codes.items():
        url = f"{basis}?{code}"
        img, versie, _ = maak_qr(url, foto_rond, args.schaal)
        versies[versie] += 1
        if not leesbaar(img, url, det):
            fouten.append(url)
        img.save(uitmap / f"{doel.replace(':', '')}_{code}.png")
        if doel.startswith("activiteit:"):
            acts.append((int(doel.split(":")[1]), code, img))
        else:
            lok.append((doel, code, img))

    acts.sort(key=lambda a: a[0])
    random.Random(42).shuffle(lok)      # soorten door elkaar, maar elke keer dezelfde volgorde

    # --- PDF 1: activiteiten + spiekbriefje ---
    W, H = A4
    c = canvas.Canvas(str(ROOT / "output" / "kaarten_activiteiten.pdf"), pagesize=A4)
    pos = raster(c, [img for _, _, img in acts])
    c.showPage()
    c.setDash()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, H - 2 * cm, "Spiekbriefje - activiteiten")
    c.setFont("Helvetica", 10)
    y = H - 3.2 * cm
    for (nummer, code, img), (pag, rij, kol) in zip(acts, pos):
        c.drawImage(ImageReader(img), 2 * cm, y - 0.9 * cm, 1.5 * cm, 1.5 * cm)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(4 * cm, y, f"#{nummer}  {titels.get(nummer, '')}")
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(4 * cm, y - 0.5 * cm, f"pagina {pag}, rij {rij}, kolom {kol}   ·   ?{code}")
        y -= 2.0 * cm
        if y < 3 * cm:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = H - 2.5 * cm
    c.setFillColorRGB(0, 0, 0)
    c.drawString(2 * cm, y - 0.3 * cm, "Lokcodes (andere PDF, onderling verwisselbaar): " +
                 ", ".join(f"{s} {n}" for s, n in Counter(s for s, _, _ in lok).items()))
    c.save()

    # --- PDF 2: lokcodes ---
    c = canvas.Canvas(str(ROOT / "output" / "kaarten_lokcodes.pdf"), pagesize=A4)
    raster(c, [img for _, _, img in lok])
    c.save()

    per = KOLOMMEN * RIJEN
    print(f"{len(acts)} activiteiten ({-(-len(acts) // per)} pagina), "
          f"{len(lok)} lokcodes ({-(-len(lok) // per)} pagina's). QR-versie(s): {dict(versies)}")
    print("Alles leesbaar." if not fouten else f"LET OP, niet betrouwbaar leesbaar: {fouten}")


if __name__ == "__main__":
    main()
