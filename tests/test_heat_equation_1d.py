"""Verification tests for 1D Heat Equation PDE (SymPy exact, Fourier series, Crank-Nicolson + Rannacher, Plotly 3D)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import pytest
import sympy as sp

from math_modeling.heat_equation_1d import (
    build_heat_equation_figure,
    evaluate_fourier_exact,
    evaluate_initial_condition,
    solve_heat_equation_crank_nicolson,
    solve_heat_equation_symbolic,
    verify_second_order_convergence,
)


def test_heat_equation_symbolic_properties() -> None:
    """SymPy exact solution must satisfy PDE, boundary conditions, and initial condition."""
    alpha = 0.05
    length = 1.0
    res = solve_heat_equation_symbolic(alpha=alpha, length=length)

    x, t = sp.symbols("x t", real=True)
    assert sp.simplify(sp.diff(res.expr, t) - sp.nsimplify(alpha) * sp.diff(res.expr, x, 2)) == 0
    assert sp.simplify(res.expr.subs(x, 0)) == 0
    assert sp.simplify(res.expr.subs(x, length)) == 0
    assert sp.simplify(res.expr.subs(t, 0) - sp.sin(sp.pi * x / length)) == 0
    assert isinstance(res.latex, str) and len(res.latex) > 0


@pytest.mark.parametrize("alpha", [0.02, 0.05, 0.1])
def test_heat_equation_numeric_matches_symbolic_and_boundaries(alpha: float) -> None:
    """Crank-Nicolson solution must match SymPy exact solution and preserve Dirichlet BCs."""
    length = 1.0
    t_max = 2.0
    x_grid, t_grid, u_num = solve_heat_equation_crank_nicolson(
        alpha=alpha, length=length, t_max=t_max, nx=101, nt=201
    )
    sym_res = solve_heat_equation_symbolic(alpha=alpha, length=length)
    x_mesh, t_mesh = np.meshgrid(x_grid, t_grid)
    u_exact = sym_res.evaluator(x_mesh, t_mesh)

    # Boundary conditions u(0, t) = u(L, t) = 0 across all time steps
    assert np.allclose(u_num[:, 0], 0.0, atol=1e-12)
    assert np.allclose(u_num[:, -1], 0.0, atol=1e-12)

    # Initial condition u(x, 0) = sin(pi * x / L)
    assert np.allclose(u_num[0, :], np.sin(np.pi * x_grid / length), atol=1e-12)

    # Accuracy check against SymPy exact solution
    max_err = float(np.max(np.abs(u_num - u_exact)))
    assert max_err < 1e-4


@pytest.mark.parametrize("ic", ["sine", "square", "triangle"])
def test_fourier_exact_initial_and_boundary_conditions(ic: str) -> None:
    """Fourier series exact evaluator must satisfy BCs and approximate initial conditions."""
    length = 1.0
    x = np.linspace(0.0, length, 51)
    t_zero = np.zeros_like(x)
    u0_exact = evaluate_fourier_exact(x, t_zero, alpha=0.05, length=length, initial_condition=ic, n_terms=100)  # type: ignore[arg-type]
    u0_ref = evaluate_initial_condition(x, length=length, initial_condition=ic)  # type: ignore[arg-type]

    assert np.allclose(u0_exact[0], 0.0, atol=1e-12)
    assert np.allclose(u0_exact[-1], 0.0, atol=1e-12)
    if ic == "sine":
        assert np.allclose(u0_exact, u0_ref, atol=1e-12)
    elif ic == "triangle":
        assert np.allclose(u0_exact, u0_ref, atol=1e-2)
    else:  # square has Gibbs phenomenon at endpoints; check interior midpoint
        mid = len(x) // 2
        assert abs(u0_exact[mid] - 1.0) < 2e-2


def test_crank_nicolson_second_order_convergence() -> None:
    """Halving (dx, dt) must yield ~4x error reduction (observed order >= 1.8)."""
    conv = verify_second_order_convergence(
        alpha=0.05,
        length=1.0,
        t_max=2.0,
        nx_coarse=51,
        nt_coarse=101,
        initial_condition="sine",
        rannacher_steps=0,
    )
    assert conv.fine_max_error < conv.coarse_max_error
    assert conv.error_ratio >= 3.5
    assert conv.observed_order >= 1.8


def test_rannacher_smoothing_reduces_discontinuous_oscillation() -> None:
    """Rannacher smoothing must damp high-frequency oscillation on square-wave initial data."""
    x_grid, t_grid, u_no_ran = solve_heat_equation_crank_nicolson(
        alpha=0.05,
        length=1.0,
        t_max=0.2,
        nx=101,
        nt=41,
        initial_condition="square",
        rannacher_steps=0,
    )
    _, _, u_ran = solve_heat_equation_crank_nicolson(
        alpha=0.05,
        length=1.0,
        t_max=0.2,
        nx=101,
        nt=41,
        initial_condition="square",
        rannacher_steps=4,
    )

    # With large dt/dx^2 on discontinuous IC, Rannacher smoothing prevents overshoot > 1.0
    assert float(np.max(u_ran[1:, :])) <= float(np.max(u_no_ran[1:, :])) + 1e-12
    assert float(np.min(u_ran[1:, :])) >= -1e-12
    assert np.allclose(u_ran[:, 0], 0.0, atol=1e-12)
    assert np.allclose(u_ran[:, -1], 0.0, atol=1e-12)


def test_heat_equation_plotly_surface_figure() -> None:
    """Plotly figure must contain a valid 3D Surface trace and two interactive dropdowns."""
    fig = build_heat_equation_figure(nx=51, nt=61)
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Surface)
    assert fig.data[0].z.shape == (61, 51)

    updatemenus = fig.layout.updatemenus
    assert len(updatemenus) == 2
    mode_labels = [btn.label for btn in updatemenus[0].buttons]
    ic_labels = [btn.label for btn in updatemenus[1].buttons]
    assert "数値解 u_num" in mode_labels
    assert "厳密解 u_exact" in mode_labels
    assert "絶対誤差分布 |u_num - u_exact|" in mode_labels
    assert "正弦波 (sine)" in ic_labels
    assert "矩形波 (square)" in ic_labels
    assert "三角波 (triangle)" in ic_labels
