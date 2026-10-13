"""ANFIS (Adaptive Neuro-Fuzzy Inference System) — sıfırdan NumPy gerçekleştirimi.

Referans mimari: J.-S. R. Jang, "ANFIS: Adaptive-network-based fuzzy inference
system," IEEE Trans. SMC, 1993.  (Ouifak & Idri 2025, Bölüm 6.1 / Denk. 9-13)

5 katman:
  L1  Bulanıklaştırma : mu_l(x) = exp(-(x_j - c_l)^2 / (2 s_l^2))       (Gauss MF)
  L2  Kural ateşleme  : w_r = prod_{l in A_r} mu_l(x)                     (product t-norm)
  L3  Normalizasyon   : wbar_r = w_r / sum_q w_q
  L4  Sonuç (TSK-1)   : f_r^k = p_r^k . [x, 1]                           (birinci dereceden Sugeno)
  L5  Toplama         : y^k = sum_r wbar_r f_r^k  ->  sınıf = argmax_k y^k

Hibrit öğrenme (Jang): her epokta
  ileri geçiş  -> sonuç parametreleri P en küçük kareler (LSE, ridge) ile çözülür
  geri geçiş   -> öncül (MF) parametreleri c, s gradyan inişi (Adam) ile güncellenir

Kural yapısı genel tutulmuştur: her kural, her öznitelik için bir MF indeksine
(veya -1 = "önemsiz / don't care") sahiptir. Böylece hem grid-partition ANFIS
(baseline) hem de kümeleme tabanlı kompakt ANFIS (önerilen C-ANFIS) aynı sınıfla
temsil edilir.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from itertools import product

import numpy as np

SIGMA_MIN = 0.02  # MF genişliği alt sınırı (sayısal kararlılık)


@dataclass
class ANFIS:
    """Genel kural yapılı birinci dereceden TSK ANFIS sınıflandırıcı.

    Parametreler
    ------------
    mf_feat : (L,)   her MF'nin ait olduğu öznitelik indeksi
    c, s    : (L,)   Gauss MF merkezi ve genişliği
    A       : (R, d) kural öncül matrisi; A[r, j] = MF indeksi ya da -1 (önemsiz)
    n_classes : çıkış (sınıf) sayısı K
    """

    mf_feat: np.ndarray
    c: np.ndarray
    s: np.ndarray
    A: np.ndarray
    n_classes: int
    feature_names: list[str] | None = None
    class_names: list[str] | None = None
    ridge: float = 1e-3
    P: np.ndarray | None = None              # (R, d+1, K) sonuç parametreleri
    history: dict = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Yardımcı yapı
    # ------------------------------------------------------------------ #
    @property
    def n_rules(self) -> int:
        return self.A.shape[0]

    @property
    def n_features(self) -> int:
        return self.A.shape[1]

    def _rule_mf_mask(self) -> np.ndarray:
        """(R, L) 0/1 matris: kural r, MF l'yi kullanıyor mu?"""
        R, L = self.n_rules, self.c.shape[0]
        M = np.zeros((R, L))
        rr, jj = np.nonzero(self.A >= 0)
        M[rr, self.A[rr, jj]] = 1.0
        return M

    # ------------------------------------------------------------------ #
    # Katman 1-3
    # ------------------------------------------------------------------ #
    def log_memberships(self, X: np.ndarray) -> np.ndarray:
        """Katman 1: log mu (n, L). Log-alanında çalışmak taşmayı önler."""
        diff = X[:, self.mf_feat] - self.c
        return -0.5 * (diff / self.s) ** 2

    def firing(self, X: np.ndarray):
        """Katman 2-3: ham (w) ve normalize (wbar) ateşleme kuvvetleri."""
        logmu = self.log_memberships(X)
        logw = logmu @ self._rule_mf_mask().T          # (n, R)  = log prod mu
        m = logw.max(axis=1, keepdims=True)
        e = np.exp(logw - m)
        wbar = e / e.sum(axis=1, keepdims=True)        # softmax(logw) = w / sum w
        return np.exp(logw), wbar, logmu

    # ------------------------------------------------------------------ #
    # Katman 4-5
    # ------------------------------------------------------------------ #
    @staticmethod
    def _augment(X: np.ndarray) -> np.ndarray:
        return np.hstack([X, np.ones((X.shape[0], 1))])

    def _design(self, X: np.ndarray, wbar: np.ndarray) -> np.ndarray:
        """LSE tasarım matrisi Phi (n, R*(d+1)): Phi[n, r, :] = wbar_r * [x, 1]."""
        Xa = self._augment(X)
        return (wbar[:, :, None] * Xa[:, None, :]).reshape(X.shape[0], -1)

    def _solve_consequents(self, X, wbar, T):
        Phi = self._design(X, wbar)
        G = Phi.T @ Phi
        G[np.diag_indices_from(G)] += self.ridge
        theta = np.linalg.solve(G, Phi.T @ T)          # (R*(d+1), K)
        self.P = theta.reshape(self.n_rules, self.n_features + 1, self.n_classes)

    def rule_outputs(self, X: np.ndarray) -> np.ndarray:
        """f (n, R, K): her kuralın doğrusal sonuç çıktısı."""
        return np.einsum("nd,rdk->nrk", self._augment(X), self.P)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        _, wbar, _ = self.firing(X)
        return np.einsum("nr,nrk->nk", wbar, self.rule_outputs(X))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.decision_function(X).argmax(axis=1)

    # ------------------------------------------------------------------ #
    # Gradyan (öncül parametreler)
    # ------------------------------------------------------------------ #
    def loss_and_grads(self, X: np.ndarray, T: np.ndarray):
        """MSE kaybı ve dE/dc, dE/ds (sonuç parametreleri sabitken).

        Türetme:
          E = 1/(2n) sum ||y - t||^2,   y = sum_r wbar_r f_r
          g_r   = dE/dwbar_r = (y - t) . f_r
          q_r   = dE/dlogw_r = wbar_r (g_r - sum_q wbar_q g_q)   (softmax türevi)
          dE/dlogmu_l = sum_r q_r * M[r, l]
          dlogmu/dc = (x - c)/s^2 ,  dlogmu/ds = (x - c)^2/s^3
        """
        n = X.shape[0]
        _, wbar, _ = self.firing(X)
        F = self.rule_outputs(X)                       # (n, R, K)
        Y = np.einsum("nr,nrk->nk", wbar, F)
        E = Y - T
        loss = 0.5 * np.mean(np.sum(E ** 2, axis=1))
        g = np.einsum("nk,nrk->nr", E, F) / n
        q = wbar * (g - np.sum(wbar * g, axis=1, keepdims=True))
        dlogmu = q @ self._rule_mf_mask()              # (n, L)
        diff = X[:, self.mf_feat] - self.c
        grad_c = np.sum(dlogmu * diff / self.s ** 2, axis=0)
        grad_s = np.sum(dlogmu * diff ** 2 / self.s ** 3, axis=0)
        return loss, grad_c, grad_s

    # ------------------------------------------------------------------ #
    # Eğitim: Jang hibrit öğrenme (LSE + Adam)
    # ------------------------------------------------------------------ #
    def fit(self, X, y, epochs: int = 100, lr: float = 0.01,
            X_val=None, y_val=None, verbose: bool = False, seed: int = 0):
        T = np.eye(self.n_classes)[y]
        m_c = np.zeros_like(self.c); v_c = np.zeros_like(self.c)
        m_s = np.zeros_like(self.s); v_s = np.zeros_like(self.s)
        b1, b2, eps = 0.9, 0.999, 1e-8
        best = (np.inf, None)
        hist = {"train_loss": [], "val_acc": []}
        t0 = time.perf_counter()
        for ep in range(1, epochs + 1):
            # (1) ileri geçiş + LSE
            _, wbar, _ = self.firing(X)
            self._solve_consequents(X, wbar, T)
            # (2) geri geçiş: öncül parametreler
            loss, gc, gs = self.loss_and_grads(X, T)
            m_c = b1 * m_c + (1 - b1) * gc; v_c = b2 * v_c + (1 - b2) * gc ** 2
            m_s = b1 * m_s + (1 - b1) * gs; v_s = b2 * v_s + (1 - b2) * gs ** 2
            bc1, bc2 = 1 - b1 ** ep, 1 - b2 ** ep
            self.c -= lr * (m_c / bc1) / (np.sqrt(v_c / bc2) + eps)
            self.s -= lr * (m_s / bc1) / (np.sqrt(v_s / bc2) + eps)
            self.s = np.maximum(self.s, SIGMA_MIN)
            hist["train_loss"].append(loss)
            # erken durdurma kriteri: doğrulama kaybı (varsa), yoksa eğitim kaybı
            if X_val is not None:
                Tv = np.eye(self.n_classes)[y_val]
                vloss = 0.5 * np.mean(np.sum((self.decision_function(X_val) - Tv) ** 2, axis=1))
                hist["val_acc"].append(float(np.mean(self.predict(X_val) == y_val)))
                crit = vloss
            else:
                crit = loss
            if crit < best[0]:
                best = (crit, (self.c.copy(), self.s.copy(), self.P.copy()))
            if verbose and ep % 20 == 0:
                print(f"epoch {ep:4d}  loss={loss:.4f}")
        self.c, self.s, self.P = best[1]
        # en iyi öncül parametrelerle sonuç parametrelerini son kez çöz
        _, wbar, _ = self.firing(X)
        self._solve_consequents(X, wbar, T)
        hist["fit_time"] = time.perf_counter() - t0
        self.history = hist
        return self

    # ------------------------------------------------------------------ #
    # Yorumlanabilirlik: dilsel etiketler ve kural metni
    # ------------------------------------------------------------------ #
    def mf_labels(self) -> list[str]:
        """Her MF'ye, kendi özniteliği içindeki merkez sırasına göre dilsel etiket."""
        names = {1: ["Herhangi"], 2: ["Düşük", "Yüksek"], 3: ["Düşük", "Orta", "Yüksek"],
                 4: ["Çok Düşük", "Düşük", "Yüksek", "Çok Yüksek"],
                 5: ["Çok Düşük", "Düşük", "Orta", "Yüksek", "Çok Yüksek"]}
        labels = [""] * len(self.c)
        for j in range(self.n_features):
            idx = np.where(self.mf_feat == j)[0]
            order = idx[np.argsort(self.c[idx])]
            p = len(order)
            lab = names.get(p, [f"T{k+1}" for k in range(p)])
            for k, l in enumerate(order):
                labels[l] = lab[k]
        return labels

    def rule_dominant_class(self) -> np.ndarray:
        """Her kuralın sonuç fonksiyonunu kural prototipinde (MF merkezleri) değerlendir."""
        proto = np.full((self.n_rules, self.n_features), 0.5)
        for r in range(self.n_rules):
            for j in range(self.n_features):
                if self.A[r, j] >= 0:
                    proto[r, j] = self.c[self.A[r, j]]
        out = np.einsum("rd,rdk->rk", self._augment(proto), self.P)
        return out.argmax(axis=1)

    def rules_text(self, X_ref: np.ndarray | None = None) -> list[str]:
        labels = self.mf_labels()
        fn = self.feature_names or [f"x{j}" for j in range(self.n_features)]
        cn = self.class_names or [str(k) for k in range(self.n_classes)]
        dom = self.rule_dominant_class()
        cov = None
        if X_ref is not None:
            _, wbar, _ = self.firing(X_ref)
            cov = wbar.mean(axis=0)
        out = []
        for r in range(self.n_rules):
            conds = [f"{fn[j]} {labels[self.A[r, j]]}" for j in range(self.n_features)
                     if self.A[r, j] >= 0]
            ant = " VE ".join(conds) if conds else "(her zaman)"
            s = f"R{r+1}: EĞER {ant} İSE sınıf ≈ {cn[dom[r]]}"
            if cov is not None:
                s += f"   [kapsama={cov[r]:.2f}]"
            out.append(s)
        return out

    def copy(self) -> "ANFIS":
        return ANFIS(self.mf_feat.copy(), self.c.copy(), self.s.copy(), self.A.copy(),
                     self.n_classes, self.feature_names, self.class_names, self.ridge,
                     None if self.P is None else self.P.copy())


# ---------------------------------------------------------------------- #
# Baseline başlatma: grid partition (Jang 1993)
# ---------------------------------------------------------------------- #
def grid_anfis(n_features: int, n_mfs: int, n_classes: int, **kw) -> ANFIS:
    """Her özniteliğe n_mfs eşit aralıklı Gauss MF; tüm kombinasyonlar = n_mfs^d kural.

    Girdilerin [0, 1] aralığına ölçeklendiği varsayılır. Komşu MF'ler 0.5 üyelikte
    kesişecek şekilde sigma = aralık / (2 sqrt(2 ln 2)) seçilir.
    """
    centers = np.linspace(0.0, 1.0, n_mfs)
    spacing = 1.0 / (n_mfs - 1)
    sigma = spacing / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    mf_feat = np.repeat(np.arange(n_features), n_mfs)
    c = np.tile(centers, n_features).astype(float)
    s = np.full(n_features * n_mfs, sigma)
    A = np.array([[j * n_mfs + combo[j] for j in range(n_features)]
                  for combo in product(range(n_mfs), repeat=n_features)], dtype=int)
    return ANFIS(mf_feat, c, s, A, n_classes, **kw)
