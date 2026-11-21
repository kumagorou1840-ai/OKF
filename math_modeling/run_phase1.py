"""Run Phase 1 ODE models and export interactive Plotly HTML visualizations."""

from __future__ import annotations

from pathlib import Path

from math_modeling.damped_oscillator import (
    export_damped_oscillator_html,
    solve_damped_oscillator_symbolic,
)
from math_modeling.lotka_volterra import (
    analyze_lotka_volterra_equilibrium,
    export_lotka_volterra_html,
)


def main() -> None:
    """Execute Phase 1 symbolic/numeric ODE pipelines and save HTML reports."""
    out_dir = Path(__file__).resolve().parent / "outputs"

    sym_osc = solve_damped_oscillator_symbolic(omega_n=2.0, zeta=0.15, x0=1.0, v0=0.0)
    osc_html = export_damped_oscillator_html(out_dir / "damped_oscillator.html")

    lv_analysis = analyze_lotka_volterra_equilibrium()
    lv_html = export_lotka_volterra_html(out_dir / "lotka_volterra.html")

    print(f"[Damped Oscillator] SymPy exact: x(t) = {sym_osc.expr}")
    print(f"[Damped Oscillator] HTML saved: {osc_html}")
    print(
        f"[Lotka-Volterra] Coexistence eq={lv_analysis.coexistence_eq}, "
        f"eigenvalues={lv_analysis.coexistence_eigenvalues}"
    )
    print(f"[Lotka-Volterra] HTML saved: {lv_html}")


if __name__ == "__main__":
    main()
