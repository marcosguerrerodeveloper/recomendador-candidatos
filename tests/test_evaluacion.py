import pytest

from requisitos import Perfil, Requisitos, Veredicto, evaluar, extraer_de_cv, extraer_de_oferta


def test_cumple_todo_no_penaliza():
    v = evaluar(Requisitos(anios=3, titulacion=2, ingles=4), Perfil(anios=5, titulacion=3, ingles=5))
    assert v.penalizacion == 0.0
    assert v.avisos == []


def test_dato_desconocido_no_penaliza():
    """El tercer estado: si no se pudo extraer, el candidato queda intacto.

    Es la decision central del diseno. Un fallo del parser no debe perjudicar a
    nadie, porque seria un error invisible.
    """
    v = evaluar(Requisitos(anios=5, titulacion=2, ingles=5), Perfil(anios=None, titulacion=None, ingles=None))
    assert v.penalizacion == 0.0
    assert v.avisos == []


def test_oferta_sin_requisitos_no_penaliza_a_nadie():
    v = evaluar(Requisitos(), Perfil(anios=1, titulacion=1, ingles=1))
    assert v.penalizacion == 0.0


def test_penaliza_los_anios_que_faltan():
    v = evaluar(Requisitos(anios=5), Perfil(anios=3))
    assert v.penalizacion == pytest.approx(0.10)  # 2 anios x 0,05


def test_los_anios_tienen_tope():
    """Faltando 10 anios la penalizacion se queda en 0,20."""
    v = evaluar(Requisitos(anios=12), Perfil(anios=2))
    assert v.penalizacion == pytest.approx(0.20)


def test_penaliza_el_ingles_que_falta():
    v = evaluar(Requisitos(ingles=5), Perfil(ingles=4))  # pide C1, tiene B2
    assert v.penalizacion == pytest.approx(0.03)


def test_penaliza_la_titulacion_que_falta():
    v = evaluar(Requisitos(titulacion=3), Perfil(titulacion=2))  # pide Master, tiene Grado
    assert v.penalizacion == pytest.approx(0.04)


def test_las_penalizaciones_se_acumulan():
    v = evaluar(Requisitos(anios=5, titulacion=3, ingles=5), Perfil(anios=4, titulacion=2, ingles=4))
    assert v.penalizacion == pytest.approx(0.05 + 0.04 + 0.03)
    assert len(v.avisos) == 3


def test_los_avisos_son_legibles_y_citan_las_dos_cifras():
    v = evaluar(Requisitos(anios=5), Perfil(anios=3))
    assert v.avisos == ["pide 5 años de experiencia, se le calculan 3"]


def test_el_aviso_de_ingles_usa_codigos_mcer():
    v = evaluar(Requisitos(ingles=5), Perfil(ingles=4))
    assert v.avisos == ["pide inglés C1, acredita B2"]


def test_extraccion_completa_de_una_oferta():
    oferta = """Software Tools Developer
Requisitos:
- Grado en Ingenieria Informatica o similar.
- Al menos 1 ano de experiencia en desarrollo de software.
- Nivel de ingles minimo B2.
Se valorara:
- Conocimientos de Modbus.
"""
    r = extraer_de_oferta(oferta)
    assert r == Requisitos(anios=1, titulacion=2, ingles=4)


def test_extraccion_completa_de_un_cv():
    cv = """Ana Ruiz Melgar
EXPERIENCIA
Backend en Tuvalum (2021-2026). Programadora en Nunsys (2019-2021).
FORMACION
Grado en Ingenieria Informatica, UPV (2014-2018).
IDIOMAS
Espanol nativo. Ingles C1 (Cambridge CAE).
"""
    assert extraer_de_cv(cv) == Perfil(anios=7, titulacion=2, ingles=5)
