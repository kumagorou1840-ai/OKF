"""Verification tests for Phase 1 ODE models (SymPy exact vs SciPy numeric + Plotly)."""

from __future__ import annotations

import numpy as np
import pytest

from math_modeling.damped_oscillator import (
    build_damped_oscillator_figure,
    solve_damped_oscillator_numeric,
    solve_damped_oscillator_symbolic,
)
from math_modeling.lotka_volterra import (
    analyze_lotka_volterra_equilibrium,
    build_lotka_volterra_figure,
    compute_lotka_volterra_invariant,
    solve_lotka_volterra_numeric,
)


@pytest.mark.parametrize("zeta", [0.15, 1.0, 2.0])
def test_damped_oscillator_symbolic_matches_numeric(zeta: float) -> None:
    """SymPy exact solution and SciPy RK45 numeric solution must agree within 1e-6."""
    sym_res = solve_damped_oscillator_symbolic(omega_n=2.0, zeta=zeta, x0=1.0, v0=0.5)
    t_num, x_num, _ = solve_damped_oscillator_numeric(omega_n=2.0, zeta=zeta, x0=1.0, v0=0.5)
    x_sym = sym_res.evaluator(t_num)

    assert np.isclose(x_sym[0], 1.0, atol=1e-12)
    max_err = float(np.max(np.abs(x_sym - x_num)))
    assert max_err < 1e-6


def test_lotka_volterra_equilibrium_and_invariant() -> None:
    """Coexistence equilibrium must have pure imaginary eigenvalues and conserved first integral."""
    analysis = analyze_lotka_volterra_equilibrium(alpha=1.0, beta=0.1, delta=0.075, gamma=1.5)
    assert np.isclose(analysis.coexistence_eq[0], 20.0)
    assert np.isclose(analysis.coexistence_eq[1], 10.0)
    for ev in analysis.coexistence_eigenvalues:
        assert abs(ev.real) < 1e-10
        assert abs(ev.imag) > 0.1

    _, prey, pred = solve_lotka_volterra_numeric()
    inv = compute_lotka_volterra_invariant(prey, pred)
    drift = float(np.max(inv) - np.min(inv))
    assert drift < 1e-7


def test_plotly_figures_generation() -> None:
    """Both Plotly figures should contain expected traces without errors."""
    fig_osc = build_damped_oscillator_figure()
    fig_lv = build_lotka_volterra_figure()
    assert len(fig_osc.data) == 6
    assert len(fig_lv.data) == 6
