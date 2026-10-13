"""Önerilen yöntem (C-ANFIS) deneyleri.

P1  Ana karşılaştırma  : C-ANFIS vs Grid-ANFIS baseline (aynı kıvrımlar, eşleştirilmiş)
P2  Ablation           : C-ANFIS bileşenlerinin tek tek katkısı
P3  Gürültü/robustness : test girdilerine Gauss gürültüsü (σ = 0, .05, .1, .2)
P4  Ölçeklenebilirlik  : öznitelik sayısı k ∈ {2,4,6,8} — kural sayısı ve süre
P5  İstatistik         : Wilcoxon işaretli sıra testi (30 eşleştirilmiş kat)
P6  Borda (genişletilmiş): doğruluk + kural (makale yöntemi) ve + Nauck indeksi
P7  Parametre duyarlılığı: küme sayısı/sınıf ve birleştirme eşiği tau

Önkoşul: python -m experiments.baseline.r2_r3_baseline  (baseline_raw.csv)
Çalıştırma: python -m experiments.proposed.p_canfis_experiments
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from src.borda import borda
from src.experiment import cross_validate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/tables"
DATASETS = ["iris", "wdbc", "pima"]
NOISE = (0.0, 0.05, 0.1, 0.2)
ABLATION = ["FCM-ANFIS (yalnız FCM)", "FCM + birleştirme", "FCM + birleştirme + önemsiz koşul",
            "C-ANFIS", "Grid + sadeleştirme (FCM yok)"]


def summarize(df):
    return (df.groupby(["dataset", "model"])
            .agg(acc_mean=("accuracy", "mean"), acc_std=("accuracy", "std"), f1_mean=("f1", "mean"),
                 rules=("n_rules", "mean"), n_mfs=("n_mfs", "mean"), rule_len=("total_rule_length", "mean"),
                 distinguish=("distinguishability", "mean"), nauck=("nauck", "mean"),
                 fit_time_s=("fit_time_s", "mean"), infer_ms=("infer_ms_per_sample", "mean"))
            .round(3).reset_index())


def main():
    base = pd.read_csv(OUT / "baseline_raw.csv")

    # ---------------- P1 + P2 + P3 ----------------
    print("P1-P3: C-ANFIS + ablation (10-kat CV, gürültü seviyeleri dahil)")
    prop = pd.concat([cross_validate(d, ABLATION, noise_levels=NOISE) for d in DATASETS])
    prop.to_csv(OUT / "proposed_raw.csv", index=False)
    allr = pd.concat([base, prop], ignore_index=True)
    clean = allr[allr.noise == 0]
    summ = summarize(clean); summ.to_csv(OUT / "p1_p2_summary.csv", index=False)
    print(summ.to_string(index=False))

    # P1 tablo: yönerge 6.2 formatı (Baseline / Geliştirilen / Değişim)
    rows = []
    for d in DATASETS + ["TÜMÜ"]:
        sel = clean if d == "TÜMÜ" else clean[clean.dataset == d]
        b = sel[sel.model == "Grid-ANFIS (2MF)"]; p = sel[sel.model == "C-ANFIS"]
        for metric, col in [("Accuracy (%)", "accuracy"), ("Macro-F1 (%)", "f1"),
                            ("Kural sayısı", "n_rules"), ("Toplam kural uzunluğu", "total_rule_length"),
                            ("MF sayısı", "n_mfs"), ("Nauck indeksi", "nauck"),
                            ("Eğitim süresi (s)", "fit_time_s"), ("Çıkarım (ms/örnek)", "infer_ms_per_sample")]:
            bv, pv = b[col].mean(), p[col].mean()
            rows.append({"veri": d, "ölçüt": metric, "baseline": round(bv, 4), "C-ANFIS": round(pv, 4),
                         "değişim_%": round(100 * (pv - bv) / bv, 1) if bv else np.nan})
    p1 = pd.DataFrame(rows); p1.to_csv(OUT / "p1_baseline_vs_proposed.csv", index=False)
    print("\n", p1[p1.veri == "TÜMÜ"].to_string(index=False))

    # P3 gürültü
    nz = (allr[allr.model.isin(["Grid-ANFIS (2MF)", "Grid-ANFIS (3MF)", "C-ANFIS", "Wang-Mendel (3MF)",
                                 "Karar Ağacı (d≤4)", "MLP"])]
          .groupby(["dataset", "model", "noise"]).accuracy.mean().round(2).reset_index())
    nz.to_csv(OUT / "p3_noise.csv", index=False)

    # ---------------- P5 Wilcoxon ----------------
    tests = []
    for d in DATASETS + ["TÜMÜ"]:
        sel = clean if d == "TÜMÜ" else clean[clean.dataset == d]
        for other in ["Grid-ANFIS (2MF)", "Grid-ANFIS (3MF)", "FCM-ANFIS (yalnız FCM)"]:
            a = sel[sel.model == "C-ANFIS"].sort_values(["dataset", "fold"]).accuracy.to_numpy()
            b = sel[sel.model == other].sort_values(["dataset", "fold"]).accuracy.to_numpy()
            diff = a - b
            p = wilcoxon(a, b, zero_method="zsplit").pvalue if np.any(diff != 0) else 1.0
            tests.append({"veri": d, "karşılaştırma": f"C-ANFIS vs {other}", "n_kat": len(a),
                          "ort_fark_puan": round(diff.mean(), 2), "p_değeri": round(float(p), 4),
                          "anlamlı_(α=0.05)": "evet" if p < 0.05 else "hayır"})
    # gürültü altında (σ=0.1) da test et
    n1 = allr[allr.noise == 0.1]
    a = n1[n1.model == "C-ANFIS"].sort_values(["dataset", "fold"]).accuracy.to_numpy()
    b = n1[n1.model == "Grid-ANFIS (2MF)"].sort_values(["dataset", "fold"]).accuracy.to_numpy()
    tests.append({"veri": "TÜMÜ (σ=0.1 gürültü)", "karşılaştırma": "C-ANFIS vs Grid-ANFIS (2MF)",
                  "n_kat": len(a), "ort_fark_puan": round((a - b).mean(), 2),
                  "p_değeri": round(float(wilcoxon(a, b, zero_method="zsplit").pvalue), 4),
                  "anlamlı_(α=0.05)": "evet" if wilcoxon(a, b, zero_method="zsplit").pvalue < 0.05 else "hayır"})
    wt = pd.DataFrame(tests); wt.to_csv(OUT / "p5_wilcoxon.csv", index=False)
    print("\n", wt.to_string(index=False))

    # ---------------- P6 Borda ----------------
    fuzzy = ["Grid-ANFIS (2MF)", "Grid-ANFIS (3MF)", "Wang-Mendel (3MF)"] + ABLATION
    med = (clean[clean.model.isin(fuzzy)].groupby("model")
           .agg(accuracy=("accuracy", "median"), rules=("n_rules", "median"), nauck=("nauck", "median"))
           .reset_index().rename(columns={"model": "system"}))
    b2 = borda(med, {"accuracy": True, "rules": False}).assign(yöntem="makale (acc+kural)")
    b3 = borda(med, {"accuracy": True, "rules": False, "nauck": True}).assign(yöntem="genişletilmiş (+Nauck)")
    pd.concat([b2, b3]).to_csv(OUT / "p6_borda_ours.csv", index=False)
    print("\n", b2[["system", "accuracy", "rules", "tradeoff_rank"]].to_string(index=False))
    print("\n", b3[["system", "accuracy", "rules", "nauck", "tradeoff_rank"]].to_string(index=False))

    # ---------------- P4 Ölçeklenebilirlik ----------------
    print("\nP4: ölçeklenebilirlik (5-kat CV)")
    sc = []
    for d in ["wdbc", "pima"]:
        for k in [2, 4, 6, 8]:
            r = cross_validate(d, ["Grid-ANFIS (2MF)", "C-ANFIS"], k_features=k, n_folds=5, verbose=False)
            r["k"] = k; sc.append(r)
            print(f"  {d} k={k} tamam", flush=True)
    sc = pd.concat(sc)
    scs = (sc.groupby(["dataset", "k", "model"])
           .agg(acc=("accuracy", "mean"), rules=("n_rules", "mean"), rule_len=("total_rule_length", "mean"),
                fit_time_s=("fit_time_s", "mean"), nauck=("nauck", "mean")).round(3).reset_index())
    scs.to_csv(OUT / "p4_scalability.csv", index=False)
    print(scs.to_string(index=False))

    # ---------------- P7 Parametre duyarlılığı ----------------
    print("\nP7: parametre duyarlılığı")
    sens = []
    for d in ["wdbc", "pima"]:
        for cpc in [1, 2, 3, 4]:
            r = cross_validate(d, ["C-ANFIS"], verbose=False, model_kw={"clusters_per_class": cpc})
            sens.append({"veri": d, "parametre": "küme/sınıf", "değer": cpc, "acc": r.accuracy.mean(),
                         "rules": r.n_rules.mean(), "nauck": r.nauck.mean()})
        for tau in [0.4, 0.5, 0.6, 0.7, 0.8]:
            r = cross_validate(d, ["C-ANFIS"], verbose=False, model_kw={"tau": tau})
            sens.append({"veri": d, "parametre": "tau", "değer": tau, "acc": r.accuracy.mean(),
                         "rules": r.n_rules.mean(), "nauck": r.nauck.mean()})
    sens = pd.DataFrame(sens).round(3); sens.to_csv(OUT / "p7_sensitivity.csv", index=False)
    print(sens.to_string(index=False))


if __name__ == "__main__":
    main()
