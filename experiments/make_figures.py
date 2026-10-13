"""Sonuç tablolarından rapor/sunum grafiklerini üretir (results/figures/).
Çalıştırma: python -m experiments.make_figures
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.anfis import grid_anfis
from src.canfis import build_canfis
from src.data import Preprocessor, load_dataset

ROOT = Path(__file__).resolve().parents[1]
TAB, FIG = ROOT / "results/tables", ROOT / "results/figures"

# Her model her grafikte aynı rengi taşır (renk varlığı izler, sırayı değil)
COL = {"C-ANFIS": "#2a78d6", "Grid-ANFIS (2MF)": "#eb6834", "Grid-ANFIS (3MF)": "#1baf7a",
       "Wang-Mendel (3MF)": "#eda100", "Karar Ağacı (d≤4)": "#e87ba4", "MLP": "#008300"}
MARK = {"C-ANFIS": "o", "Grid-ANFIS (2MF)": "s", "Grid-ANFIS (3MF)": "D",
        "Wang-Mendel (3MF)": "^", "Karar Ağacı (d≤4)": "v", "MLP": "P"}
DS = {"iris": "Iris", "wdbc": "Breast Cancer (WDBC)", "pima": "Pima Diabetes"}

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.edgecolor": "#888",
                     "legend.frameon": False, "figure.dpi": 100})


def fig_tradeoff():
    s = pd.read_csv(TAB / "p1_p2_summary.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, d in zip(axes, DS):
        for m in [k for k in COL if k != "MLP"]:
            r = s[(s.dataset == d) & (s.model == m)]
            ax.scatter(r.rules, r.acc_mean, s=70, color=COL[m], marker=MARK[m], label=m,
                       edgecolor="white", linewidth=1.5, zorder=3)
        mlp = s[(s.dataset == d) & (s.model == "MLP")].acc_mean.iloc[0]
        ax.axhline(mlp, color=COL["MLP"], ls="--", lw=1.2, label="MLP (black-box, kural yok)")
        ax.set_xscale("log"); ax.set_xlabel("Kural sayısı (log ölçek, az = yorumlanabilir)")
        ax.set_title(DS[d]); ax.set_xlim(2, 120)
    axes[0].set_ylabel("Doğruluk (%) — 10-kat CV ort.")
    axes[0].legend(fontsize=7.5, loc="lower left")
    fig.suptitle("Performans–yorumlanabilirlik dengesi: C-ANFIS sol üst köşeye yakın (az kural, benzer doğruluk)", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "p1_tradeoff.png", dpi=200); plt.close(fig)


def fig_scalability():
    s = pd.read_csv(TAB / "p4_scalability.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.3))
    for d, ls in [("wdbc", "-"), ("pima", ":")]:
        for m in ["Grid-ANFIS (2MF)", "C-ANFIS"]:
            r = s[(s.dataset == d) & (s.model == m)]
            kw = dict(color=COL[m], marker=MARK[m], ls=ls, lw=2, ms=7, label=f"{m} — {DS[d]}")
            axes[0].plot(r.k, r.rules, **kw); axes[1].plot(r.k, r.fit_time_s, **kw); axes[2].plot(r.k, r.acc, **kw)
    axes[0].set_yscale("log"); axes[0].set_ylabel("Kural sayısı (log)"); axes[0].set_title("Kural sayısı: 2^k vs sabit")
    axes[1].set_yscale("log"); axes[1].set_ylabel("Eğitim süresi / kat (s, log)"); axes[1].set_title("Hesaplama maliyeti")
    axes[2].set_ylabel("Doğruluk (%)"); axes[2].set_title("Doğruluk")
    for ax in axes:
        ax.set_xlabel("Girdi öznitelik sayısı k"); ax.set_xticks([2, 4, 6, 8])
    h, l = axes[2].get_legend_handles_labels()
    fig.legend(h, l, fontsize=7.5, ncol=4, loc="lower center")
    fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig(FIG / "p4_scalability.png", dpi=200); plt.close(fig)


def fig_noise():
    s = pd.read_csv(TAB / "p3_noise.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.3), sharey=False)
    for ax, d in zip(axes, DS):
        for m in COL:
            r = s[(s.dataset == d) & (s.model == m)]
            ax.plot(r.noise, r.accuracy, color=COL[m], marker=MARK[m], lw=2, ms=6, label=m)
        ax.set_title(DS[d]); ax.set_xlabel("Test gürültüsü σ ([0,1] ölçekte)"); ax.set_xticks([0, .05, .1, .2])
    axes[0].set_ylabel("Doğruluk (%)"); axes[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "p3_noise.png", dpi=200); plt.close(fig)


def fig_ablation():
    s = pd.read_csv(TAB / "p1_p2_summary.csv")
    order = ["Grid-ANFIS (2MF)", "Grid + sadeleştirme (FCM yok)", "FCM-ANFIS (yalnız FCM)",
             "FCM + birleştirme", "FCM + birleştirme + önemsiz koşul", "C-ANFIS"]
    short = ["Grid (baseline)", "Grid+sadeleştirme", "Yalnız FCM", "+MF birleştirme", "+önemsiz koşul", "C-ANFIS (tam)"]
    agg = s[s.model.isin(order)].groupby("model")[["acc_mean", "rules", "rule_len", "nauck"]].mean().loc[order]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.3))
    y = np.arange(len(order))
    colors = ["#eb6834", "#f2a07f", "#9cc2ef", "#6aa2e6", "#4a8ddd", "#2a78d6"]
    for ax, col, title in [(axes[0], "acc_mean", "Ortalama doğruluk (%)"),
                           (axes[1], "rule_len", "Toplam kural uzunluğu (koşul sayısı)"),
                           (axes[2], "nauck", "Nauck indeksi (yüksek = iyi)")]:
        if col == "acc_mean":   # doğruluk farkları küçük: kesik eksenli çubuk yerine nokta grafiği
            ax.hlines(y, 80, agg[col], color="#ddd", lw=1); ax.scatter(agg[col], y, color=colors, s=60, zorder=3)
        else:
            ax.barh(y, agg[col], color=colors, height=0.6)
        for yi, v in zip(y, agg[col]):
            ax.text(v, yi, f" {v:.3f}" if col == "nauck" else f" {v:.1f}", va="center", fontsize=7.5, color="#333")
        ax.set_yticks(y); ax.set_yticklabels(short if ax is axes[0] else []); ax.invert_yaxis(); ax.set_title(title)
        ax.grid(axis="y", visible=False)
    axes[0].set_xlim(80, 96)
    fig.suptitle("Ablation: C-ANFIS bileşenlerinin katkısı (3 veri seti ortalaması)", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "p2_ablation.png", dpi=200); plt.close(fig)


def fig_fidelity():
    s = pd.read_csv(TAB / "r3_surrogate_summary.csv")
    s = s[s.model != "MLP (black-box)"]
    models = ["Wang-Mendel (3MF)", "Grid-ANFIS (2MF)", "C-ANFIS", "Karar Ağacı (d≤4)"]
    fig, ax = plt.subplots(figsize=(8, 3.2))
    w = 0.2; x = np.arange(3)
    for i, m in enumerate(models):
        r = s[s.model == m].set_index("dataset").loc[list(DS)]
        bars = ax.bar(x + (i - 1.5) * w, r.fidelity, w * 0.92, color=COL[m], label=f"{m}")
        for b, ru in zip(bars, r.rules):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, f"{ru:g}\nkural", ha="center", fontsize=6, color="#333")
    ax.set_xticks(x); ax.set_xticklabels([DS[d] for d in DS]); ax.set_ylim(0, 112)
    ax.set_ylabel("Fidelity (%) — MLP ile uyuşma"); ax.legend(fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.set_title("R3: Black-box MLP'nin bulanık surrogate'lerle açıklanması (çubuk üstü: kural sayısı)")
    fig.tight_layout(); fig.savefig(FIG / "r3_fidelity.png", dpi=200); plt.close(fig)


def fig_mfs():
    """Öğrenilmiş üyelik fonksiyonları: grid ANFIS vs C-ANFIS (WDBC, tek bölünme)."""
    X, y, fn, cn = load_dataset("wdbc")
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=0)
    pp = Preprocessor(k=4).fit(Xtr, ytr, fn); A = pp.transform(Xtr)
    g0 = grid_anfis(4, 2, 2)
    g = grid_anfis(4, 2, 2).fit(A, ytr, epochs=100, lr=0.01)
    c = build_canfis(A, ytr, 2)
    xs = np.linspace(0, 1, 300)
    fig, axes = plt.subplots(3, 4, figsize=(11, 6), sharey=True)
    for row, (m, name) in enumerate([(g0, "Grid-ANFIS başlangıç"), (g, "Grid-ANFIS eğitim sonrası"), (c, "C-ANFIS (sadeleştirilmiş)")]):
        labels = m.mf_labels()
        used = set(m.A[m.A >= 0].tolist())
        for j in range(4):
            ax = axes[row, j]
            for l in np.where(m.mf_feat == j)[0]:
                if l not in used:
                    continue
                ax.plot(xs, np.exp(-0.5 * ((xs - m.c[l]) / m.s[l]) ** 2), lw=2, label=labels[l],
                        color={"Düşük": "#2a78d6", "Orta": "#1baf7a", "Yüksek": "#eb6834"}.get(labels[l], "#6250d6"))
            if row == 0:
                ax.set_title(pp.names[j].replace("_", " "), fontsize=8.5)
            if j == 0:
                ax.set_ylabel(name, fontsize=8)
            ax.set_ylim(0, 1.05); ax.legend(fontsize=6.5, loc="upper right")
    fig.suptitle("Üyelik fonksiyonları (WDBC, [0,1] ölçek): eğitimle grid MF'leri anlamsal olarak bozuluyor", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "mf_comparison.png", dpi=200); plt.close(fig)
    with open(TAB / "example_rules_wdbc.txt", "w", encoding="utf-8") as f:
        f.write("C-ANFIS kuralları (WDBC, tek bölünme)\n")
        f.write("\n".join(_named(c, pp.names, cn).rules_text(A)) + "\n\n")
        f.write(f"Test doğruluğu C-ANFIS: {np.mean(c.predict(pp.transform(Xte)) == yte)*100:.2f}%\n")
        f.write(f"Test doğruluğu Grid-ANFIS: {np.mean(g.predict(pp.transform(Xte)) == yte)*100:.2f}%\n\n")
        f.write("Grid-ANFIS kuralları (ilk 16)\n" + "\n".join(_named(g, pp.names, cn).rules_text(A)))
    # eğitim eğrisi
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(g.history["train_loss"], color=COL["Grid-ANFIS (2MF)"], lw=2, label="Grid-ANFIS (2MF)")
    c2 = build_canfis(A, ytr, 2, merge=False, dont_care=False, prune=False)
    ax.plot(c2.history["train_loss"], color=COL["C-ANFIS"], lw=2, label="FCM-ANFIS (C-ANFIS ön eğitim)")
    ax.set_xlabel("Epok"); ax.set_ylabel("Eğitim MSE"); ax.set_title("Hibrit öğrenme yakınsaması (WDBC)"); ax.legend()
    fig.tight_layout(); fig.savefig(FIG / "training_curve.png", dpi=200); plt.close(fig)


def _named(m, names, cn):
    m.feature_names = [n.replace("_", " ") for n in names]; m.class_names = cn
    return m


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    for f in [fig_tradeoff, fig_scalability, fig_noise, fig_ablation, fig_fidelity, fig_mfs]:
        f(); print("ok:", f.__name__)
