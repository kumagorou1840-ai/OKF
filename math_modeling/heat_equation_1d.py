"""1D Heat Equation PDE: SymPy exact solution, Fourier series, Crank-Nicolson + Rannacher smoothing, and Plotly 3D surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

import numpy as np
import plotly.graph_objects as go
import sympy as sp
from scipy.linalg import solve_banded

InitialConditionType = Literal["sine", "square", "triangle"]

_INITIAL_CONDITION_LABELS: dict[InitialConditionType, str] = {
    "sine": "正弦波 (sine)",
    "square": "矩形波 (square)",
    "triangle": "三角波 (triangle)",
}


@dataclass(frozen=True)
class SymbolicHeatResult:
    """Container for symbolic 1D heat equation solution and compiled numeric evaluator."""

    expr: sp.Expr
    latex: str
    evaluator: Callable[[np.ndarray, np.ndarray], np.ndarray]


@dataclass(frozen=True)
class ConvergenceResult:
    """Result of second-order spatial-temporal grid convergence verification."""

    coarse_max_error: float
    fine_max_error: float
    error_ratio: float
    observed_order: float
    dx_coarse: float
    dt_coarse: float
    dx_fine: float
    dt_fine: float


def _validate_initial_condition(initial_condition: str) -> InitialConditionType:
    """Validate initial condition identifier."""
    if initial_condition not in _INITIAL_CONDITION_LABELS:
        raise ValueError(
            f"Unsupported initial_condition={initial_condition!r}. "
            f"Expected one of {tuple(_INITIAL_CONDITION_LABELS)}."
        )
    return initial_condition  # type: ignore[return-value]


def evaluate_initial_condition(
    x: np.ndarray,
    length: float = 1.0,
    initial_condition: InitialConditionType = "sine",
) -> np.ndarray:
    """Evaluate Dirichlet initial condition u(x, 0) on [0, L] with u(0, 0) = u(L, 0) = 0."""
    if length <= 0:
        raise ValueError("length must be positive.")
    ic = _validate_initial_condition(initial_condition)
    x_arr = np.asarray(x, dtype=float)
    interior = (x_arr > 0.0) & (x_arr < length)

    if ic == "sine":
        vals = np.sin(np.pi * x_arr / length)
    elif ic == "square":
        vals = np.ones_like(x_arr, dtype=float)
    else:  # triangle
        vals = 1.0 - np.abs(2.0 * x_arr / length - 1.0)

    return np.where(interior, vals, 0.0)


def evaluate_fourier_exact(
    x: np.ndarray,
    t: np.ndarray,
    alpha: float = 0.05,
    length: float = 1.0,
    initial_condition: InitialConditionType = "sine",
    n_terms: int = 50,
) -> np.ndarray:
    """Evaluate exact 1D heat equation solution via Fourier sine series truncation."""
    if alpha <= 0:
        raise ValueError("alpha must be positive.")
    if length <= 0:
        raise ValueError("length must be positive.")
    if n_terms < 1:
        raise ValueError("n_terms must be at least 1.")
    ic = _validate_initial_condition(initial_condition)

    x_arr, t_arr = np.broadcast_arrays(np.asarray(x, dtype=float), np.asarray(t, dtype=float))
    interior = (x_arr > 0.0) & (x_arr < length)

    if ic == "sine":
        k1 = np.pi / length
        result = np.exp(-alpha * (k1**2) * t_arr) * np.sin(k1 * x_arr)
        return np.where(interior, result, 0.0)

    result = np.zeros_like(x_arr, dtype=float)
    for n in range(1, n_terms + 1):
        if n % 2 == 0:
            continue
        k_n = n * np.pi / length
        if ic == "square":
            b_n = 4.0 / (n * np.pi)
        else:  # triangle
            sign = -1.0 if ((n - 1) // 2) % 2 == 1 else 1.0
            b_n = 8.0 * sign / ((n * np.pi) ** 2)
        result += b_n * np.exp(-alpha * (k_n**2) * t_arr) * np.sin(k_n * x_arr)

    return np.where(interior, result, 0.0)


def solve_heat_equation_symbolic(
    alpha: float = 0.05,
    length: float = 1.0,
) -> SymbolicHeatResult:
    """Derive and verify the exact SymPy solution for ∂u/∂t = α ∂²u/∂x².

    Boundary conditions: u(0, t) = u(L, t) = 0
    Initial condition: u(x, 0) = sin(π x / L)
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive.")
    if length <= 0:
        raise ValueError("length must be positive.")

    x, t = sp.symbols("x t", real=True)
    alpha_sym = sp.nsimplify(alpha, rational=True)
    length_sym = sp.nsimplify(length, rational=True)

    # Separation of variables ansatz for the fundamental mode sin(pi * x / L)
    k = sp.pi / length_sym
    u_expr = sp.simplify(sp.exp(-alpha_sym * k**2 * t) * sp.sin(k * x))

    # Verify PDE residual and boundary/initial conditions symbolically
    pde_residual = sp.simplify(sp.diff(u_expr, t) - alpha_sym * sp.diff(u_expr, x, 2))
    if pde_residual != 0:
        raise RuntimeError(f"Symbolic solution failed PDE verification: residual={pde_residual}")
    if sp.simplify(u_expr.subs(x, 0)) != 0 or sp.simplify(u_expr.subs(x, length_sym)) != 0:
        raise RuntimeError("Symbolic solution failed Dirichlet boundary verification.")
    if sp.simplify(u_expr.subs(t, 0) - sp.sin(sp.pi * x / length_sym)) != 0:
        raise RuntimeError("Symbolic solution failed initial condition verification.")

    raw_func = sp.lambdify((x, t), u_expr, modules=["numpy"])

    def evaluator(x_arr: np.ndarray, t_arr: np.ndarray) -> np.ndarray:
        vals = np.asarray(raw_func(x_arr, t_arr), dtype=float)
        return np.real_if_close(vals, tol=1e-10).astype(float)

    return SymbolicHeatResult(expr=u_expr, latex=sp.latex(u_expr), evaluator=evaluator)


def solve_heat_equation_crank_nicolson(
    alpha: float = 0.05,
    length: float = 1.0,
    t_max: float = 2.0,
    nx: int = 101,
    nt: int = 201,
    initial_condition: InitialConditionType = "sine",
    rannacher_steps: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve 1D heat equation numerically using Crank-Nicolson with optional Rannacher smoothing.

    When ``rannacher_steps > 0``, the first ``rannacher_steps`` time steps are each split
    into two half-step Backward Euler steps of size ``dt / 2`` to damp high-frequency
    oscillations caused by non-smooth initial data while preserving second-order accuracy.

    Returns:
        x_grid: 1D spatial grid of shape (nx,)
        t_grid: 1D temporal grid of shape (nt,)
        u: 2D solution array of shape (nt, nx)
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive.")
    if length <= 0:
        raise ValueError("length must be positive.")
    if t_max <= 0:
        raise ValueError("t_max must be positive.")
    if nx < 3:
        raise ValueError("nx must be at least 3.")
    if nt < 2:
        raise ValueError("nt must be at least 2.")
    if rannacher_steps < 0:
        raise ValueError("rannacher_steps must be non-negative.")
    ic = _validate_initial_condition(initial_condition)

    x_grid = np.linspace(0.0, length, nx)
    t_grid = np.linspace(0.0, t_max, nt)
    dx = x_grid[1] - x_grid[0]
    dt = t_grid[1] - t_grid[0]
    r = alpha * dt / (2.0 * dx**2)

    u = np.zeros((nt, nx), dtype=float)
    u[0, :] = evaluate_initial_condition(x_grid, length=length, initial_condition=ic)

    # Tridiagonal matrix A in banded form (1 upper, 1 lower diagonal) for interior nodes.
    # Both Crank-Nicolson (dt) and half-step Backward Euler (dt/2) share the same LHS matrix.
    m = nx - 2
    ab = np.zeros((3, m), dtype=float)
    ab[0, 1:] = -r
    ab[1, :] = 1.0 + 2.0 * r
    ab[2, :-1] = -r

    for n in range(nt - 1):
        u_int = u[n, 1:-1]
        if n < rannacher_steps:
            u_half = solve_banded((1, 1), ab, u_int)
            u[n + 1, 1:-1] = solve_banded((1, 1), ab, u_half)
        else:
            rhs = r * u[n, :-2] + (1.0 - 2.0 * r) * u_int + r * u[n, 2:]
            u[n + 1, 1:-1] = solve_banded((1, 1), ab, rhs)
        u[n + 1, 0] = 0.0
        u[n + 1, -1] = 0.0

    return x_grid, t_grid, u


def verify_second_order_convergence(
    alpha: float = 0.05,
    length: float = 1.0,
    t_max: float = 2.0,
    nx_coarse: int = 51,
    nt_coarse: int = 101,
    initial_condition: InitialConditionType = "sine",
    rannacher_steps: int = 0,
    n_terms: int = 50,
) -> ConvergenceResult:
    """Verify O(dt^2 + dx^2) convergence by halving (dx, dt) and checking error ratio."""
    nx_fine = 2 * nx_coarse - 1
    nt_fine = 2 * nt_coarse - 1

    x_c, t_c, u_c = solve_heat_equation_crank_nicolson(
        alpha=alpha,
        length=length,
        t_max=t_max,
        nx=nx_coarse,
        nt=nt_coarse,
        initial_condition=initial_condition,
        rannacher_steps=rannacher_steps,
    )
    xc_mesh, tc_mesh = np.meshgrid(x_c, t_c)
    exact_c = evaluate_fourier_exact(
        xc_mesh,
        tc_mesh,
        alpha=alpha,
        length=length,
        initial_condition=initial_condition,
        n_terms=n_terms,
    )
    coarse_err = float(np.max(np.abs(u_c - exact_c)))

    x_f, t_f, u_f = solve_heat_equation_crank_nicolson(
        alpha=alpha,
        length=length,
        t_max=t_max,
        nx=nx_fine,
        nt=nt_fine,
        initial_condition=initial_condition,
        rannacher_steps=rannacher_steps,
    )
    xf_mesh, tf_mesh = np.meshgrid(x_f, t_f)
    exact_f = evaluate_fourier_exact(
        xf_mesh,
        tf_mesh,
        alpha=alpha,
        length=length,
        initial_condition=initial_condition,
        n_terms=n_terms,
    )
    fine_err = float(np.max(np.abs(u_f - exact_f)))

    if fine_err <= 0.0:
        raise RuntimeError("Fine grid error must be positive to compute convergence order.")

    error_ratio = coarse_err / fine_err
    observed_order = float(np.log2(error_ratio))

    return ConvergenceResult(
        coarse_max_error=coarse_err,
        fine_max_error=fine_err,
        error_ratio=error_ratio,
        observed_order=observed_order,
        dx_coarse=float(x_c[1] - x_c[0]),
        dt_coarse=float(t_c[1] - t_c[0]),
        dx_fine=float(x_f[1] - x_f[0]),
        dt_fine=float(t_f[1] - t_f[0]),
    )


def build_heat_equation_figure(
    alpha: float = 0.05,
    length: float = 1.0,
    t_max: float = 2.0,
    nx: int = 101,
    nt: int = 201,
    initial_condition: InitialConditionType = "sine",
    rannacher_steps: int = 2,
    n_terms: int = 50,
) -> go.Figure:
    """Build an interactive Plotly 3D Surface visualization with display-mode & IC dropdowns."""
    default_ic = _validate_initial_condition(initial_condition)

    datasets: dict[InitialConditionType, dict[str, np.ndarray | float]] = {}
    for ic in _INITIAL_CONDITION_LABELS:
        x_grid, t_grid, u_num = solve_heat_equation_crank_nicolson(
            alpha=alpha,
            length=length,
            t_max=t_max,
            nx=nx,
            nt=nt,
            initial_condition=ic,
            rannacher_steps=rannacher_steps,
        )
        x_mesh, t_mesh = np.meshgrid(x_grid, t_grid)
        u_exact = evaluate_fourier_exact(
            x_mesh,
            t_mesh,
            alpha=alpha,
            length=length,
            initial_condition=ic,
            n_terms=n_terms,
        )
        abs_err = np.abs(u_num - u_exact)
        datasets[ic] = {
            "x": x_grid,
            "t": t_grid,
            "u_num": u_num,
            "u_exact": u_exact,
            "abs_err": abs_err,
            "max_err": float(np.max(abs_err)),
        }

    base = datasets[default_ic]
    base_label = _INITIAL_CONDITION_LABELS[default_ic]
    base_err = float(base["max_err"])

    fig = go.Figure(
        data=[
            go.Surface(
                x=base["x"],
                y=base["t"],
                z=base["u_num"],
                colorscale="Viridis",
                colorbar=dict(title="温度 u(x, t)"),
                name="Crank-Nicolson 数値解",
                hovertemplate="x: %{x:.3f}<br>t: %{y:.3f}<br>z: %{z:.5f}<extra></extra>",
            )
        ]
    )

    mode_buttons = [
        dict(
            label="数値解 u_num",
            method="update",
            args=[
                {
                    "z": [base["u_num"]],
                    "colorscale": ["Viridis"],
                    "colorbar.title": ["温度 u(x, t)"],
                },
                {
                    "title.text": (
                        f"1次元熱伝導方程式 [数値解] {base_label} "
                        f"| α={alpha}, L={length}, Rannacher={rannacher_steps}, 最大絶対誤差={base_err:.2e}"
                    ),
                    "scene.zaxis.title": "温度 u(x, t)",
                },
            ],
        ),
        dict(
            label="厳密解 u_exact",
            method="update",
            args=[
                {
                    "z": [base["u_exact"]],
                    "colorscale": ["Viridis"],
                    "colorbar.title": ["厳密解 u_exact(x, t)"],
                },
                {
                    "title.text": (
                        f"1次元熱伝導方程式 [厳密解 (Fourier {n_terms}項)] {base_label} "
                        f"| α={alpha}, L={length}"
                    ),
                    "scene.zaxis.title": "厳密解 u_exact(x, t)",
                },
            ],
        ),
        dict(
            label="絶対誤差分布 |u_num - u_exact|",
            method="update",
            args=[
                {
                    "z": [base["abs_err"]],
                    "colorscale": ["Inferno"],
                    "colorbar.title": ["絶対誤差 |u_num - u_exact|"],
                },
                {
                    "title.text": (
                        f"1次元熱伝導方程式 [絶対誤差分布] {base_label} "
                        f"| α={alpha}, L={length}, 最大絶対誤差={base_err:.2e}"
                    ),
                    "scene.zaxis.title": "絶対誤差 |u_num - u_exact|",
                },
            ],
        ),
    ]

    ic_buttons = []
    for ic, label in _INITIAL_CONDITION_LABELS.items():
        d = datasets[ic]
        ic_err = float(d["max_err"])
        ic_buttons.append(
            dict(
                label=label,
                method="update",
                args=[
                    {
                        "z": [d["u_num"]],
                        "colorscale": ["Viridis"],
                        "colorbar.title": ["温度 u(x, t)"],
                    },
                    {
                        "title.text": (
                            f"1次元熱伝導方程式 [数値解] {label} "
                            f"| α={alpha}, L={length}, Rannacher={rannacher_steps}, 最大絶対誤差={ic_err:.2e}"
                        ),
                        "scene.zaxis.title": "温度 u(x, t)",
                    },
                ],
            )
        )

    fig.update_layout(
        title=(
            f"1次元熱伝導方程式 [数値解] {base_label} "
            f"| α={alpha}, L={length}, Rannacher={rannacher_steps}, 最大絶対誤差={base_err:.2e}"
        ),
        scene=dict(
            xaxis_title="位置 x [m]",
            yaxis_title="時間 t [s]",
            zaxis_title="温度 u(x, t)",
        ),
        updatemenus=[
            dict(
                buttons=mode_buttons,
                direction="down",
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.12,
                yanchor="top",
            ),
            dict(
                buttons=ic_buttons,
                direction="down",
                showactive=True,
                x=0.28,
                xanchor="left",
                y=1.12,
                yanchor="top",
            ),
        ],
        template="plotly_white",
        margin=dict(l=0, r=0, b=0, t=90),
    )
    return fig


def export_heat_equation_html(
    output_path: Path = Path(__file__).resolve().parent / "outputs" / "heat_equation_1d.html",
) -> Path:
    """Generate and save the 1D heat equation interactive 3D Surface HTML chart."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = build_heat_equation_figure()
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    return output_path


if __name__ == "__main__":
    out = export_heat_equation_html()
    print(f"Generated: {out}")
