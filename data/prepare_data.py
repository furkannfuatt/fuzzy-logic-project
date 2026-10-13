"""Veri setlerini hazirlar ve data/ klasorune CSV olarak yazar.

- Iris  ve Wisconsin Diagnostic Breast Cancer (WDBC): scikit-learn icinde gomulu
  gelir (internet gerekmez).
- Pima Indians Diabetes: UCI kaynakli veri; repoya `pima_raw.csv` olarak eklenmistir
  (kaynak: https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv).

Calistirma:  python data/prepare_data.py
"""
from pathlib import Path

import pandas as pd
from sklearn.datasets import load_breast_cancer, load_iris

DATA_DIR = Path(__file__).resolve().parent

PIMA_COLS = ["pregnancies", "glucose", "blood_pressure", "skin_thickness",
             "insulin", "bmi", "diabetes_pedigree", "age", "target"]


def main() -> None:
    iris = load_iris(as_frame=True)
    df = iris.frame.rename(columns=lambda c: c.replace(" (cm)", "").replace(" ", "_"))
    df.to_csv(DATA_DIR / "iris.csv", index=False)

    bc = load_breast_cancer(as_frame=True)
    df = bc.frame.copy()
    df.columns = [c.replace(" ", "_") for c in df.columns]
    # sklearn: 0 = malignant, 1 = benign  ->  1 = malignant (pozitif sinif) yapiyoruz
    df["target"] = 1 - df["target"]
    df.to_csv(DATA_DIR / "wdbc.csv", index=False)

    pima = pd.read_csv(DATA_DIR / "pima_raw.csv", header=None, names=PIMA_COLS)
    pima.to_csv(DATA_DIR / "pima.csv", index=False)

    for name in ["iris", "wdbc", "pima"]:
        d = pd.read_csv(DATA_DIR / f"{name}.csv")
        print(f"{name:5s}: {d.shape[0]} ornek, {d.shape[1]-1} oznitelik, "
              f"sinif dagilimi={d['target'].value_counts().sort_index().to_dict()}")


if __name__ == "__main__":
    main()
