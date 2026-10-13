// Sunum üreteci (pptxgenjs). Çalıştırma: node presentation/build_presentation.js
// Grafikler results/figures/ altından okunur (önce: python run_all.py).
const path = require("path");
const pptxgen = require("pptxgenjs");
const ROOT = path.resolve(__dirname, "..");
const FIG = (f) => path.join(ROOT, "results", "figures", f);
const ASSET = (f) => path.join(__dirname, "assets", f);
const SKILL = process.env.PPTX_SKILL_DIR;

const THEME = {
  name: "Fuzzy XAI",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1A1A", lt1: "FFFFFF", dk2: "13243A", lt2: "EEF2F7",
    accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A", accent4: "EDA100",
    accent5: "6250D6", accent6: "E34948", hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = { navy: "13243A", blue: "2A78D6", orange: "EB6834", green: "1BAF7A", gray: "5A6472", light: "EEF2F7", white: "FFFFFF" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "Furkan Fuat Küçükbayrak";
pres.title = "Bulanık Mantık Tabanlı Yorumlanabilirlik — ANFIS ve C-ANFIS";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.333;

// ---------------- Layouts ----------------
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HEX.navy },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontSize: 38, bold: true, color: C.background1, valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 2.2, fontSize: 18, color: "CADCFC", valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION",
  background: { color: HEX.navy },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 11.7, h: 1.3, fontSize: 40, bold: true, color: C.background1 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.9, w: 11.7, h: 1.0, fontSize: 18, color: "CADCFC" }, text: "" } },
  ],
  slideNumber: { x: 12.4, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: "CADCFC" },
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.white },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 30, bold: true, color: C.text2, valign: "middle" }, text: "" } },
    { text: { text: "Bulanık Mantık Dönem Projesi · F. F. Küçükbayrak", options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: "8A93A0" } } },
  ],
  slideNumber: { x: 12.4, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: "8A93A0" },
});

let sec = "";
function slide(master, title, notes) {
  const s = pres.addSlide({ masterName: master, sectionTitle: sec });
  if (title) s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
function section(t) { sec = t; pres.addSection({ title: t }); }
function txt(s, text, o) { s.addText(text, { isTextBox: true, fontSize: 16, color: C.text1, valign: "top", ...o }); }
function bullets(s, items, o) {
  s.addText(items.map((t, i) => {
    const run = typeof t === "string" ? { text: t, options: {} } : t;
    return { text: run.text, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8, ...run.options } };
  }), { isTextBox: true, fontSize: 16, color: C.text1, valign: "top", ...o });
}
function card(s, x, y, w, h, head, body, color, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: name });
  s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: y + 0.25, w: 0.42, h: 0.42, fill: { color }, line: { color } });
  txt(s, head, { x: x + 0.8, y: y + 0.18, w: w - 1.0, h: 0.55, fontSize: 17, bold: true, color: C.text2, valign: "middle", margin: 0 });
  txt(s, body, { x: x + 0.25, y: y + 0.85, w: w - 0.5, h: h - 1.0, fontSize: 14, color: C.text1 });
}
function stat(s, x, y, w, big, label, color) {
  txt(s, big, { x, y, w, h: 1.0, fontSize: 48, bold: true, color, fontFace: "Cambria", margin: 0 });
  txt(s, label, { x, y: y + 1.0, w, h: 0.8, fontSize: 14, color: HEX.gray, margin: 0 });
}
function img(s, file, x, y, w, h) { s.addImage({ path: file, x, y, w, h }); }
function caption(s, t, y) { txt(s, t, { x: 0.6, y, w: 12.1, h: 0.4, fontSize: 11, color: HEX.gray, italic: true, margin: 0 }); }

// =========================== 1. Başlık ===========================
section("Giriş");
let s = slide("TITLE_DARK", null,
  "Merhaba. Projem, bulanık mantığın makine öğrenmesi modellerini açıklanabilir yapmadaki rolünü inceleyen bir derleme makalesine dayanıyor. Makalenin analizini yeniden ürettim, ANFIS'i sıfırdan yazdım ve kural patlaması sorununa C-ANFIS adını verdiğim bir çözüm önerdim.");
s.addText("Bulanık Mantık Tabanlı Yorumlanabilirlik: ANFIS'in Yeniden Gerçekleştirilmesi ve Kompakt C-ANFIS", { placeholder: "title" });
s.addText([
  { text: "Furkan Fuat Küçükbayrak · 1306230124", options: { breakLine: true } },
  { text: "İÜC Bilgisayar Mühendisliği · Bulanık Mantık Dönem Projesi 2026–2027 Güz", options: { breakLine: true } },
  { text: "Referans: H. Ouifak & A. Idri, Neurocomputing 647 (2025) 130602", options: { italic: true } },
], { placeholder: "body" });

// =========================== 2. Problem ===========================
s = slide("CONTENT", "Problem: doğru ama açıklanamayan modeller",
  "Derin öğrenme ve MLP gibi kara kutu modeller çok doğru ama kararlarının nedenini söyleyemiyor. Tıpta yanlış bir karar bir hastanın hayatına, bankacılıkta müşteri güvenine mal olabilir. Bulanık mantık, modelin davranışını 'EĞER glikoz yüksek İSE risk yüksek' gibi insanın okuyabileceği kurallara çeviriyor. Makale bunu iki yolla yapıldığını söylüyor: kara kutudan kural çıkarmak ve ANFIS gibi nöro-bulanık modeller kurmak.");
bullets(s, [
  { text: "Kara kutu modeller (DNN, MLP, SVM) yüksek doğruluk sağlar, ama kararın nedenini açıklayamaz", options: {} },
  "Tıp, finans, otonom sistemler: açıklanamayan karar = güven ve denetim sorunu",
  "Bulanık mantık: sayısal modeli dilsel kurallara çevirir",
  "İki ana yol [makale]: (1) kara kutudan bulanık kural çıkarımı, (2) nöro-bulanık modelleme (ANFIS)",
], { x: 0.6, y: 1.5, w: 6.6, h: 4.8 });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.7, y: 1.7, w: 5.0, h: 3.9, rectRadius: 0.15, fill: { color: C.text2 }, line: { color: C.text2 } });
txt(s, "Bulanık kural örneği (projeden, WDBC)", { x: 8.0, y: 1.9, w: 4.4, h: 0.5, fontSize: 14, color: "CADCFC", bold: true, margin: 0 });
txt(s, [
  { text: "EĞER ", options: { bold: true, color: "CADCFC" } }, { text: "mean concave points Yüksek ", options: { color: "FFFFFF" } },
  { text: "VE ", options: { bold: true, color: "CADCFC" } }, { text: "worst area Yüksek ", options: { color: "FFFFFF" } },
  { text: "VE ", options: { bold: true, color: "CADCFC" } }, { text: "worst concave points Yüksek", options: { color: "FFFFFF", breakLine: true } },
  { text: "İSE ", options: { bold: true, color: "CADCFC" } }, { text: "malign", options: { color: "F6B79E", bold: true } },
], { x: 8.0, y: 2.5, w: 4.4, h: 2.0, fontSize: 18, fontFace: "Cambria", margin: 0 });
txt(s, "Bir hekim bu kuralı okuyup kontrol edebilir.", { x: 8.0, y: 4.7, w: 4.4, h: 0.6, fontSize: 14, italic: true, color: "CADCFC", margin: 0 });

// =========================== 3. Makale ===========================
s = slide("CONTENT", "Referans makale: 30 yılın sistematik derlemesi",
  "Makale bir sistematik literatür derlemesi. 1994'ten 2024'e kadar altı veri tabanında tarama yapıp 330 çalışmayı seçiyor ve sekiz araştırma sorusuyla analiz ediyor. Yani yeni bir algoritma önermiyor; alanın haritasını çıkarıyor. Bu yüzden 'yeniden gerçekleştirme'yi makalenin nicel analizini ve merkezî tekniği ANFIS'i yeniden üretmek olarak tanımladım.");
stat(s, 0.6, 1.6, 2.9, "330", "seçilen çalışma", HEX.blue);
stat(s, 3.7, 1.6, 2.9, "6", "dijital kütüphane (IEEE, ScienceDirect, PubMed, ACM, Wiley, Scholar)", HEX.blue);
stat(s, 6.8, 1.6, 2.9, "30 yıl", "kapsanan dönem: 1994 – Ocak 2024", HEX.blue);
stat(s, 9.9, 1.6, 2.9, "3 + 8", "haritalama + araştırma sorusu", HEX.blue);
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 4.1, w: 12.1, h: 2.4, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2 } });
txt(s, "Önemli not: Bu bir derleme makalesidir — tek bir algoritma önermez", { x: 0.9, y: 4.25, w: 11.5, h: 0.5, fontSize: 18, bold: true, color: C.text2, margin: 0 });
txt(s, "Bu nedenle yeniden gerçekleştirme (MRR) şöyle tanımlandı: (R1) makalenin nicel analizinin (Borda sıralaması) yeniden üretimi, (R2) makalenin merkezî tekniği ANFIS'in sıfırdan yazılıp benchmark verilerinde makale medyanlarıyla karşılaştırılması, (R3) bulanık modellerle kara kutu açıklama ve fidelity ölçümü.", { x: 0.9, y: 4.8, w: 11.5, h: 1.6, fontSize: 15, margin: 0 });

// =========================== 4. Bulgular ===========================
s = slide("CONTENT", "Makalenin temel bulguları",
  "Dört bulgu projeyi şekillendirdi. ANFIS en çok kullanılan teknik: 19 çalışmada medyan %95 doğruluk ve 17 kural. Açıklamalar çoğunlukla kural tabanlı, veri çoğunlukla tablo verisi. Yorumlanabilirlik neredeyse hep kural sayısıyla ölçülüyor. Makalenin kendi söylediği sınırlılıklar ise kural patlaması, ölçeklenebilirlik ve standart metrik eksikliği. Benim katkım doğrudan bu son maddeyi hedefliyor.");
card(s, 0.6, 1.5, 5.9, 2.4, "ANFIS en çok kullanılan teknik", "19 çalışma · medyan doğruluk %95 · medyan 17 kural (Tablo 6, 9). En iyi performans–yorumlanabilirlik dengesine sahip tekniklerden biri.", HEX.blue);
card(s, 6.8, 1.5, 5.9, 2.4, "Açıklamalar kural tabanlı", "En çok açıklanan kara kutu: sinir ağları. En çok kullanılan veri tipi: tablo verisi.", HEX.green);
card(s, 0.6, 4.15, 5.9, 2.4, "Yorumlanabilirlik = kural sayısı", "296 çalışma kural sayısını kullanıyor. MF sayısı (11) ve fidelity (8) çok daha az. Denge Borda sayımı ile sıralanıyor (Şekil 21).", HEX.orange);
card(s, 6.8, 4.15, 5.9, 2.4, "Belirtilen sınırlılıklar", "Grid ANFIS'te kural patlaması (p^d), hesaplama maliyeti ve ölçeklenebilirlik, standart yorumlanabilirlik metriğinin olmaması.", "E34948");

// =========================== 5. Literatür ===========================
s = slide("CONTENT", "Güncel literatür",
  "Literatürde üç kol öne çıkıyor. Birincisi yorumlanabilirlik ölçütleri: Gacto ve arkadaşları karmaşıklık ve anlamsal ölçütleri ayırıyor, Nauck bunları tek indekste birleştiriyor. İkincisi kara kutudan bulanık açıklama: Aghaeipoor 2023 ve Yin 2025. Üçüncüsü kompakt nöro-bulanık modeller: Huang 2022 FCM ile kural azaltıyor, Setnes benzer kümeleri birleştiriyor. C-ANFIS bu fikirleri birleştiriyor.");
const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.navy } } });
const rows = [
  [hdr("Çalışma"), hdr("Yöntem"), hdr("Ölçüt"), hdr("Projedeki rolü")],
  ["Jang (1993)", "Grid ANFIS, hibrit öğrenme", "—", "Baseline"],
  ["Setnes vd. (1998)", "Benzerlikle MF birleştirme", "MF sayısı", "C-ANFIS adım 3"],
  ["Nauck (2003)", "comp × cov × part indeksi", "Bileşik", "Ek metrik"],
  ["Gacto vd. (2011)", "Yorumlanabilirlik taksonomisi", "Karmaşıklık + anlamsal", "Metrik çerçevesi"],
  ["Huang vd. (2022)", "FCM + derin yama öğrenme", "Kural sayısı", "FCM ile kural üretimi"],
  ["Aghaeipoor vd. (2023)", "DNN için bulanık açıklayıcı", "Fidelity", "R3 deneyi"],
  ["Ouifak & Idri (2025)", "SLR, 330 çalışma", "Kural sayısı, Borda", "Referans makale"],
  ["Yin vd. (2025)", "Hiyerarşik model-agnostik", "Fidelity", "Güncel örnek"],
];
s.addTable(rows, { x: 0.6, y: 1.45, w: 12.1, colW: [2.6, 3.6, 2.6, 3.3], fontSize: 14, color: C.text1, border: { type: "solid", pt: 0.5, color: "C8CED6" }, rowH: 0.52, fill: { color: "FFFFFF" } });

// =========================== 6. Teori 1 ===========================
section("Teorik altyapı");
s = slide("CONTENT", "Bulanık küme, üyelik fonksiyonu ve çıkarım",
  "Klasik kümede bir eleman ya vardır ya yoktur; bulanık kümede üyelik 0 ile 1 arasında bir derecedir. Gauss üyelik fonksiyonu kullandım, çünkü türevlenebilir ve gradyanla öğrenilebilir. Mamdani'de kural sonucu bir bulanık küme, TSK'da ise girdilerin doğrusal bir fonksiyonudur. Projede ANFIS için birinci derece TSK, Wang-Mendel referans modeli için Mamdani kullandım. VE için çarpım t-normu, durulaştırma için ağırlıklı ortalama.");
bullets(s, [
  { text: "Bulanık küme: μA(x) ∈ [0, 1] — kısmi üyelik (Zadeh, 1965)", options: {} },
  "Gauss MF: μ(x) = exp(−(x − c)² / 2σ²) — türevlenebilir, öğrenilebilir",
  "Dilsel değişken: worst area ∈ {Düşük, Orta, Yüksek}",
  "Mamdani: sonuç bulanık küme → ağırlık merkezi ile durulaştırma",
  "TSK (1. derece): sonuç f = p·[x, 1] → ağırlıklı ortalama",
  "VE: çarpım t-normu · Durulaştırma: Σ w̄ f",
], { x: 0.6, y: 1.5, w: 6.3, h: 5.2 });
img(s, FIG("mf_comparison.png"), 7.2, 1.6, 5.6, 3.05);
caption(s, "Üstte: grid ANFIS başlangıç MF'leri (Düşük/Yüksek, 0,5'te kesişir).", 4.75);
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.2, y: 5.3, w: 5.6, h: 1.25, rectRadius: 0.1, fill: { color: C.background2 }, line: { color: C.background2 } });
txt(s, "Projede: ANFIS → TSK-1 + Gauss MF  ·  Wang–Mendel → Mamdani + üçgen MF", { x: 7.4, y: 5.4, w: 5.2, h: 1.05, fontSize: 14, bold: true, color: C.text2, valign: "middle", margin: 0 });

// =========================== 7. ANFIS ===========================
s = slide("CONTENT", "ANFIS: 5 katmanlı mimari ve hibrit öğrenme",
  "ANFIS, TSK sistemini beş katmanlı bir ağ olarak yazar. Birinci katman bulanıklaştırır, ikinci katman üyelikleri çarparak kural ateşleme kuvvetini bulur, üçüncü katman normalize eder, dördüncü katman her kuralın doğrusal çıktısını hesaplar, beşinci katman toplar. Hibrit öğrenmede ileri geçişte sonuç parametreleri en küçük kareler ile kapalı formda çözülür, geri geçişte MF merkez ve genişlikleri gradyanla güncellenir. Ben softmax gözlemiyle gradyanı kompakt türettim ve sayısal türevle doğruladım; hata 10 üzeri eksi 5'ten küçük.");
const layers = [["L1", "Bulanıklaştırma", "μ(x; c, σ)"], ["L2", "Kural ateşleme", "w = ∏ μ"], ["L3", "Normalizasyon", "w̄ = w / Σw"], ["L4", "Sonuç (TSK)", "w̄ · p·[x,1]"], ["L5", "Toplama", "y = Σ w̄ f"]];
layers.forEach(([l, n, f], i) => {
  const x = 0.6 + i * 2.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w: 2.15, h: 1.9, rectRadius: 0.12, fill: { color: i === 0 || i === 3 ? HEX.blue : C.text2 }, line: { color: i === 0 || i === 3 ? HEX.blue : C.text2 } });
  txt(s, l, { x, y: 1.7, w: 2.15, h: 0.45, fontSize: 20, bold: true, color: "FFFFFF", align: "center", margin: 0 });
  txt(s, n, { x, y: 2.15, w: 2.15, h: 0.5, fontSize: 14, color: "FFFFFF", align: "center", margin: 0 });
  txt(s, f, { x, y: 2.7, w: 2.15, h: 0.5, fontSize: 14, color: "CADCFC", align: "center", fontFace: "Cambria", italic: true, margin: 0 });
  if (i < 4) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.18, y: 2.35, w: 0.3, h: 0.4, fill: { color: "9AA5B4" }, line: { color: "9AA5B4" } });
});
txt(s, "Mavi katmanlar öğrenilebilir parametre içerir: L1 (c, σ) ve L4 (p).", { x: 0.6, y: 3.6, w: 12, h: 0.4, fontSize: 13, italic: true, color: HEX.gray, margin: 0 });
card(s, 0.6, 4.2, 5.9, 2.4, "İleri geçiş: LSE", "MF'ler sabitken çıktı p'ye göre doğrusaldır → p kapalı formda çözülür: (ΦᵀΦ + λI)p = Φᵀt (ridge, λ = 10⁻³).", HEX.blue);
card(s, 6.8, 4.2, 5.9, 2.4, "Geri geçiş: gradyan (Adam)", "∂E/∂log wᵣ = w̄ᵣ(gᵣ − Σ w̄q gq) — softmax türevi. Analitik gradyan sayısal türevle doğrulandı (bağıl hata < 10⁻⁵).", HEX.orange);

// =========================== 8. Kapsam ===========================
section("Yeniden gerçekleştirme");
s = slide("CONTENT", "Proje kapsamı: 3 yeniden üretim + 1 özgün katkı",
  "Projeyi dört blok olarak kurdum. R1 makalenin kendi analizini, R2 makalenin merkezî tekniğini, R3 kara kutu açıklama senaryosunu yeniden üretiyor. Özgün katkı C-ANFIS. Hepsi aynı on katlı çapraz doğrulama kıvrımlarında, sabit seed ile çalışıyor; yani karşılaştırmalar eşleştirilmiş ve adil.");
const blocks = [["R1", "Borda yeniden üretimi", "Tablo 6 + 9 → Şekil 21", HEX.navy], ["R2", "ANFIS sıfırdan", "Iris · WDBC · Pima, 10-kat CV", HEX.navy], ["R3", "Kara kutu açıklama", "MLP → bulanık vekil, fidelity", HEX.navy], ["+", "C-ANFIS (katkı)", "FCM + birleştirme + budama", HEX.blue]];
blocks.forEach(([k, h, b, col], i) => {
  const x = 0.6 + i * 3.1;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w: 2.8, h: 3.0, rectRadius: 0.15, fill: { color: col }, line: { color: col } });
  txt(s, k, { x, y: 1.75, w: 2.8, h: 0.9, fontSize: 40, bold: true, color: "FFFFFF", align: "center", fontFace: "Cambria", margin: 0 });
  txt(s, h, { x: x + 0.15, y: 2.75, w: 2.5, h: 0.8, fontSize: 18, bold: true, color: "FFFFFF", align: "center", margin: 0 });
  txt(s, b, { x: x + 0.15, y: 3.55, w: 2.5, h: 0.9, fontSize: 14, color: "CADCFC", align: "center", margin: 0 });
});
bullets(s, [
  "Python 3 + NumPy: ANFIS, FCM, Wang–Mendel ve C-ANFIS hazır bulanık kütüphane kullanılmadan yazıldı",
  "Adil protokol: aynı kıvrımlar, aynı ön işleme, ölçekleme ve öznitelik seçimi yalnızca eğitim kıvrımında fit edilir",
  "Tekrar üretilebilirlik: tek komut python run_all.py (~8 dk), tüm ham sonuçlar CSV olarak kaydedilir",
], { x: 0.6, y: 4.95, w: 12.1, h: 1.8, fontSize: 15 });

// =========================== 9. R1 ===========================
s = slide("CONTENT", "R1: Borda sıralaması 20/20 sistemde birebir üretildi",
  "Makalenin Tablo 6 ve 9'daki medyanlarından Borda sıralamasını hesapladım ve Şekil 21 ile 20 sistemin 20'sinde birebir aynı sonucu aldım. Bunu yaparken iki şey fark ettim. Birincisi, makale doğrulukta bağları keyfi kırıyor, kural sayısında ise eşitlere aynı sırayı veriyor. Tutarlı bir politika uygulanırsa ANFIS üçüncülükten beşinciliğe düşüyor. İkincisi, Tablo 9'daki FRI doğruluk satırı Tablo 6'daki kural sayılarıyla birebir aynı; muhtemelen kopyalama hatası.");
img(s, FIG("r1_borda.png"), 0.6, 1.4, 7.9, 3.0);
stat(s, 9.0, 1.45, 3.7, "20 / 20", "sistemin doğruluk, kural ve tradeoff sırası Şekil 21 ile aynı", HEX.green);
card(s, 0.6, 4.65, 5.9, 2.0, "Bulgu 1: Bağ politikası tutarsız", "Doğruluk: ordinal · kural: dense. Tutarlı 'min' politikasıyla ANFIS 3. sıradan 5. sıraya düşüyor.", HEX.orange);
card(s, 6.8, 4.65, 5.9, 2.0, "Bulgu 2: Olası veri hatası", "Tablo 9'daki FRI doğruluk değerleri (4; 20; 11; 11,33; 5,22) Tablo 6'daki kural sayılarıyla birebir aynı.", "E34948");

// =========================== 10. R2 ===========================
s = slide("CONTENT", "R2: Sıfırdan ANFIS, makale medyanlarıyla uyumlu",
  "Grid ANFIS'i, her öznitelikte iki MF ve mutual information ile seçilen dört öznitelikle çalıştırdım; bu 16 kural demek. Makalenin medyanı 17 kural ve yüzde 95. Bizim 30 kattaki medyanımız yüzde 93. Pima zor bir veri seti, yüzde 75 civarında. Üç MF'li grid ise 81 kuralla hiçbir yerde daha iyi değil, Pima'da aşırı öğreniyor.");
const t2 = [
  [hdr("Model"), hdr("Iris"), hdr("WDBC"), hdr("Pima"), hdr("Kural")],
  [{ text: "Grid-ANFIS (2MF) — baseline", options: { bold: true } }, "95,3 ± 4,5", "93,8 ± 2,2", "74,9 ± 6,8", "16"],
  ["Grid-ANFIS (3MF)", "94,7 ± 5,3", "92,6 ± 3,2", "69,4 ± 5,3", "81"],
  ["Wang–Mendel (3MF)", "91,3 ± 4,5", "91,6 ± 4,7", "74,5 ± 3,6", "16–23"],
  ["Karar ağacı (d ≤ 4)", "94,0 ± 5,8", "92,1 ± 3,8", "74,3 ± 7,3", "7–16"],
  ["MLP (kara kutu)", "96,0 ± 3,4", "93,8 ± 3,0", "77,0 ± 5,9", "—"],
];
s.addTable(t2, { x: 0.6, y: 1.5, w: 7.6, colW: [2.9, 1.25, 1.25, 1.25, 0.95], fontSize: 14, color: C.text1, border: { type: "solid", pt: 0.5, color: "C8CED6" }, rowH: 0.5, align: "center" });
caption(s, "Doğruluk %, 10-kat çapraz doğrulama ortalaması ± std; k = 4 öznitelik.", 4.65);
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.6, y: 1.5, w: 4.1, h: 4.9, rectRadius: 0.15, fill: { color: C.background2 }, line: { color: C.background2 } });
txt(s, "Makale ile karşılaştırma", { x: 8.85, y: 1.65, w: 3.6, h: 0.5, fontSize: 17, bold: true, color: C.text2, margin: 0 });
stat(s, 8.85, 2.2, 1.8, "%95", "makale medyanı (19 çalışma)", HEX.gray);
stat(s, 10.75, 2.2, 1.8, "%93", "bizim medyan (30 kat)", HEX.blue);
stat(s, 8.85, 4.0, 1.8, "17", "makale medyan kural", HEX.gray);
stat(s, 10.75, 4.0, 1.8, "16", "bizim kural sayısı", HEX.blue);
txt(s, "Uyumlu (makale aralığı %78–99,9)", { x: 8.85, y: 5.75, w: 3.6, h: 0.5, fontSize: 14, italic: true, color: HEX.green, bold: true, margin: 0 });

// =========================== 11. R3 ===========================
s = slide("CONTENT", "R3: Bulanık kurallarla kara kutu MLP'yi açıklamak",
  "Burada MLP'yi tüm özniteliklerle kara kutu olarak eğittim. Sonra bulanık modelleri gerçek etiketlerle değil, MLP'nin tahminleriyle eğittim. Bu, pedagojik kural çıkarımı. Fidelity, test kümesinde bulanık modelin MLP ile aynı kararı verme oranı; makaledeki 25 numaralı denklem. C-ANFIS 3,5 ila 5 kuralla Iris ve Pima'da en yüksek fidelity'yi verdi.");
img(s, FIG("r3_fidelity.png"), 0.6, 1.4, 8.2, 3.3);
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 9.2, y: 1.5, w: 3.5, h: 2.1, rectRadius: 0.12, fill: { color: C.text2 }, line: { color: C.text2 } });
txt(s, "Fidelity = eşleşen tahmin / toplam × 100", { x: 9.4, y: 1.65, w: 3.1, h: 1.0, fontSize: 16, color: "FFFFFF", bold: true, fontFace: "Cambria", margin: 0 });
txt(s, "(makale Denk. 25)", { x: 9.4, y: 2.8, w: 3.1, h: 0.5, fontSize: 13, color: "CADCFC", margin: 0 });
bullets(s, [
  "Iris: %90,7–99,3 · WDBC: %91,0–93,3 · Pima: %77,1–79,5",
  "C-ANFIS: 3,5–5 kuralla Iris ve Pima'da en yüksek fidelity",
  "Pima'da düşük fidelity: MLP 8 öznitelik kullanıyor, vekil yalnızca 4 öznitelik görüyor",
], { x: 0.6, y: 4.95, w: 12.1, h: 1.8, fontSize: 15 });

// =========================== 12. Eleştiri ===========================
s = slide("CONTENT", "Referans çalışmanın eleştirel değerlendirmesi",
  "Makalenin güçlü yanları geniş ve sistematik kapsamı, nicel tablolar sunması ve sınırlılıkları dürüstçe tartışması. Zayıf yanları: sonuçlar farklı veri setlerinden toplanan medyanlar, yani doğrudan karşılaştırılamaz. Borda yöntemi sıralı veriyle çalıştığı için yüzde 99 ile yüzde 95 arasındaki fark ve yüzde 95 ile 94,9 arasındaki fark aynı ağırlıkta. 2 çalışmalı bir teknik ile 19 çalışmalı ANFIS aynı güvenle sıralanıyor. Bağ politikası ve FRI hatası sonucu değiştirebiliyor.");
card(s, 0.6, 1.5, 5.9, 5.0, "Güçlü yönler", "• 330 çalışma, 6 kütüphane, 30 yıl: geniş ve sistematik kapsam\n\n• Nicel tablolar: medyan doğruluk ve kural sayısı\n\n• Performans–yorumlanabilirlik dengesini tek bir sıralamaya indirgeyen Borda yaklaşımı\n\n• Sınırlılıkların ve gelecek çalışmaların açıkça tartışılması", HEX.green);
card(s, 6.8, 1.5, 5.9, 5.0, "Sınırlılıklar / riskler", "• Farklı veri setleri ve protokollerden toplanan medyanlar doğrudan karşılaştırılamaz\n\n• Borda ordinal çalışır: büyüklük farkı ve çalışma sayısı yok sayılır\n\n• Bağ politikası tutarsız → ANFIS 3. ↔ 5.\n\n• FRI doğruluk satırında olası kopyalama hatası\n\n• Yorumlanabilirlik neredeyse yalnızca kural sayısıyla ölçülüyor", "E34948");

// =========================== 13. C-ANFIS ===========================
section("Özgün katkı");
s = slide("CONTENT", "Özgün katkı: C-ANFIS boru hattı",
  "Grid ANFIS'te kural sayısı p üzeri d; dört öznitelikte 16, sekizde 256 kural. C-ANFIS'te kuralları veriden üretiyorum: her sınıfı FCM ile 2 kümeye ayırıyorum, her küme bir kural oluyor. Böylece kural sayısı öznitelik sayısından bağımsız. Sonra aynı hibrit öğrenmeyle eğitiyorum, Jaccard benzerliği 0,6'nın üzerindeki MF'leri birleştiriyorum, evrenin çoğunu kaplayan anlamsız koşulları siliyorum, kapsaması düşük kuralları budayıp kısa bir ince ayar yapıyorum.");
const steps = [["1", "Sınıf-bazlı FCM", "her küme = 1 kural; kural sayısı K·c, d'den bağımsız"], ["2", "Hibrit eğitim", "baseline ile aynı LSE + Adam"], ["3", "MF birleştirme", "Jaccard > τ = 0,6 ise birleştir"], ["4", "Önemsiz koşul", "evrenin ≥ %80'ini kaplayan MF'yi kuraldan çıkar"], ["5", "Kural budama", "kapsama < θ/R ise sil (θ = 0,3)"], ["6", "İnce ayar", "50 epok, η/2"]];
steps.forEach(([n, h, b], i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = 0.6 + col * 4.1, y = 1.55 + row * 2.05;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 3.8, h: 1.8, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2 } });
  s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.25, w: 0.6, h: 0.6, fill: { color: HEX.blue }, line: { color: HEX.blue } });
  txt(s, n, { x: x + 0.2, y: y + 0.25, w: 0.6, h: 0.6, fontSize: 20, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
  txt(s, h, { x: x + 0.95, y: y + 0.25, w: 2.7, h: 0.6, fontSize: 18, bold: true, color: C.text2, valign: "middle", margin: 0 });
  txt(s, b, { x: x + 0.2, y: y + 0.95, w: 3.45, h: 0.8, fontSize: 14, margin: 0 });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.75, w: 12.1, h: 0.95, rectRadius: 0.1, fill: { color: C.text2 }, line: { color: C.text2 } });
txt(s, "Ek metrikler (makalenin \"yeni metrik\" çağrısına yanıt): toplam kural uzunluğu · MF sayısı · Jaccard ayırt edilebilirlik · Nauck indeksi = comp × cov × part", { x: 0.85, y: 5.8, w: 11.6, h: 0.85, fontSize: 15, color: "FFFFFF", valign: "middle", margin: 0 });

// =========================== 14. Deney ===========================
s = slide("CONTENT", "Deney düzeneği",
  "Üç veri seti var: Iris, WDBC ve Pima; hepsi makalede sık geçen tablo verileri. On katlı tabakalı çapraz doğrulama kullandım, seed sıfır. Ölçekleme ve öznitelik seçimi sadece eğitim kıvrımında yapılıyor, yani veri sızıntısı yok. Başarı ölçütünü baştan tanımladım: kural sayısı belirgin azalmalı ve doğruluk farkı Wilcoxon testinde anlamlı olmamalı.");
const t3 = [
  [hdr("Veri seti"), hdr("Örnek"), hdr("Öznitelik"), hdr("Sınıf")],
  ["Iris", "150", "4", "3"], ["Breast Cancer (WDBC)", "569", "30", "2 (212 malign)"], ["Pima Diabetes", "768", "8", "2 (268 pozitif)"],
];
s.addTable(t3, { x: 0.6, y: 1.5, w: 6.2, colW: [2.6, 1.0, 1.2, 1.4], fontSize: 14, color: C.text1, border: { type: "solid", pt: 0.5, color: "C8CED6" }, rowH: 0.5, align: "center" });
bullets(s, [
  "10-kat tabakalı CV, seed = 0, tüm modeller aynı kıvrımlarda",
  "MinMax + mutual information (k = 4), yalnızca eğitim kıvrımında",
  "100 epok, η = 0,01, Adam — tüm ANFIS türevlerinde aynı",
  "Wilcoxon işaretli sıra testi (30 eşleştirilmiş kat, α = 0,05)",
], { x: 0.6, y: 3.75, w: 6.2, h: 3.0, fontSize: 15 });
card(s, 7.2, 1.5, 5.5, 2.4, "Deneyler", "P1 ana karşılaştırma · P2 ablation · P3 gürültü (σ ≤ 0,2) · P4 ölçeklenebilirlik (k = 2…8) · P5 Wilcoxon · P6 Borda · P7 parametre duyarlılığı", HEX.blue);
card(s, 7.2, 4.15, 5.5, 2.4, "Başarı ölçütü (önceden)", "(i) Kural sayısı ve kural uzunluğu belirgin azalmalı. (ii) Doğruluk farkı istatistiksel olarak anlamlı olmamalı.", HEX.green);

// =========================== 15. P1 ===========================
section("Sonuçlar");
s = slide("CONTENT", "P1: %76 daha az kural, anlamlı doğruluk kaybı yok",
  "Ana sonuç: C-ANFIS kural sayısını 16'dan 3,8'e, yani yüzde 76 azaltıyor. Nauck indeksi 6,7 kat artıyor. Doğruluk 0,84 puan düşük ama Wilcoxon p değeri 0,15, yani istatistiksel olarak anlamlı değil. Grafikte sol üst köşe iyi: az kural ve yüksek doğruluk. C-ANFIS her veri setinde en az kurallı bulanık model.");
stat(s, 0.6, 1.4, 3.0, "−%76", "kural sayısı (16 → 3,8)", HEX.blue);
stat(s, 3.7, 1.4, 3.0, "×6,7", "Nauck indeksi (0,007 → 0,046)", HEX.blue);
stat(s, 6.8, 1.4, 3.0, "−0,84", "doğruluk puanı · p = 0,15 (anlamlı değil)", HEX.gray);
stat(s, 9.9, 1.4, 2.8, "+%68", "MF sayısı (8 → 13,4) — olumsuz", HEX.orange);
img(s, FIG("p1_tradeoff.png"), 1.1, 3.45, 11.1, 3.43);

// =========================== 16. Kurallar ===========================
s = slide("CONTENT", "Örnek: C-ANFIS'in 3 kuralı (WDBC)",
  "Tek bir bölünmede C-ANFIS'in ürettiği kurallar bunlar. Sadece üç kural var ve test doğruluğu yüzde 93,6. Grid'de 16 kural var ve ilki dışındakilerin çoğunun kapsaması yüzde 1 ila 3, yani neredeyse hiç ateşlenmiyorlar. Bu, grid partition'ın verinin olmadığı hücreler için de kural ürettiğini gösteriyor.");
const rules = [
  ["R1", "mean concave points Düşük VE worst perimeter Düşük VE worst area Düşük VE worst concave points Düşük", "benign", "0,61", HEX.green],
  ["R2", "mean concave points Yüksek VE worst perimeter Yüksek VE worst area Yüksek VE worst concave points Yüksek", "malign", "0,32", "E34948"],
  ["R3", "mean concave points Orta VE worst perimeter Düşük VE worst area Orta VE worst concave points Orta", "benign", "0,07", HEX.green],
];
rules.forEach(([r, a, c, k], i) => {
  const y = 1.5 + i * 1.35;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 12.1, h: 1.15, rectRadius: 0.1, fill: { color: C.background2 }, line: { color: C.background2 } });
  txt(s, r, { x: 0.8, y, w: 0.8, h: 1.15, fontSize: 22, bold: true, color: HEX.blue, valign: "middle", fontFace: "Cambria", margin: 0 });
  txt(s, [{ text: "EĞER ", options: { bold: true } }, { text: a + " " }, { text: "İSE ", options: { bold: true } }, { text: c, options: { bold: true, color: rules[i][4] } }], { x: 1.6, y, w: 9.0, h: 1.15, fontSize: 15, valign: "middle", margin: 0 });
  txt(s, "kapsama " + k, { x: 10.7, y, w: 1.9, h: 1.15, fontSize: 15, color: HEX.gray, valign: "middle", align: "right", margin: 0 });
});
bullets(s, [
  "Test doğruluğu: C-ANFIS %93,6 (3 kural) · Grid-ANFIS %93,0 (16 kural)",
  "Grid'de 16 kuralın çoğunun kapsaması %1–3: veri olmayan hücreler için de kural üretiliyor",
], { x: 0.6, y: 5.7, w: 12.1, h: 1.1, fontSize: 15 });

// =========================== 17. Ablation ===========================
s = slide("CONTENT", "P2 Ablation: kazancın asıl kaynağı FCM ile kural üretimi",
  "Ablation'da adımları tek tek ekledim. Kural uzunluğundaki düşüşün büyük kısmı, 64'ten 18,7'ye, FCM ile kural üretiminden geliyor. Birleştirme ve önemsiz koşul adımlarının etkisi küçük; budama 14,8'e indiriyor. Nauck indeksi her adımda artıyor. FCM olmadan sadece sadeleştirme uygulayınca 35'e inebiliyoruz. Doğruluk tüm varyantlarda 87 ile 88 arasında.");
img(s, FIG("p2_ablation.png"), 0.6, 1.4, 12.1, 12.1 * 660 / 2200);
bullets(s, [
  "Kural uzunluğu: 64 → 18,7 (yalnız FCM) → 17,7 (+birleştirme, +önemsiz koşul) → 14,8 (+budama)",
  "Nauck indeksi her adımda monoton artıyor: 0,023 → 0,029 → 0,031 → 0,046",
  "FCM olmadan sadeleştirme: kural uzunluğu yalnızca 35'e iniyor → kural üretim stratejisi belirleyici",
], { x: 0.6, y: 5.2, w: 12.1, h: 1.7, fontSize: 15 });

// =========================== 18. Ölçeklenebilirlik ===========================
s = slide("CONTENT", "P4 Ölçeklenebilirlik: en güçlü sonuç",
  "En güçlü sonuç ölçeklenebilirlik. Sekiz öznitelikte grid 256 kurala ve 2048 koşula çıkıyor, bir kat 20 saniyeden fazla sürüyor. C-ANFIS 3-4 kuralla 0,15 saniyede eğitiliyor; 120-160 kat hızlı. Üstelik Pima'da grid aşırı öğrenip yüzde 66'ya düşüyor, C-ANFIS yüzde 74'te kalıyor. Bunun nedeni grid'in 614 örnekle 4608 sonuç parametresi kestirmeye çalışması.");
img(s, FIG("p4_scalability.png"), 0.6, 1.4, 12.1, 12.1 * 660 / 2200);
const t4 = [
  [hdr("k = 8"), hdr("Doğruluk"), hdr("Kural"), hdr("Eğitim (s)")],
  ["WDBC Grid", "93,9", "256", "20,3"], [{ text: "WDBC C-ANFIS", options: { bold: true } }, "93,9", "2,6", "0,13 (161×)"],
  ["Pima Grid", "66,2", "256", "21,9"], [{ text: "Pima C-ANFIS", options: { bold: true } }, { text: "74,2", options: { bold: true, color: HEX.green } }, "3,6", "0,18 (122×)"],
];
s.addTable(t4, { x: 0.6, y: 5.15, w: 7.4, colW: [2.2, 1.6, 1.4, 2.2], fontSize: 13, color: C.text1, border: { type: "solid", pt: 0.5, color: "C8CED6" }, rowH: 0.34, align: "center" });
txt(s, "Grid'de kural sayısı 2^k ile üstel artıyor, LSE maliyeti bundan da hızlı büyüyor. Pima'da 614 örnekle 4608 parametre → aşırı öğrenme.", { x: 8.3, y: 5.15, w: 4.4, h: 1.7, fontSize: 14, color: C.text1, margin: 0 });

// =========================== 19. Gürültü ===========================
s = slide("CONTENT", "P3 Gürültü: iyileşme yok — olumsuz sonuç",
  "Gürültüde C-ANFIS daha dayanıklı değil. Sıfır virgül bir gürültüde fark eksi 1,8 puan, anlamlı değil, ama WDBC'de iki ANFIS türevi de Wang-Mendel ve MLP'den çok daha hızlı düşüyor. Üç neden düşünüyorum: TSK'nın doğrusal sonuçları gürültüyü doğrusal taşıyor; dar MF'ler küçük kaymalarda ateşleme dağılımını sert değiştiriyor; az kural olduğu için yedek kural yok. Yönerge, iyileşme olmasa da bilimsel tartışmayı istiyor; bu yüzden raporladım.");
img(s, FIG("p3_noise.png"), 0.6, 1.4, 12.1, 12.1 * 660 / 2200);
card(s, 0.6, 5.15, 5.9, 1.65, "Sonuç", "σ = 0,1'de C-ANFIS − Grid = −1,8 puan (p = 0,21). WDBC'de σ = 0,2: C-ANFIS %60, Grid %66, WM %81, MLP %84.", "E34948");
card(s, 6.8, 5.15, 5.9, 1.65, "Olası nedenler", "TSK doğrusal sonuçları gürültüyü taşır · dar MF'ler (küçük σ) · az kural = yedek kural yok.", HEX.orange);

// =========================== 20. Tartışma ===========================
s = slide("CONTENT", "Tartışma: öğrenme, MF'lerin anlamını bozabiliyor",
  "Beklenmeyen bir bulgu: kısıtsız hibrit öğrenmeden sonra grid ANFIS'in 'Düşük' MF'si evrenin dışına kayıyor ve daralıyor. Model yine doğru çalışıyor, çünkü normalizasyon yalnızca göreli ateşleme kuvvetine bakıyor. Ama 'Düşük' etiketi artık anlam taşımıyor. Ayırt edilebilirlik metriği buna mükemmel diyor, Nauck'un kapsama bileşeni ise bozulmayı yakalıyor. Bu, tek bir metriğe güvenilemeyeceğini ve makalenin bileşik metrik çağrısının haklı olduğunu gösteriyor.");
img(s, FIG("mf_comparison.png"), 0.6, 1.4, 7.4, 7.4 * 1200 / 2200);
bullets(s, [
  "Grid ANFIS: eğitim sonrası \"Düşük\" MF'nin merkezi c ≈ −0,26'ya kayıyor, MF daralıyor",
  "Model çalışmaya devam ediyor (normalizasyon göreli), ama dilsel anlam kayboluyor",
  "Ayırt edilebilirlik ≈ 1,0 (yanıltıcı) · Nauck kapsama bileşeni bozulmayı yakalıyor",
  "Borda sıralaması metriğe bağlı: kural sayısıyla Grid, Nauck ile C-ANFIS birinci",
], { x: 8.3, y: 1.5, w: 4.4, h: 5.3, fontSize: 15 });

// =========================== 21. Sınırlılıklar ===========================
s = slide("CONTENT", "Sınırlılıklar ve gelecek çalışmalar",
  "Sınırlılıklar: bu bir derleme olduğu için karşılaştırma niteliksel bir tutarlılık kontrolü. Üç küçük tablo verisi kullandım. Hiperparametreler sabitti; hatta duyarlılık analizinde sınıf başına tek küme daha iyi çıktı. Anlamsal kısıt yok, kullanıcı çalışması yok. Gelecekte MF sıralamasını koruyan kısıtlı öğrenme, çok amaçlı optimizasyon ve Tip-2 MF'lerle gürültü dayanıklılığı denenebilir.");
card(s, 0.6, 1.5, 5.9, 5.2, "Sınırlılıklar", "• Derleme düzeyi karşılaştırma niteliksel bir tutarlılık kontrolüdür\n\n• 3 küçük/orta tablo verisi; görüntü ve zaman serisi yok\n\n• Hiperparametreler sabit (P7: c = 1 daha iyi: 2 kural, Pima %77,5)\n\n• Öğrenmede anlamsal MF kısıtı yok\n\n• Kullanıcı çalışması yok; Nauck indeksi TSK'ya uyarlandı", "E34948");
card(s, 6.8, 1.5, 5.9, 5.2, "Gelecek çalışmalar", "• MF sıralamasını ve kapsamayı koruyan kısıtlı öğrenme\n\n• Doğruluk + Nauck için çok amaçlı hiperparametre optimizasyonu\n\n• Tip-2 MF'ler ile gürültü dayanıklılığı\n\n• Yüksek boyutlu veriler ve kullanıcı çalışmaları", HEX.green);

// =========================== 22. Demo ===========================
s = slide("CONTENT", "Canlı demo: streamlit run demo/app.py",
  "Şimdi canlı demoya geçiyorum. Soldan veri setini ve parametreleri seçiyorum, üstteki kaydırıcılarla giriş değeri veriyorum. Altta üyelik dereceleri, her kuralın ateşleme kuvveti, kural çıktısı ve nihai karar görünüyor. Bu ekranda modelin her katmanını adım adım gösterebiliyorum. Hocam isterseniz farklı bir değer söyleyin, birlikte deneyelim.");
img(s, ASSET("demo.png"), 0.6, 1.4, 7.4, 7.4 * 1100 / 1600);
bullets(s, [
  "Veri seti, k, küme/sınıf ve τ seçilir",
  "Kaydırıcılarla gerçek birimlerde giriş verilir",
  "L1: üyelik dereceleri (grafik)",
  "L2–L3: kural ateşleme kuvvetleri (tablo)",
  "L4–L5: kural çıktıları ve nihai karar",
  "C-ANFIS ve Grid-ANFIS sekmeleri arasında karşılaştırma",
], { x: 8.3, y: 1.5, w: 4.4, h: 5.3, fontSize: 15 });

// =========================== 23. Sonuç ===========================
section("Sonuç");
s = slide("TITLE_DARK", null,
  "Özetle: makalenin Borda analizini birebir ürettim ve iki tutarsızlık buldum. ANFIS'i sıfırdan yazdım ve sonuçlar makaleyle uyumlu. C-ANFIS, anlamlı doğruluk kaybı olmadan kuralları yüzde 76 azalttı ve yüksek boyutta yüz kattan fazla hızlandı. Gürültüde iyileşme yok, bunu da raporladım. Teşekkür ederim, sorularınızı alabilirim.");
s.addText("Sonuç", { placeholder: "title" });
s.addText([
  { text: "R1: Borda sıralaması 20/20 üretildi, 2 tutarsızlık bulundu", options: { bullet: true, breakLine: true } },
  { text: "R2–R3: Sıfırdan ANFIS makale medyanlarıyla uyumlu (%93, 16 kural); fidelity %77–99", options: { bullet: true, breakLine: true } },
  { text: "C-ANFIS: −%76 kural, Nauck ×6,7, doğruluk farkı anlamlı değil (p = 0,15)", options: { bullet: true, breakLine: true } },
  { text: "k = 8: 120–160× hızlı, Pima'da +8 puan · Gürültüde iyileşme yok (olumsuz sonuç)", options: { bullet: true, breakLine: true } },
  { text: "Teşekkürler — Sorular?", options: { bold: true, color: "FFFFFF" } },
], { placeholder: "body" });

(async () => {
  const out = path.join(__dirname, "presentation.pptx");
  await pres.writeFile({ fileName: out });
  if (SKILL) {
    const { applyTheme } = require(path.join(SKILL, "scripts", "apply_theme.js"));
    await applyTheme(out, THEME);
  }
  console.log("yazıldı:", out);
})();
