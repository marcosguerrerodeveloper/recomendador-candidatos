"""Pruebas de la segmentacion previa a cualquier extraccion."""

from requisitos import secciones_cv, secciones_oferta

CV = """Ana Ruiz Melgar
Desarrolladora Backend Python | 6 anos de experiencia
PERFIL
Ingeniera de software especializada en backend con Python.
EXPERIENCIA
Backend Engineer senior en Tuvalum (2021-2026). Migracion de un
monolito de siete anos a servicios desacoplados.
Programadora Python en Nunsys (2019-2021). ETLs internos.
FORMACION
Grado en Ingenieria Informatica, UPV (2014-2018).
IDIOMAS
Espanol nativo. Ingles C1 (Cambridge CAE).
"""


def test_separa_experiencia_de_formacion():
    s = secciones_cv(CV)
    assert "2021-2026" in s["experiencia"]
    assert "2014-2018" not in s["experiencia"]
    assert "2014-2018" in s["formacion"]


def test_reconoce_cabeceras_en_ingles():
    s = secciones_cv("EXPERIENCE\nBackend at Acme (2020-2024).\nEDUCATION\nBSc (2016-2020).\nLANGUAGES\nEnglish native.")
    assert "2020-2024" in s["experiencia"]
    assert "2016-2020" in s["formacion"]
    assert "native" in s["idiomas"]


def test_reconoce_experiencia_laboral_como_variante():
    s = secciones_cv("EXPERIENCIA LABORAL\nAnalista en Acme (2019-2023).")
    assert "2019-2023" in s["experiencia"]


def test_ignora_falsas_cabeceras():
    """'ITC (2018-2019).' y 'MVC.' van en mayusculas pero no son secciones.

    Aparecen de verdad en los CVs del repositorio. Si se toman por cabecera,
    parten la seccion de experiencia por la mitad y se pierden rangos.
    """
    s = secciones_cv("EXPERIENCIA\nBecario en ITC (2018-2019).\nMVC.\nAnalista (2019-2024).")
    assert "2018-2019" in s["experiencia"]
    assert "2019-2024" in s["experiencia"]


def test_texto_sin_cabeceras_va_entero_a_otros():
    s = secciones_cv("Un texto plano sin ninguna cabecera reconocible.")
    assert "texto plano" in s["otros"]


def test_oferta_separa_requisitos_de_lo_valorado():
    oferta = """Data Engineer
Sobre el puesto
Buscamos a alguien.
Requisitos
- Al menos 3 anos de experiencia.
- Grado en Ingenieria Informatica.
Se valorara
- Ingles B2 o superior.
Que ofrecemos
- Horario flexible.
"""
    s = secciones_oferta(oferta)
    assert "3 anos" in s["requisitos"]
    assert "B2" not in s["requisitos"]
    assert "B2" in s["valorado"]


def test_oferta_en_ingles():
    oferta = "Requirements\n- At least 3 years of experience.\nNice to have\n- Kafka.\n"
    s = secciones_oferta(oferta)
    assert "3 years" in s["requisitos"]
    assert "Kafka" in s["valorado"]


def test_oferta_sin_seccion_de_requisitos():
    """frontend_react no tiene seccion de requisitos: 'requisitos' queda vacia."""
    s = secciones_oferta("Frontend React\nSobre el puesto\nNos importa el criterio.\n")
    assert s["requisitos"] == ""
