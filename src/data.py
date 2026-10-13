"""Veri yükleme, ölçekleme ve öznitelik seçimi (sızıntısız: yalnızca eğitim kıvrımında fit edilir)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

CLASS_NAMES = {
    "iris": ["setosa", "versicolor", "virginica"],
    "wdbc": ["benign", "malignant"],
    "pima": ["sağlıklı", "diyabet"],
}


def load_dataset(name: str):
    df = pd.read_csv(DATA_DIR / f"{name}.csv")
    y = df["target"].to_numpy().astype(int)
    X = df.drop(columns="target")
    return X.to_numpy(float), y, list(X.columns), CLASS_NAMES[name]


class Preprocessor:
    """MinMax ölçekleme [0,1] + karşılıklı bilgi (mutual information) ile k öznitelik seçimi.

    Grid-partition ANFIS'te kural sayısı p^d ile üstel büyüdüğü için (kural patlaması,
    Ouifak & Idri 2025 Bölüm 9.1) öznitelik sayısını sınırlamak zorunludur.
    """

    def __init__(self, k: int | None = None, seed: int = 0):
        self.k, self.seed = k, seed

    def fit(self, X, y, feature_names):
        if self.k is None or self.k >= X.shape[1]:
            self.idx = np.arange(X.shape[1])
        else:
            mi = mutual_info_classif(X, y, random_state=self.seed)
            self.idx = np.sort(np.argsort(mi)[::-1][: self.k])
        self.scaler = MinMaxScaler().fit(X[:, self.idx])
        self.names = [feature_names[i] for i in self.idx]
        return self

    def transform(self, X):
        # test verisi eğitim aralığının dışına taşabilir; [−0.1, 1.1] ile sınırla
        return np.clip(self.scaler.transform(X[:, self.idx]), -0.1, 1.1)
