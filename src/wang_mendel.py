"""Wang–Mendel kural üretimi ile Mamdani tipi bulanık kural tabanlı sınıflandırıcı.

L.-X. Wang and J. M. Mendel, "Generating fuzzy rules by learning from examples,"
IEEE Trans. SMC, 22(6), 1992.

Adımlar:
 1) Her girişi p adet üçgen MF ile eşit böl (Düşük / Orta / Yüksek ...).
 2) Her örnek için, her öznitelikte en yüksek üyelikli MF seçilir -> aday kural.
 3) Kural derecesi = üyeliklerin çarpımı. Aynı öncüle sahip çakışan kurallar:
    - conflict="max" (orijinal WM): en yüksek dereceli örneğin sınıfı seçilir;
    - conflict="sum" (varsayılan): her sınıf için derece toplamı alınır, en büyüğü
      seçilir (Ishibuchi vd. 1992 tarzı sınıflandırma sezgisi). Orijinal "max" kuralı,
      sınıfların çakıştığı yoğun hücrelerde tek bir (olası gürültülü) örneğe bağlı
      kaldığından Pima'da çoğunluk sınıfının altında doğruluk vermiştir (bkz. rapor).
 4) Çıkarım: "tek kazanan kural" (single winner) — en yüksek ateşleme kuvvetli
    kuralın sınıfı atanır (Mamdani/klasik bulanık sınıflandırıcı çıkarımı).

Bu model, black-box bir modelin (MLP) tahminlerinden öğrenildiğinde post-hoc
"bulanık kural çıkarımı" (fuzzy rule extraction) tabanlı açıklayıcı olur.
"""
from __future__ import annotations

import numpy as np


def tri_memberships(X: np.ndarray, n_mfs: int) -> np.ndarray:
    """(n, d, p) üçgen üyelikler; eşit aralıklı, komşular 0.5'te kesişir."""
    centers = np.linspace(0, 1, n_mfs)
    width = 1.0 / (n_mfs - 1)
    return np.clip(1 - np.abs(X[:, :, None] - centers) / width, 0, 1)


class WangMendelClassifier:
    def __init__(self, n_mfs: int = 3, conflict: str = "sum", feature_names=None, class_names=None):
        self.n_mfs, self.conflict = n_mfs, conflict
        self.feature_names, self.class_names = feature_names, class_names

    def fit(self, X, y):
        mu = tri_memberships(X, self.n_mfs)
        best_mf = mu.argmax(axis=2)                       # (n, d)
        degree = mu.max(axis=2).prod(axis=1)               # (n,)
        K = int(y.max()) + 1
        table: dict[tuple, np.ndarray] = {}
        for ant, deg, cls in zip(map(tuple, best_mf), degree, y):
            acc = table.setdefault(ant, np.zeros(K))
            if self.conflict == "max":      # orijinal WM: en yüksek dereceli örnek kazanır
                acc[cls] = max(acc[cls], deg)
            else:                           # "sum": sınıf başına derece toplamı (Ishibuchi tipi)
                acc[cls] += deg
        self.antecedents = np.array(list(table.keys()), dtype=int)
        self.consequents = np.array([v.argmax() for v in table.values()], dtype=int)
        self.default_class = int(np.bincount(y).argmax())
        return self

    @property
    def n_rules(self) -> int:
        return len(self.consequents)

    def firing(self, X):
        mu = tri_memberships(X, self.n_mfs)               # (n, d, p)
        d = X.shape[1]
        # w[n, r] = prod_j mu[n, j, A[r, j]]
        w = np.ones((X.shape[0], self.n_rules))
        for j in range(d):
            w *= mu[:, j, self.antecedents[:, j]]
        return w

    def predict(self, X):
        w = self.firing(X)
        win = w.argmax(axis=1)
        pred = self.consequents[win]
        pred[w.max(axis=1) == 0] = self.default_class     # hiçbir kural ateşlenmezse
        return pred

    def rules_text(self):
        lab = {2: ["Düşük", "Yüksek"], 3: ["Düşük", "Orta", "Yüksek"]}.get(
            self.n_mfs, [f"T{k}" for k in range(self.n_mfs)])
        fn = self.feature_names or [f"x{j}" for j in range(self.antecedents.shape[1])]
        cn = self.class_names or [str(k) for k in range(self.consequents.max() + 1)]
        return [f"R{r+1}: EĞER " + " VE ".join(f"{fn[j]} {lab[a]}" for j, a in enumerate(ant))
                + f" İSE {cn[c]}" for r, (ant, c) in enumerate(zip(self.antecedents, self.consequents))]
