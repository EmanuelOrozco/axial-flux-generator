#!/usr/bin/env bash
# Regenera gráficas, piezas y valores del modelo, y compila los documentos PDF en docs/.
#
# Uso:  ./docs/compilar_pdf.sh            (todos los documentos)
#       ./docs/compilar_pdf.sh 01_marco_teorico
set -euo pipefail

DOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(dirname "$DOCS")"
FUENTES="$DOCS/latex"
COMPILACION="$FUENTES/build"

# Fecha fija en los metadatos: recompilar sin cambios en las fuentes produce PDF idénticos.
if [ -z "${SOURCE_DATE_EPOCH:-}" ]; then
  SOURCE_DATE_EPOCH="$(git -C "$RAIZ" log --max-parents=0 --format=%ct 2>/dev/null | tail -1 || true)"
fi
if [ -n "$SOURCE_DATE_EPOCH" ]; then export SOURCE_DATE_EPOCH; else unset SOURCE_DATE_EPOCH; fi

cd "$RAIZ"
uv run generador-axial todo > /dev/null

documentos=("$@")
if [ ${#documentos[@]} -eq 0 ]; then
  documentos=(01_marco_teorico 02_memoria_de_calculo 03_guia_fabricacion 04_arquitectura_software 05_modelo_realista 06_presentacion)
fi

mkdir -p "$COMPILACION"
cd "$FUENTES"
for documento in "${documentos[@]}"; do
  echo "Compilando $documento.pdf ..."
  for _ in 1 2; do
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$COMPILACION" "$documento.tex" > "$COMPILACION/$documento.salida" \
      || { tail -40 "$COMPILACION/$documento.log"; exit 1; }
  done
  cp "$COMPILACION/$documento.pdf" "$DOCS/$documento.pdf"
done
echo "PDF disponibles en $DOCS"
