#!/usr/bin/env python3
"""
sympy_engine.py — Motor simbólico puro para el solver híbrido Go+Python.

Protocolo (por línea):
  stdin  → JSON: {"accion": "<accion>", "ecuacion": "<lhs>=<rhs>"}
  stdout → JSON: {"valido": bool, "resultado": "<lhs>=<rhs>",
                  "descripcion": "<texto>", "error": "<msg>"}

RESTRICCIONES:
  - NO usa solve() para encontrar soluciones directamente.
  - NO toma decisiones heurísticas.
  - SOLO aplica UNA transformación atómica por llamada.

DISEÑO:
  - parse_equation usa evaluate=False para preservar la estructura original.
  - eq_to_str usa as_numer_denom() para mantener fracciones intactas.
  - Esto permite separar "aplicar distributiva" de "eliminar denominador".
"""

import sys
import json
import re

from sympy import (
    Symbol, expand, expand_mul, collect, simplify,
    Mul, Add, Pow, Rational, S, nsimplify, preorder_traversal
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)

x = Symbol('x')
TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


# ---------------------------------------------------------------------------
# PARSING / SERIALIZACIÓN
# ---------------------------------------------------------------------------

def parse_equation(eq_str: str, evaluate: bool = False):
    """
    Parsea 'lhs = rhs'.
    evaluate=False preserva la estructura (no simplifica 2/8 ni 1-3+0).
    """
    eq_str = eq_str.strip()
    idx = eq_str.index('=')
    lhs = parse_expr(eq_str[:idx].strip(), transformations=TRANSFORMATIONS,
                     evaluate=evaluate)
    rhs = parse_expr(eq_str[idx + 1:].strip(), transformations=TRANSFORMATIONS,
                     evaluate=evaluate)
    return lhs, rhs


def fmt_expr(expr) -> str:
    """
    Representa una expresión manteniendo fracciones y estructuras sin evaluar.
    - Si es un Mul que contiene un Add (e.g. 2*(3x+5)/8 o (6x+10)/8):
      usa str() directamente para no perder la estructura.
    - Para el resto: usa as_numer_denom() para agrupar la fracción.
    """
    # Preservar Mul-con-Add sin evaluar (evita que 2*(3x+5)/8 → 3x/4+5/4)
    if isinstance(expr, Mul) and any(isinstance(f, Add) for f in expr.args):
        return str(expr)
    # Resto: forma canónica numer/denom
    n, d = expr.as_numer_denom()
    if d == 1:
        return str(n)
    n_str = f"({n})" if isinstance(n, Add) else str(n)
    return f"{n_str}/{d}"


def eq_to_str(lhs, rhs) -> str:
    return f"{fmt_expr(lhs)} = {fmt_expr(rhs)}"


# ---------------------------------------------------------------------------
# VALIDACIÓN ALGEBRAICA
# ---------------------------------------------------------------------------

def validate(lhs_orig, rhs_orig, lhs_new, rhs_new) -> bool:
    """
    Verifica equivalencia:
    - Aceptar transformaciones exactas.
    - Aceptar multiplicación por escalar numérico constante.
    - Aceptar multiplicación por polinomio en x (e.g. multiplicar por x
      para eliminar denominador variable), siempre que el resultado
      del ratio sea un polinomio sin denominador (sin Pow negativo).
    """
    diff_orig = simplify(lhs_orig - rhs_orig)
    diff_new  = simplify(lhs_new  - rhs_new)

    if simplify(diff_orig - diff_new) == 0:
        return True
    try:
        ratio = simplify(diff_new / diff_orig)
        # Caso escalar numérico
        if not ratio.free_symbols:
            return ratio != 0
        # Caso multiplicación por polinomio en x:
        # el ratio es válido si su denominador es 1 (no introduce fracciones nuevas)
        from sympy import cancel
        ratio_c = cancel(ratio)
        _, d = ratio_c.as_numer_denom()
        if simplify(d) == 1 and ratio_c != 0:
            return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# UTILITARIOS
# ---------------------------------------------------------------------------

def compute_lcm(lhs, rhs):
    """MCM de denominadores numéricos en la ecuación."""
    from sympy import lcm as sym_lcm
    denoms = set()
    for expr in [lhs, rhs]:
        for sub in preorder_traversal(expr):
            try:
                _, d = sub.as_numer_denom()
                d_eval = simplify(d)
                if d_eval != 1 and not d_eval.free_symbols:
                    denoms.add(abs(d_eval))
            except Exception:
                pass
    if not denoms:
        return S.One
    result = list(denoms)[0]
    for d in list(denoms)[1:]:
        result = sym_lcm(result, d)
    return result


def _is_pure_arithmetic(s: str) -> bool:
    """True si 's' no contiene variables (solo números y operadores)."""
    return not re.search(r'[a-zA-Z]', s)


def _looks_unsimplified(raw: str, expr) -> bool:
    """
    True si el string raw parece tener aritmética sin reducir
    (tiene +/- entre numbers) y la representación evaluada difiere.
    """
    # Must be pure arithmetic
    if not _is_pure_arithmetic(raw):
        return False
    # Must have multiple terms (not just a single number)
    if not re.search(r'[\+\-]', raw.strip()):
        return False
    evaluated = str(simplify(expr))
    # Compare normalized strings
    return raw.replace(' ', '') != evaluated.replace(' ', '')


# ---------------------------------------------------------------------------
# ACCIONES ATÓMICAS
# ---------------------------------------------------------------------------

def accion_simplificar_constantes(lhs_uneval, rhs_uneval, eq_str_raw: str):
    """
    Paso 0: Evalúa aritmética constante en los lados de la ecuación.
    Separamos la simplificación de constantes (1-3+0 → -2) de cualquier
    transformación algebraica sobre términos con x.
    """
    idx = eq_str_raw.index('=')
    lhs_raw = eq_str_raw[:idx].strip()
    rhs_raw = eq_str_raw[idx + 1:].strip()

    changes = []

    # Para el lado con variables: devolver SIN evaluar (preservar 2*(3x+5)/8)
    # Para el lado puramente aritmético: evaluar y describir
    new_lhs = lhs_uneval  # conservar estructura por defecto
    new_rhs = rhs_uneval

    if _looks_unsimplified(rhs_raw, rhs_uneval):
        val = simplify(rhs_uneval)
        changes.append(f"Calcular {rhs_raw.strip()} = {val}")
        new_rhs = val  # sólo aquí simplificamos

    if _looks_unsimplified(lhs_raw, lhs_uneval):
        val = simplify(lhs_uneval)
        changes.append(f"Calcular {lhs_raw.strip()} = {val}")
        new_lhs = val  # sólo aquí simplificamos

    if not changes:
        return new_lhs, new_rhs, None   # None → no-op

    return new_lhs, new_rhs, "Aritmética: " + "; ".join(changes)


def accion_aplicar_distributiva(lhs, rhs):
    """
    Paso 1: Multiplica el coeficiente por los términos del paréntesis
    SIN eliminar el denominador.
    Ejemplo: 2*(3x+5)/8  →  (6x+10)/8   (no simplifica 6/8)
    Retorna None si no hay nada que distribuir.
    """
    # First, check if there is actually something to distribute
    def find_distributable(expr):
        """Find first Mul containing an Add in its numerator."""
        n_top, _ = expr.as_numer_denom()
        for sub in preorder_traversal(n_top):
            if isinstance(sub, Mul) and not sub.is_number:
                if any(isinstance(f, Add) for f in sub.args):
                    return sub
        return None

    target_lhs = find_distributable(lhs)
    target_rhs = find_distributable(rhs)

    if target_lhs is None and target_rhs is None:
        return lhs, rhs, None  # no-op: nothing to distribute

    def distribute_numerator(expr):
        """Distribuye en el numerador manteniendo el denominador intacto."""
        n, d = expr.as_numer_denom()
        n_expanded = expand_mul(n)   # distributiva pura en el numerador
        if d == 1:
            return n_expanded
        return Mul(n_expanded, Pow(d, -1, evaluate=False), evaluate=False)

    new_lhs = distribute_numerator(lhs)
    new_rhs = distribute_numerator(rhs)

    # Build explicit description from the found target
    target = target_lhs or target_rhs
    adds    = [f for f in target.args if isinstance(f, Add)]
    scalars = [f for f in target.args if f.is_number]
    if adds and scalars:
        c  = scalars[0]
        pa = adds[0]
        desc = (f"Multiplicar {c} por cada término de ({pa}): "
                f"{c}·({pa}) = {expand_mul(target)}")
    else:
        desc = "Aplicar propiedad distributiva"

    return new_lhs, new_rhs, desc


def accion_eliminar_denominador(lhs, rhs):
    """
    Paso 2: Multiplica ambos lados por el MCM de los denominadores
    para eliminar fracciones.
    """
    # Compute MCM on the UNevaluated form to find the true denominator.
    # e.g. 2*(3x+5)/8 → denom=8, not 4 (which simplify() would give).
    mcm = compute_lcm(lhs, rhs)
    if mcm == S.One:
        # Try with evaluated form as fallback
        lhs_e = simplify(lhs)
        rhs_e = simplify(rhs)
        mcm = compute_lcm(lhs_e, rhs_e)
        if mcm == S.One:
            return lhs_e, rhs_e, None  # no-op
    else:
        lhs_e = simplify(lhs)
        rhs_e = simplify(rhs)

    new_lhs = expand(lhs_e * mcm)
    new_rhs = expand(rhs_e * mcm)
    return new_lhs, new_rhs, (
        f"Multiplicar ambos lados por {mcm} "
        f"para eliminar el denominador"
    )


def accion_eliminar_denominador_simbolico(lhs, rhs):
    """
    Paso 2b: Multiplica por el MCM de denominadores que contienen x
    (e.g. 3/x = 1 → ×x → 3 = x).
    Nota: introduce la restricción de dominio (denominador ≠ 0).
    """
    from sympy import lcm as sym_lcm
    denoms = set()
    for expr in [simplify(lhs), simplify(rhs)]:
        for sub in preorder_traversal(expr):
            try:
                _, d = sub.as_numer_denom()
                d_s = simplify(d)
                if d_s != 1 and d_s.free_symbols:   # denom con variable
                    denoms.add(d_s)
            except Exception:
                pass

    if not denoms:
        return lhs, rhs, None  # no-op

    mcm = list(denoms)[0]
    for d in list(denoms)[1:]:
        mcm = sym_lcm(mcm, d)

    lhs_e = simplify(lhs)
    rhs_e = simplify(rhs)
    new_lhs = expand(lhs_e * mcm)
    new_rhs = expand(rhs_e * mcm)
    return new_lhs, new_rhs, (
        f"Multiplicar ambos lados por {mcm} para eliminar el denominador "
        f"(restricción de dominio: {mcm} ≠ 0)"
    )


def accion_reducir_semejantes(lhs, rhs):
    """
    Paso 2: Recolecta y suma términos semejantes en cada lado.
    Guarda: se salta si algún lado todavía tiene un Mul-con-Add pendiente
    de distributiva (ej. 2*(3x+5)/8), para no colapsar esa estructura
    antes de que aplicar_distributiva tenga oportunidad de actuar.
    """
    def has_distributable(expr):
        for sub in preorder_traversal(expr):
            if isinstance(sub, Mul) and not sub.is_number:
                if any(isinstance(f, Add) for f in sub.args):
                    return True
        return False

    if has_distributable(lhs) or has_distributable(rhs):
        return lhs, rhs, None  # no-op: esperar a distributiva primero

    lhs_e = simplify(lhs)
    rhs_e = simplify(rhs)
    new_lhs = collect(expand(lhs_e), x)
    new_rhs = collect(expand(rhs_e), x)
    return new_lhs, new_rhs, "Sumar fracciones y reducir términos semejantes"


def accion_voltear_ecuacion(lhs, rhs):
    """
    Paso 3b: Si x está únicamente en el RHS y el LHS es constante,
    voltea la ecuación para que x quede a la izquierda.
    Ejemplos: 3 = x → x = 3  |  5 = 3*x → 3*x = 5
    """
    lhs_e = simplify(lhs)
    rhs_e = simplify(rhs)

    # No-op si LHS ya tiene x, o si RHS no tiene x
    if lhs_e.free_symbols or not rhs_e.free_symbols:
        return lhs_e, rhs_e, None

    return rhs_e, lhs_e, "Voltear la ecuación (x estaba en el lado derecho)"


def accion_mover_constante_lhs(lhs, rhs):
    """
    Paso 4: Suma o resta la constante del LHS en ambos lados
    para dejar solo el término con x.
    """
    lhs_e = simplify(lhs)
    rhs_e = simplify(rhs)
    lhs_exp = expand(lhs_e)

    if not lhs_exp.has(x):
        return lhs_e, rhs_e, None  # no-op, no hay x en LHS

    xcoeff    = lhs_exp.coeff(x)
    const_lhs = expand(lhs_exp - xcoeff * x)

    if const_lhs == 0:
        return lhs_e, rhs_e, None  # no-op

    new_lhs = collect(xcoeff * x, x)
    new_rhs = expand(rhs_e - const_lhs)

    c = nsimplify(abs(const_lhs), rational=True)
    if const_lhs > 0:
        desc = f"Restar {c} de ambos lados (pasar +{c} al otro lado)"
    else:
        desc = f"Sumar {c} a ambos lados (pasar -{c} al otro lado)"
    return new_lhs, new_rhs, desc


def accion_mover_variable_rhs(lhs, rhs):
    """
    Paso 5: Resta el término con x del RHS en ambos lados
    para juntar todas las x en la izquierda.
    """
    lhs_e = simplify(lhs)
    rhs_e = simplify(rhs)
    rhs_exp = expand(rhs_e)

    if not rhs_exp.has(x):
        return lhs_e, rhs_e, None  # no-op

    xcoeff_rhs = rhs_exp.coeff(x)
    if xcoeff_rhs == 0:
        return lhs_e, rhs_e, None  # no-op

    x_term = xcoeff_rhs * x
    new_lhs = collect(expand(lhs_e - x_term), x)
    new_rhs = expand(rhs_e - x_term)

    coef = nsimplify(abs(xcoeff_rhs), rational=True)
    term_str = f"{coef}x" if coef != 1 else "x"
    if xcoeff_rhs > 0:
        desc = f"Restar {term_str} de ambos lados (juntar términos con x a la izquierda)"
    else:
        desc = f"Sumar {term_str} a ambos lados (juntar términos con x a la izquierda)"
    return new_lhs, new_rhs, desc


def accion_dividir_coeficiente(lhs, rhs):
    """
    Paso 8: Divide ambos lados entre el coeficiente de x.
    Si el cociente es una fracción reducible (ej. -26/6),
    devuelve la forma SIN reducir como 4-tupla para que el siguiente
    paso (simplificar_fraccion) la muestre explícitamente.
    """
    from math import gcd as math_gcd

    lhs_e = simplify(lhs)
    rhs_e = simplify(rhs)
    lhs_exp = expand(lhs_e)
    coeff   = lhs_exp.coeff(x)

    if coeff == 0:
        raise ValueError("No hay coeficiente de x en el LHS.")
    if coeff == 1:
        return lhs_e, rhs_e, None  # no-op

    new_lhs = x
    new_rhs = nsimplify(rhs_e / coeff, rational=True)   # forma reducida final

    n, d = nsimplify(coeff, rational=True).as_numer_denom()
    if d == 1:
        desc = ("Multiplicar ambos lados por -1 para aislar x"
                if n == -1
                else f"Dividir ambos lados entre {n} para aislar x")
    else:
        desc = f"Multiplicar ambos lados por {d}/{n} para aislar x"

    # ¿El cociente es una fracción reducible (entero/entero con mcd > 1)?
    # Si es así, devuelve la forma cruda para visualizar la división explícita.
    try:
        rhs_num   = int(rhs_e)      # falla si no es entero
        coeff_num = int(coeff)      # falla si no es entero
        g = math_gcd(abs(rhs_num), abs(coeff_num))
        if g > 1 and coeff_num != -1:
            # 4-tupla: (new_lhs, new_rhs_simplificado, desc, resultado_crudo_str)
            raw_resultado = f"x = {rhs_num}/{coeff_num}"
            return new_lhs, new_rhs, desc, raw_resultado
    except (TypeError, ValueError):
        pass

    return new_lhs, new_rhs, desc


def accion_simplificar_fraccion(lhs, rhs, eq_str_raw: str):
    """
    Paso post-división: Reduce una fracción numérica a su mínima expresión.
    Ejemplo: x = -26/6  →  x = -13/3
    Solo actúa sobre fracciones enteras puras (a/b, sin variables).
    """
    import re
    from math import gcd as math_gcd

    idx = eq_str_raw.index('=')
    lhs_raw = eq_str_raw[:idx].strip()
    rhs_raw = eq_str_raw[idx + 1:].strip()

    _FRAC = re.compile(r'^(-?\d+)/(-?\d+)$')

    def _reducible(s):
        m = _FRAC.match(s.strip())
        if not m:
            return False, None, None
        a, b = int(m.group(1)), int(m.group(2))
        g = math_gcd(abs(a), abs(b))
        return g > 1, a, b

    def _format_reduced(num, den):
        n = num // math_gcd(abs(num), abs(den))
        d = den // math_gcd(abs(num), abs(den))
        if d == 1:
            return str(n)
        if d == -1:
            return str(-n)
        if d < 0:
            return f"{-n}/{-d}"
        return f"{n}/{d}"

    changes = []
    new_lhs = simplify(lhs)
    new_rhs = simplify(rhs)

    ok_r, ar, br = _reducible(rhs_raw)
    if ok_r:
        g = math_gcd(abs(ar), abs(br))
        changes.append(f"Simplificar fracción: {ar}/{br} = {_format_reduced(ar, br)}")

    ok_l, al, bl = _reducible(lhs_raw)
    if ok_l:
        g = math_gcd(abs(al), abs(bl))
        changes.append(f"Simplificar fracción: {al}/{bl} = {_format_reduced(al, bl)}")

    if not changes:
        return new_lhs, new_rhs, None  # no-op

    return new_lhs, new_rhs, "; ".join(changes)


# ---------------------------------------------------------------------------
# ACCIÓN DE VALIDACIÓN EXPLÍCITA (llamada desde Go)
# ---------------------------------------------------------------------------

def accion_validar_ext(eq_orig_str: str, eq_new_str: str) -> dict:
    try:
        lo, ro = parse_equation(eq_orig_str, evaluate=True)
        ln, rn = parse_equation(eq_new_str, evaluate=True)
        ok = validate(lo, ro, ln, rn)
        
        if ok:
            return {"valido": True, "resultado": eq_new_str}
            
        # Clasificador empírico de error
        error_msg = "El paso altera la equivalencia matemática original."
        try:
            e1 = simplify(lo - ro)
            e2 = simplify(ln - rn)

            if not e2.has(x):
                error_msg = "Error grave: La operación eliminó por completo la incógnita 'x'."
            else:
                e1_exp = expand(e1)
                e2_exp = expand(e2)

                c1 = e1_exp.coeff(x)
                c2 = e1_exp - c1 * x
                k1 = e2_exp.coeff(x)
                k2 = e2_exp - k1 * x

                # Identificar si la 'x' se mantuvo intacta y el error es sólo en constantes
                if simplify(c1 - k1) == 0 and simplify(c2 - k2) != 0:
                    error_msg = "Tus términos con 'x' están correctos. Tienes un error de cálculo o de signo en los números libres (constantes)."
                # Identificar si las constantes intactas pero error en 'x'
                elif simplify(c2 - k2) == 0 and simplify(c1 - k1) != 0:
                    error_msg = "Tus constantes están correctas. Tienes un error al reducir o mover los términos con 'x'."
                # Identificar operaciones inversas de despeje (ej. multiplicó en vez de dividir)
                elif c1 != 0 and k1 != 0 and c2 != 0 and k2 != 0:
                    r_x = simplify(c1 / k1)
                    r_c = simplify(c2 / k2)
                    if simplify(r_x * r_c - 1) == 0 or simplify(r_x * r_c + 1) == 0:
                        error_msg = "Cuidado al despejar: Parece que ejecutaste la operación inversa (ej. multiplicaste en vez de dividir)."
        except Exception:
            pass
            
        return {"valido": False, "resultado": "", "error": error_msg}
    except Exception as e:
        return {"valido": False, "resultado": "", "error": f"Error de parseo: {str(e)}"}


# ---------------------------------------------------------------------------
# DESPACHADOR
# ---------------------------------------------------------------------------

def process_request(req: dict) -> dict:
    accion    = req.get("accion", "").strip()
    eq_raw    = req.get("ecuacion", "").strip()

    if accion == "validar":
        return accion_validar_ext(req.get("ecuacion_original", ""), eq_raw)

    try:
        # Parse preserving structure (evaluate=False)
        lhs_u, rhs_u = parse_equation(eq_raw, evaluate=False)
    except Exception as e:
        return {"valido": False, "resultado": "", "error": f"Parse error: {e}"}

    try:
        if accion == "simplificar_constantes":
            result = accion_simplificar_constantes(lhs_u, rhs_u, eq_raw)
        elif accion == "aplicar_distributiva":
            result = accion_aplicar_distributiva(lhs_u, rhs_u)
        elif accion == "eliminar_denominador":
            result = accion_eliminar_denominador(lhs_u, rhs_u)
        elif accion == "eliminar_denominador_simbolico":
            result = accion_eliminar_denominador_simbolico(lhs_u, rhs_u)
        elif accion == "reducir_semejantes":
            result = accion_reducir_semejantes(lhs_u, rhs_u)
        elif accion == "voltear_ecuacion":
            result = accion_voltear_ecuacion(lhs_u, rhs_u)
        elif accion == "mover_constante_lhs":
            result = accion_mover_constante_lhs(lhs_u, rhs_u)
        elif accion == "mover_variable_rhs":
            result = accion_mover_variable_rhs(lhs_u, rhs_u)
        elif accion == "dividir_coeficiente":
            result = accion_dividir_coeficiente(lhs_u, rhs_u)
        elif accion == "simplificar_fraccion":
            result = accion_simplificar_fraccion(lhs_u, rhs_u, eq_raw)
        else:
            return {"valido": False, "resultado": "",
                    "error": f"Acción desconocida: {accion}"}

        # Handling 3-tuple (normal) or 4-tuple (raw result string)
        if len(result) == 4:
            new_lhs, new_rhs, descripcion, raw_resultado = result
        else:
            new_lhs, new_rhs, descripcion = result
            raw_resultado = None

        # None descripcion → action returned no-op (signal via same resultado)
        if descripcion is None:
            return {"valido": True,
                    "resultado": eq_raw,  # identical to input → Go sees no-op
                    "descripcion": ""}

        # Validate algebraic equivalence (evaluate both for comparison)
        lhs_eval = simplify(lhs_u)
        rhs_eval = simplify(rhs_u)
        if not validate(lhs_eval, rhs_eval, simplify(new_lhs), simplify(new_rhs)):
            return {
                "valido": False, "resultado": "",
                "error": "La transformación no preserva la equivalencia algebraica."
            }

        resultado = raw_resultado if raw_resultado else eq_to_str(new_lhs, new_rhs)
        return {"valido": True, "resultado": resultado, "descripcion": descripcion}

    except Exception as e:
        return {"valido": False, "resultado": "", "error": str(e)}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            print(json.dumps({"valido": False, "resultado": "",
                              "error": f"JSON inválido: {e}"}), flush=True)
            continue
        print(json.dumps(process_request(req)), flush=True)


if __name__ == "__main__":
    main()
