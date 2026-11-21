"""Verification tests for Lorenz attractor (SymPy equilibria/eigenvalues, sensitivity, 3D Plotly)."""

from __future__ import annotations

import numpy as np

from math_modeling.lorenz_attractor import (
    analyze_lorenz_equilibria,
    build_lorenz_figure,
    estimate_max_lyapunov_exponent,
    solve_lorenz_numeric,
)


def test_lorenz_equilibria_and_instability() -> None:
    """All three equilibria at standard parameters must be unstable (positive real eigenvalue)."""
    analysis = analyze_lorenz_equilibria(sigma=10.0, rho=28.0, beta=8.0 / 3.0)
    assert np.allclose(analysis.origin_eq, (0.0, 0.0, 0.0))
    assert np.isclose(analysis.positive_eq[2], 27.0)
    assert np.isclose(analysis.negative_eq[2], 27.0)
    assert any(ev.real > 0.0 for ev in analysis.origin_eigenvalues)
    assert any(ev.real > 0.0 for ev in analysis.positive_eigenvalues)


def test_lorenz_butterfly_effect_sensitivity() -> None:
    """Nearby initial conditions (1e-5 apart) must diverge substantially over t=[0, 35]."""
    _, x1, y1, z1 = solve_lorenz_numeric(initial_state=(1.0, 1.0, 1.0))
    _, x2, y2, z2 = solve_lorenz_numeric(initial_state=(1.0 + 1e-5, 1.0, 1.0))

    dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)
    assert dist[0] < 2e-5
    assert float(np.max(dist)) > 10.0


def test_lorenz_max_lyapunov_exponent_chaos_vs_convergence() -> None:
    """Largest Lyapunov exponent must be positive for chaos (rho=28) and negative for convergence (rho=10)."""
    lambda_chaos = estimate_max_lyapunov_exponent(sigma=10.0, rho=28.0, beta=8.0 / 3.0)
    lambda_conv = estimate_max_lyapunov_exponent(sigma=10.0, rho=10.0, beta=8.0 / 3.0)
    assert lambda_chaos > 0.0
    assert lambda_conv < 0.0


def test_lorenz_plotly_3d_figure() -> None:
    """Lorenz 3D figure should contain trajectories, equilibrium markers, and rho dropdown."""
    fig = build_lorenz_figure()
    assert len(fig.data) == 3
    assert fig.data[0].type == "scatter3d"
    assert "λ_max=" in fig.layout.title.text
    assert len(fig.layout.updatemenus) == 1
    buttons = fig.layout.updatemenus[0].buttons
    assert len(buttons) == 3
    assert all("λ_max=" in btn.args[1]["title"]["text"] for btn in buttons)
