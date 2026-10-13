"""Canlı demo — Grid-ANFIS (baseline) ve C-ANFIS (önerilen) karşılaştırmalı açıklanabilir çıkarım.

Çalıştırma:  streamlit run demo/app.py

Sunumda: veri seti seç → kaydırıcılarla giriş değeri ver → her iki modelin
  * bulanıklaştırma (üyelik dereceleri),
  * kural ateşleme kuvvetleri (normalize),
  * kural sonuç çıktıları ve nihai karar
adım adım gösterilir.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.anfis import grid_anfis  # noqa: E402
from src.canfis import build_canfis  # noqa: E402
from src.data import Preprocessor, load_dataset  # noqa: E402
from src.metrics import interpretability  # noqa: E402

st.set_page_config(page_title="Bulanık Mantık – ANFIS vs C-ANFIS", layout="wide")


@st.cache_resource
def train(dataset: str, k: int, cpc: int, tau: float):
    X, y, fn, cn = load_dataset(dataset)
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(y)); cut = int(0.7 * len(y))
    tr, te = idx[:cut], idx[cut:]
    pp = Preprocessor(k=k).fit(X[tr], y[tr], fn)
    A, B = pp.transform(X[tr]), pp.transform(X[te])
    names = [n.replace("_", " ") for n in pp.names]
    g = grid_anfis(k, 2, len(cn), feature_names=names, class_names=cn).fit(A, y[tr], epochs=100, lr=0.01)
    c = build_canfis(A, y[tr], len(cn), clusters_per_class=cpc, tau=tau,
                     feature_names=names, class_names=cn)
    acc = {m: float(np.mean(model.predict(B) == y[te])) for m, model in [("grid", g), ("canfis", c)]}
    raw_rng = (X[tr][:, pp.idx].min(0), X[tr][:, pp.idx].max(0))
    return g, c, pp, names, cn, acc, A, raw_rng


st.title("Bulanık Mantık Tabanlı Açıklanabilirlik — Canlı Demo")
st.caption("Referans: Ouifak & Idri, Neurocomputing 647 (2025) 130602 · Grid-ANFIS (Jang 1993) vs önerilen C-ANFIS")

with st.sidebar:
    st.header("Ayarlar")
    dataset = st.selectbox("Veri seti", ["wdbc", "pima", "iris"],
                           format_func=lambda d: {"wdbc": "Breast Cancer (WDBC)", "pima": "Pima Diabetes", "iris": "Iris"}[d])
    k = st.slider("Öznitelik sayısı k (grid kural sayısı = 2^k)", 2, 6, 4)
    cpc = st.slider("C-ANFIS: küme / sınıf", 1, 4, 2)
    tau = st.slider("C-ANFIS: MF birleştirme eşiği τ", 0.3, 0.9, 0.6, 0.05)

g, c, pp, names, cn, acc, A, (lo, hi) = train(dataset, k, cpc, tau)

st.subheader("1) Giriş değerleri (gerçek birimler)")
cols = st.columns(len(names))
raw = []
for j, (col, n) in enumerate(zip(cols, names)):
    med = float(np.median(A[:, j]) * (hi[j] - lo[j]) + lo[j])
    raw.append(col.slider(n, float(lo[j]), float(hi[j]), med, float((hi[j] - lo[j]) / 100)))
x = ((np.array(raw) - lo) / np.where(hi > lo, hi - lo, 1))[None, :]


def explain(model, title, acc_val):
    st.markdown(f"### {title}")
    it = interpretability(model)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Test doğruluğu", f"{100 * acc_val:.1f}%")
    m2.metric("Kural sayısı", it["n_rules"])
    m3.metric("Toplam koşul", it["total_rule_length"])
    m4.metric("Nauck indeksi", f"{it['nauck']:.3f}")
    _, wbar, _ = model.firing(x)
    f = model.rule_outputs(x)[0]                     # (R, K)
    y = wbar[0] @ f
    pred = int(np.argmax(y))
    st.success(f"**Karar: {cn[pred]}**   (çıktılar: " + ", ".join(f"{cn[i]}={v:.2f}" for i, v in enumerate(y)) + ")")

    # bulanıklaştırma grafiği
    labels = model.mf_labels(); used = set(model.A[model.A >= 0].tolist())
    xs = np.linspace(0, 1, 200)
    fig, axes = plt.subplots(1, len(names), figsize=(3.4 * len(names), 2.6), sharey=True)
    axes = np.atleast_1d(axes)
    for j, ax in enumerate(axes):
        for l in np.where(model.mf_feat == j)[0]:
            if l in used:
                mu = np.exp(-0.5 * ((xs - model.c[l]) / model.s[l]) ** 2)
                line, = ax.plot(xs, mu, lw=1.8, label=labels[l])
                mux = np.exp(-0.5 * ((x[0, j] - model.c[l]) / model.s[l]) ** 2)
                ax.plot([x[0, j]], [mux], "o", color=line.get_color())
        ax.axvline(x[0, j], color="k", lw=1, ls="--")
        ax.set_title(names[j], fontsize=8); ax.legend(fontsize=6); ax.tick_params(labelsize=7)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)

    # kural tablosu
    rules = model.rules_text()
    df = pd.DataFrame({"kural": [r.split(" İSE")[0] for r in rules],
                       "baskın sınıf": [cn[i] for i in model.rule_dominant_class()],
                       "ateşleme (wbar)": wbar[0],
                       **{f"f({cn[i]})": f[:, i] for i in range(len(cn))}})
    df = df.sort_values("ateşleme (wbar)", ascending=False).reset_index(drop=True)
    st.dataframe(df.head(12).style.format({c_: "{:.3f}" for c_ in df.columns if c_ not in ("kural", "baskın sınıf")})
                 .bar(subset=["ateşleme (wbar)"], color="#9cc2ef", vmin=0, vmax=1), width="stretch")
    if len(df) > 12:
        st.caption(f"En güçlü 12 kural gösterildi (toplam {len(df)}).")


tab1, tab2 = st.tabs(["Önerilen: C-ANFIS", "Baseline: Grid-ANFIS"])
with tab1:
    explain(c, "Önerilen: C-ANFIS (FCM + birleştirme + budama)", acc["canfis"])
with tab2:
    explain(g, "Baseline: Grid-ANFIS (2 MF / öznitelik)", acc["grid"])

with st.expander("Nasıl okunur?"):
    st.markdown("""
* **Katman 1 – Bulanıklaştırma:** kesikli çizgi girişin konumu; noktalar her MF'deki üyelik derecesi.
* **Katman 2-3 – Ateşleme:** her kuralın üyeliklerinin çarpımı, tüm kuralların toplamına bölünür (wbar).
* **Katman 4 – Sonuç:** her kural için doğrusal fonksiyon f = p·[x, 1] (birinci derece Sugeno).
* **Katman 5 – Karar:** çıktı = Σ wbar · f ; en büyük çıktı sınıfı seçilir (defuzzification = ağırlıklı ortalama).
""")
