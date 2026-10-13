"""Fuzzy C-Means (Bezdek, 1981) — sıfırdan NumPy gerçekleştirimi.

Amaç fonksiyonu  J_m = sum_i sum_k u_ik^m ||x_k - v_i||^2,   sum_i u_ik = 1
Güncellemeler:
  v_i  = sum_k u_ik^m x_k / sum_k u_ik^m
  u_ik = 1 / sum_j ( ||x_k - v_i|| / ||x_k - v_j|| )^(2/(m-1))
"""
from __future__ import annotations

import numpy as np


def fcm(X: np.ndarray, n_clusters: int, m: float = 2.0, max_iter: int = 300,
        tol: float = 1e-5, seed: int = 0):
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    U = rng.random((n_clusters, n)); U /= U.sum(axis=0, keepdims=True)
    for _ in range(max_iter):
        Um = U ** m
        V = (Um @ X) / Um.sum(axis=1, keepdims=True)
        D = np.linalg.norm(X[None, :, :] - V[:, None, :], axis=2) + 1e-12   # (c, n)
        inv = D ** (-2.0 / (m - 1.0))
        U_new = inv / inv.sum(axis=0, keepdims=True)
        if np.max(np.abs(U_new - U)) < tol:
            U = U_new
            break
        U = U_new
    Um = U ** m
    V = (Um @ X) / Um.sum(axis=1, keepdims=True)
    # bulanık standart sapma (her küme, her öznitelik)  ->  Gauss MF genişliği
    S = np.sqrt((Um[:, :, None] * (X[None] - V[:, None]) ** 2).sum(axis=1)
                / Um.sum(axis=1)[:, None])
    return V, S, U
