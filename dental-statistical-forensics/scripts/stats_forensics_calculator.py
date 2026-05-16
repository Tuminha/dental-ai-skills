#!/usr/bin/env python3
"""Small deterministic calculations for dental statistical forensics.

This helper intentionally uses only Python's standard library. It is not a
replacement for a full biostatistical analysis package; it provides transparent
screening calculations that reduce arithmetic drift during paper critique.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from typing import Any


Z_95 = 1.959963984540054


@dataclass
class ContinuousResult:
    outcome_type: str
    mean_difference: float
    standard_error: float
    ci95: list[float]
    group_a_individual_interval_approx: list[float]
    group_b_individual_interval_approx: list[float]
    sd_to_effect_ratio_a: float | None
    sd_to_effect_ratio_b: float | None
    max_sd_to_between_group_effect_ratio: float | None
    clinical_threshold: float | None
    crosses_clinical_threshold: bool | None
    flags: list[str]
    assumptions: list[str]


@dataclass
class BinaryResult:
    outcome_type: str
    risk_a: float
    risk_b: float
    absolute_risk_difference: float
    risk_ratio: float | None
    odds_ratio: float | None
    nnt_or_nnh: float | None
    ci95_risk_difference: list[float]
    flags: list[str]
    assumptions: list[str]


@dataclass
class DiagnosticResult:
    outcome_type: str
    sensitivity: float
    specificity: float
    false_positive_rate: float
    false_negative_rate: float
    positive_likelihood_ratio: float | None
    negative_likelihood_ratio: float | None
    diagnostic_odds_ratio: float | None
    flags: list[str]
    assumptions: list[str]


def rounded(value: float | None) -> float | None:
    if value is None or math.isnan(value) or math.isinf(value):
        return None
    return round(value, 4)


def interval(center: float, spread: float) -> list[float]:
    return [round(center - Z_95 * spread, 4), round(center + Z_95 * spread, 4)]


def safe_div(num: float, den: float) -> float | None:
    if den == 0:
        return None
    return num / den


def continuous(args: argparse.Namespace) -> dict[str, Any]:
    effect = args.mean_a - args.mean_b
    se = math.sqrt((args.sd_a**2 / args.n_a) + (args.sd_b**2 / args.n_b))
    ci = interval(effect, se)
    abs_effect = abs(effect)
    threshold = args.clinical_threshold
    max_sd = max(args.sd_a, args.sd_b)
    flags: list[str] = []

    if abs_effect == 0:
        ratio_a = None
        ratio_b = None
        max_ratio = None
        flags.append("Mean difference is zero; SD/effect ratios are undefined.")
    else:
        ratio_a = args.sd_a / abs_effect
        ratio_b = args.sd_b / abs_effect
        max_ratio = max_sd / abs_effect
        if max_ratio >= 1:
            flags.append("At least one SD is as large as or larger than the between-group effect; individual predictability needs caution.")
        elif max_ratio >= 0.5:
            flags.append("SD is substantial relative to the between-group effect; inspect ranges or individual data.")

    if ci[0] <= 0 <= ci[1]:
        flags.append("Approximate 95% CI crosses the null.")

    crosses_threshold = None
    if threshold is not None:
        crosses_threshold = ci[0] <= threshold <= ci[1] or ci[0] <= -threshold <= ci[1]
        if abs_effect < threshold:
            flags.append("Point estimate is smaller than the supplied clinical threshold.")
        if crosses_threshold:
            flags.append("Approximate 95% CI crosses the supplied clinical threshold.")

    result = ContinuousResult(
        outcome_type="continuous",
        mean_difference=rounded(effect) or 0.0,
        standard_error=rounded(se) or 0.0,
        ci95=ci,
        group_a_individual_interval_approx=interval(args.mean_a, args.sd_a),
        group_b_individual_interval_approx=interval(args.mean_b, args.sd_b),
        sd_to_effect_ratio_a=rounded(ratio_a),
        sd_to_effect_ratio_b=rounded(ratio_b),
        max_sd_to_between_group_effect_ratio=rounded(max_ratio),
        clinical_threshold=threshold,
        crosses_clinical_threshold=crosses_threshold,
        flags=flags,
        assumptions=[
            "Approximate normal-theory calculations.",
            "CI uses z=1.96 screening approximation, not exact t distribution.",
            "Individual intervals are mean +/- 1.96 SD and assume approximate normality.",
        ],
    )
    return asdict(result)


def binary(args: argparse.Namespace) -> dict[str, Any]:
    risk_a = args.events_a / args.n_a
    risk_b = args.events_b / args.n_b
    rd = risk_a - risk_b
    se_rd = math.sqrt((risk_a * (1 - risk_a) / args.n_a) + (risk_b * (1 - risk_b) / args.n_b))
    rr = safe_div(risk_a, risk_b)
    odds_a = safe_div(args.events_a, args.n_a - args.events_a)
    odds_b = safe_div(args.events_b, args.n_b - args.events_b)
    or_value = None if odds_a is None or odds_b is None else safe_div(odds_a, odds_b)
    nnt = None if rd == 0 else 1 / abs(rd)
    flags: list[str] = []

    if min(args.events_a, args.events_b, args.n_a - args.events_a, args.n_b - args.events_b) < 5:
        flags.append("Sparse cells present; exact methods or continuity correction may be needed.")
    if interval(rd, se_rd)[0] <= 0 <= interval(rd, se_rd)[1]:
        flags.append("Approximate 95% CI for risk difference crosses the null.")

    result = BinaryResult(
        outcome_type="binary",
        risk_a=rounded(risk_a) or 0.0,
        risk_b=rounded(risk_b) or 0.0,
        absolute_risk_difference=rounded(rd) or 0.0,
        risk_ratio=rounded(rr),
        odds_ratio=rounded(or_value),
        nnt_or_nnh=rounded(nnt),
        ci95_risk_difference=interval(rd, se_rd),
        flags=flags,
        assumptions=[
            "Approximate Wald CI for risk difference.",
            "NNT/NNH is reported as absolute 1/risk difference magnitude and needs clinical direction from outcome desirability.",
        ],
    )
    return asdict(result)


def diagnostic(args: argparse.Namespace) -> dict[str, Any]:
    fpr = 1 - args.specificity
    fnr = 1 - args.sensitivity
    lr_pos = safe_div(args.sensitivity, fpr)
    lr_neg = safe_div(fnr, args.specificity)
    dor = None if lr_pos is None or lr_neg is None else safe_div(lr_pos, lr_neg)
    flags: list[str] = []

    if args.sensitivity < 0.8 or args.specificity < 0.8:
        flags.append("Sensitivity or specificity below 0.80; clinical role depends heavily on context and consequences.")
    if lr_pos is not None and lr_pos < 5:
        flags.append("LR+ below 5; positive tests may not strongly rule in disease.")
    if lr_neg is not None and lr_neg > 0.2:
        flags.append("LR- above 0.2; negative tests may not strongly rule out disease.")

    result = DiagnosticResult(
        outcome_type="diagnostic_accuracy",
        sensitivity=rounded(args.sensitivity) or 0.0,
        specificity=rounded(args.specificity) or 0.0,
        false_positive_rate=rounded(fpr) or 0.0,
        false_negative_rate=rounded(fnr) or 0.0,
        positive_likelihood_ratio=rounded(lr_pos),
        negative_likelihood_ratio=rounded(lr_neg),
        diagnostic_odds_ratio=rounded(dor),
        flags=flags,
        assumptions=[
            "Inputs are proportions from 0 to 1.",
            "No confidence intervals are computed unless raw 2x2 counts are available.",
            "PPV/NPV require prevalence and are not derived here.",
        ],
    )
    return asdict(result)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def proportion(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    cont = sub.add_parser("continuous", help="Mean difference, approximate CI, dispersion flags")
    cont.add_argument("--mean-a", type=float, required=True)
    cont.add_argument("--sd-a", type=float, required=True)
    cont.add_argument("--n-a", type=positive_int, required=True)
    cont.add_argument("--mean-b", type=float, required=True)
    cont.add_argument("--sd-b", type=float, required=True)
    cont.add_argument("--n-b", type=positive_int, required=True)
    cont.add_argument("--clinical-threshold", type=float)
    cont.set_defaults(func=continuous)

    binp = sub.add_parser("binary", help="Risk difference, RR, OR, NNT/NNH screening calculations")
    binp.add_argument("--events-a", type=int, required=True)
    binp.add_argument("--n-a", type=positive_int, required=True)
    binp.add_argument("--events-b", type=int, required=True)
    binp.add_argument("--n-b", type=positive_int, required=True)
    binp.set_defaults(func=binary)

    diag = sub.add_parser("diagnostic", help="Likelihood ratios from sensitivity and specificity")
    diag.add_argument("--sensitivity", type=proportion, required=True)
    diag.add_argument("--specificity", type=proportion, required=True)
    diag.set_defaults(func=diagnostic)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "events_a", 0) > getattr(args, "n_a", 1) or getattr(args, "events_b", 0) > getattr(args, "n_b", 1):
        parser.error("events cannot exceed n")
    print(json.dumps(args.func(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
