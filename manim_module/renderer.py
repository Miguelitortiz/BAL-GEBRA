from manim import *
import os
import re

# To allow math-like LaTeX formatting out of SymPy's string outputs
def clean_latex(eq_str):
    # Remove literal multiplication asterisks
    eq_str = eq_str.replace("*", "")
    return eq_str

class EquationTransition(Scene):
    def construct(self):
        # 1. Parámetros de entrada dinámicos desde CLI/Env
        eq_old_str = os.environ.get("EQ_OLD", "3x - 2 = x + 4")
        eq_new_str = os.environ.get("EQ_NEW", "3x = x + 6")
        desc = os.environ.get("DESC", "Sumar 2 a ambos lados")

        eq_old_latex = clean_latex(eq_old_str)
        eq_new_latex = clean_latex(eq_new_str)

        # 2. Elementos visuales
        # El título en la parte superior explica la pista/heurística (empatía cognitiva)
        title = Text(desc, font_size=28, color=BLUE).to_edge(UP)
        self.play(FadeIn(title, shift=DOWN), run_time=0.8)

        # Usamos MathTex interactivo
        eq1 = MathTex(eq_old_latex, font_size=96)
        eq2 = MathTex(eq_new_latex, font_size=96)

        # 3. Presentamos la ecuación previa
        self.play(Write(eq1), run_time=1.2)
        self.wait(0.5)
        
        # 4. Magia Neuro-Simbólica: Transición Coherente
        # TransformMatchingShapes mapea las partes idénticas (como la 'x' o el '=' o los números) 
        # y las desplaza físicamente por la pantalla mientras desaparece/aparece lo diferente.
        self.play(TransformMatchingShapes(eq1, eq2), run_time=2.0)
        self.wait(1.5)
