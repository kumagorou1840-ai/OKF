"""Lotka-Volterra predator-prey ODE: SymPy equilibrium analysis, SciPy solver, and Plotly phase portrait."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import sympy as sp
from plotly.subplots import make_subplots
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class LotkaVolterraAnalysis:
    """Symbolic equilibrium points and Jacobian eigenvalues at coexistence equilibrium."""

    trivial_eq: tuple[float, float]
    coexistence_eq: tuple[float, float]
    coexistence_eigenvalues: tuple[complex, complex]


def analyze_lotka_volterra_equilibrium(
    alpha: float = 1.0,
    beta: float = 0.1,
    delta: float = 0.075,
    gamma: float = 1.5,
) -> LotkaVolterraAnalysis:
    """Compute equilibria and Jacobian eigenvalues at the coexistence fixed point using SymPy."""
    if min(alpha, beta, delta, gamma) <= 0:
        raise ValueError("All Lotka-Volterra parameters must be positive.")

    x, y = sp.symbols("x y", real=True, nonnegative=True)
    a_sym = sp.nsimplify(alpha, rational=True)
    b_sym = sp.nsimplify(beta, rational=True)
    d_sym = sp.nsimplify(delta, rational=True)
    g_sym = sp.nsimplify(gamma, rational=True)

    dx = a_sym * x - b_sym * x * y
    dy = d_sym * x * y - g_sym * y

    eq_points = sp.solve([dx, dy], (x, y))
    coex_pt = next(pt for pt in eq_points if abs(float(pt[0])) > 1e-12 and abs(float(pt[1])) > 1e-12)

    jacobian = sp.Matrix([dx, dy]).jacobian([x, y])
    j_at_coex = jacobian.subs({x: coex_pt[0], y: coex_pt[1]})
    eig_vals = [complex(ev.evalf()) for ev in j_at_coex.eigenvals().keys()]
    if len(eig_vals) == 1:
        eig_vals = [eig_vals[0], eig_vals[0]]

    return LotkaVolterraAnalysis(
        trivial_eq=(0.0, 0.0),
        coexistence_eq=(float(coex_pt[0]), float(coex_pt[1])),
        coexistence_eigenvalues=(eig_vals[0], eig_vals[1]),
    )


def compute_lotka_volterra_invariant(
    x: np.ndarray,
    y: np.ndarray,
    alpha: float = 1.0,
    beta: float = 0.1,
    delta: float = 0.075,
    gamma: float = 1.5,
) -> np.ndarray:
    """Compute conserved first integral V(x, y) = delta*x - gamma*ln(x) + beta*y - alpha*ln(y)."""
    return delta * x - gamma * np.log(x) + beta * y - alpha * np.log(y)


def solve_lotka_volterra_numeric(
    alpha: float = 1.0,
    beta: float = 0.1,
    delta: float = 0.075,
    gamma: float = 1.5,
    initial_state: tuple[float, float] = (10.0, 5.0),
    t_span: tuple[float, float] = (0.0, 20.0),
    num_points: int = 500,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve Lotka-Volterra ODE numerically using SciPy solve_ivp (DOP853)."""
    if min(alpha, beta, delta, gamma) <= 0:
        raise ValueError("All parameters must be positive.")
    if initial_state[0] <= 0 or initial_state[1] <= 0:
        raise ValueError("Initial populations must be positive.")

    def rhs(_t: float, state: list[float]) -> list[float]:
        prey, pred = state
        return [alpha * prey - beta * prey * pred, delta * prey * pred - gamma * pred]

    t_eval = np.linspace(t_span[0], t_span[1], num_points)
    sol = solve_ivp(rhs, t_span, list(initial_state), t_eval=t_eval, method="DOP853", rtol=1e-10, atol=1e-12)
    if not sol.success:
        raise RuntimeError(f"Numeric ODE solver failed: {sol.message}")
    return sol.t, sol.y[0], sol.y[1]


def build_lotka_volterra_figure(
    alpha: float = 1.0,
    beta: float = 0.1,
    delta: float = 0.075,
    gamma: float = 1.5,
) -> go.Figure:
    """Build a 2-panel Plotly chart: time series (left) and phase portrait (right)."""
    analysis = analyze_lotka_volterra_equilibrium(alpha=alpha, beta=beta, delta=delta, gamma=gamma)
    t_arr, prey, pred = solve_lotka_volterra_numeric(
        alpha=alpha, beta=beta, delta=delta, gamma=gamma, initial_state=(10.0, 5.0)
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("個体数時系列 (x₀=10, y₀=5)", "相図 (Phase Portrait & 共存平衡点)"),
    )

    fig.add_trace(go.Scatter(x=t_arr, y=prey, mode="lines", name="被食者 x(t)", line=dict(color="#1f77b4")), row=1, col=1)
    fig.add_trace(go.Scatter(x=t_arr, y=pred, mode="lines", name="捕食者 y(t)", line=dict(color="#d62728")), row=1, col=1)

    initial_orbits = [(10.0, 5.0), (15.0, 7.0), (25.0, 12.0)]
    orbit_colors = ["#2ca02c", "#9467bd", "#ff7f0e"]
    for init, color in zip(initial_orbits, orbit_colors):
        _, ox, oy = solve_lotka_volterra_numeric(
            alpha=alpha, beta=beta, delta=delta, gamma=gamma, initial_state=init
        )
        fig.add_trace(
            go.Scatter(
                x=ox,
                y=oy,
                mode="lines",
                name=f"軌道 (x₀={init[0]}, y₀={init[1]})",
                line=dict(color=color),
            ),
            row=1,
            col=2,
        )

    eq_x, eq_y = analysis.coexistence_eq
    fig.add_trace(
        go.Scatter(
            x=[eq_x],
            y=[eq_y],
            mode="markers+text",
            name=f"共存平衡点 ({eq_x:.1f}, {eq_y:.1f})",
            text=[f"({eq_x:.1f}, {eq_y:.1f})"],
            textposition="top right",
            marker=dict(color="black", size=10, symbol="x"),
        ),
        row=1,
        col=2,
    )

    fig.update_xaxes(title_text="時間 t", row=1, col=1)
    fig.update_yaxes(title_text="個体数", row=1, col=1)
    fig.update_xaxes(title_text="被食者 x", row=1, col=2)
    fig.update_yaxes(title_text="捕食者 y", row=1, col=2)
    fig.update_layout(
        title="ロトカ＝ヴォルテラ方程式：時系列と相図",
        template="plotly_white",
        hovermode="closest",
    )
    return fig


def export_lotka_volterra_html(output_path: Path) -> Path:
    """Generate and save the Lotka-Volterra interactive HTML chart."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = build_lotka_volterra_figure()
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    return output_path
