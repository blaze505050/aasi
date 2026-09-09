import ast
from typing import Any, Dict, List, Optional
import sympy as sp

ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Call,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
)

ALLOWED_MATH_FUNCS = {
    "sqrt", "log", "ln", "exp", "sin", "cos", "tan",
    "asin", "acos", "atan", "sinh", "cosh", "tanh", "abs",
    "pi", "e"
}

DISALLOWED_IDENTIFIERS = {
    "import", "eval", "exec", "open", "os", "sys", "subprocess",
    "builtins", "globals", "locals", "getattr", "setattr", "compile",
    "breakpoint", "help", "input", "exit", "quit"
}


def validate_safe_math_expression(expr_str: str) -> None:
    """
    Validate that an expression string contains ONLY safe mathematical syntax.
    Rejects dangerous constructs, attributes, non-math calls, and dunder methods.
    """
    if not expr_str or not expr_str.strip():
        raise ValueError("Expression string cannot be empty.")

    # Disallow explicit dunder methods or import patterns directly
    if "__" in expr_str:
        raise ValueError("Invalid expression: contains disallowed dunder attributes.")

    # Strip whitespace and replace ^ with ** for AST evaluation
    py_expr = expr_str.strip().replace("^", "**")
    try:
        tree = ast.parse(py_expr, mode="eval")
    except Exception as exc:
        raise ValueError(f"Syntax error in mathematical expression '{expr_str}': {str(exc)}")

    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ValueError(f"Security validation error: Disallowed syntax element '{type(node).__name__}' in expression.")
        if isinstance(node, ast.Name):
            name_lower = node.id.lower()
            if node.id.startswith("_") or name_lower in DISALLOWED_IDENTIFIERS:
                raise ValueError(f"Security validation error: Disallowed identifier '{node.id}' in expression.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Security validation error: Attribute/nested function calls are disallowed.")
            func_name = node.func.id.lower()
            if func_name not in ALLOWED_MATH_FUNCS:
                raise ValueError(f"Security validation error: Function '{node.func.id}' is not an allowed mathematical function.")


def evaluate_symbolic_expression(
    expression_str: str,
    substitutions: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Safely parse and evaluate a symbolic mathematical expression.
    """
    validate_safe_math_expression(expression_str)
    try:
        expr = sp.sympify(expression_str.replace("^", "**"))
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
    var_name = variable_str.strip()
    if not var_name.isidentifier() or var_name.startswith("_") or var_name.lower() in DISALLOWED_IDENTIFIERS:
        raise ValueError(f"Invalid target variable name '{variable_str}'")
    var = sp.Symbol(var_name)

    try:
        if "=" in equation_str:
            lhs_str, rhs_str = equation_str.split("=", 1)
            validate_safe_math_expression(lhs_str)
            validate_safe_math_expression(rhs_str)
            lhs = sp.sympify(lhs_str.replace("^", "**"))
            rhs = sp.sympify(rhs_str.replace("^", "**"))
            eq = sp.Eq(lhs, rhs)
        else:
            validate_safe_math_expression(equation_str)
            eq = sp.Eq(sp.sympify(equation_str.replace("^", "**")), 0)
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
    validate_safe_math_expression(reference_formula)
    try:
        expr = sp.sympify(reference_formula.replace("^", "**"))
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
