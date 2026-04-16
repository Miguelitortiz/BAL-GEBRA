from manim import *
import os

# ─── helpers ─────────────────────────────────────────────────────────────────

def clean_latex(eq_str: str) -> str:
    """Convierte el string de SymPy a LaTeX presentable."""
    s = eq_str.replace("*", " \\cdot ")   # × simbólico
    s = s.replace("**", "^")              # exponentes
    return s

def op_annotation(accion: str, desc: str) -> str:
    """
    Devuelve un string LaTeX corto que representa la operación matemática.
    Ej: 'dividir_coeficiente' → '\\div k'
    """
    mapping = {
        "dividir_coeficiente":        r"\div\, k",
        "mover_constante_lhs":        r"- c \text{ en ambos lados}",
        "mover_variable_rhs":         r"\text{mover } x \text{ al LHS}",
        "eliminar_denominador":       r"\times \text{MCM}",
        "eliminar_denominador_simbolico": r"\times x",
        "aplicar_distributiva":       r"\text{distributiva}",
        "reducir_semejantes":         r"\text{reducir semejantes}",
        "simplificar_constantes":     r"\text{simplificar}",
        "simplificar_fraccion":       r"\text{simplificar fracción}",
        "voltear_ecuacion":           r"\text{voltear}",
    }
    return mapping.get(accion, r"\text{" + desc[:30] + "}")

# ─── scene ───────────────────────────────────────────────────────────────────

class EquationTransition(Scene):
    def construct(self):
        # ── parámetros desde variables de entorno ────────────────────────────
        eq_old_str = os.environ.get("EQ_OLD", "3x - 1 = 8")
        eq_new_str = os.environ.get("EQ_NEW", "3x = 9")
        desc       = os.environ.get("DESC", "Sumar 1 a ambos lados")
        accion     = os.environ.get("OP_ACCION", "")

        old_tex = clean_latex(eq_old_str)
        new_tex = clean_latex(eq_new_str)
        ann_tex = op_annotation(accion, desc)
        
        # ── colores ──────────────────────────────────────────────────────────
        C_OLD  = WHITE
        C_OP   = YELLOW
        C_NEW  = GREEN
        C_TITLE = BLUE_B

        # ── título ───────────────────────────────────────────────────────────
        title = Text(desc, font_size=28, color=C_TITLE).to_edge(UP, buff=0.3)
        self.play(FadeIn(title), run_time=0.5)

        # ── ecuación original ─────────────────────────────────────────────────
        eq1 = MathTex(old_tex, font_size=72, color=C_OLD)
        eq1.move_to(UP * 1.2)
        self.play(Write(eq1), run_time=1.0)
        self.wait(0.3)

        # ── bloque de operación: [ old ] OP ──────────────────────────────────
        # Creamos los corchetes de "ambos lados"
        brace_l = MathTex(r"\big[", font_size=72, color=C_OP)
        brace_r = MathTex(r"\big]", font_size=72, color=C_OP)
        brace_l.next_to(eq1,  LEFT,  buff=0.15)
        brace_r.next_to(eq1,  RIGHT, buff=0.15)

        # Texto de la operación centrado debajo de la eq1
        op_label = MathTex(ann_tex, font_size=40, color=C_OP)
        op_label.next_to(eq1, DOWN, buff=0.4)

        self.play(
            FadeIn(brace_l, shift=RIGHT*0.15),
            FadeIn(brace_r, shift=LEFT*0.15),
            Write(op_label),
            run_time=0.8,
        )
        self.wait(0.4)

        # ── flecha descendente ────────────────────────────────────────────────
        arrow = Arrow(
            start=op_label.get_bottom() + DOWN * 0.1,
            end=op_label.get_bottom()   + DOWN * 1.0,
            color=C_OP, stroke_width=4, buff=0,
        )
        self.play(GrowArrow(arrow), run_time=0.5)

        # ── ecuación resultado ────────────────────────────────────────────────
        eq2 = MathTex(new_tex, font_size=72, color=C_NEW)
        eq2.next_to(arrow, DOWN, buff=0.25)

        self.play(TransformFromCopy(eq1, eq2), run_time=1.8)
        self.wait(0.5)

        # ── resaltar la diferencia limpiando el ruido visual ─────────────────
        self.play(
            FadeOut(brace_l), FadeOut(brace_r),
            FadeOut(op_label), FadeOut(arrow),
            FadeOut(title),
            eq1.animate.fade(0.6),   # atenúa la vieja
            run_time=0.7,
        )
        self.wait(1.2)
