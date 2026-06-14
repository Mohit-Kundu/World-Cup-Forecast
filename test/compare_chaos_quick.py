"""Quick compare chaos methods 0-2 from predictions.json only."""

from __future__ import annotations

import json
import math
from pathlib import Path

from src.config import WC2026_GROUPS

pred = json.loads(Path("output/predictions.json").read_text(encoding="utf-8"))
qp = pred["qualify_probs"]


def probs(group: str) -> list[float]:
    return [qp.get(team, 0.0) for team in WC2026_GROUPS[group]]


def variance(ps: list[float]) -> float:
    mean = sum(ps) / len(ps)
    return sum((p - mean) ** 2 for p in ps) / len(ps)


def entropy(ps: list[float]) -> float:
    total = sum(ps)
    if total <= 0:
        return 0.0
    normalized = [p / total for p in ps if p > 0]
    return -sum(p * math.log(p) for p in normalized)


def fav_vuln(ps: list[float]) -> float:
    return 1.0 - max(ps) if ps else 0.0


methods = [
    ("0_current_qual_variance", variance),
    ("1_shannon_entropy", entropy),
    ("2_favorite_vulnerability", fav_vuln),
]

print("=== PER-GROUP (methods 0-2) ===")
print("Grp      Var     Ent  FavVuln")
for group in sorted(WC2026_GROUPS):
    ps = probs(group)
    print(f"{group:<4} {variance(ps):7.4f} {entropy(ps):6.3f} {fav_vuln(ps):7.3f}")

print()
for name, fn in methods:
    scores = {group: fn(probs(group)) for group in WC2026_GROUPS}
    winner = max(scores, key=scores.get)
    teams = WC2026_GROUPS[winner]
    qual = {team: round(qp.get(team, 0.0) * 100, 1) for team in teams}
    print(f"{name}: Group {winner} ({scores[winner]:.4f})")
    print(f"  teams: {teams}")
    print(f"  qual%: {qual}")
    if name == "2_favorite_vulnerability":
        fav = max(qual, key=qual.get)
        print(f"  favorite: {fav} ({qual[fav]}% qual)")
    print()
