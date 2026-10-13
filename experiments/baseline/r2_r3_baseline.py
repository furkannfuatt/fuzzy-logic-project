"""Deney R2 + R3 — Baseline yeniden gerçekleştirme deneyleri.

R2: Grid-partition ANFIS (Jang 1993) — makalenin en çok çalışılan bulanık tekniği —
    makalede sık geçen benchmark veri setlerinde (Iris, WDBC, Pima) 10-kat CV ile
    çalıştırılır; doğruluk ve kural sayısı makalenin ANFIS medyanlarıyla
    (Tablo 9: %95 doğruluk, Tablo 6: 17 kural) karşılaştırılır. Referans olarak
    Wang–Mendel FRBS, karar ağacı ve MLP de aynı kıvrımlarda koşulur.
R3: Black-box MLP'nin bulanık surrogate'lerle açıklanması; fidelity (Denk. 25).

Çalıştırma: python -m experiments.baseline.r2_r3_baseline
"""
from pathlib import Path

import pandas as pd

from src.experiment import cross_validate, surrogate_cv

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/tables"
DATASETS = ["iris", "wdbc", "pima"]
BASELINE_MODELS = ["Grid-ANFIS (2MF)", "Grid-ANFIS (3MF)", "Wang-Mendel (3MF)",
                   "Wang-Mendel orijinal (max)", "Karar Ağacı (d≤4)", "MLP"]
NOISE = (0.0, 0.05, 0.1, 0.2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("R2: baseline çapraz doğrulama")
    raw = pd.concat([cross_validate(d, BASELINE_MODELS, noise_levels=NOISE) for d in DATASETS])
    raw.to_csv(OUT / "baseline_raw.csv", index=False)

    clean = raw[raw.noise == 0]
    summ = (clean.groupby(["dataset", "model"])
            .agg(acc_mean=("accuracy", "mean"), acc_std=("accuracy", "std"),
                 f1_mean=("f1", "mean"), rules=("n_rules", "median"),
                 rule_len=("total_rule_length", "median"), nauck=("nauck", "mean"),
                 fit_time_s=("fit_time_s", "mean"))
            .round(3).reset_index())
    summ.to_csv(OUT / "r2_baseline_summary.csv", index=False)
    print(summ.to_string(index=False))

    # Makale ile karşılaştırma (ANFIS)
    an = clean[clean.model == "Grid-ANFIS (2MF)"]
    cmp = pd.DataFrame([
        {"kaynak": "Makale (Tablo 9/6, 19 çalışmanın medyanı)", "medyan_doğruluk": 95.0,
         "min_doğruluk": 78.0, "maks_doğruluk": 99.9, "medyan_kural": 17},
        {"kaynak": "Bizim Grid-ANFIS (2MF), 3 veri × 10 kat", "medyan_doğruluk": round(an.accuracy.median(), 2),
         "min_doğruluk": round(an.accuracy.min(), 2), "maks_doğruluk": round(an.accuracy.max(), 2),
         "medyan_kural": int(an.n_rules.median())},
    ] + [{"kaynak": f"  └ {d}", "medyan_doğruluk": round(an[an.dataset == d].accuracy.median(), 2),
          "min_doğruluk": round(an[an.dataset == d].accuracy.min(), 2),
          "maks_doğruluk": round(an[an.dataset == d].accuracy.max(), 2),
          "medyan_kural": int(an[an.dataset == d].n_rules.median())} for d in DATASETS])
    cmp.to_csv(OUT / "r2_paper_comparison.csv", index=False)
    print("\n", cmp.to_string(index=False))

    print("\nR3: black-box MLP + bulanık surrogate (fidelity)")
    sur = pd.concat([surrogate_cv(d, ["Wang-Mendel (3MF)", "Grid-ANFIS (2MF)", "C-ANFIS",
                                      "Karar Ağacı (d≤4)"]) for d in DATASETS])
    sur.to_csv(OUT / "r3_surrogate_raw.csv", index=False)
    s = (sur.groupby(["dataset", "model"])
         .agg(fidelity=("fidelity", "mean"), fidelity_std=("fidelity", "std"),
              accuracy=("accuracy", "mean"), rules=("n_rules", "median"))
         .round(2).reset_index())
    s.to_csv(OUT / "r3_surrogate_summary.csv", index=False)
    print(s.to_string(index=False))


if __name__ == "__main__":
    main()
