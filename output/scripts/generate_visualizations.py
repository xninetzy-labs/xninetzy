"""Generate all visualizations for the SID303 Data Exploration assignment.

Run:  python scripts/generate_visualizations.py
Output: ../figures/figure_01..05_*.png  (300 DPI, white background)
"""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NAVY = "#1F4E78"
BLUE = "#4472C4"
LIGHT_BLUE = "#D9EAF7"
DARK = "#1F2937"
GRAY = "#6B7280"
LIGHT_GRAY = "#E5E7EB"

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

TABLE_1A_CSV = """Male,Age,Eye Color,Shoe Size,Height (in),Weight (lb),Siblings,Units,Handedness
1,20,Brown,9.5,71,170,1,16,Right
0,19,Blue,8,66,135,1,13,Right
0,42,Brown,7.5,63,130,3,5,Right
0,19,Brown,8.5,65,150,0,15,Left
1,21,Brown,11,70,185,5,19.5,Right
0,20,Hazel,5.5,60,105,2,11.5,Right
1,21,Blue,12,76,210,2,9.5,Right
0,21,Brown,10,70,140,0,8,Left
0,32,Brown,8,64,165,1,13.5,Right
1,23,Brown,7.5,63,145,6,12,Right
0,21,Brown,6.5,61.5,110,4,14,Right"""


def load_and_validate() -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(TABLE_1A_CSV))

    assert len(df) == 11, f"expected 11 rows, got {len(df)}"
    assert list(df.columns) == [
        "Male", "Age", "Eye Color", "Shoe Size", "Height (in)",
        "Weight (lb)", "Siblings", "Units", "Handedness",
    ], "column order mismatch"

    eye_counts = df["Eye Color"].value_counts().to_dict()
    assert eye_counts == {"Brown": 8, "Blue": 2, "Hazel": 1}, eye_counts

    hand_counts = df["Handedness"].value_counts().to_dict()
    assert hand_counts == {"Right": 9, "Left": 2}, hand_counts

    df["Full"] = (df["Units"] >= 12).astype(int)
    assert int(df["Full"].sum()) == 7, "full-time count mismatch"
    assert int((df["Full"] == 0).sum()) == 4, "part-time count mismatch"

    assert 12 + 55 == 67
    assert 55 + 39 == 94
    assert 23 + 94 == 117
    assert 67 + 50 == 117

    return df


def save(fig: plt.Figure, name: str) -> Path:
    out = FIGURES_DIR / name
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")
    return out


def figure_01_framework() -> Path:
    """Conceptual framework: data visualization vs visual data mining."""
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, text, fc, ec, fs=10.5):
        from matplotlib.patches import FancyBboxPatch
        patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.12,rounding_size=0.18",
            linewidth=1.4, edgecolor=ec, facecolor=fc,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=DARK, fontweight="bold")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.8))

    # Left column: data visualization path
    box(0.4, 8.2, 4.2, 1.1, "BUSINESS DATA", LIGHT_BLUE, NAVY)
    box(0.4, 5.9, 4.2, 1.1, "DATA VISUALIZATION", LIGHT_BLUE, NAVY)
    box(0.4, 3.6, 4.2, 1.1, "HUMAN PATTERN RECOGNITION", LIGHT_BLUE, NAVY)
    box(0.4, 1.3, 4.2, 1.1, "PATTERN / INSIGHT", LIGHT_BLUE, NAVY)
    arrow(2.5, 8.2, 2.5, 7.0)
    arrow(2.5, 5.9, 2.5, 4.7)
    arrow(2.5, 3.6, 2.5, 2.4)

    # Right column: visual data mining path
    box(5.4, 8.2, 4.2, 1.1, "BUSINESS DATA", "#E8F0FA", BLUE)
    box(5.4, 5.9, 4.2, 1.1, "DATA MINING MODEL", "#E8F0FA", BLUE)
    box(5.4, 3.6, 4.2, 1.1, "VISUAL DATA MINING", "#E8F0FA", BLUE)
    box(5.4, 1.3, 4.2, 1.1, "MODEL INTERPRETATION / VALIDATION", "#E8F0FA", BLUE)
    arrow(7.5, 8.2, 7.5, 7.0)
    arrow(7.5, 5.9, 7.5, 4.7)
    arrow(7.5, 3.6, 7.5, 2.4)

    ax.text(2.5, 9.55, "Data Visualization", ha="center", fontsize=11.5,
            fontweight="bold", color=NAVY)
    ax.text(7.5, 9.55, "Visual Data Mining", ha="center", fontsize=11.5,
            fontweight="bold", color=BLUE)

    return save(fig, "figure_01_visualization_framework.png")


def figure_02_eye_color(df: pd.DataFrame) -> Path:
    counts = df["Eye Color"].value_counts()
    counts = counts.reindex(["Brown", "Blue", "Hazel"])

    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(counts.index, counts.values, color=[NAVY, BLUE, LIGHT_BLUE],
                  edgecolor=NAVY, linewidth=0.8, width=0.55)
    for bar, value in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.12,
                str(value), ha="center", va="bottom", fontsize=11,
                fontweight="bold", color=DARK)

    ax.set_title("Eye Color Distribution", fontsize=13, fontweight="bold",
                 color=DARK, pad=12)
    ax.set_ylabel("Jumlah Observasi", fontsize=11, color=DARK)
    ax.set_ylim(0, 9.5)
    ax.yaxis.set_major_locator(plt.MultipleLocator(2))
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.7)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(LIGHT_GRAY)
    ax.spines["bottom"].set_color(LIGHT_GRAY)
    ax.tick_params(colors=DARK, labelsize=10.5)

    return save(fig, "figure_02_eye_color_distribution.png")


def figure_03_fulltime(df: pd.DataFrame) -> Path:
    full = int(df["Full"].sum())
    part = int((df["Full"] == 0).sum())
    labels = ["Full-time", "Part-time"]
    values = [full, part]

    fig, ax = plt.subplots(figsize=(8, 4.4))
    bars = ax.bar(labels, values, color=[NAVY, BLUE], width=0.5)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.12,
                str(value), ha="center", va="bottom", fontsize=11,
                fontweight="bold", color=DARK)

    ax.set_title("Distribusi Status Full-time dan Part-time", fontsize=13,
                 fontweight="bold", color=DARK, pad=12)
    ax.set_ylabel("Jumlah Mahasiswa", fontsize=11, color=DARK)
    ax.set_ylim(0, 8.5)
    ax.yaxis.set_major_locator(plt.MultipleLocator(2))
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.7)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(LIGHT_GRAY)
    ax.spines["bottom"].set_color(LIGHT_GRAY)
    ax.tick_params(colors=DARK, labelsize=10.5)

    return save(fig, "figure_03_fulltime_distribution.png")


def figure_04_height_weight(df: pd.DataFrame) -> Path:
    x = df["Height (in)"].values.astype(float)
    y = df["Weight (lb)"].values.astype(float)
    correlation = float(df["Height (in)"].corr(df["Weight (lb)"]))

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.scatter(x, y, s=70, color=NAVY, edgecolor="white", linewidth=0.8, zorder=3)

    slope, intercept = np.polyfit(x, y, 1)
    xs = np.linspace(x.min() - 0.5, x.max() + 0.5, 100)
    ax.plot(xs, slope * xs + intercept, color=BLUE, linewidth=1.8,
            label=f"Trend (r = {correlation:.3f})")

    ax.set_title("Hubungan Tinggi dan Berat Badan", fontsize=13,
                 fontweight="bold", color=DARK, pad=12)
    ax.set_xlabel("Tinggi (in)", fontsize=11, color=DARK)
    ax.set_ylabel("Berat (lb)", fontsize=11, color=DARK)
    ax.grid(color=LIGHT_GRAY, linewidth=0.7)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(LIGHT_GRAY)
    ax.spines["bottom"].set_color(LIGHT_GRAY)
    ax.tick_params(colors=DARK, labelsize=10.5)
    ax.legend(frameon=False, fontsize=10, loc="upper left")

    print(f"correlation height-weight: r = {correlation:.4f}")
    return save(fig, "figure_04_height_weight_scatter.png")


def figure_05_older_sibling() -> Path:
    data = pd.DataFrame({
        "Gender": ["Men", "Women"],
        "Yes": [12, 55],
        "No": [11, 39],
    })

    x = np.arange(len(data))
    width = 0.34

    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars1 = ax.bar(x - width / 2, data["Yes"], width, label="Yes, Older Sibling",
                   color=NAVY)
    bars2 = ax.bar(x + width / 2, data["No"], width, label="No Older Sibling",
                   color=BLUE)
    for bars in (bars1, bars2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                    str(int(bar.get_height())), ha="center", va="bottom",
                    fontsize=11, fontweight="bold", color=DARK)

    ax.set_title("Older Sibling berdasarkan Gender", fontsize=13,
                 fontweight="bold", color=DARK, pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(data["Gender"], fontsize=11)
    ax.set_ylabel("Jumlah Mahasiswa", fontsize=11, color=DARK)
    ax.set_ylim(0, 62)
    ax.yaxis.set_major_locator(plt.MultipleLocator(10))
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.7)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(LIGHT_GRAY)
    ax.spines["bottom"].set_color(LIGHT_GRAY)
    ax.tick_params(colors=DARK, labelsize=10.5)
    ax.legend(frameon=False, fontsize=10, loc="upper left")

    return save(fig, "figure_05_older_sibling_gender.png")


def main() -> None:
    df = load_and_validate()
    print("validation OK: 11 rows, 9 variables, all counts verified")

    pct = {
        "men_yes": 12 / 23 * 100,
        "men_no": 11 / 23 * 100,
        "women_yes": 55 / 94 * 100,
        "people_yes": 67 / 117 * 100,
        "women_of_yes": 55 / 67 * 100,
        "est_600": 600 * 55 / 94,
    }
    for key, value in pct.items():
        print(f"{key}: {value:.2f}")

    figure_01_framework()
    figure_02_eye_color(df)
    figure_03_fulltime(df)
    figure_04_height_weight(df)
    figure_05_older_sibling()
    print("all figures generated")


if __name__ == "__main__":
    main()