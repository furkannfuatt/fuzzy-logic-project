"""Ortak deney altyapısı: model fabrikası ve 10-kat tabakalı çapraz doğrulama.

Adil karşılaştırma ilkeleri (yönerge 6.2):
  * Tüm modeller aynı kıvrımları (folds), aynı ön işlemeyi ve aynı k özniteliği kullanır.
  * Ölçekleme ve öznitelik seçimi YALNIZCA eğitim kıvrımında fit edilir (veri sızıntısı yok).
  * ANFIS tabanlı tüm modeller aynı hibrit öğrenme algoritması ve aynı epok/öğrenme hızıyla eğitilir.
  * Rastgelelik sabit tohumlarla (seed) kontrol edilir.
"""
from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .anfis import grid_anfis
from .canfis import build_canfis
from .data import Preprocessor, load_dataset
from .metrics import fidelity, interpretability, perf, wm_interpretability
from .wang_mendel import WangMendelClassifier

warnings.filterwarnings("ignore", category=ConvergenceWarning)

EPOCHS, LR = 100, 0.01          # tüm ANFIS türevleri için ortak
K_FEATURES = 4
N_FOLDS = 10


# ---------------------------------------------------------------------- #
# Model fabrikası: her fonksiyon (model, interpretability_dict) döndürür
# ---------------------------------------------------------------------- #
def tree_interp(dt) -> dict:
    t = dt.tree_
    depth = np.zeros(t.node_count, int)
    for i in range(t.node_count):
        for ch in (t.children_left[i], t.children_right[i]):
            if ch != -1:
                depth[ch] = depth[i] + 1
    leaves = t.children_left == -1
    return {"n_rules": int(leaves.sum()), "total_rule_length": int(depth[leaves].sum()),
            "avg_rule_length": float(depth[leaves].mean()), "n_mfs": np.nan,
            "distinguishability": np.nan, "nauck": np.nan,
            "n_features_used": int(len(set(t.feature[~leaves])))}


def make_model(name: str, Xtr, ytr, K: int, seed: int = 0, **kw):
    if name == "Grid-ANFIS (2MF)":
        m = grid_anfis(Xtr.shape[1], 2, K, **kw).fit(Xtr, ytr, epochs=EPOCHS, lr=LR)
        return m, interpretability(m)
    if name == "Grid-ANFIS (3MF)":
        m = grid_anfis(Xtr.shape[1], 3, K, **kw).fit(Xtr, ytr, epochs=EPOCHS, lr=LR)
        return m, interpretability(m)
    if name == "C-ANFIS":
        m = build_canfis(Xtr, ytr, K, epochs=EPOCHS, lr=LR, seed=seed, **kw)
        return m, interpretability(m)
    # --- ablation varyantları ---
    if name == "FCM-ANFIS (yalnız FCM)":
        m = build_canfis(Xtr, ytr, K, merge=False, dont_care=False, prune=False,
                         epochs=EPOCHS, lr=LR, seed=seed, **kw)
        return m, interpretability(m)
    if name == "FCM + birleştirme":
        m = build_canfis(Xtr, ytr, K, dont_care=False, prune=False, epochs=EPOCHS, lr=LR, seed=seed, **kw)
        return m, interpretability(m)
    if name == "FCM + birleştirme + önemsiz koşul":
        m = build_canfis(Xtr, ytr, K, prune=False, epochs=EPOCHS, lr=LR, seed=seed, **kw)
        return m, interpretability(m)
    if name == "Grid + sadeleştirme (FCM yok)":
        m = build_canfis(Xtr, ytr, K, init="grid", grid_mfs=2, epochs=EPOCHS, lr=LR, seed=seed, **kw)
        return m, interpretability(m)
    # --- referans modeller ---
    if name == "Wang-Mendel (3MF)":
        m = WangMendelClassifier(3, **kw).fit(Xtr, ytr)
        return m, wm_interpretability(m, K)
    if name == "Wang-Mendel orijinal (max)":
        m = WangMendelClassifier(3, conflict="max", **kw).fit(Xtr, ytr)
        return m, wm_interpretability(m, K)
    if name == "Karar Ağacı (d≤4)":
        m = DecisionTreeClassifier(max_depth=4, random_state=seed).fit(Xtr, ytr)
        return m, tree_interp(m)
    if name == "MLP":
        m = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=1500, random_state=seed).fit(Xtr, ytr)
        return m, {"n_rules": np.nan}
    raise ValueError(name)


# ---------------------------------------------------------------------- #
# Çapraz doğrulama
# ---------------------------------------------------------------------- #
def cross_validate(dataset: str, models: list[str], k_features: int = K_FEATURES,
                   n_folds: int = N_FOLDS, seed: int = 0, noise_levels=(0.0,),
                   verbose=True, model_kw: dict | None = None) -> pd.DataFrame:
    X, y, fn, cn = load_dataset(dataset)
    K = len(cn)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    rows = []
    rng = np.random.default_rng(seed)
    for fold, (tr, te) in enumerate(skf.split(X, y)):
        pp = Preprocessor(k=k_features, seed=seed).fit(X[tr], y[tr], fn)
        Xtr, Xte = pp.transform(X[tr]), pp.transform(X[te])
        noise = {s: rng.normal(0, s, Xte.shape) for s in noise_levels}
        for name in models:
            t0 = time.perf_counter()
            model, interp = make_model(name, Xtr, y[tr], K, seed=seed + fold, **(model_kw or {}))
            fit_t = time.perf_counter() - t0
            for s in noise_levels:
                t1 = time.perf_counter()
                pred = model.predict(Xte + noise[s])
                inf_t = time.perf_counter() - t1
                rows.append({"dataset": dataset, "fold": fold, "model": name, "noise": s,
                             **perf(y[te], pred), **interp, "fit_time_s": fit_t,
                             "infer_ms_per_sample": 1000 * inf_t / len(te)})
        if verbose:
            print(f"  [{dataset}] kat {fold + 1}/{n_folds} tamam", flush=True)
    return pd.DataFrame(rows)


def surrogate_cv(dataset: str, surrogates: list[str], k_features: int = K_FEATURES,
                 n_folds: int = N_FOLDS, seed: int = 0) -> pd.DataFrame:
    """Black-box MLP (TÜM öznitelikler) -> bulanık surrogate (k öznitelik) ile açıklama.

    Surrogate'ler gerçek etiketlerle değil, MLP'nin eğitim kümesi tahminleriyle eğitilir
    (pedagojik kural çıkarımı). Fidelity = test kümesinde MLP ile uyuşma yüzdesi (Denk. 25).
    """
    X, y, fn, cn = load_dataset(dataset)
    K = len(cn)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    rows = []
    for fold, (tr, te) in enumerate(skf.split(X, y)):
        sc = StandardScaler().fit(X[tr])
        bb = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=1500,
                           random_state=seed + fold).fit(sc.transform(X[tr]), y[tr])
        bb_tr, bb_te = bb.predict(sc.transform(X[tr])), bb.predict(sc.transform(X[te]))
        rows.append({"dataset": dataset, "fold": fold, "model": "MLP (black-box)",
                     **perf(y[te], bb_te), "fidelity": 100.0})
        pp = Preprocessor(k=k_features, seed=seed).fit(X[tr], bb_tr, fn)
        Xtr, Xte = pp.transform(X[tr]), pp.transform(X[te])
        for name in surrogates:
            if len(np.unique(bb_tr)) < K:     # nadir: MLP bir sınıfı hiç tahmin etmezse
                continue
            model, interp = make_model(name, Xtr, bb_tr, K, seed=seed + fold)
            pred = model.predict(Xte)
            rows.append({"dataset": dataset, "fold": fold, "model": name,
                         **perf(y[te], pred), "fidelity": fidelity(pred, bb_te), **interp})
    return pd.DataFrame(rows)
