"""Lorenz attractor ODE: SymPy equilibrium/Jacobian analysis, butterfly effect, and 3D Plotly visualization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import sympy as sp
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class LorenzEquilibriumAnalysis:
    """Symbolic equilibria and Jacobian eigenvalues for the Lorenz system."""

    origin_eq: tuple[float, float, float]
    positive_eq: tuple[float, float, float]
    negative_eq: tuple[float, float, float]
    origin_eigenvalues: tuple[complex, ...]
    positive_eigenvalues: tuple[complex, ...]


def analyze_lorenz_equilibria(
    sigma: float = 10.0,
    rho: float = 28.0,
    beta: float = 8.0 / 3.0,
) -> LorenzEquilibriumAnalysis:
    """Compute Lorenz equilibria and Jacobian eigenvalues using SymPy."""
    if min(sigma, rho, beta) <= 0:
        raise ValueError("All Lorenz parameters must be positive.")

    x, y, z = sp.symbols("x y z", real=True)
    s_sym = sp.nsimplify(sigma, rational=True)
    r_sym = sp.nsimplify(rho, rational=True)
    b_sym = sp.nsimplify(beta, rational=True)

    dx = s_sym * (y - x)
    dy = x * (r_sym - z) - y
    dz = x * y - b_sym * z

    eqs = sp.solve([dx, dy, dz], (x, y, z))
    jacobian = sp.Matrix([dx, dy, dz]).jacobian([x, y, z])

    origin_pt = (0.0, 0.0, 0.0)
    pos_pt = None
    neg_pt = None
    origin_eigs: tuple[complex, ...] = ()
    pos_eigs: tuple[complex, ...] = ()

    for pt in eqs:
        coords = tuple(float(v.evalf()) for v in pt)
        eigs = tuple(complex(ev.evalf()) for ev in jacobian.subs({x: pt[0], y: pt[1], z: pt[2]}).eigenvals().keys())
        if all(abs(c) < 1e-12 for c in coords):
            origin_pt = coords
            origin_eigs = eigs
        elif coords[0] > 0:
            pos_pt = coords
            pos_eigs = eigs
        else:
            neg_pt = coords

    if pos_pt is None or neg_pt is None:
        raise RuntimeError("Non-trivial equilibria exist only when rho > 1.")

    return LorenzEquilibriumAnalysis(
        origin_eq=origin_pt,
        positive_eq=pos_pt,
        negative_eq=neg_pt,
        origin_eigenvalues=origin_eigs,
        positive_eigenvalues=pos_eigs,
    )


def solve_lorenz_numeric(
    sigma: float = 10.0,
    rho: float = 28.0,
    beta: float = 8.0 / 3.0,
    initial_state: tuple[float, float, float] = (1.0, 1.0, 1.0),
    t_span: tuple[float, float] = (0.0, 35.0),
    num_points: int = 3500,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Solve Lorenz ODE numerically using SciPy solve_ivp (DOP853)."""

    def rhs(_t: float, state: list[float]) -> list[float]:
        xv, yv, zv = state
        return [sigma * (yv - xv), xv * (rho - zv) - yv, xv * yv - beta * zv]

    t_eval = np.linspace(t_span[0], t_span[1], num_points)
    sol = solve_ivp(rhs, t_span, list(initial_state), t_eval=t_eval, method="DOP853", rtol=1e-10, atol=1e-12)
    if not sol.success:
        raise RuntimeError(f"Numeric ODE solver failed: {sol.message}")
    return sol.t, sol.y[0], sol.y[1], sol.y[2]


def estimate_max_lyapunov_exponent(
    sigma: float = 10.0,
    rho: float = 28.0,
    beta: float = 8.0 / 3.0,
    initial_state: tuple[float, float, float] = (1.0, 1.0, 1.0),
    perturbation_norm: float = 1e-8,
    dt_renorm: float = 0.5,
    transient_time: float = 5.0,
    sample_time: float = 40.0,
) -> float:
    """Estimate the largest Lyapunov exponent via Benettin's renormalization method."""
    if min(sigma, rho, beta) <= 0:
        raise ValueError("All Lorenz parameters must be positive.")
    if perturbation_norm <= 0 or dt_renorm <= 0 or sample_time <= 0:
        raise ValueError("perturbation_norm, dt_renorm, and sample_time must be positive.")

    def rhs_single(_t: float, state: list[float] | np.ndarray) -> list[float]:
        xv, yv, zv = state
        return [sigma * (yv - xv), xv * (rho - zv) - yv, xv * yv - beta * zv]

    def rhs_pair(_t: float, state: list[float] | np.ndarray) -> list[float]:
        x1, y1, z1, x2, y2, z2 = state
        return [
            sigma * (y1 - x1),
            x1 * (rho - z1) - y1,
            x1 * y1 - beta * z1,
            sigma * (y2 - x2),
            x2 * (rho - z2) - y2,
            x2 * y2 - beta * z2,
        ]

    ref_state = np.array(initial_state, dtype=float)
    if transient_time > 0:
        sol_tr = solve_ivp(
            rhs_single,
            (0.0, transient_time),
            ref_state,
            method="DOP853",
            rtol=1e-10,
            atol=1e-12,
        )
        if not sol_tr.success:
            raise RuntimeError(f"Transient ODE solver failed: {sol_tr.message}")
        ref_state = sol_tr.y[:, -1].copy()

    delta = np.array([1.0, 0.0, 0.0], dtype=float) * perturbation_norm
    num_steps = max(1, int(round(sample_time / dt_renorm)))
    log_sum = 0.0

    for step in range(num_steps):
        t0 = step * dt_renorm
        t1 = t0 + dt_renorm
        y0 = np.concatenate([ref_state, ref_state + delta])
        sol = solve_ivp(rhs_pair, (t0, t1), y0, method="DOP853", rtol=1e-10, atol=1e-12)
        if not sol.success:
            raise RuntimeError(f"Lyapunov ODE solver failed: {sol.message}")

        ref_next = sol.y[:3, -1]
        pert_next = sol.y[3:, -1]
        diff = pert_next - ref_next
        dist = float(np.linalg.norm(diff))

        if dist <= 0.0:
            log_sum += float(np.log(1e-300 / perturbation_norm))
            delta = np.array([1.0, 0.0, 0.0], dtype=float) * perturbation_norm
        else:
            log_sum += float(np.log(dist / perturbation_norm))
            delta = (diff / dist) * perturbation_norm
        ref_state = ref_next

    return float(log_sum / (num_steps * dt_renorm))


def _compute_lorenz_case_data(
    sigma: float,
    rho: float,
    beta: float,
    delta_x0: float,
) -> dict[str, object]:
    """Compute trajectories, equilibria, and Lyapunov exponent title for a given rho."""
    _, x1, y1, z1 = solve_lorenz_numeric(sigma=sigma, rho=rho, beta=beta, initial_state=(1.0, 1.0, 1.0))
    _, x2, y2, z2 = solve_lorenz_numeric(
        sigma=sigma, rho=rho, beta=beta, initial_state=(1.0 + delta_x0, 1.0, 1.0)
    )
    if rho > 1.0:
        analysis = analyze_lorenz_equilibria(sigma=sigma, rho=rho, beta=beta)
        eqs = [analysis.origin_eq, analysis.positive_eq, analysis.negative_eq]
    else:
        eqs = [(0.0, 0.0, 0.0)]

    lam_max = estimate_max_lyapunov_exponent(sigma=sigma, rho=rho, beta=beta)
    title = (
        f"ローレンツ・アトラクタ：3Dカオス軌道と初期値鋭敏性 "
        f"(σ={sigma}, ρ={rho}, β={beta:.2f}, λ_max={lam_max:.4f})"
    )
    return {
        "x1": x1,
        "y1": y1,
        "z1": z1,
        "x2": x2,
        "y2": y2,
        "z2": z2,
        "eq_x": [p[0] for p in eqs],
        "eq_y": [p[1] for p in eqs],
        "eq_z": [p[2] for p in eqs],
        "title": title,
    }


def build_lorenz_figure(
    sigma: float = 10.0,
    rho: float = 28.0,
    beta: float = 8.0 / 3.0,
    delta_x0: float = 1e-5,
) -> go.Figure:
    """Build 3D Plotly trajectory with rho bifurcation dropdown and Lyapunov exponent display."""
    bifurcation_cases = [
        (0.5, "ρ=0.5 (原点収束)"),
        (15.0, "ρ=15 (平衡点収束)"),
        (28.0, "ρ=28 (カオスアトラクタ)"),
    ]

    buttons = []
    initial_case: dict[str, object] | None = None
    active_idx = 2

    for idx, (rho_val, label) in enumerate(bifurcation_cases):
        case = _compute_lorenz_case_data(sigma=sigma, rho=rho_val, beta=beta, delta_x0=delta_x0)
        if np.isclose(rho, rho_val):
            initial_case = case
            active_idx = idx
        buttons.append(
            dict(
                label=label,
                method="update",
                args=[
                    {
                        "x": [case["x1"], case["x2"], case["eq_x"]],
                        "y": [case["y1"], case["y2"], case["eq_y"]],
                        "z": [case["z1"], case["z2"], case["eq_z"]],
                    },
                    {"title": {"text": case["title"]}},
                ],
            )
        )

    if initial_case is None:
        initial_case = _compute_lorenz_case_data(sigma=sigma, rho=rho, beta=beta, delta_x0=delta_x0)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter3d(
            x=initial_case["x1"],
            y=initial_case["y1"],
            z=initial_case["z1"],
            mode="lines",
            name="軌道A (x₀=1.0)",
            line=dict(color="#1f77b4", width=2.5),
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=initial_case["x2"],
            y=initial_case["y2"],
            z=initial_case["z2"],
            mode="lines",
            name=f"軌道B (x₀=1.0+{delta_x0:.0e})",
            line=dict(color="#d62728", width=2.0),
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=initial_case["eq_x"],
            y=initial_case["eq_y"],
            z=initial_case["eq_z"],
            mode="markers",
            name="平衡点 (O, C+, C-)",
            marker=dict(color="black", size=5, symbol="diamond"),
        )
    )

    fig.update_layout(
        title=initial_case["title"],
        scene=dict(xaxis_title="x", yaxis_title="y", zaxis_title="z"),
        template="plotly_white",
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                active=active_idx,
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                showactive=True,
                buttons=buttons,
            )
        ],
    )
    return fig


def export_lorenz_html(output_path: Path) -> Path:
    """Generate and save the Lorenz attractor interactive 3D HTML chart."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = build_lorenz_figure()
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    return output_path


if __name__ == "__main__":
    out = export_lorenz_html(Path(__file__).resolve().parent / "outputs" / "lorenz_attractor.html")
    print(f"[Lorenz Attractor] HTML saved: {out}")
