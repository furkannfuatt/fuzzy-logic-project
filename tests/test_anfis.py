"""ANFIS birim testleri: analitik gradyanın sayısal gradyanla doğrulanması ve basit öğrenme testi.
Çalıştırma: python -m pytest tests  (veya)  python tests/test_anfis.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.anfis import grid_anfis  # noqa: E402


def test_gradient_check():
    rng = np.random.default_rng(0)
    X = rng.random((40, 3)); y = (X[:, 0] + X[:, 1] > 1).astype(int)
    T = np.eye(2)[y]
    m = grid_anfis(3, 2, 2)
    m.c += rng.normal(0, 0.05, m.c.shape)
    _, wbar, _ = m.firing(X); m._solve_consequents(X, wbar, T)
    loss, gc, gs = m.loss_and_grads(X, T)
    eps = 1e-6
    for arr, g in [(m.c, gc), (m.s, gs)]:
        num = np.zeros_like(arr)
        for i in range(arr.size):
            old = arr[i]
            arr[i] = old + eps; lp, _, _ = m.loss_and_grads(X, T)
            arr[i] = old - eps; lm, _, _ = m.loss_and_grads(X, T)
            arr[i] = old
            num[i] = (lp - lm) / (2 * eps)
        rel = np.linalg.norm(num - g) / (np.linalg.norm(num) + np.linalg.norm(g))
        assert rel < 1e-5, rel


def test_learns_xor_like():
    rng = np.random.default_rng(1)
    X = rng.random((300, 2)); y = ((X[:, 0] > 0.5) ^ (X[:, 1] > 0.5)).astype(int)
    m = grid_anfis(2, 2, 2).fit(X, y, epochs=150, lr=0.02)
    assert np.mean(m.predict(X) == y) > 0.9


if __name__ == "__main__":
    test_gradient_check(); test_learns_xor_like(); print("Tüm testler geçti.")
