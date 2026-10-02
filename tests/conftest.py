import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalogo.core.almacen import Almacen  # noqa: E402

EJEMPLOS = RAIZ / "ejemplos"


@pytest.fixture
def almacen():
    a = Almacen(":memory:")
    yield a
    a.cerrar()
