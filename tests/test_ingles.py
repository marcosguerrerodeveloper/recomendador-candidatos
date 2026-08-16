from requisitos import ingles_de_cv, ingles_de_oferta

CV = "IDIOMAS\nEspanol nativo. Valenciano nativo. Ingles C1 (Cambridge CAE).\n"


def test_lee_el_nivel_del_cv():
    assert ingles_de_cv(CV) == 5  # C1


def test_ignora_el_nivel_de_otro_idioma():
    """'Frances B1' no debe rebajar un 'Ingles C1' que va en la misma linea."""
    assert ingles_de_cv("IDIOMAS\nIngles C1. Frances B1.") == 5


def test_nativo_equivale_a_c2():
    assert ingles_de_cv("LANGUAGES\nEnglish native. Spanish fluent.") == 6


def test_nivel_alto_equivale_a_c1():
    assert ingles_de_cv("IDIOMAS\nIngles: nivel alto.") == 5


def test_cv_sin_idiomas_es_desconocido():
    assert ingles_de_cv("PERFIL\nDesarrollador backend.") is None


def test_requisito_explicito_de_la_oferta():
    oferta = "Requisitos\n- Nivel de ingles minimo B2.\nSe valorara\n- Kafka.\n"
    assert ingles_de_oferta(oferta) == 4  # B2


def test_no_toma_por_requisito_lo_que_solo_se_valora():
    """La oferta data_engineer pone el ingles bajo 'Se valorara'."""
    oferta = "Requisitos\n- SQL avanzado.\nSe valorara\n- Ingles B2 o superior.\n"
    assert ingles_de_oferta(oferta) is None


def test_requisito_en_ingles():
    oferta = "Requirements\n- Minimum English level C1.\n"
    assert ingles_de_oferta(oferta) == 5


def test_oferta_sin_requisito_de_idioma():
    assert ingles_de_oferta("Requisitos\n- Grado en Informatica.\n") is None
