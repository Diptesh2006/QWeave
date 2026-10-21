"""Build paper-only SWAP-distribution and synthetic-fidelity figures.

The input is the immutable benchmark-v2 raw record.  Seeded methods are
collapsed to a within-case median before any distribution is drawn, matching
the statistical unit used by the manuscript.
"""

from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
import statistics

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "benchmark_v2" / "raw.json"
OUTPUT = Path(__file__).resolve().parent / "assets" / "swap_fidelity_distributions.png"

METHODS = ["basic", "weighted", "sabre", "gnn_ppo", "mlp_ppo", "gnn_untrained"]
LABELS = {
    "basic": "Basic",
    "weighted": "Weighted",
    "sabre": "SABRE",
    "gnn_ppo": "GNN-PPO",
    "mlp_ppo": "No-message",
    "gnn_untrained": "Untrained",
}
COLORS = {
    "basic": "#6B7280",
    "weighted": "#059669",
    "sabre": "#7C3AED",
    "gnn_ppo": "#2463EB",
    "mlp_ppo": "#E27618",
    "gnn_untrained": "#B91C1C",
}


def font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def quantile(values: list[float], q: float) -> float:
    values = sorted(values)
    if len(values) == 1:
        return float(values[0])
    position = (len(values) - 1) * q
    low = int(position)
    high = min(low + 1, len(values) - 1)
    fraction = position - low
    return float(values[low] * (1 - fraction) + values[high] * fraction)


def collapse_records(payload: dict) -> dict[str, dict[str, list[float]]]:
    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for record in payload["records"]:
        if record["status"] == "ok":
            grouped[record["method"]][record["case_id"]].append(record)

    collapsed: dict[str, dict[str, list[float]]] = {}
    for method in METHODS:
        cases = grouped[method]
        collapsed[method] = {
            "swaps": [
                statistics.median(item["swap_count"] for item in records)
                for records in cases.values()
            ],
            "fidelity": [
                statistics.median(item["estimated_success_probability"] for item in records)
                for records in cases.values()
            ],
        }
    return collapsed


def draw() -> None:
    payload = json.loads(RAW.read_text(encoding="utf-8"))
    data = collapse_records(payload)
    image = Image.new("RGB", (1900, 1080), "white")
    draw = ImageDraw.Draw(image)
    draw.text((75, 35), "Held-out SWAP distribution and fidelity proxy", font=font(38, True), fill="#111827")
    draw.text(
        (75, 87),
        "36 test cases; seeded methods collapsed within case before analysis",
        font=font(22),
        fill="#4B5563",
    )

    # Panel A: empirical CDF of the discrete SWAP-count distribution.
    left, top, right, bottom = 120, 205, 900, 865
    draw.text(((left + right) / 2, 155), "(a) Empirical SWAP-count distribution", anchor="ma", font=font(25, True), fill="#111827")
    draw.line((left, bottom, right, bottom), fill="#111827", width=3)
    draw.line((left, top, left, bottom), fill="#111827", width=3)
    max_log = math.log1p(max(max(data[m]["swaps"]) for m in METHODS))
    sx = lambda value: left + math.log1p(value) / max_log * (right - left)
    sy = lambda value: bottom - value * (bottom - top)
    swap_ticks = [0, 1, 3, 10, 30, 100, 300]
    for value in swap_ticks:
        x = sx(value)
        draw.line((x, bottom, x, bottom + 8), fill="#111827", width=2)
        draw.text((x, bottom + 18), str(value), anchor="ma", font=font(17), fill="#374151")
    for value in [0, 0.25, 0.5, 0.75, 1.0]:
        y = sy(value)
        draw.line((left, y, right, y), fill="#E5E7EB", width=2)
        draw.text((left - 16, y), f"{value:.2f}", anchor="rm", font=font(17), fill="#374151")
    draw.text(((left + right) / 2, bottom + 66), "SWAP count (log-scaled axis)", anchor="ma", font=font(20, True), fill="#111827")
    draw.text((left, top - 18), "Cumulative probability", anchor="ls", font=font(20, True), fill="#111827")
    for method in METHODS:
        values = sorted(data[method]["swaps"])
        points = [(sx(0), sy(0))]
        for index, value in enumerate(values, start=1):
            y = index / len(values)
            points.extend([(sx(value), points[-1][1]), (sx(value), sy(y))])
        points.append((right, points[-1][1]))
        draw.line(points, fill=COLORS[method], width=5)

    # Panel B: case-level distributions of the independent-error success proxy.
    left, top, right, bottom = 1020, 205, 1815, 865
    draw.text(((left + right) / 2, 155), "(b) Estimated success-probability proxy", anchor="ma", font=font(25, True), fill="#111827")
    draw.line((left, bottom, right, bottom), fill="#111827", width=3)
    draw.line((left, top, left, bottom), fill="#111827", width=3)
    sy_f = lambda value: bottom - value * (bottom - top)
    for value in [0, 0.25, 0.5, 0.75, 1.0]:
        y = sy_f(value)
        draw.line((left, y, right, y), fill="#E5E7EB", width=2)
        draw.text((left - 16, y), f"{value:.2f}", anchor="rm", font=font(17), fill="#374151")
    draw.text((left, top - 18), "Synthetic success proxy", anchor="ls", font=font(20, True), fill="#111827")
    spacing = (right - left) / len(METHODS)
    for index, method in enumerate(METHODS):
        values = data[method]["fidelity"]
        minimum, q1 = min(values), quantile(values, 0.25)
        median, q3, maximum = statistics.median(values), quantile(values, 0.75), max(values)
        x = left + (index + 0.5) * spacing
        box_half = 40
        draw.line((x, sy_f(minimum), x, sy_f(maximum)), fill=COLORS[method], width=4)
        draw.line((x - 18, sy_f(minimum), x + 18, sy_f(minimum)), fill=COLORS[method], width=4)
        draw.line((x - 18, sy_f(maximum), x + 18, sy_f(maximum)), fill=COLORS[method], width=4)
        draw.rectangle((x - box_half, sy_f(q3), x + box_half, sy_f(q1)), outline=COLORS[method], width=5, fill="#F9FAFB")
        draw.line((x - box_half, sy_f(median), x + box_half, sy_f(median)), fill=COLORS[method], width=6)
        draw.text((x, bottom + 24), LABELS[method], anchor="ma", font=font(16), fill="#374151")
        draw.text((x, sy_f(median) - 11), f"{median:.3f}", anchor="ms", font=font(16, True), fill="#111827")

    # Shared legend and caution.
    for index, method in enumerate(METHODS):
        x = 150 + index * 275
        draw.line((x, 955, x + 45, 955), fill=COLORS[method], width=6)
        draw.text((x + 55, 955), LABELS[method], anchor="lm", font=font(18, True), fill="#111827")
    draw.text(
        (950, 1025),
        "The fidelity quantity uses declared synthetic independent gate-error rates; it is not measured device fidelity.",
        anchor="mm",
        font=font(18),
        fill="#4B5563",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, dpi=(200, 200))
    print(OUTPUT)


if __name__ == "__main__":
    draw()
