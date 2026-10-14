# Bulanık Mantık Tabanlı Yorumlanabilirlik: ANFIS'in Yeniden Gerçekleştirilmesi ve Kompakt C-ANFIS

Bulanık Mantık Dersi Dönem Projesi · 2026–2027 Güz · İstanbul Üniversitesi-Cerrahpaşa, Bilgisayar Mühendisliği

## Student Information

| | |
|---|---|
| Öğrenci | Furkan Fuat Küçükbayrak |
| Numara | 1306230124 |
| Ders sorumlusu | Tolgahan Öztürk |
| Teknik rapor | [`report/report.pdf`](report/report.pdf) |
| Sunum | [`presentation/presentation.pptx`](presentation/presentation.pptx) · [`presentation/presentation.pdf`](presentation/presentation.pdf) |

## Original Paper

H. Ouifak and A. Idri, "A comprehensive review of fuzzy logic based interpretability and explainability of machine learning techniques across domains," *Neurocomputing*, vol. 647, Art. no. 130602, 2025. doi: [10.1016/j.neucom.2025.130602](https://doi.org/10.1016/j.neucom.2025.130602)

Referans çalışma, 1994–2024 yılları arasındaki 330 çalışmayı inceleyen **sistematik bir derlemedir**. Yeni bir algoritma önermez. Bu nedenle bu projede yeniden üretim kapsamı (MRR) şöyle tanımlanmıştır:

| Kod | Yeniden üretilen bileşen | Makaledeki karşılığı |
|---|---|---|
| **R1** | Performans–yorumlanabilirlik Borda sıralaması | Tablo 6, Tablo 9, Bölüm 11, Şekil 21 |
| **R2** | Makalenin merkezî tekniği **ANFIS**'in sıfırdan gerçekleştirilmesi ve benchmark verilerinde makale medyanlarıyla (%95 doğruluk, 17 kural) karşılaştırılması | Bölüm 6.1, Tablo 6, Tablo 9 |
| **R3** | Kara kutu MLP'nin bulanık vekillerle (surrogate) açıklanması ve **fidelity** ölçümü | Bölüm 9.1, Denk. (25) |

## Problem Description

Kara kutu modeller (DNN, MLP, SVM) yüksek doğruluk sağlar, ancak kararlarını açıklayamaz. Bulanık mantık, model davranışını dilsel kurallara (*EĞER glikoz Yüksek VE BMI Yüksek İSE diyabet*) çevirerek yorumlanabilirlik sağlar. Derleme, en çok kullanılan tekniğin ANFIS olduğunu raporlar. Bununla birlikte derleme şu sınırlılıklara dikkat çeker:

- Grid-partition ANFIS'te kural sayısı **p^d** ile üstel büyür (kural patlaması).
- Bu durum hesaplama maliyetini ve ölçeklenebilirliği olumsuz etkiler.
- Yorumlanabilirlik neredeyse yalnızca kural sayısıyla ölçülmektedir; standart bir metrik yoktur.

## Method

### Baseline: Grid-ANFIS (Jang, 1993)

`src/anfis.py` — NumPy ile sıfırdan yazılmıştır; bulanık mantık kütüphanesi kullanılmamıştır.

- 5 katman: Gauss MF → çarpım t-normu → normalizasyon → birinci derece TSK sonucu → ağırlıklı toplam.
- Hibrit öğrenme: sonuç parametreleri ridge-LSE ile, MF parametreleri analitik gradyan + Adam ile öğrenilir.
- Gradyan, sayısal türevle doğrulanmıştır: `tests/test_anfis.py`.

### Önerilen: C-ANFIS (özgün katkı)

`src/canfis.py`

1. **Sınıf-bazlı Fuzzy C-Means** ile kural üretimi. Kural sayısı K·c olur ve öznitelik sayısından bağımsızdır.
2. Baseline ile **aynı hibrit eğitim**.
3. **Jaccard benzerliği** > τ olan MF'lerin birleştirilmesi.
4. Evrenin ≥%80'ini kaplayan **önemsiz koşulların** kaldırılması.
5. Kapsamı düşük **kuralların budanması**.
6. **İnce ayar**.

Ek yorumlanabilirlik metrikleri (`src/metrics.py`): toplam kural uzunluğu, MF sayısı, Jaccard ayırt edilebilirlik ve **Nauck indeksi** (comp × cov × part).

### Referans modeller

- **Wang–Mendel** (Mamdani, `src/wang_mendel.py`)
- **Karar ağacı** (d ≤ 4)
- **MLP** (kara kutu)

## Fuzzy System Architecture

```
x ∈ [0,1]^k ──► L1 Bulanıklaştırma  μ_l(x_j) = exp(-(x_j-c_l)²/2σ_l²)      [öğrenilir: c, σ — gradyan]
            ──► L2 Kural ateşleme   w_r = ∏ μ (product t-norm)
            ──► L3 Normalizasyon    w̄_r = w_r / Σ w
            ──► L4 TSK sonucu       f_r^k = p_r^k · [x, 1]                  [öğrenilir: p — LSE]
            ──► L5 Toplama          y^k = Σ_r w̄_r f_r^k  →  sınıf = argmax_k y^k
```

| | Grid-ANFIS (baseline) | C-ANFIS (önerilen) |
|---|---|---|
| Girdi | MI ile seçilen k = 4 öznitelik, MinMax [0,1] | aynı |
| MF | 2 Gauss MF/öznitelik (Düşük, Yüksek), 0,5'te kesişir | FCM merkez/std'den Gauss; birleştirmeyle 1–4 MF/öznitelik |
| Kural tabanı | tüm kombinasyonlar: 2^k = 16 | K × 2 küme → budama sonrası ≈ 3–5 |
| Çıkarım | TSK-1, çarpım t-normu | aynı |
| Durulaştırma | ağırlıklı ortalama, argmax | aynı |

## Dataset

| Veri | Örnek | Öznitelik | Sınıf | Kaynak |
|---|---|---|---|---|
| Iris | 150 | 4 | 3 | scikit-learn (Fisher, 1936) |
| Breast Cancer Wisconsin Diagnostic (WDBC) | 569 | 30 | 2 | scikit-learn (Street vd., 1993) |
| Pima Indians Diabetes | 768 | 8 | 2 | `data/pima_raw.csv` (Smith vd., 1988; UCI aynası: jbrownlee/Datasets) |

`python data/prepare_data.py` komutu, üç veri setini `data/*.csv` olarak hazırlar. Komut internet gerektirmez. WDBC'de hedef değişken 1 = malign olacak biçimde yeniden kodlanmıştır.

## Installation / Requirements

```bash
git clone <repo-url> fuzzy-logic-project && cd fuzzy-logic-project
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Test edilen ortamlar:

- Python 3.13, numpy 2.5, scipy 1.18, pandas 3.0, scikit-learn 1.9, matplotlib 3.11, streamlit 1.65 (raporlanan sonuçlar bu ortamda üretildi).
- Python 3.10, numpy 2.2, scikit-learn 1.7, pandas 2.3 (macOS üzerinde Linux VM): testler ve R1 birebir aynı sonucu verdi. C-ANFIS doğruluğu kütüphane sürümü farkından dolayı ±0,2 puan oynayabilir (ör. WDBC: 92,79 → 92,97). Grid-ANFIS sonuçları birebir aynı çıktı.

GPU gerekmez. Süre ölçümleri donanıma bağlıdır.

## How to Run

```bash
python run_all.py                       # tüm deneyler + grafikler (~8 dk, 2 çekirdek CPU)
streamlit run demo/app.py               # canlı demo (tarayıcıda açılır)
python tests/test_anfis.py              # gradyan doğrulama ve öğrenme testi
```

Tek tek çalıştırma:

```bash
python -m experiments.baseline.r1_borda_reproduction    # R1
python -m experiments.baseline.r2_r3_baseline           # R2 + R3 (baseline)
python -m experiments.proposed.p_canfis_experiments     # P1–P7 (önerilen)
python -m experiments.make_figures                      # results/figures/*.png
python presentation/build_presentation.py              # sunum (python-pptx)
```

## Reproduction Experiments

| Deney | Sonuç |
|---|---|
| **R1** Borda sıralaması | Şekil 21, **20/20 sistemde birebir** üretildi. Makalede bağ politikası tutarsızdır: tutarlı "min" politikasıyla ANFIS 3. sıradan 5. sıraya düşer. Ayrıca Tablo 9'daki FRI doğruluk satırı, Tablo 6'daki kural sayılarıyla birebir aynıdır (olası veri hatası). |
| **R2** Grid-ANFIS | Iris %95,3 · WDBC %93,8 · Pima %74,9 (10-kat CV). Medyan %93, 16 kural; makaledeki %95 / 17 kural ile uyumlu. |
| **R3** Fidelity | Iris %91–99 · WDBC %91–93 · Pima %77–80. C-ANFIS 3,5–5 kuralla Iris ve Pima'da en yüksek fidelity'yi verdi. |

## Proposed Extension — Experimental Results

Grid-ANFIS (2MF) ve C-ANFIS karşılaştırması (3 veri seti × 10 kat, eşleştirilmiş):

| Performans ölçütü | Baseline | C-ANFIS | Değişim |
|---|---|---|---|
| Accuracy (%) | 88,02 | 87,18 | −0,84 puan (Wilcoxon p = 0,152, anlamlı değil) |
| Macro-F1 (%) | 86,70 | 85,88 | −0,82 puan |
| Kural sayısı | 16,0 | 3,83 | **−%76** |
| Toplam kural uzunluğu | 64,0 | 14,8 | **−%77** |
| MF sayısı | 8,0 | 13,4 | +%68 (olumsuz) |
| Nauck indeksi | 0,0069 | 0,0462 | **×6,7** |
| Execution time — eğitim (s/kat) | 0,121 | 0,100 | −%17 |
| Execution time — çıkarım (ms/örnek) | 0,0045 | 0,0030 | −%33 |

- **Ölçeklenebilirlik (k = 8):** Grid-ANFIS 256 kural kullanır ve bir kat ≈21 s sürer. C-ANFIS ise 3–4 kuralla ≈0,15 s'de eğitilir; bu **122–161 kat** daha hızlıdır. Pima'da doğruluk %66,2'ye karşı **%74,2**'dir.
- **Ablation:** Kazancın asıl kaynağı FCM ile kural üretimidir. Nauck indeksi her adımda artar.
- **Gürültü:** İyileşme yoktur (σ = 0,1'de −1,8 puan, p = 0,21). Olası nedenler raporun Bölüm 9'unda tartışılmıştır.

Grafikler `results/figures/`, tablolar `results/tables/` (ham CSV dahil) altındadır.

## Repository Structure

```
fuzzy-logic-project/
├── README.md · LICENSE · requirements.txt · .gitignore · run_all.py
├── src/                  anfis.py · canfis.py · fcm.py · wang_mendel.py · metrics.py · borda.py · data.py · experiment.py
├── data/                 prepare_data.py · pima_raw.csv · iris.csv · wdbc.csv · pima.csv
├── experiments/baseline/ r1_borda_reproduction.py · r2_r3_baseline.py
├── experiments/proposed/ p_canfis_experiments.py
├── experiments/          make_figures.py
├── results/figures/      *.png       results/tables/  *.csv, example_rules_wdbc.txt
├── demo/app.py           Streamlit canlı demo
├── tests/test_anfis.py   gradyan doğrulama
├── presentation/         presentation.pptx · presentation.pdf · build_presentation.py · speaker_notes.json
├── report/               report.pdf · report.html (kaynak)
└── references/README.md
```

## Limitations

- Referans çalışma bir derleme olduğundan, makaleyle karşılaştırma niteliksel bir tutarlılık kontrolüdür.
- Yalnızca 3 küçük/orta ölçekli tablo verisi kullanılmıştır.
- Hiperparametreler önceden sabitlenmiştir. P7 duyarlılık analizinde küme/sınıf = 1 daha iyi sonuç vermiştir.
- Öğrenme sırasında MF anlamsal kısıtları yoktur; grid MF'leri eğitimle anlamını yitirebilir (rapor, Şekil 7).
- Kullanıcı çalışması yapılmamıştır.
- Gürültüye dayanıklılıkta iyileşme sağlanamamıştır.

## Code Provenance and Generative AI Disclosure

- Kodların tamamı bu proje için yazılmıştır. Referans makalenin yazarlarına ait resmi bir kod yoktur ve kullanılmamıştır. Harici bulanık mantık kütüphanesi (scikit-fuzzy, anfis vb.) kullanılmamıştır.
- scikit-learn yalnızca veri bölme, karşılıklı bilgi, MinMax ölçekleme, MLP ve karar ağacı için kullanılmıştır.
- Üretken yapay zekâ (Anthropic Claude) kodun yazılması ve hata ayıklanmasında kullanılmıştır. Deney tasarımı ve hiperparametre seçimi, literatür taraması ile rapor ve sunum metni öğrenciye aittir; Claude bu metinlerde yalnızca dil düzenlemesi için kullanılmıştır. Ayrıntılar raporun "Generative AI Usage Disclosure" bölümündedir.
- API anahtarı, parola veya erişim belirteci içermez.

## References

Tam IEEE kaynakça: [`references/README.md`](references/README.md) ve [`report/report.pdf`](report/report.pdf).
