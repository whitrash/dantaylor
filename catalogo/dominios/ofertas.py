"""Ofertas: un producto, en un comercio, a un precio, con un enlace.

Regla de oro: **ninguna oferta se publica sin un enlace verificado** (vivo, a la
página del producto, con stock y con el precio anunciado). De nada sirve decir
que algo está barato si el enlace está muerto, lleva a la portada o el
producto está agotado. La verificación la hace `core/enlaces.py` sin modelo;
el modelo solo normaliza el nombre, la marca, la presentación y la categoría.
"""

from __future__ import annotations

from ..core.modelos import Item, Registro
from ..core.taxonomia import Taxonomia
from ..core.texto import clave_texto, leer_numero, normalizar_medida, primero
from .base import Dominio, nullable, opciones, texto

UNIDADES = ["g", "ml", "unidad", "desconocida"]

TAXONOMIA = Taxonomia(
    {
        "Alimentos": {
            "Lácteos": ["leche", "yogur", "yogurt", "queso", "manteca", "crema", "dulce de leche"],
            "Almacén": [
                "arroz",
                "fideos",
                "harina",
                "aceite",
                "azúcar",
                "yerba",
                "café",
                "té",
                "galletitas",
                "conserva",
                "atún",
                "mermelada",
                "puré",
                "sal",
                "polenta",
                "lentejas",
            ],
            "Bebidas": ["gaseosa", "agua", "jugo", "cerveza", "vino", "fernet", "soda", "bebida"],
            "Carnes y pescados": ["carne", "pollo", "pescado", "milanesa", "hamburguesa", "asado", "cerdo"],
            "Frutas y verduras": ["banana", "manzana", "papa", "tomate", "lechuga", "cebolla", "naranja", "zanahoria"],
            "Panificados": ["pan", "facturas", "tostadas", "budín", "prepizza"],
            "Congelados": ["helado", "congelado", "papas fritas congeladas", "nuggets"],
            "Snacks y golosinas": ["chocolate", "alfajor", "papas fritas", "caramelos", "chicle", "snack", "turrón"],
        },
        "Limpieza": {
            "Lavandería": ["jabón en polvo", "jabón líquido", "suavizante", "lavandina", "quitamanchas"],
            "Limpieza del hogar": [
                "detergente",
                "limpiador",
                "desinfectante",
                "esponja",
                "papel higiénico",
                "rollo de cocina",
                "bolsas de residuos",
                "lustramuebles",
            ],
        },
        "Cuidado personal": {
            "Higiene": ["shampoo", "acondicionador", "jabón", "desodorante", "pasta dental", "cepillo", "afeitadora"],
            "Bebés": ["pañales", "toallitas húmedas", "leche infantil"],
            "Farmacia": ["analgésico", "protector solar", "vitaminas", "alcohol en gel"],
        },
        "Librería y papelería": {
            "Útiles": ["cuaderno", "lapicera", "lápiz", "resma", "marcador", "cartuchera", "mochila", "carpeta"],
            "Libros": ["libro", "novela", "manual", "diccionario"],
        },
        "Hogar y bazar": {
            "Cocina": ["olla", "sartén", "vaso", "plato", "cubiertos", "jarra", "termo"],
            "Electro": [
                "televisor",
                "smart tv",
                "heladera",
                "lavarropas",
                "microondas",
                "pava eléctrica",
                "auriculares",
                "celular",
                "notebook",
                "ventilador",
            ],
        },
        "Mascotas": {
            "Alimento para mascotas": ["alimento para perro", "alimento para gato", "balanceado", "piedritas"],
        },
        "Otros": {"Otros productos": []},
    }
)


class Ofertas(Dominio):
    nombre = "ofertas"
    tema = "productos y ofertas de supermercados, librerías y comercios"
    version_prompt = "1"
    ttl_dias = None  # la ficha (nombre, marca, categoría) no vence; lo que vence es el ENLACE
    taxonomia = TAXONOMIA
    facetas = ("comercio", "marca")
    prioridad_fuentes = {"relevamiento": 3, "sitio": 2, "web": 1}
    campos_busqueda = ("producto", "categoria", "marca", "presentacion")
    politica_web = "nunca"  # la web la mira el verificador de enlaces, no el modelo
    campo_enlace = "enlace"
    campo_producto = "producto"
    campo_precio = "precio"
    exige_enlace = True
    max_edad_enlace_horas = 24.0
    reglas = """
- "producto": nombre limpio y completo: marca + producto + variante, sin el precio ni el comercio. Ej.: "Leche entera La Serenísima 1 L".
- "marca": la marca comercial; cadena vacía si no se sabe.
- "presentacion": tamaño o cantidad tal como se vende ("1,5 L", "500 g", "pack x 6", "unidad").
- "contenido" y "unidad": cantidad en gramos o mililitros si se puede deducir de la presentación ("1,5 L" -> 1500, "ml"; "500 g" -> 500, "g"); "unidad" con el número de unidades para lo que se vende por unidad; null y "desconocida" si no se sabe. Nunca inventes.
- No corrijas el precio ni el enlace: vienen del registro y los verifica otro paso.
"""

    def normalizar(self, fila: dict) -> dict:
        producto = primero(fila, "producto", "nombre", "titulo", "título", "descripcion", "item", "articulo")
        if not producto:
            return {}
        datos: dict = {"producto": producto}
        comercio = primero(fila, "comercio", "tienda", "supermercado", "negocio", "local", "cadena", "vendedor")
        if comercio:
            datos["comercio"] = comercio
        precio = leer_numero(primero(fila, "precio", "precio_oferta", "price", "importe"))
        if precio is not None and precio > 0:
            datos["precio"] = precio
        anterior = leer_numero(primero(fila, "precio_anterior", "precio_lista", "precio_regular", "antes"))
        if anterior is not None and anterior > 0:
            datos["precio_anterior"] = anterior
        enlace = primero(fila, "enlace", "link", "url", "url_producto", "href")
        if enlace:
            datos["enlace"] = enlace
        for campo, alias in (
            ("marca", ("marca", "brand")),
            ("presentacion", ("presentacion", "presentación", "contenido", "formato", "cantidad")),
            ("ean", ("ean", "codigo_barras", "código_barras", "gtin", "sku", "codigo")),
            ("vigencia_hasta", ("vigencia_hasta", "hasta", "vigencia", "valido_hasta", "válido_hasta")),
            ("sucursal", ("sucursal", "ciudad", "zona")),
        ):
            valor = primero(fila, *alias)
            if valor:
                datos[campo] = valor
        imagen = primero(fila, "imagen_url", "imagen", "foto", "image_url")
        if imagen:
            datos["imagen_url" if imagen.startswith(("http://", "https://")) else "imagen_archivo"] = imagen
        return datos

    def clave(self, datos: dict) -> str:
        comercio = clave_texto(datos.get("comercio") or "")
        identidad = clave_texto(datos["ean"]) if datos.get("ean") else clave_texto(datos["producto"])
        return f"{comercio}--{identidad}" if comercio else identidad

    def propiedades(self) -> dict[str, dict]:
        return {
            "producto": texto("Marca + producto + variante, sin precio ni comercio."),
            "marca": texto("Marca comercial; vacío si no se sabe."),
            "presentacion": texto("Tamaño o cantidad tal como se vende."),
            "contenido": nullable({"type": "number"}),
            "unidad": opciones(UNIDADES),
        }

    # --- catálogo --------------------------------------------------------

    def titulo(self, registro: Registro) -> str:
        producto = registro.analisis.get("producto") or registro.item.datos.get("producto")
        comercio = registro.item.datos.get("comercio")
        return f"{producto} · {comercio}" if comercio else str(producto)

    def titulo_item(self, item: Item) -> str:
        producto = item.datos.get("producto") or item.clave
        comercio = item.datos.get("comercio")
        return f"{producto} · {comercio}" if comercio else str(producto)

    def enriquecer(self, registro: Registro, enlace: dict | None = None) -> dict:
        datos = registro.item.datos
        extra: dict = {
            "comercio": datos.get("comercio"),
            "precio": datos.get("precio"),
            "precio_anterior": datos.get("precio_anterior"),
            "enlace": datos.get("enlace"),
            "verificacion": enlace,
        }
        precio = datos.get("precio")
        anterior = datos.get("precio_anterior")
        if isinstance(precio, (int, float)) and isinstance(anterior, (int, float)) and anterior > precio > 0:
            extra["descuento_pct"] = round((anterior - precio) / anterior * 100)
        unitario = self.precio_unitario(registro)
        if unitario:
            extra["precio_unitario"], extra["unidad_precio"] = unitario
        return extra

    def precio_unitario(self, registro: Registro) -> tuple[float, str] | None:
        """($ por kg / L / unidad) a partir de contenido+unidad de la ficha (o de la presentación)."""
        precio = registro.item.datos.get("precio")
        if not isinstance(precio, (int, float)) or precio <= 0:
            return None
        contenido = registro.analisis.get("contenido")
        unidad = registro.analisis.get("unidad")
        if not isinstance(contenido, (int, float)) or contenido <= 0 or unidad not in ("g", "ml", "unidad"):
            medida = normalizar_medida(registro.item.datos.get("presentacion"))
            if not medida or medida[1] not in ("g", "ml"):
                return None
            contenido, unidad = medida
        if unidad == "unidad":
            return round(precio / contenido, 2), "unidad"
        return round(precio / contenido * 1000, 2), ("kg" if unidad == "g" else "L")

    def bloqueos(self, registro: Registro, enlace: dict | None = None) -> list[str]:
        motivos = []
        if not isinstance(registro.item.datos.get("precio"), (int, float)):
            motivos.append("sin precio")
        return motivos + super().bloqueos(registro, enlace)

    def clave_orden(self, registro: Registro) -> tuple:
        # Dentro de cada categoría, lo más barato por kilo/litro primero; sin medida, por precio.
        unitario = self.precio_unitario(registro)
        precio = registro.item.datos.get("precio")
        return (
            0 if unitario else 1,
            unitario[0] if unitario else (precio if isinstance(precio, (int, float)) else 10**9),
            clave_texto(self.titulo(registro)),
        )

    def valores_faceta(self, registro: Registro, faceta: str) -> list[str]:
        if faceta == "comercio":
            comercio = registro.item.datos.get("comercio")
            return [str(comercio)] if comercio else []
        return super().valores_faceta(registro, faceta)
