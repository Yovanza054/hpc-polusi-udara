import itertools
import json
import os
import time
from multiprocessing import Pool, cpu_count

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.model import run_scenario, simulate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "output")


def build_scenarios():
    wind_x_values = [0.5, 1.0, 1.5, 2.0]
    wind_y_values = [-1.0, 0.0, 1.0]
    emission_values = [5.0, 10.0, 20.0]
    return list(itertools.product(wind_x_values, wind_y_values, emission_values))


def run_serial(scenarios):
    start = time.perf_counter()
    results = [run_scenario(s) for s in scenarios]
    return results, time.perf_counter() - start


def run_parallel(scenarios, workers):
    start = time.perf_counter()
    with Pool(processes=workers) as pool:
        results = pool.map(run_scenario, scenarios)
    return results, time.perf_counter() - start


def plot_maps():
    cases = [
        ("Angin lemah (0.5, 0)", 0.5, 0.0),
        ("Angin kuat (2.0, 0)", 2.0, 0.0),
        ("Angin diagonal (1.5, 1.0)", 1.5, 1.0),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for ax, (title, wx, wy) in zip(axes, cases):
        field = simulate(wx, wy, 10.0)
        im = ax.imshow(field, cmap="inferno", origin="lower")
        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.colorbar(im, ax=ax, fraction=0.046, label="Konsentrasi")
    fig.suptitle("Peta Sebaran Polutan dari Satu Sumber Emisi", fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "peta_sebaran.png"), dpi=130)
    plt.close(fig)


def plot_wind_effect(results):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for emission in sorted({r["emission"] for r in results}):
        winds = sorted({r["wind_x"] for r in results})
        means = []
        for w in winds:
            rows = [
                r["max_concentration"]
                for r in results
                if r["wind_x"] == w and r["emission"] == emission
            ]
            means.append(np.mean(rows))
        ax.plot(winds, means, marker="o", label=f"Emisi {emission:g}")
    ax.set_xlabel("Kecepatan angin arah x")
    ax.set_ylabel("Konsentrasi maksimum")
    ax.set_title("Pengaruh Angin terhadap Konsentrasi Maksimum")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "pengaruh_angin.png"), dpi=130)
    plt.close(fig)


def plot_speedup(t_serial, t_parallel, workers):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(["Serial", f"Paralel ({workers} core)"], [t_serial, t_parallel], color=["#888888", "#e4572e"])
    ax.set_ylabel("Waktu (detik)")
    ax.set_title(f"Speedup: {t_serial / t_parallel:.2f}x")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "perbandingan_waktu.png"), dpi=130)
    plt.close(fig)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    scenarios = build_scenarios()
    workers = max(1, cpu_count())

    print(f"Jumlah skenario : {len(scenarios)}")
    print(f"Jumlah core     : {workers}")

    serial_results, t_serial = run_serial(scenarios)
    parallel_results, t_parallel = run_parallel(scenarios, workers)

    same = all(
        abs(a["max_concentration"] - b["max_concentration"]) < 1e-9
        for a, b in zip(serial_results, parallel_results)
    )

    summary = {
        "jumlah_skenario": len(scenarios),
        "jumlah_core": workers,
        "waktu_serial_detik": round(t_serial, 3),
        "waktu_paralel_detik": round(t_parallel, 3),
        "speedup": round(t_serial / t_parallel, 2),
        "hasil_serial_sama_dengan_paralel": same,
        "hasil": parallel_results,
    }
    with open(os.path.join(OUT_DIR, "hasil.json"), "w") as f:
        json.dump(summary, f, indent=2)

    plot_maps()
    plot_wind_effect(parallel_results)
    plot_speedup(t_serial, t_parallel, workers)

    worst = max(parallel_results, key=lambda r: r["max_concentration"])
    print(f"Waktu serial    : {t_serial:.2f} s")
    print(f"Waktu paralel   : {t_parallel:.2f} s")
    print(f"Speedup         : {t_serial / t_parallel:.2f}x")
    print(f"Hasil identik   : {same}")
    print(f"Skenario terburuk: {worst}")
    print(f"Output tersimpan di: {OUT_DIR}")


if __name__ == "__main__":
    main()
