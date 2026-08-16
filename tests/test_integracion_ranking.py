"""El ajuste del ranking, sin base de datos.

Se prueba 'aplicar_requisitos' por separado justamente para poder hacerlo sin
levantar MySQL ni cargar el modelo de embeddings. La prueba de extremo a
extremo con datos reales es manual y va en la tarea 9.
"""

from match import aplicar_requisitos

OFERTA = "Requisitos\n- Minimo 5 anos de experiencia.\n"

CV_JUNIOR = "EXPERIENCIA\nDesarrollador en Acme (2024-2026).\n"
CV_SENIOR = "EXPERIENCIA\nDesarrollador en Acme (2016-2026).\n"
CV_MUDO = "PERFIL\nDesarrollador backend.\n"


def test_el_junior_baja_y_el_senior_no():
    filas = [
        {"id": 1, "nombre": "Junior", "score": 0.60},
        {"id": 2, "nombre": "Senior", "score": 0.55},
    ]
    textos = {1: CV_JUNIOR, 2: CV_SENIOR}

    ajustadas = aplicar_requisitos(filas, OFERTA, textos)
    por_nombre = {f["nombre"]: f for f in ajustadas}

    assert por_nombre["Junior"]["penalizacion"] > 0
    assert por_nombre["Senior"]["penalizacion"] == 0.0
    assert por_nombre["Senior"]["score_ajustado"] > por_nombre["Junior"]["score_ajustado"]


def test_el_score_original_no_se_toca():
    filas = [{"id": 1, "nombre": "Junior", "score": 0.60}]
    ajustadas = aplicar_requisitos(filas, OFERTA, {1: CV_JUNIOR})

    assert ajustadas[0]["score"] == 0.60
    assert ajustadas[0]["score_ajustado"] < 0.60


def test_el_candidato_sin_dato_queda_intacto():
    filas = [{"id": 1, "nombre": "Mudo", "score": 0.50}]
    ajustadas = aplicar_requisitos(filas, OFERTA, {1: CV_MUDO})

    assert ajustadas[0]["penalizacion"] == 0.0
    assert ajustadas[0]["score_ajustado"] == 0.50
    assert ajustadas[0]["avisos"] == []


def test_oferta_sin_requisitos_no_cambia_nada():
    filas = [{"id": 1, "nombre": "Junior", "score": 0.60}]
    ajustadas = aplicar_requisitos(filas, "Frontend React\nNos importa el criterio.\n", {1: CV_JUNIOR})

    assert ajustadas[0]["score_ajustado"] == 0.60
    assert ajustadas[0]["avisos"] == []
