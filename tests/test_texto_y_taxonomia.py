from catalogo.core.taxonomia import Taxonomia
from catalogo.core.texto import clave_texto, normalizar_medida
from catalogo.dominios.animales import TAXONOMIA


def test_clave_texto_ignora_acentos_mayusculas_y_signos():
    assert clave_texto("  León Africano ") == "leon-africano"
    assert clave_texto("Ñandú!!") == "nandu"
    assert clave_texto(None) == ""


def test_normalizar_medida_lleva_a_unidad_base():
    assert normalizar_medida("1,5 kg") == (1500.0, "g")
    assert normalizar_medida("3 m") == (300.0, "cm")
    assert normalizar_medida("150 t") == (150_000_000.0, "g")
    assert normalizar_medida("500 ml") == (500.0, "ml")
    assert normalizar_medida("1 L") == (1000.0, "ml")
    assert normalizar_medida("grande") is None
    assert normalizar_medida("5 parsecs") is None


def test_hojas_en_orden_de_declaracion():
    t = Taxonomia({"A": {"A1": [], "A2": []}, "B": {"B1": {"B1a": []}}})
    assert t.hojas() == ["A > A1", "A > A2", "B > B1 > B1a"]
    assert t.posicion("A > A2") == 1
    assert t.posicion("no existe") == 3
    assert t.es_valida("B > B1 > B1a") and not t.es_valida("B > B1")


def test_sugerir_por_palabras_clave():
    assert TAXONOMIA.sugerir("Oso panda") == "Mamíferos > Osos"
    assert TAXONOMIA.sugerir("Yacaré overo") == "Reptiles > Cocodrilos"
    # gana la palabra que aparece primero en el texto
    assert TAXONOMIA.sugerir("tiburón ballena") == "Peces > Tiburones y rayas"
    # palabra entera: "raya" no matchea dentro de "rayado"
    assert TAXONOMIA.sugerir("pez rayado") == "Peces > Peces óseos"
    assert TAXONOMIA.sugerir("algo desconocido") is None


def test_describir_es_estable_y_jerarquico():
    texto = TAXONOMIA.describir()
    assert texto == TAXONOMIA.describir()
    assert texto.startswith("- Mamíferos\n  - Felinos (p. ej.: león, tigre")
