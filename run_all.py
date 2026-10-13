"""Tüm deneyleri baştan sona yeniden üretir (≈ 7-8 dk, 2 çekirdekli CPU).

    python run_all.py

Adımlar: veri hazırlama -> testler -> R1 -> R2/R3 (baseline) -> P1-P7 (önerilen) -> grafikler
"""
import subprocess
import sys

STEPS = [
    ["data/prepare_data.py"],
    ["tests/test_anfis.py"],
    ["-m", "experiments.baseline.r1_borda_reproduction"],
    ["-m", "experiments.baseline.r2_r3_baseline"],
    ["-m", "experiments.proposed.p_canfis_experiments"],
    ["-m", "experiments.make_figures"],
]

if __name__ == "__main__":
    for step in STEPS:
        print(f"\n=== python {' '.join(step)} ===", flush=True)
        subprocess.run([sys.executable, *step], check=True)
    print("\nTüm sonuçlar results/tables ve results/figures altında.")
