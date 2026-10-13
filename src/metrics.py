"""Performans ve yorumlanabilirlik metrikleri.

Performans (Ouifak & Idri 2025, Tablo 8): Accuracy, F1, Fidelity (Denk. 25).
Yorumlanabilirlik (Bölüm 9.1): kural sayısı, MF sayısı, kural uzunluğu
+ önerilen ek metrikler: MF ayırt edilebilirliği (Jaccard tabanlı) ve Nauck indeksi.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

GRID = np.linspace(0.0, 1.0, 201)   # [0,1] evren ayrıklaştırması


def fidelity(surrogate_pred, blackbox_pred) -> float:
    """Denk. (25): surrogate'in black-box ile aynı etiketi verdiği örneklerin yüzdesi."""
    return 100.0 * float(np.mean(np.asarray(surrogate_pred) == np.asarray(blackbox_pred)))


def perf(y_true, y_pred) -> dict:
    return {"accuracy": 100 * accuracy_score(y_true, y_pred),
            "f1": 100 * f1_score(y_true, y_pred, average="macro")}


# ---------------------------------------------------------------------- #
# ANFIS yorumlanabilirlik metrikleri
# ---------------------------------------------------------------------- #
def _gauss(c, s):
    return np.exp(-0.5 * ((GRID - c) / s) ** 2)


def jaccard(c1, s1, c2, s2) -> float:
    """İki Gauss bulanık kümenin Jaccard benzerliği |A∩B| / |A∪B| (min/max t-norm/konorm)."""
    a, b = _gauss(c1, s1), _gauss(c2, s2)
    return float(np.minimum(a, b).sum() / np.maximum(a, b).sum())


def used_mfs(model) -> np.ndarray:
    return np.unique(model.A[model.A >= 0])


def distinguishability(model) -> float:
    """1 - (öznitelik başına en büyük ikili Jaccard benzerliği) ortalaması.
    1'e yakın -> MF'ler birbirinden net ayrışıyor (anlamsal yorumlanabilirlik yüksek)."""
    u = used_mfs(model)
    vals = []
    for j in range(model.n_features):
        idx = [l for l in u if model.mf_feat[l] == j]
        if len(idx) < 2:
            continue
        mx = max(jaccard(model.c[a], model.s[a], model.c[b], model.s[b])
                 for i, a in enumerate(idx) for b in idx[i + 1:])
        vals.append(1 - mx)
    return float(np.mean(vals)) if vals else 1.0


def nauck_index(model) -> float:
    """Nauck (2003) yorumlanabilirlik indeksi: comp × cov × part  (∈ (0, 1]).

    comp = m / sum_r n_r      (m: sınıf sayısı, n_r: kural r'deki koşul sayısı)
    cov_i = (1/|X|) ∫ ĥ_i(x) dx,   h_i = sum_k mu_k,  ĥ = h (h<=1) ; (p-h)/(p-1) (aksi)
    part_i = 1 / (p_i - 1)    (p_i: öznitelik i'deki MF sayısı; p_i=1 için 1 kabul edildi)
    cov, part : kullanılan öznitelikler üzerinden ortalama
    """
    trl = int((model.A >= 0).sum())
    comp = min(1.0, model.n_classes / max(trl, 1))
    u = used_mfs(model)
    covs, parts = [], []
    for j in range(model.n_features):
        idx = [l for l in u if model.mf_feat[l] == j]
        p = len(idx)
        if p == 0:
            continue
        h = sum(_gauss(model.c[l], model.s[l]) for l in idx)
        hhat = np.where(h <= 1, h, (p - h) / (p - 1) if p > 1 else 1.0)
        covs.append(float(np.clip(hhat, 0, 1).mean()))
        parts.append(1.0 / (p - 1) if p > 1 else 1.0)
    if not covs:
        return comp
    return float(comp * np.mean(covs) * np.mean(parts))


def interpretability(model) -> dict:
    """ANFIS / C-ANFIS için tüm yorumlanabilirlik metrikleri."""
    A = model.A
    return {
        "n_rules": int(A.shape[0]),
        "n_mfs": int(len(used_mfs(model))),
        "total_rule_length": int((A >= 0).sum()),
        "avg_rule_length": float((A >= 0).sum(axis=1).mean()),
        "n_features_used": int(np.any(A >= 0, axis=0).sum()),
        "distinguishability": distinguishability(model),
        "nauck": nauck_index(model),
    }


def wm_interpretability(wm, n_classes: int) -> dict:
    """Wang–Mendel modeli için aynı metrikler (eşit bölümlü üçgen MF'ler, sayısal hesap)."""
    from .wang_mendel import tri_memberships
    p, d = wm.n_mfs, wm.antecedents.shape[1]
    trl = wm.n_rules * d
    mu = tri_memberships(GRID[:, None], p)[:, 0, :]          # (G, p)
    jac = max(np.minimum(mu[:, a], mu[:, b]).sum() / np.maximum(mu[:, a], mu[:, b]).sum()
              for a in range(p) for b in range(a + 1, p))
    h = mu.sum(axis=1)
    hhat = np.where(h <= 1, h, (p - h) / (p - 1))
    return {"n_rules": wm.n_rules, "n_mfs": p * d, "total_rule_length": trl,
            "avg_rule_length": float(d), "n_features_used": d,
            "distinguishability": float(1 - jac),
            "nauck": float(min(1.0, n_classes / trl) * hhat.mean() * (1.0 / (p - 1)))}
