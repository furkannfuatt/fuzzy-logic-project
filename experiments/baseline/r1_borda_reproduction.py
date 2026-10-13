"""Deney R1 — Makalenin Borda count analizinin (Bölüm 11, Şekil 21) yeniden üretimi.

Girdi : makalenin Tablo 6 (medyan kural sayısı) ve Tablo 9 (medyan doğruluk) değerleri
Çıktı : results/tables/r1_borda_reproduction.csv, results/tables/r1_tie_sensitivity.csv,
        results/figures/r1_borda.png
Çalıştırma: python -m experiments.baseline.r1_borda_reproduction
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.borda import PAPER_FIG21, PAPER_TABLE, borda

ROOT = Path(__file__).resolve().parents[2]
TAB, FIG = ROOT / "results/tables", ROOT / "results/figures"


def main():
    TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    res = borda(PAPER_TABLE, {"accuracy": True, "rules": False})
    res["paper_acc_rank"] = res["system"].map(lambda s: PAPER_FIG21[s][0])
    res["paper_rules_rank"] = res["system"].map(lambda s: PAPER_FIG21[s][1])
    res["paper_tradeoff_rank"] = res["system"].map(lambda s: PAPER_FIG21[s][2])
    res["match"] = ((res.accuracy_rank == res.paper_acc_rank) & (res.rules_rank == res.paper_rules_rank)
                    & (res.tradeoff_rank == res.paper_tradeoff_rank))
    res.to_csv(TAB / "r1_borda_reproduction.csv", index=False)
    n_match = int(res["match"].sum())
    print(res[["system", "accuracy", "rules", "accuracy_rank", "rules_rank", "tradeoff_rank",
               "paper_tradeoff_rank", "match"]].to_string(index=False))
    print(f"\nŞekil 21 ile birebir eşleşen sistem: {n_match}/{len(res)}")

    # Duyarlılık analizi: farklı bağ (tie) politikaları ve FRI veri hatası
    rows = []
    for name, kw, table in [
        ("Makale (acc=ordinal, rules=dense, total=dense)", dict(), PAPER_TABLE),
        ("Tutarlı: hepsi 'min' (standart yarışma sırası)", dict(acc_method="min", other_method="min", total_method="min"), PAPER_TABLE),
        ("Tutarlı: hepsi 'average'", dict(acc_method="average", other_method="average", total_method="dense"), PAPER_TABLE),
        ("FRI hariç (şüpheli veri)", dict(), PAPER_TABLE[PAPER_TABLE.system != "FRI"]),
    ]:
        r = borda(table, {"accuracy": True, "rules": False}, **kw)
        top = r.loc[r.tradeoff_rank <= 2, "system"].tolist()
        rows.append({"senaryo": name, "ilk_2_sira": ", ".join(top),
                     "ANFIS_tradeoff_rank": int(r.loc[r.system == "ANFIS", "tradeoff_rank"].iloc[0])})
    sens = pd.DataFrame(rows); sens.to_csv(TAB / "r1_tie_sensitivity.csv", index=False)
    print("\n", sens.to_string(index=False))

    # Grafik: bizim hesapladığımız vs makale tradeoff sırası
    r = res.sort_values("tradeoff_rank")
    x = np.arange(len(r))
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.bar(x - 0.2, r.accuracy_rank, 0.4, label="Doğruluk sırası", color="#2a6f97")
    ax.bar(x + 0.2, r.rules_rank, 0.4, label="Kural sayısı sırası", color="#e07a5f")
    ax.plot(x, r.tradeoff_rank, "-o", color="#1b4332", label="Tradeoff sırası (bizim)")
    ax.plot(x, r.paper_tradeoff_rank, "x", color="black", ms=9, label="Tradeoff sırası (makale Şekil 21)")
    ax.set_xticks(x); ax.set_xticklabels(r.system, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("Sıra (düşük = iyi)")
    ax.set_title(f"R1: Borda count yeniden üretimi — {n_match}/{len(r)} sistem Şekil 21 ile birebir aynı")
    ax.legend(fontsize=8, ncol=2); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "r1_borda.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    main()
