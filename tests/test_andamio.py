"""Verifica que pytest encuentra los modulos de la raiz del proyecto.

Si esta prueba falla con ImportError, el problema es el sys.path y no el
codigo: pytest se ejecuta desde la raiz para que la raiz este en el path.
"""


def test_pytest_importa_modulos_de_la_raiz():
    import extract_text

    assert hasattr(extract_text, "extraer_texto")
