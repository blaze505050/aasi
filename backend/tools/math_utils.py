"""
Symbolic mathematics and independent verification tool for AASI using SymPy.
"""

from typing import Any, Dict, List, Optional
import sympy as sp


def evaluate_symbolic_expression(
    expression_str: str,
    substitutions: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Safely parse and evaluate a symbolic mathematical expression.
    """
    try:
        expr = sp.sympify(expression_str)
    except Exception as exc:
        raise ValueError(f"Failed to parse mathematical expression '{expression_str}': {str(exc)}")

    simplified = sp.simplify(expr)
    free_symbols = [str(s) for s in expr.free_symbols]

    result_numeric = None
    if substitutions:
        # Convert string keys to sympy symbols
        sub_dict = {sp.Symbol(k): float(v) for k, v in substitutions.items()}
        substituted_expr = expr.subs(sub_dict)
        try:
            result_numeric = float(substituted_expr.evalf())
        except Exception:
            result_numeric = str(substituted_expr)

    return {
        "tool": "math",
        "calculation": "symbolic_evaluation",
        "inputs": {
            "expression": expression_str,
            "substitutions": substitutions or {},
        },
        "results": {
            "symbolic_form": str(expr),
            "simplified_form": str(simplified),
            "latex_form": sp.latex(simplified),
            "free_symbols": sorted(free_symbols),
            "numeric_result": result_numeric,
        },
        "assumptions": [
            "Analytical algebraic simplification under standard complex/real mathematical conventions",
        ],
    }


def solve_symbolic_equation(
    equation_str: str,
    variable_str: str,
) -> Dict[str, Any]:
    """
    Analytically solve an equation for a specified target variable.
    Equation can be 'lhs = rhs' or an expression implicitly equal to 0.
    """
    var = sp.Symbol(variable_str.strip())

    try:
        if "=" in equation_str:
            lhs_str, rhs_str = equation_str.split("=", 1)
            lhs = sp.sympify(lhs_str)
            rhs = sp.sympify(rhs_str)
            eq = sp.Eq(lhs, rhs)
        else:
            eq = sp.Eq(sp.sympify(equation_str), 0)
    except Exception as exc:
        raise ValueError(f"Failed to parse equation '{equation_str}': {str(exc)}")

    try:
        solutions = sp.solve(eq, var)
    except Exception as exc:
        raise ValueError(f"Failed to solve equation for '{variable_str}': {str(exc)}")

    return {
        "tool": "math",
        "calculation": "symbolic_equation_solver",
        "inputs": {
            "equation": equation_str,
            "target_variable": variable_str,
        },
        "results": {
            "equation_form": str(eq),
            "solutions": [str(s) for s in solutions],
            "solutions_latex": [sp.latex(s) for s in solutions],
            "solution_count": len(solutions),
        },
        "assumptions": [
            "Analytical algebraic solution over the complex domain restricted to real branches",
        ],
    }


def verify_calculation(
    calculated_value: float,
    reference_formula: str,
    parameters: Dict[str, float],
    tolerance_rel: float = 1e-4,
) -> Dict[str, Any]:
    """
    Independently verify a numerical calculation by recomputing it from first principles with SymPy.
    """
    try:
        expr = sp.sympify(reference_formula)
    except Exception as exc:
        raise ValueError(f"Invalid reference formula '{reference_formula}': {str(exc)}")

    sub_dict = {sp.Symbol(k): float(v) for k, v in parameters.items()}
    recomputed_expr = expr.subs(sub_dict)

    try:
        recomputed_val = float(recomputed_expr.evalf())
    except Exception as exc:
        raise ValueError(f"Failed to evaluate reference formula with parameters: {str(exc)}")

    denom = max(abs(recomputed_val), 1e-12)
    relative_error = abs(calculated_value - recomputed_val) / denom
    is_verified = relative_error <= tolerance_rel

    return {
        "is_verified": is_verified,
        "calculated_value": calculated_value,
        "recomputed_value": round(recomputed_val, 6),
        "relative_error": round(relative_error, 8),
        "tolerance_rel": tolerance_rel,
        "reference_formula": reference_formula,
    }
