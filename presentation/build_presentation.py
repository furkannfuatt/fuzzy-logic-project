"""Sunum üreteci (python-pptx). Çalıştırma: python presentation/build_presentation.py

Grafikler results/figures/ altından okunur (önce: python run_all.py).
Konuşmacı notları presentation/speaker_notes.json dosyasındadır.

Not: Sunum, PowerPoint'in kendi varsayılan şablonu (python-pptx) üzerinde yalnızca "Boş"
düzen, metin kutuları ve şekillerle kurulur. Özel yer tutucu (placeholder) / düzen
kullanılmaz; bu, sunumun PowerPoint, Keynote, LibreOffice ve macOS Hızlı Bakış'ta aynı
görünmesini sağlar.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIG = lambda f: ROOT / "results" / "figures" / f  # noqa: E731
ASSET = lambda f: HERE / "assets" / f  # noqa: E731
NOTES = json.loads((HERE / "speaker_notes.json").read_text(encoding="utf-8"))

NAVY, BLUE, ORANGE, GREEN, RED = "13243A", "2A78D6", "EB6834", "1BAF7A", "E34948"
GRAY, LIGHT, WHITE, TEXT, ICE = "5A6472", "EEF2F7", "FFFFFF", "1A1A1A", "CADCFC"
HEAD, BODY = "Cambria", "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
_slide_no = 0


def rgb(h):
    return RGBColor.from_string(h)


# ---------------------------------------------------------------- yardımcılar
def _fmt_run(run, size, bold=False, italic=False, color=TEXT, font=BODY):
    f = run.font
    f.size, f.bold, f.italic, f.name = Pt(size), bold, italic, font
    f.color.rgb = rgb(color)


def txt(s, content, x, y, w, h, size=16, bold=False, italic=False, color=TEXT, font=BODY,
        align="l", valign="t", margin=True):
    """content: str  ya da  [(metin, {bold, italic, color, font, br}), ...]"""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[valign]
    if not margin:
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    runs = [(content, {})] if isinstance(content, str) else content
    p = tf.paragraphs[0]
    p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
    for text, o in runs:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if i > 0:
                p = tf.add_paragraph(); p.alignment = tf.paragraphs[0].alignment
            r = p.add_run(); r.text = line
            _fmt_run(r, o.get("size", size), o.get("bold", bold), o.get("italic", italic),
                     o.get("color", color), o.get("font", font))
        if o.get("br"):
            p = tf.add_paragraph(); p.alignment = tf.paragraphs[0].alignment
    return tb


def bullets(s, items, x, y, w, h, size=16, color=TEXT, space=8):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(Inches(0.3))); pPr.set("indent", str(-Inches(0.3)))
        bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
        pPr.append(bu)
        p.space_after = Pt(space)
        r = p.add_run(); r.text = item
        _fmt_run(r, size, color=color)
    return tb


def shape(s, kind, x, y, w, h, fill, radius=None):
    shp = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
    shp.line.fill.background()
    style = shp._element.find(qn("p:style"))      # tema stilini (gölge vb.) kaldır
    if style is not None:
        shp._element.remove(style)
    if radius is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = min(0.5, radius / min(w, h))
    return shp


def box(s, x, y, w, h, fill=LIGHT, radius=0.12):
    return shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, radius)


def dot(s, x, y, d, fill):
    return shape(s, MSO_SHAPE.OVAL, x, y, d, d, fill)


def card(s, x, y, w, h, head, body, color, size=14):
    box(s, x, y, w, h)
    dot(s, x + 0.25, y + 0.25, 0.42, color)
    txt(s, head, x + 0.8, y + 0.18, w - 1.0, 0.55, 17, bold=True, color=NAVY, valign="m", margin=False)
    txt(s, body, x + 0.25, y + 0.85, w - 0.5, h - 1.0, size)


def card_list(s, x, y, w, h, head, items, color):
    box(s, x, y, w, h)
    dot(s, x + 0.25, y + 0.25, 0.42, color)
    txt(s, head, x + 0.8, y + 0.18, w - 1.0, 0.55, 17, bold=True, color=NAVY, valign="m", margin=False)
    bullets(s, items, x + 0.3, y + 0.9, w - 0.6, h - 1.0, size=14, space=10)


def stat(s, x, y, w, big, label, color):
    txt(s, big, x, y, w, 1.0, 48, bold=True, color=color, font=HEAD, margin=False)
    txt(s, label, x, y + 1.0, w, 0.8, 14, color=GRAY, margin=False)


def img(s, path, x, y, w=None, h=None):
    """En-boy oranını koruyarak (w ya da h verilir; ikisi de verilirse kutuya sığdırılır)."""
    iw, ih = Image.open(path).size
    if w and h:
        scale = min(w / iw, h / ih); w2, h2 = iw * scale, ih * scale
        x, y = x + (w - w2) / 2, y + (h - h2) / 2
    elif w:
        w2, h2 = w, w * ih / iw
    else:
        w2, h2 = h * iw / ih, h
    s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w2), Inches(h2))
    return y + h2


def caption(s, t, y, x=0.6, w=12.1):
    txt(s, t, x, y, w, 0.4, 11, italic=True, color=GRAY, margin=False)


def table(s, rows, x, y, col_w, row_h=0.5, size=14, first_left=True, bold_rows=(), highlight=None):
    nr, nc = len(rows), len(rows[0])
    gt = s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(sum(col_w)), Inches(row_h * nr))
    tbl = gt.table
    tbl.first_row = True
    tblPr = tbl._tbl.tblPr
    for el in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(el)
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i in range(nr):
        tbl.rows[i].height = Inches(row_h)
        for j in range(nc):
            c = tbl.cell(i, j)
            c.fill.solid(); c.fill.fore_color.rgb = rgb(NAVY if i == 0 else (WHITE if i % 2 else "F6F8FB"))
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tcPr = c._tc.get_or_add_tcPr()
            for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                ln = tcPr.makeelement(qn(tag), {"w": "6350"})
                sf = ln.makeelement(qn("a:solidFill"), {})
                sf.append(sf.makeelement(qn("a:srgbClr"), {"val": "C8CED6"}))
                ln.append(sf)
                tcPr.append(ln)
            fill_el = tcPr.find(qn("a:solidFill"))       # şema sırası: çizgiler dolgudan önce
            if fill_el is not None:
                tcPr.remove(fill_el); tcPr.append(fill_el)
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if (j == 0 and first_left) else PP_ALIGN.CENTER
            r = p.add_run(); r.text = str(rows[i][j])
            col = WHITE if i == 0 else TEXT
            if highlight and (i, j) in highlight:
                col = highlight[(i, j)]
            _fmt_run(r, size, bold=(i == 0 or i in bold_rows or bool(highlight and (i, j) in highlight)), color=col)
    return gt


def new_slide(title=None, dark=False):
    global _slide_no
    _slide_no += 1
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill; bg.solid(); bg.fore_color.rgb = rgb(NAVY if dark else WHITE)
    if not dark:
        txt(s, title, 0.6, 0.35, 12.1, 0.9, 30, bold=True, color=NAVY, font=HEAD, valign="m", margin=False)
        txt(s, "Bulanık Mantık Dönem Projesi · F. F. Küçükbayrak", 0.6, 7.0, 8, 0.3, 10, color="8A93A0", margin=False)
        txt(s, str(_slide_no), 12.1, 7.0, 0.6, 0.3, 10, color="8A93A0", align="r", margin=False)
    note = NOTES[_slide_no - 1]
    if note:
        s.notes_slide.notes_text_frame.text = note
    return s


# ======================================================================= 1
s = new_slide(dark=True)
txt(s, "Bulanık Mantık Tabanlı Yorumlanabilirlik: ANFIS'in Yeniden Gerçekleştirilmesi ve Kompakt C-ANFIS",
    0.8, 1.7, 11.7, 2.2, 38, bold=True, color=WHITE, font=HEAD, valign="b", margin=False)
txt(s, [("Furkan Fuat Küçükbayrak · 1306230124", {"br": True}),
        ("İÜC Bilgisayar Mühendisliği · Bulanık Mantık Dönem Projesi 2026–2027 Güz", {"br": True}),
        ("Referans: H. Ouifak & A. Idri, Neurocomputing 647 (2025) 130602", {"italic": True})],
    0.8, 4.2, 11.7, 1.6, 18, color=ICE, margin=False)

# ======================================================================= 2
s = new_slide("Problem: doğru ama açıklanamayan modeller")
bullets(s, ["Kara kutu modeller (DNN, MLP, SVM) yüksek doğruluk sağlar, ama kararın nedenini açıklayamaz",
            "Tıp, finans, otonom sistemler: açıklanamayan karar = güven ve denetim sorunu",
            "Bulanık mantık: sayısal modeli dilsel kurallara çevirir",
            "İki ana yol (makale): (1) kara kutudan bulanık kural çıkarımı, (2) nöro-bulanık modelleme (ANFIS)"],
        0.6, 1.6, 6.6, 4.8)
box(s, 7.7, 1.7, 5.0, 3.9, NAVY, 0.15)
txt(s, "Bulanık kural örneği (projeden, WDBC)", 8.0, 1.9, 4.4, 0.5, 14, bold=True, color=ICE, margin=False)
txt(s, [("EĞER ", {"bold": True, "color": ICE}), ("mean concave points Yüksek ", {}),
        ("VE ", {"bold": True, "color": ICE}), ("worst area Yüksek ", {}),
        ("VE ", {"bold": True, "color": ICE}), ("worst concave points Yüksek", {"br": True}),
        ("İSE ", {"bold": True, "color": ICE}), ("malign", {"bold": True, "color": "F6B79E"})],
    8.0, 2.5, 4.4, 2.0, 18, color=WHITE, font=HEAD, margin=False)
txt(s, "Bir hekim bu kuralı okuyup kontrol edebilir.", 8.0, 4.8, 4.4, 0.6, 14, italic=True, color=ICE, margin=False)

# ======================================================================= 3
s = new_slide("Referans makale: 30 yılın sistematik derlemesi")
stat(s, 0.6, 1.6, 2.9, "330", "seçilen çalışma", BLUE)
stat(s, 3.7, 1.6, 2.9, "6", "dijital kütüphane (IEEE, ScienceDirect, PubMed, ACM, Wiley, Scholar)", BLUE)
stat(s, 6.8, 1.6, 2.9, "30 yıl", "kapsanan dönem: 1994 – Ocak 2024", BLUE)
stat(s, 9.9, 1.6, 2.9, "3 + 8", "haritalama + araştırma sorusu", BLUE)
box(s, 0.6, 4.1, 12.1, 2.4)
txt(s, "Önemli not: Bu bir derleme makalesidir — tek bir algoritma önermez", 0.9, 4.3, 11.5, 0.5, 18,
    bold=True, color=NAVY, margin=False)
txt(s, "Bu nedenle yeniden gerçekleştirme (MRR) şöyle tanımlandı: (R1) makalenin nicel analizinin (Borda "
       "sıralaması) yeniden üretimi, (R2) makalenin merkezî tekniği ANFIS'in sıfırdan yazılıp benchmark "
       "verilerinde makale medyanlarıyla karşılaştırılması, (R3) bulanık modellerle kara kutu açıklama ve "
       "fidelity ölçümü.", 0.9, 4.9, 11.5, 1.5, 15, margin=False)

# ======================================================================= 4
s = new_slide("Makalenin temel bulguları")
card(s, 0.6, 1.5, 5.9, 2.4, "ANFIS en çok kullanılan teknik",
     "19 çalışma · medyan doğruluk %95 · medyan 17 kural (Tablo 6, 9). En iyi performans–yorumlanabilirlik "
     "dengesine sahip tekniklerden biri.", BLUE)
card(s, 6.8, 1.5, 5.9, 2.4, "Açıklamalar kural tabanlı",
     "En çok açıklanan kara kutu: sinir ağları. En çok kullanılan veri tipi: tablo verisi.", GREEN)
card(s, 0.6, 4.15, 5.9, 2.4, "Yorumlanabilirlik = kural sayısı",
     "296 çalışma kural sayısını kullanıyor. MF sayısı (11) ve fidelity (8) çok daha az. Denge Borda "
     "sayımı ile sıralanıyor (Şekil 21).", ORANGE)
card(s, 6.8, 4.15, 5.9, 2.4, "Belirtilen sınırlılıklar",
     "Grid ANFIS'te kural patlaması (p^d), hesaplama maliyeti ve ölçeklenebilirlik, standart "
     "yorumlanabilirlik metriğinin olmaması.", RED)

# ======================================================================= 5
s = new_slide("Güncel literatür")
table(s, [["Çalışma", "Yöntem", "Ölçüt", "Projedeki rolü"],
          ["Jang (1993)", "Grid ANFIS, hibrit öğrenme", "—", "Baseline"],
          ["Setnes vd. (1998)", "Benzerlikle MF birleştirme", "MF sayısı", "C-ANFIS adım 3"],
          ["Nauck (2003)", "comp × cov × part indeksi", "Bileşik", "Ek metrik"],
          ["Gacto vd. (2011)", "Yorumlanabilirlik taksonomisi", "Karmaşıklık + anlamsal", "Metrik çerçevesi"],
          ["Huang vd. (2022)", "FCM + derin yama öğrenme", "Kural sayısı", "FCM ile kural üretimi"],
          ["Aghaeipoor vd. (2023)", "DNN için bulanık açıklayıcı", "Fidelity", "R3 deneyi"],
          ["Ouifak & Idri (2025)", "SLR, 330 çalışma", "Kural sayısı, Borda", "Referans makale"],
          ["Yin vd. (2025)", "Hiyerarşik model-agnostik", "Fidelity", "Güncel örnek"]],
      0.6, 1.5, [2.8, 3.6, 2.6, 3.1], row_h=0.55, size=14)

# ======================================================================= 6
s = new_slide("Bulanık küme, üyelik fonksiyonu ve çıkarım")
bullets(s, ["Bulanık küme: μA(x) ∈ [0, 1] — kısmi üyelik (Zadeh, 1965)",
            "Gauss MF: μ(x) = exp(−(x − c)² / 2σ²) — türevlenebilir, öğrenilebilir",
            "Dilsel değişken: worst area ∈ {Düşük, Orta, Yüksek}",
            "Mamdani: sonuç bulanık küme → ağırlık merkezi ile durulaştırma",
            "TSK (1. derece): sonuç f = p·[x, 1] → ağırlıklı ortalama",
            "VE: çarpım t-normu · Durulaştırma: Σ w̄ f"], 0.6, 1.6, 6.3, 5.0)
yb = img(s, FIG("mf_comparison.png"), 7.2, 1.55, w=5.6)
caption(s, "Grid ANFIS başlangıç (üst), eğitim sonrası (orta) ve C-ANFIS (alt) MF'leri — WDBC.", yb + 0.05, 7.2, 5.6)
box(s, 7.2, 5.55, 5.6, 1.1)
txt(s, "Projede: ANFIS → TSK-1 + Gauss MF  ·  Wang–Mendel → Mamdani + üçgen MF", 7.4, 5.6, 5.2, 1.0, 14,
    bold=True, color=NAVY, valign="m", margin=False)

# ======================================================================= 7
s = new_slide("ANFIS: 5 katmanlı mimari ve hibrit öğrenme")
layers = [("L1", "Bulanıklaştırma", "μ(x; c, σ)"), ("L2", "Kural ateşleme", "w = ∏ μ"),
          ("L3", "Normalizasyon", "w̄ = w / Σw"), ("L4", "Sonuç (TSK)", "w̄ · p·[x, 1]"), ("L5", "Toplama", "y = Σ w̄ f")]
for i, (l, n, f) in enumerate(layers):
    x = 0.6 + i * 2.5
    col = BLUE if i in (0, 3) else NAVY
    box(s, x, 1.6, 2.15, 1.9, col)
    txt(s, l, x, 1.72, 2.15, 0.45, 20, bold=True, color=WHITE, align="c", margin=False)
    txt(s, n, x, 2.2, 2.15, 0.45, 14, color=WHITE, align="c", margin=False)
    txt(s, f, x, 2.75, 2.15, 0.45, 14, italic=True, color=ICE, font=HEAD, align="c", margin=False)
    if i < 4:
        shape(s, MSO_SHAPE.RIGHT_ARROW, x + 2.18, 2.35, 0.3, 0.4, "9AA5B4")
txt(s, "Mavi katmanlar öğrenilebilir parametre içerir: L1 (c, σ) ve L4 (p).", 0.6, 3.65, 12, 0.4, 13,
    italic=True, color=GRAY, margin=False)
card(s, 0.6, 4.2, 5.9, 2.4, "İleri geçiş: LSE",
     "MF'ler sabitken çıktı p'ye göre doğrusaldır → p kapalı formda çözülür: (ΦᵀΦ + λI)p = Φᵀt "
     "(ridge, λ = 10⁻³).", BLUE)
card(s, 6.8, 4.2, 5.9, 2.4, "Geri geçiş: gradyan (Adam)",
     "∂E/∂log wᵣ = w̄ᵣ(gᵣ − Σ w̄q gq) — softmax türevi. Analitik gradyan sayısal türevle doğrulandı "
     "(bağıl hata < 10⁻⁵).", ORANGE)

# ======================================================================= 8
s = new_slide("Proje kapsamı: 3 yeniden üretim + 1 özgün katkı")
blocks = [("R1", "Borda yeniden üretimi", "Tablo 6 + 9 → Şekil 21", NAVY),
          ("R2", "ANFIS sıfırdan", "Iris · WDBC · Pima, 10-kat CV", NAVY),
          ("R3", "Kara kutu açıklama", "MLP → bulanık vekil, fidelity", NAVY),
          ("+", "C-ANFIS (katkı)", "FCM + birleştirme + budama", BLUE)]
for i, (k, h_, b, col) in enumerate(blocks):
    x = 0.6 + i * 3.1
    box(s, x, 1.6, 2.8, 3.0, col, 0.15)
    txt(s, k, x, 1.75, 2.8, 0.9, 40, bold=True, color=WHITE, font=HEAD, align="c", margin=False)
    txt(s, h_, x + 0.15, 2.8, 2.5, 0.7, 18, bold=True, color=WHITE, align="c", margin=False)
    txt(s, b, x + 0.15, 3.6, 2.5, 0.8, 14, color=WHITE if col == BLUE else ICE, align="c", margin=False)
bullets(s, ["Python 3 + NumPy: ANFIS, FCM, Wang–Mendel ve C-ANFIS hazır bulanık kütüphane kullanılmadan yazıldı",
            "Adil protokol: aynı kıvrımlar, aynı ön işleme; ölçekleme ve öznitelik seçimi yalnızca eğitim kıvrımında",
            "Tekrar üretilebilirlik: tek komut python run_all.py (~8 dk), tüm ham sonuçlar CSV olarak kaydedilir"],
        0.6, 4.95, 12.1, 1.8, size=15)

# ======================================================================= 9
s = new_slide("R1: Borda sıralaması 20/20 sistemde birebir üretildi")
img(s, FIG("r1_borda.png"), 0.6, 1.35, 8.2, 3.15)
stat(s, 9.2, 1.6, 3.5, "20 / 20", "sistemin doğruluk, kural ve tradeoff sırası Şekil 21 ile aynı", GREEN)
card(s, 0.6, 4.65, 5.9, 2.0, "Bulgu 1: Bağ politikası tutarsız",
     "Doğruluk: ordinal · kural: dense. Tutarlı 'min' politikasıyla ANFIS 3. sıradan 5. sıraya düşüyor.", ORANGE)
card(s, 6.8, 4.65, 5.9, 2.0, "Bulgu 2: Olası veri hatası",
     "Tablo 9'daki FRI doğruluk değerleri (4; 20; 11; 11,33; 5,22) Tablo 6'daki kural sayılarıyla birebir aynı.", RED)

# ======================================================================= 10
s = new_slide("R2: Sıfırdan ANFIS, makale medyanlarıyla uyumlu")
table(s, [["Model", "Iris", "WDBC", "Pima", "Kural"],
          ["Grid-ANFIS (2MF) — baseline", "95,3 ± 4,5", "93,8 ± 2,2", "74,9 ± 6,8", "16"],
          ["Grid-ANFIS (3MF)", "94,7 ± 5,3", "92,6 ± 3,2", "69,4 ± 5,3", "81"],
          ["Wang–Mendel (3MF)", "91,3 ± 4,5", "91,6 ± 4,7", "74,5 ± 3,6", "16–23"],
          ["Karar ağacı (d ≤ 4)", "94,0 ± 5,8", "92,1 ± 3,8", "74,3 ± 7,3", "7–16"],
          ["MLP (kara kutu)", "96,0 ± 3,4", "93,8 ± 3,0", "77,0 ± 5,9", "—"]],
      0.6, 1.5, [3.0, 1.25, 1.25, 1.25, 0.95], row_h=0.5, size=14, bold_rows=(1,))
caption(s, "Doğruluk %, 10-kat çapraz doğrulama ortalaması ± std; k = 4 öznitelik.", 4.6, 0.6, 7.7)
box(s, 8.6, 1.5, 4.1, 4.9, LIGHT, 0.15)
txt(s, "Makale ile karşılaştırma", 8.85, 1.65, 3.6, 0.5, 17, bold=True, color=NAVY, margin=False)
stat(s, 8.85, 2.2, 1.8, "%95", "makale medyanı (19 çalışma)", GRAY)
stat(s, 10.75, 2.2, 1.8, "%93", "bizim medyan (30 kat)", BLUE)
stat(s, 8.85, 4.0, 1.8, "17", "makale medyan kural", GRAY)
stat(s, 10.75, 4.0, 1.8, "16", "bizim kural sayısı", BLUE)
txt(s, "Uyumlu (makale aralığı %78–99,9)", 8.85, 5.8, 3.6, 0.5, 14, bold=True, italic=True, color=GREEN, margin=False)

# ======================================================================= 11
s = new_slide("R3: Bulanık kurallarla kara kutu MLP'yi açıklamak")
img(s, FIG("r3_fidelity.png"), 0.6, 1.35, 8.3, 3.4)
box(s, 9.2, 1.5, 3.5, 2.1, NAVY)
txt(s, "Fidelity = eşleşen tahmin / toplam × 100", 9.4, 1.65, 3.1, 1.0, 16, bold=True, color=WHITE, font=HEAD, margin=False)
txt(s, "(makale Denk. 25)", 9.4, 2.85, 3.1, 0.5, 13, color=ICE, margin=False)
bullets(s, ["Iris: %90,7–99,3 · WDBC: %91,0–93,3 · Pima: %77,1–79,5",
            "C-ANFIS: 3,5–5 kuralla Iris ve Pima'da en yüksek fidelity",
            "Pima'da düşük fidelity: MLP 8 öznitelik kullanıyor, vekil yalnızca 4 öznitelik görüyor"],
        0.6, 4.95, 12.1, 1.8, size=15)

# ======================================================================= 12
s = new_slide("Referans çalışmanın eleştirel değerlendirmesi")
card_list(s, 0.6, 1.5, 5.9, 5.1, "Güçlü yönler",
          ["330 çalışma, 6 kütüphane, 30 yıl: geniş ve sistematik kapsam",
           "Nicel tablolar: medyan doğruluk ve kural sayısı",
           "Performans–yorumlanabilirlik dengesini tek bir sıralamaya indirgeyen Borda yaklaşımı",
           "Sınırlılıkların ve gelecek çalışmaların açıkça tartışılması"], GREEN)
card_list(s, 6.8, 1.5, 5.9, 5.1, "Sınırlılıklar / riskler",
          ["Farklı veri setleri ve protokollerden toplanan medyanlar doğrudan karşılaştırılamaz",
           "Borda ordinal çalışır: büyüklük farkı ve çalışma sayısı yok sayılır",
           "Bağ politikası tutarsız → ANFIS 3. ↔ 5.",
           "FRI doğruluk satırında olası kopyalama hatası",
           "Yorumlanabilirlik neredeyse yalnızca kural sayısıyla ölçülüyor"], RED)

# ======================================================================= 13
s = new_slide("Özgün katkı: C-ANFIS boru hattı")
steps = [("1", "Sınıf-bazlı FCM", "her küme = 1 kural; kural sayısı K·c, d'den bağımsız"),
         ("2", "Hibrit eğitim", "baseline ile aynı LSE + Adam"),
         ("3", "MF birleştirme", "Jaccard > τ = 0,6 ise birleştir"),
         ("4", "Önemsiz koşul", "evrenin ≥ %80'ini kaplayan MF'yi kuraldan çıkar"),
         ("5", "Kural budama", "kapsama < θ/R ise sil (θ = 0,3)"),
         ("6", "İnce ayar", "50 epok, η/2")]
for i, (n, h_, b) in enumerate(steps):
    x, y = 0.6 + (i % 3) * 4.1, 1.55 + (i // 3) * 2.05
    box(s, x, y, 3.8, 1.8)
    dot(s, x + 0.2, y + 0.25, 0.6, BLUE)
    txt(s, n, x + 0.2, y + 0.25, 0.6, 0.6, 20, bold=True, color=WHITE, align="c", valign="m", margin=False)
    txt(s, h_, x + 0.95, y + 0.25, 2.7, 0.6, 18, bold=True, color=NAVY, valign="m", margin=False)
    txt(s, b, x + 0.2, y + 1.0, 3.45, 0.75, 14, margin=False)
box(s, 0.6, 5.75, 12.1, 0.95, NAVY, 0.1)
txt(s, "Ek metrikler (makalenin \"yeni metrik\" çağrısına yanıt): toplam kural uzunluğu · MF sayısı · "
       "Jaccard ayırt edilebilirlik · Nauck indeksi = comp × cov × part",
    0.85, 5.8, 11.6, 0.85, 15, color=WHITE, valign="m", margin=False)

# ======================================================================= 14
s = new_slide("Deney düzeneği")
table(s, [["Veri seti", "Örnek", "Öznitelik", "Sınıf"],
          ["Iris", "150", "4", "3"],
          ["Breast Cancer (WDBC)", "569", "30", "2 (212 malign)"],
          ["Pima Diabetes", "768", "8", "2 (268 pozitif)"]],
      0.6, 1.5, [2.6, 1.0, 1.2, 1.6], row_h=0.5, size=14)
bullets(s, ["10-kat tabakalı CV, seed = 0, tüm modeller aynı kıvrımlarda",
            "MinMax + mutual information (k = 4), yalnızca eğitim kıvrımında",
            "100 epok, η = 0,01, Adam — tüm ANFIS türevlerinde aynı",
            "Wilcoxon işaretli sıra testi (30 eşleştirilmiş kat, α = 0,05)"],
        0.6, 3.75, 6.3, 3.0, size=15)
card(s, 7.2, 1.5, 5.5, 2.4, "Deneyler",
     "P1 ana karşılaştırma · P2 ablation · P3 gürültü (σ ≤ 0,2) · P4 ölçeklenebilirlik (k = 2…8) · "
     "P5 Wilcoxon · P6 Borda · P7 parametre duyarlılığı", BLUE)
card(s, 7.2, 4.15, 5.5, 2.4, "Başarı ölçütü (önceden)",
     "(i) Kural sayısı ve kural uzunluğu belirgin azalmalı. (ii) Doğruluk farkı istatistiksel olarak "
     "anlamlı olmamalı.", GREEN)

# ======================================================================= 15
s = new_slide("P1: %76 daha az kural, anlamlı doğruluk kaybı yok")
stat(s, 0.6, 1.35, 3.0, "−%76", "kural sayısı (16 → 3,8)", BLUE)
stat(s, 3.7, 1.35, 3.0, "×6,7", "Nauck indeksi (0,007 → 0,046)", BLUE)
stat(s, 6.8, 1.35, 3.0, "−0,84", "doğruluk puanı · p = 0,15 (anlamlı değil)", GRAY)
stat(s, 9.9, 1.35, 2.8, "+%68", "MF sayısı (8 → 13,4) — olumsuz", ORANGE)
img(s, FIG("p1_tradeoff.png"), 0.6, 3.3, 12.1, 3.55)

# ======================================================================= 16
s = new_slide("Örnek: C-ANFIS'in 3 kuralı (WDBC)")
rules = [("R1", "mean concave points Düşük VE worst perimeter Düşük VE worst area Düşük VE worst concave points Düşük", "benign", "0,61", GREEN),
         ("R2", "mean concave points Yüksek VE worst perimeter Yüksek VE worst area Yüksek VE worst concave points Yüksek", "malign", "0,32", RED),
         ("R3", "mean concave points Orta VE worst perimeter Düşük VE worst area Orta VE worst concave points Orta", "benign", "0,07", GREEN)]
for i, (r, a, c, k, col) in enumerate(rules):
    y = 1.5 + i * 1.35
    box(s, 0.6, y, 12.1, 1.15, LIGHT, 0.1)
    txt(s, r, 0.8, y, 0.8, 1.15, 22, bold=True, color=BLUE, font=HEAD, valign="m", margin=False)
    txt(s, [("EĞER ", {"bold": True}), (a + " ", {}), ("İSE ", {"bold": True}), (c, {"bold": True, "color": col})],
        1.6, y, 9.0, 1.15, 15, valign="m", margin=False)
    txt(s, "kapsama " + k, 10.7, y, 1.8, 1.15, 15, color=GRAY, valign="m", align="r", margin=False)
bullets(s, ["Test doğruluğu: C-ANFIS %93,6 (3 kural) · Grid-ANFIS %93,0 (16 kural)",
            "Grid'de 16 kuralın çoğunun kapsaması %1–3: veri olmayan hücreler için de kural üretiliyor"],
        0.6, 5.7, 12.1, 1.1, size=15)

# ======================================================================= 17
s = new_slide("P2 Ablation: kazancın asıl kaynağı FCM ile kural üretimi")
img(s, FIG("p2_ablation.png"), 0.6, 1.35, w=12.1)
bullets(s, ["Kural uzunluğu: 64 → 18,7 (yalnız FCM) → 17,7 (+birleştirme, +önemsiz koşul) → 14,8 (+budama)",
            "Nauck indeksi her adımda monoton artıyor: 0,023 → 0,029 → 0,031 → 0,046",
            "FCM olmadan sadeleştirme: kural uzunluğu yalnızca 35'e iniyor → kural üretim stratejisi belirleyici"],
        0.6, 5.2, 12.1, 1.7, size=15)

# ======================================================================= 18
s = new_slide("P4 Ölçeklenebilirlik: en güçlü sonuç")
img(s, FIG("p4_scalability.png"), 0.6, 1.3, w=11.4)
table(s, [["k = 8", "Doğruluk", "Kural", "Eğitim (s)"],
          ["WDBC Grid", "93,9", "256", "20,3"],
          ["WDBC C-ANFIS", "93,9", "2,6", "0,13 (161×)"],
          ["Pima Grid", "66,2", "256", "21,9"],
          ["Pima C-ANFIS", "74,2", "3,6", "0,18 (122×)"]],
      0.6, 4.95, [2.2, 1.6, 1.4, 2.2], row_h=0.36, size=13, bold_rows=(2, 4), highlight={(4, 1): "13804F"})
txt(s, "Grid'de kural sayısı 2^k ile üstel artıyor, LSE maliyeti bundan da hızlı büyüyor. Pima'da 614 örnekle "
       "4608 parametre → aşırı öğrenme.", 8.3, 5.0, 4.4, 1.7, 14, margin=False)

# ======================================================================= 19
s = new_slide("P3 Gürültü: iyileşme yok — olumsuz sonuç")
img(s, FIG("p3_noise.png"), 0.6, 1.3, w=12.1)
card(s, 0.6, 5.1, 5.9, 1.75, "Sonuç",
     "σ = 0,1'de C-ANFIS − Grid = −1,8 puan (p = 0,21). WDBC'de σ = 0,2: C-ANFIS %60, Grid %66, WM %81, MLP %84.", RED)
card(s, 6.8, 5.1, 5.9, 1.75, "Olası nedenler",
     "TSK doğrusal sonuçları gürültüyü taşır · dar MF'ler (küçük σ) · az kural = yedek kural yok.", ORANGE)

# ======================================================================= 20
s = new_slide("Tartışma: öğrenme, MF'lerin anlamını bozabiliyor")
img(s, FIG("mf_comparison.png"), 0.6, 1.4, w=7.4)
bullets(s, ["Grid ANFIS: eğitim sonrası \"Düşük\" MF'nin merkezi c ≈ −0,26'ya kayıyor, MF daralıyor",
            "Model çalışmaya devam ediyor (normalizasyon göreli), ama dilsel anlam kayboluyor",
            "Ayırt edilebilirlik ≈ 1,0 (yanıltıcı) · Nauck kapsama bileşeni bozulmayı yakalıyor",
            "Borda sıralaması metriğe bağlı: kural sayısıyla Grid, Nauck ile C-ANFIS birinci"],
        8.3, 1.5, 4.4, 5.3, size=15)

# ======================================================================= 21
s = new_slide("Sınırlılıklar ve gelecek çalışmalar")
card_list(s, 0.6, 1.5, 5.9, 5.2, "Sınırlılıklar",
          ["Derleme düzeyi karşılaştırma niteliksel bir tutarlılık kontrolüdür",
           "3 küçük/orta tablo verisi; görüntü ve zaman serisi yok",
           "Hiperparametreler sabit (P7: c = 1 daha iyi: 2 kural, Pima %77,5)",
           "Öğrenmede anlamsal MF kısıtı yok",
           "Kullanıcı çalışması yok; Nauck indeksi TSK'ya uyarlandı"], RED)
card_list(s, 6.8, 1.5, 5.9, 5.2, "Gelecek çalışmalar",
          ["MF sıralamasını ve kapsamayı koruyan kısıtlı öğrenme",
           "Doğruluk + Nauck için çok amaçlı hiperparametre optimizasyonu",
           "Tip-2 MF'ler ile gürültü dayanıklılığı",
           "Yüksek boyutlu veriler ve kullanıcı çalışmaları"], GREEN)

# ======================================================================= 22
s = new_slide("Canlı demo: streamlit run demo/app.py")
img(s, ASSET("demo.png"), 0.6, 1.4, 7.4, 5.4)
bullets(s, ["Veri seti, k, küme/sınıf ve τ seçilir",
            "Kaydırıcılarla gerçek birimlerde giriş verilir",
            "L1: üyelik dereceleri (grafik)",
            "L2–L3: kural ateşleme kuvvetleri (tablo)",
            "L4–L5: kural çıktıları ve nihai karar",
            "C-ANFIS ve Grid-ANFIS sekmeleri arasında karşılaştırma"], 8.3, 1.5, 4.4, 5.3, size=15)

# ======================================================================= 23
s = new_slide(dark=True)
txt(s, "Sonuç", 0.8, 1.0, 11.7, 1.0, 40, bold=True, color=WHITE, font=HEAD, margin=False)
bullets(s, ["R1: Borda sıralaması 20/20 üretildi, 2 tutarsızlık bulundu",
            "R2–R3: Sıfırdan ANFIS makale medyanlarıyla uyumlu (%93, 16 kural); fidelity %77–99",
            "C-ANFIS: −%76 kural, Nauck ×6,7, doğruluk farkı anlamlı değil (p = 0,15)",
            "k = 8: 120–160× hızlı, Pima'da +8 puan · Gürültüde iyileşme yok (olumsuz sonuç)"],
        0.8, 2.3, 11.7, 3.0, size=20, color=ICE, space=14)
txt(s, "Teşekkürler — Sorular?", 0.8, 5.6, 11.7, 0.8, 26, bold=True, color=WHITE, font=HEAD, margin=False)

assert _slide_no == len(NOTES), (_slide_no, len(NOTES))
out = HERE / "presentation.pptx"
prs.save(out)
print("yazıldı:", out)
