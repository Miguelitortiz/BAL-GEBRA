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
        # Título descriptivo en la parte superior
        title = Text("Aplicando transición:", font_size=32, color=BLUE).to_edge(UP)
        self.play(FadeIn(title, shift=DOWN), run_time=0.8)

        # Usamos MathTex interactivo (bajamos un poco el tamaño para acomodar ambas de forma vertical)
        eq1 = MathTex(eq_old_latex, font_size=76)
        eq2 = MathTex(eq_new_latex, font_size=76)

        # Ubicamos la vieja arriba y la nueva abajo
        eq1.next_to(title, DOWN, buff=1.0)
        
        # 3. Presentamos la ecuación original
        self.play(Write(eq1), run_time=1.2)
        self.wait(0.5)
        
        # 4. Flecha descriptiva indicando la manipulación
        arrow = Arrow(UP, DOWN, color=YELLOW).next_to(eq1, DOWN, buff=0.5)
        operation_text = Text(desc, font_size=24, color=YELLOW).next_to(arrow, RIGHT, buff=0.2)
        
        self.play(GrowArrow(arrow), Write(operation_text), run_time=1.0)
        self.wait(0.5)

        eq2.next_to(arrow, DOWN, buff=0.5)

        # 5. Magia Pedagógica: TransformFromCopy en formato vertical
        # Toma la ecuación 1, clona sus letras y las empuja hacia abajo acomodándolas
        # en la ecuación 2, enfatizando qué símbolos sobrevivieron, se movieron o mutaron.
        self.play(TransformFromCopy(eq1, eq2), run_time=2.0)
        self.wait(1.5)
