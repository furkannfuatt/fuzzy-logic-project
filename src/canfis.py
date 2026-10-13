"""C-ANFIS: Kompakt ve yorumlanabilir ANFIS (projenin özgün katkısı).

Motivasyon (Ouifak & Idri 2025):
  * Bölüm 9.1 / 12: grid-partition ANFIS'te kural sayısı p^d ile üstel artar
    ("rule explosion"); ölçeklenebilirlik ve hesaplama maliyeti temel sınırlılıklardır.
  * Bölüm 13: yorumlanabilirliği yalnızca kural sayısıyla ölçmek yetersizdir; yeni
    metrikler gereklidir.

Önerilen boru hattı (her adım ablation deneyinde ayrı ayrı kapatılabilir):
  (1) FCM tabanlı kural üretimi   : sınıf-bazlı Fuzzy C-Means; her küme = 1 kural.
                                     Kural sayısı d'den bağımsızdır (c × K).
  (2) Hibrit eğitim (LSE + Adam)   : baseline ile aynı eğitim algoritması.
  (3) MF benzerlik birleştirme     : aynı öznitelikte Jaccard benzerliği > tau olan
                                     MF'ler birleştirilir (Setnes vd. 1998 yaklaşımı).
  (4) Önemsiz koşul kaldırma       : evrenin >= %80'ini 0.5 üzeri üyelikle kaplayan
                                     (bilgi taşımayan) MF koşulu kuraldan çıkarılır.
  (5) Kural budama                 : ortalama normalize ateşleme kuvveti (kapsama)
                                     < theta / R olan kurallar silinir.
  (6) İnce ayar                    : sadeleştirilmiş yapı tekrar kısa süre eğitilir.
"""
from __future__ import annotations

import numpy as np

from .anfis import ANFIS, SIGMA_MIN
from .fcm import fcm
from .metrics import GRID, jaccard


# ---------------------------------------------------------------------- #
# (1) FCM ile başlatma
# ---------------------------------------------------------------------- #
def fcm_anfis(X, y, n_classes, clusters_per_class=2, sigma_scale=1.5, seed=0, **kw) -> ANFIS:
    """Sınıf-bazlı FCM: her sınıfın verisi ayrı kümelenir, her küme merkezi bir kuralın
    öncülünü oluşturur. Kural sayısı = K × clusters_per_class (öznitelik sayısından bağımsız)."""
    d = X.shape[1]
    centers, sigmas = [], []
    for k in range(n_classes):
        Xk = X[y == k]
        c = min(clusters_per_class, max(1, len(Xk) // 5))
        V, S, _ = fcm(Xk, c, seed=seed + k)
        centers.append(V); sigmas.append(S)
    V = np.vstack(centers); S = np.vstack(sigmas) * sigma_scale
    S = np.clip(S, 0.05, 0.6)
    R = V.shape[0]
    # her kural, her öznitelik için kendine ait bir MF'ye sahip (L = R*d)
    mf_feat = np.tile(np.arange(d), R)
    c = V.reshape(-1).astype(float)
    s = S.reshape(-1).astype(float)
    A = np.arange(R * d).reshape(R, d)
    return ANFIS(mf_feat, c, s, A, n_classes, **kw)


# ---------------------------------------------------------------------- #
# (3) MF birleştirme
# ---------------------------------------------------------------------- #
def merge_similar_mfs(model: ANFIS, tau: float = 0.6) -> ANFIS:
    m = model.copy()
    changed = True
    while changed:
        changed = False
        used = np.unique(m.A[m.A >= 0])
        for j in range(m.n_features):
            idx = [l for l in used if m.mf_feat[l] == j]
            best, pair = tau, None
            for i, a in enumerate(idx):
                for b in idx[i + 1:]:
                    sim = jaccard(m.c[a], m.s[a], m.c[b], m.s[b])
                    if sim > best:
                        best, pair = sim, (a, b)
            if pair is not None:
                a, b = pair
                # birleşik küme: merkezlerin ortalaması, iki kümeyi de kapsayacak genişlik
                m.c[a] = 0.5 * (m.c[a] + m.c[b])
                m.s[a] = max(m.s[a], m.s[b]) + 0.25 * abs(m.c[a] - m.c[b])
                m.A[m.A == b] = a
                changed = True
                break
    return _drop_duplicate_rules(_compact(m))


# ---------------------------------------------------------------------- #
# (4) Önemsiz (don't care) koşulların kaldırılması
# ---------------------------------------------------------------------- #
def remove_dont_care(model: ANFIS, coverage_thr: float = 0.8) -> ANFIS:
    m = model.copy()
    for l in np.unique(m.A[m.A >= 0]):
        mu = np.exp(-0.5 * ((GRID - m.c[l]) / m.s[l]) ** 2)
        if np.mean(mu >= 0.5) >= coverage_thr:
            m.A[m.A == l] = -1
    return _drop_duplicate_rules(_compact(m))


# ---------------------------------------------------------------------- #
# (5) Kural budama
# ---------------------------------------------------------------------- #
def prune_rules(model: ANFIS, X, theta: float = 0.3, min_rules: int | None = None) -> ANFIS:
    m = model.copy()
    _, wbar, _ = m.firing(X)
    cov = wbar.mean(axis=0)
    keep = cov >= theta / m.n_rules
    min_rules = min_rules or m.n_classes
    if keep.sum() < min_rules:
        keep = np.zeros_like(keep); keep[np.argsort(cov)[::-1][:min_rules]] = True
    m.A = m.A[keep]
    m.P = None
    return _compact(m)


# ---------------------------------------------------------------------- #
# Yardımcılar
# ---------------------------------------------------------------------- #
def _compact(m: ANFIS) -> ANFIS:
    """Kullanılmayan MF'leri sil, indeksleri yeniden numaralandır."""
    used = np.unique(m.A[m.A >= 0])
    remap = -np.ones(len(m.c), dtype=int); remap[used] = np.arange(len(used))
    m.A = np.where(m.A >= 0, remap[np.maximum(m.A, 0)], -1)
    m.mf_feat, m.c, m.s = m.mf_feat[used], m.c[used], np.maximum(m.s[used], SIGMA_MIN)
    m.P = None
    return m


def _drop_duplicate_rules(m: ANFIS) -> ANFIS:
    _, first = np.unique(m.A, axis=0, return_index=True)
    m.A = m.A[np.sort(first)]
    return m


# ---------------------------------------------------------------------- #
# Tam boru hattı
# ---------------------------------------------------------------------- #
def build_canfis(X, y, n_classes, *, init="fcm", clusters_per_class=2, grid_mfs=2,
                 merge=True, dont_care=True, prune=True, tau=0.6, coverage_thr=0.8,
                 theta=0.3, epochs=100, finetune_epochs=50, lr=0.01,
                 X_val=None, y_val=None, seed=0, **kw) -> ANFIS:
    """Ablation için her bileşen ayrı bayrakla açılıp kapatılabilir."""
    from .anfis import grid_anfis
    if init == "fcm":
        m = fcm_anfis(X, y, n_classes, clusters_per_class, seed=seed, **kw)
    else:
        m = grid_anfis(X.shape[1], grid_mfs, n_classes, **kw)
    m.fit(X, y, epochs=epochs, lr=lr, X_val=X_val, y_val=y_val)
    t_total = m.history["fit_time"]
    simplified = False
    if merge:
        m = merge_similar_mfs(m, tau); simplified = True
    if dont_care:
        m = remove_dont_care(m, coverage_thr); simplified = True
    if prune:
        if m.P is None:  # yapı değiştiyse önce sonuçları yeniden çöz
            _, wbar, _ = m.firing(X); m._solve_consequents(X, wbar, np.eye(n_classes)[y])
        m = prune_rules(m, X, theta); simplified = True
    if simplified:
        m.fit(X, y, epochs=finetune_epochs, lr=lr * 0.5, X_val=X_val, y_val=y_val)
        t_total += m.history["fit_time"]
    m.history["fit_time"] = t_total
    return m
