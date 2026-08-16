import datetime

from requisitos import anios_de_cv, anios_de_oferta

ANIO_ACTUAL = datetime.date.today().year


def test_suma_un_rango_simple():
    assert anios_de_cv("EXPERIENCIA\nBackend en Acme (2019-2024).") == 5


def test_une_rangos_solapados_en_vez_de_sumarlos():
    """2018-2019, 2019-2021 y 2021-2026 son 8 anios, no 10.

    Los extremos se solapan: sumar cada rango por separado cuenta dos veces los
    anios de cambio de empleo. Es el caso del CV de Ana Ruiz.
    """
    cv = ("EXPERIENCIA\nSenior en Tuvalum (2021-2026).\n"
          "Programadora en Nunsys (2019-2021).\nBecaria en Solutia (2018-2019).")
    assert anios_de_cv(cv) == 8


def test_ignora_las_fechas_de_formacion():
    """El (2014-2018) del Grado no son anios trabajados."""
    cv = "EXPERIENCIA\nBackend en Acme (2020-2024).\nFORMACION\nGrado en Informatica, UPV (2014-2018)."
    assert anios_de_cv(cv) == 4


def test_actualidad_se_resuelve_contra_el_anio_en_curso():
    cv = f"EXPERIENCIA\nIngeniero en Acme ({ANIO_ACTUAL - 3}-actualidad)."
    assert anios_de_cv(cv) == 3


def test_no_confunde_la_edad_de_un_sistema_con_la_del_candidato():
    """'un monolito de siete anos' NO son siete anios de experiencia.

    Es el caso real del CV de Ana Ruiz. Por eso los rangos de fechas mandan y
    la via de las frases solo actua si no hay ningun rango.
    """
    cv = ("EXPERIENCIA\nSenior en Tuvalum (2021-2026). Lidere la migracion de "
          "un monolito de siete anos a servicios desacoplados.")
    assert anios_de_cv(cv) == 5


def test_frase_explicita_cuando_no_hay_rangos():
    cv = "PERFIL\nIngeniero de fiabilidad con siete anos de experiencia gestionando plataformas."
    assert anios_de_cv(cv) == 7


def test_frase_explicita_en_digitos():
    assert anios_de_cv("PERFIL\nDesarrolladora con 6 anos de experiencia.") == 6


def test_cv_sin_ninguna_senal_es_desconocido():
    assert anios_de_cv("PERFIL\nDesarrollador backend con interes en Python.") is None


def test_requisito_minimo_de_la_oferta():
    assert anios_de_oferta("Requisitos\n- Minimo 5 anos de experiencia en backend.\n") == 5


def test_requisito_con_al_menos():
    assert anios_de_oferta("Requisitos\n- Al menos 1 ano de experiencia en desarrollo.\n") == 1


def test_requisito_en_letra():
    assert anios_de_oferta("Requisitos\n- Al menos tres anos de experiencia.\n") == 3


def test_requisito_con_signo_mas():
    assert anios_de_oferta("Requisitos\n- 3+ anos de experiencia como Data Engineer.\n") == 3


def test_requisito_en_ingles():
    assert anios_de_oferta("Requirements\n- At least 3 years of experience building systems.\n") == 3


def test_oferta_sin_requisito_de_anios():
    assert anios_de_oferta("Requisitos\n- Grado en Informatica.\n") is None


def test_no_cuenta_lo_que_solo_se_valora():
    oferta = "Requisitos\n- SQL avanzado.\nSe valorara\n- Al menos 5 anos con Kafka.\n"
    assert anios_de_oferta(oferta) is None
