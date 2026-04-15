#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Uso: ./generate_video.sh \"<ECUACION_ANTERIOR>\" \"<ECUACION_NUEVA>\" \"<DESCRIPCION>\""
    echo "Ejemplo: ./generate_video.sh \"6*x = -26\" \"x = -26/6\" \"Dividir por 6\""
    exit 1
fi

export EQ_OLD="$1"
export EQ_NEW="$2"
export DESC="$3"

echo "========================================="
echo " Renderizando transición matemática..."
echo " Antes: $EQ_OLD"
echo " Después: $EQ_NEW"
echo " Heurística: $DESC"
echo "========================================="

# Ejecutamos Manim:
# -ql: Quality Low (480p15), indispensable para mitigar la latencia de renderizado
#      en interacciones semi-tiempo-real (Tutor LLM).
# --disable_caching: Previene conflictos de caché si reutilizamos la misma clase
manim -ql --disable_caching renderer.py EquationTransition

echo "Video generado en: media/videos/renderer/480p15/EquationTransition.mp4"
