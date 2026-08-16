from requisitos import titulacion_de_cv, titulacion_de_oferta


def test_grado_es_nivel_2():
    assert titulacion_de_cv("FORMACION\nGrado en Ingenieria Informatica, UPV (2014-2018).") == 2


def test_grado_superior_es_nivel_1():
    assert titulacion_de_cv("FORMACION\nGrado Superior en Desarrollo de Aplicaciones Web (2017-2019).") == 1


def test_master_es_nivel_3():
    assert titulacion_de_cv("FORMACION\nMaster en Ciencia de Datos, UB (2020-2022).") == 3


def test_se_queda_con_la_titulacion_mas_alta():
    """Un CV con Master y Grado vale 3: se compara el techo, no lo primero."""
    cv = "FORMACION\nMaster en Ciencia de Datos (2020-2022). Grado en Matematicas (2016-2020)."
    assert titulacion_de_cv(cv) == 3


def test_grado_superior_no_se_confunde_con_grado():
    """'Grado Superior' contiene la palabra 'Grado' y vale 1, no 2."""
    assert titulacion_de_cv("FORMACION\nGrado Superior en DAW (2017-2019).") == 1


def test_titulacion_en_ingles():
    assert titulacion_de_cv("EDUCATION\nBSc in Computer Science (2016-2020).") == 2


def test_sin_formacion_es_desconocido():
    assert titulacion_de_cv("PERFIL\nDesarrollador autodidacta.") is None


def test_requisito_de_la_oferta():
    oferta = "Requisitos\n- Grado en Ingenieria Informatica o similar.\n"
    assert titulacion_de_oferta(oferta) == 2


def test_requisito_de_master():
    oferta = "Requisitos\n- Master en Ciencia de Datos, IA o equivalente.\n"
    assert titulacion_de_oferta(oferta) == 3


def test_oferta_sin_requisito_de_titulacion():
    assert titulacion_de_oferta("Requisitos\n- Al menos 3 anos de experiencia.\n") is None
