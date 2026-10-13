"""Borda count tabanlı performans–yorumlanabilirlik dengesi sıralaması.

Ouifak & Idri (2025), Bölüm 11: her sistem doğruluk (yüksek iyi) ve kural sayısı
(düşük iyi) için ayrı ayrı sıralanır; sıralar toplanır, toplam küçükten büyüğe
yeniden sıralanarak "tradeoff rank" elde edilir.

Makaledeki Şekil 21 incelendiğinde bağların (ties) farklı ele alındığı görülür:
  * doğruluk sırası  : "ordinal" (eşitlik keyfi kırılmış, ör. Dynamic FRI=3, CFC=4)
  * kural sırası     : "dense"   (eşitler aynı sırayı alır, sonraki sıra atlanmaz)
  * tradeoff sırası  : "dense"
Bu modül, makalenin yöntemini birebir yeniden üretmek için bu kuralları uygular ve
farklı bağ politikalarının sonuca etkisini (duyarlılık analizi) incelemeye izin verir.
"""
from __future__ import annotations

import pandas as pd

# Makaleden alınan medyan değerler: Tablo 9 (doğruluk %) ve Tablo 6 (kural sayısı).
# Şekil 21'de yer alan 20 sistem. Not: "FRI" satırının Tablo 9'daki doğruluk değerleri
# (4, 20, 11, 11.33, 5.22) Tablo 6'daki kural sayısı değerleriyle birebir aynıdır;
# makaledeki olası bir kopyalama hatası olarak raporda tartışılmıştır. Şekil 20 de
# FRI medyan doğruluğunu ~11 olarak çizer, bu yüzden yeniden üretimde 11 kullanılır.
PAPER_TABLE = pd.DataFrame([
    # sistem,                 medyan doğruluk, medyan kural
    ("GFS",                    99.00,   3.2),
    ("Dynamic FRI",            93.50,  11.5),
    ("FMM",                    90.55,   6.5),
    ("SOFNN",                  91.40,   9.0),
    ("ANFIS",                  95.00,  17.0),
    ("Evolving FNN",           92.00,  13.0),
    ("CFC",                    93.50,  28.0),
    ("Fuzzy SVM",              87.00,  10.0),
    ("POPFNN",                 88.55,  13.0),
    ("FCM (cognitive map)",    87.25,  17.0),
    ("IT2FLS",                 90.00,  40.0),
    ("TSK FNN",                87.67,  28.0),
    ("FURIA",                  65.44,  10.0),
    ("Fuzzy C-means",          84.31,  25.0),
    ("FRI",                    11.00,  11.0),
    ("Fuzzy ART/ARTMAP",       82.10,  25.0),
    ("NEFCLASS",               76.75,  21.5),
    ("Monotone FRI",           82.50,  58.0),
    ("DENFIS",                 75.25,  34.135),
    ("Zero-order TSK",         73.34,  82.135),
], columns=["system", "accuracy", "rules"])

# Şekil 21'deki sıra tablosu (karşılaştırma için, makaleden okunmuştur)
PAPER_FIG21 = {
    "GFS": (1, 1, 1), "Dynamic FRI": (3, 6, 2), "FMM": (7, 2, 2), "SOFNN": (6, 3, 2),
    "ANFIS": (2, 8, 3), "Evolving FNN": (5, 7, 4), "CFC": (4, 11, 5), "Fuzzy SVM": (12, 4, 6),
    "POPFNN": (9, 7, 6), "FCM (cognitive map)": (11, 8, 7), "IT2FLS": (8, 13, 8),
    "TSK FNN": (10, 11, 8), "FURIA": (19, 4, 9), "Fuzzy C-means": (13, 10, 9), "FRI": (20, 5, 10),
    "Fuzzy ART/ARTMAP": (15, 10, 10), "NEFCLASS": (16, 9, 10), "Monotone FRI": (14, 14, 11),
    "DENFIS": (17, 12, 12), "Zero-order TSK": (18, 15, 13),
}


def borda(df: pd.DataFrame, criteria: dict[str, bool], acc_method="first",
          other_method="dense", total_method="dense") -> pd.DataFrame:
    """criteria: {sütun: yüksek_değer_iyi_mi}. İlk kriter 'acc_method', diğerleri
    'other_method' bağ politikasıyla sıralanır. Tradeoff = sıra toplamının sırası."""
    out = df.copy()
    rank_cols = []
    for i, (col, higher_better) in enumerate(criteria.items()):
        method = acc_method if i == 0 else other_method
        rc = f"{col}_rank"
        out[rc] = out[col].rank(ascending=not higher_better, method=method).astype(int)
        rank_cols.append(rc)
    out["rank_sum"] = out[rank_cols].sum(axis=1)
    out["tradeoff_rank"] = out["rank_sum"].rank(method=total_method).astype(int)
    return out.sort_values(["tradeoff_rank", rank_cols[0]]).reset_index(drop=True)
