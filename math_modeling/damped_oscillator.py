"""Damped harmonic oscillator ODE: SymPy symbolic solution, SciPy numeric solver, and Plotly visualization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import plotly.graph_objects as go
import sympy as sp
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class SymbolicOscillatorResult:
    """Container for symbolic ODE solution and compiled numeric evaluator."""

    expr: sp.Expr
    latex: str
    evaluator: Callable[[np.ndarray], np.ndarray]


def solve_damped_oscillator_symbolic(
    omega_n: float = 2.0,
    zeta: float = 0.15,
    x0: float = 1.0,
    v0: float = 0.0,
) -> SymbolicOscillatorResult:
    """Solve x'' + 2*zeta*omega_n*x' + omega_n**2 * x = 0 symbolically via SymPy."""
    if omega_n <= 0:
        raise ValueError("omega_n must be positive.")
    if zeta < 0:
        raise ValueError("zeta must be non-negative.")

    t = sp.Symbol("t", real=True, nonnegative=True)
    x = sp.Function("x")

    w_sym = sp.nsimplify(omega_n, rational=True)
    z_sym = sp.nsimplify(zeta, rational=True)
    x0_sym = sp.nsimplify(x0, rational=True)
    v0_sym = sp.nsimplify(v0, rational=True)

    ode = sp.Eq(sp.diff(x(t), t, 2) + 2 * z_sym * w_sym * sp.diff(x(t), t) + w_sym**2 * x(t), 0)
    sol = sp.dsolve(ode, x(t), ics={x(0): x0_sym, sp.diff(x(t), t).subs(t, 0): v0_sym})
    expr = sp.simplify(sol.rhs)
    raw_func = sp.lambdify(t, expr, modules=["numpy"])

    def evaluator(t_arr: np.ndarray) -> np.ndarray:
        vals = np.asarray(raw_func(t_arr), dtype=float)
        return np.real_if_close(vals, tol=1e-10).astype(float)

    return SymbolicOscillatorResult(expr=expr, latex=sp.latex(expr), evaluator=evaluator)


def solve_damped_oscillator_numeric(
    omega_n: float = 2.0,
    zeta: float = 0.15,
    x0: float = 1.0,
    v0: float = 0.0,
    t_span: tuple[float, float] = (0.0, 10.0),
    num_points: int = 400,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve damped harmonic oscillator numerically using SciPy solve_ivp (RK45)."""
    if omega_n <= 0:
        raise ValueError("omega_n must be positive.")
    if zeta < 0:
        raise ValueError("zeta must be non-negative.")

    def rhs(_t: float, state: list[float]) -> list[float]:
        pos, vel = state
        acc = -2.0 * zeta * omega_n * vel - (omega_n**2) * pos
        return [vel, acc]

    t_eval = np.linspace(t_span[0], t_span[1], num_points)
    sol = solve_ivp(rhs, t_span, [x0, v0], t_eval=t_eval, method="RK45", rtol=1e-9, atol=1e-11)
    if not sol.success:
        raise RuntimeError(f"Numeric ODE solver failed: {sol.message}")
    return sol.t, sol.y[0], sol.y[1]


def build_damped_oscillator_figure(
    omega_n: float = 2.0,
    x0: float = 1.0,
    v0: float = 0.0,
    t_span: tuple[float, float] = (0.0, 10.0),
) -> go.Figure:
    """Build an interactive Plotly comparison of underdamped, critically damped, and overdamped regimes."""
    regimes = [
        ("不足減衰 (ζ = 0.15)", 0.15, "#1f77b4"),
        ("臨界減衰 (ζ = 1.00)", 1.0, "#2ca02c"),
        ("過減衰 (ζ = 2.00)", 2.0, "#d62728"),
    ]

    fig = go.Figure()
    for label, zeta, color in regimes:
        sym_res = solve_damped_oscillator_symbolic(omega_n=omega_n, zeta=zeta, x0=x0, v0=v0)
        t_num, x_num, _ = solve_damped_oscillator_numeric(
            omega_n=omega_n, zeta=zeta, x0=x0, v0=v0, t_span=t_span, num_points=400
        )
        x_sym = sym_res.evaluator(t_num)

        fig.add_trace(
            go.Scatter(
                x=t_num,
                y=x_sym,
                mode="lines",
                name=f"{label} [SymPy 厳密解]",
                line=dict(color=color, width=2.5),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=t_num[::10],
                y=x_num[::10],
                mode="markers",
                name=f"{label} [SciPy 数値解]",
                marker=dict(color=color, size=6, symbol="circle-open"),
            )
        )

    fig.update_layout(
        title=f"減衰調和振動のSymPy厳密解 vs SciPy数値解 (ωₙ = {omega_n}, x₀ = {x0}, v₀ = {v0})",
        xaxis_title="時間 t [s]",
        yaxis_title="変位 x(t)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
    )
    return fig


def export_damped_oscillator_html(output_path: Path) -> Path:
    """Generate and save the damped oscillator interactive HTML chart."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = build_damped_oscillator_figure()
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    return output_path
