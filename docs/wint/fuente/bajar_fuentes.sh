#!/usr/bin/env bash
# Baja las tipografías (licencia OFL, repositorio google/fonts) y crea instancias estáticas
# en ../fonts/static, que es donde las busca estilo.css. Requiere curl y: pip install fonttools
set -euo pipefail
cd "$(dirname "$0")/.." && mkdir -p fonts/static && cd fonts
B=https://raw.githubusercontent.com/google/fonts/main/ofl
for f in "cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf" "cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf" \
         "ebgaramond/EBGaramond%5Bwght%5D.ttf" "ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf" "jost/Jost%5Bwght%5D.ttf" \
         "ibmplexmono/IBMPlexMono-Regular.ttf" "ibmplexmono/IBMPlexMono-Medium.ttf" "ibmplexmono/IBMPlexMono-Bold.ttf"; do
  curl -sSfL -o "$(basename "$f" | sed 's/%5B/[/; s/%5D/]/')" "$B/$f"
done
cp IBMPlexMono-*.ttf static/
python3 - <<'PY'
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
for src, base, pesos in [("CormorantGaramond[wght].ttf", "CormorantGaramond", [500, 600, 700]),
                         ("CormorantGaramond-Italic[wght].ttf", "CormorantGaramond-Italic", [500, 600]),
                         ("EBGaramond[wght].ttf", "EBGaramond", [400, 500, 600, 700]),
                         ("EBGaramond-Italic[wght].ttf", "EBGaramond-Italic", [400, 500]),
                         ("Jost[wght].ttf", "Jost", [400, 500, 600])]:
    for w in pesos:
        instancer.instantiateVariableFont(TTFont(src), {"wght": w}, inplace=False).save(f"static/{base}-{w}.ttf")
PY
echo "Listo: fonts/static"
