"""Genera CVs ficticios en PDF para probar el pipeline.

No forma parte del sistema: es utilidad de demo (Paso 7 de la hoja de ruta).

Los perfiles buscan que el ranking sea evaluable a ojo, y por eso el conjunto
esta construido a proposito con casos incomodos, no solo con perfiles faciles:

- Familias que se solapan (data engineer / data analyst / data scientist /
  ML engineer) para comprobar que el modelo distingue matices y no solo temas.
- Dos controles negativos no tecnicos (RRHH y contabilidad) que deben quedar al
  final de cualquier oferta tecnica. Si suben, hay un bug.
- Un perfil junior y varios senior del mismo dominio, para ver que el ranking
  mide afinidad TEMATICA y no seniority: ambos puntuan alto y el sistema no
  distingue quien tiene mas experiencia. Es una limitacion real, no un fallo.
- Tres CVs en ingles, para verificar que el modelo multilingue alinea ambos
  idiomas en el mismo espacio semantico.

La extension es deliberada: rondan los 3.000 caracteres, como los CVs reales
del proyecto. Con CVs de 700 caracteres el ranking sale enganosamente limpio,
porque un texto corto es casi puro titular y no tiene ruido que estorbe.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

CVS_DIR = Path(__file__).parent / "cvs"

PERFILES = [
    {
        "archivo": "ana_ruiz_backend.pdf",
        "nombre": "Ana Ruiz Melgar",
        "puesto": "Desarrolladora Backend Python",
        "detalle": "6 años de experiencia",
        "contacto": "València · ana.ruiz@correo-ficticio.es · 600 000 001",
        "secciones": [
            ("Perfil", "Ingeniera de software especializada en backend con Python. "
             "Diseño y mantengo APIs REST que soportan tráfico sostenido, con foco en "
             "calidad de código, testing automatizado y modelado de datos relacionales. "
             "Me interesa especialmente reducir deuda técnica sin frenar la entrega de "
             "producto, y he liderado dos migraciones de arquitectura sin cortes de "
             "servicio."),
            ("Experiencia", "Backend Engineer sénior en Tuvalum (2021-2026). Desarrollo y "
             "mantenimiento de microservicios en Django REST Framework y FastAPI para el "
             "marketplace de bicicletas. Lideré la migración de un monolito de siete años "
             "a servicios desacoplados, con estrangulamiento progresivo y sin ventana de "
             "mantenimiento. Optimización del modelo de datos y de las consultas MySQL "
             "más costosas, que redujo la latencia media del catálogo un 40% y eliminó "
             "los picos de bloqueo en horas punta. Introduje pruebas de contrato entre "
             "servicios con pytest, lo que bajó las incidencias de integración a la "
             "mitad. Mentorización de dos personas junior. "
             "Programadora Python en Nunsys (2019-2021). ETLs internos de facturación, "
             "integraciones con ERPs de cliente (SAP y Sage) y automatización de informes "
             "que antes se montaban a mano en Excel cada semana. "
             "Becaria de desarrollo en Solutia IT (2018-2019). Mantenimiento de una "
             "aplicación heredada en Django 1.11 y su actualización a la versión 2."),
            ("Proyectos", "Diseño e implantación de un sistema de colas con Celery y Redis "
             "para procesar altas de producto con imágenes, que absorbió un pico de diez "
             "mil altas diarias en campaña sin degradar la web. "
             "Librería interna de paginación por cursor para la API pública, adoptada "
             "después por los tres equipos de producto."),
            ("Tecnologías", "Python, Django, Django REST Framework, FastAPI, SQLAlchemy, "
             "MySQL, PostgreSQL, Redis, Celery, RabbitMQ, Docker, docker-compose, pytest, "
             "Git, GitLab CI, Sentry, Grafana. Nociones de Terraform."),
            ("Formación", "Grado en Ingeniería Informática, Universitat Politècnica de "
             "València (2014-2018). Especialidad en Ingeniería del Software."),
            ("Logros", "Reducción del tiempo de despliegue del servicio de catálogo de "
             "cuarenta minutos a seis, al partir el pipeline en etapas paralelas y "
             "cachear dependencias. "
             "Definición del estándar interno de documentación de APIs con OpenAPI, "
             "adoptado por los tres equipos de backend y hoy requisito de aceptación en "
             "cada historia. "
             "Reducción del gasto en instancias de base de datos un 25% tras un análisis "
             "de consultas lentas que destapó tres índices ausentes y dos consultas N+1 "
             "en el flujo de checkout."),
            ("Formación complementaria", "Curso de arquitectura de microservicios y "
             "patrones de resiliencia, 2023. Formación interna en modelado de dominio y "
             "diseño guiado por el dominio, 2022. Taller de rendimiento en bases de datos "
             "relacionales impartido por Percona, 2021."),
            ("Otros datos", "Disponibilidad para incorporación en un mes por preaviso "
             "contractual. Modelo de trabajo híbrido o remoto. Disponibilidad para viajar "
             "puntualmente. Carné de conducir B y vehículo propio. Colaboro como "
             "mentora en un programa de acompañamiento a mujeres que se reorientan hacia "
             "la programación."),
            ("Idiomas", "Español nativo. Valenciano nativo. Inglés C1 (Cambridge CAE)."),
        ],
    },
    {
        "archivo": "marc_soler_datascience.pdf",
        "nombre": "Marc Soler Aguirre",
        "puesto": "Data Scientist",
        "detalle": "NLP y modelos de lenguaje",
        "contacto": "Barcelona · marc.soler@correo-ficticio.es · 600 000 002",
        "secciones": [
            ("Perfil", "Científico de datos con cuatro años de experiencia en proyectos de "
             "procesamiento de lenguaje natural. Trabajo habitual con embeddings, "
             "clasificación de texto y sistemas de recuperación semántica. Me muevo con "
             "soltura entre la fase de experimentación y la de puesta en producción, y "
             "defiendo que un modelo que nadie puede explicar no llega a usarse."),
            ("Experiencia", "Data Scientist en Sanitas Digital (2023-2026). Modelos de "
             "clasificación automática de informes clínicos con transformers afinados "
             "sobre corpus propio, que redujeron el tiempo de triaje documental de doce "
             "minutos a menos de dos por informe. Implementación de un buscador semántico "
             "sobre el histórico documental usando sentence-transformers y similitud "
             "coseno, con evaluación por recall en los primeros diez resultados. Diseño "
             "del protocolo de anotación y coordinación de tres anotadores clínicos. "
             "Analista de datos en Idealista (2022-2023). Segmentación de usuarios y "
             "modelos de propensión al contacto con scikit-learn. Análisis de cohortes y "
             "diseño de test A/B para el buscador de vivienda. "
             "Investigador en prácticas en el Barcelona Supercomputing Center (2021-2022). "
             "Evaluación de modelos de lenguaje en castellano y catalán."),
            ("Proyectos", "Detector de duplicados semánticos en anuncios inmobiliarios: "
             "vectorización del texto, agrupamiento por umbral de coseno y revisión "
             "manual de la frontera de decisión. Detectó un ocho por ciento de anuncios "
             "repetidos que los filtros por palabras clave no encontraban. "
             "Publicación en el congreso SEPLN sobre desambiguación de siglas médicas."),
            ("Tecnologías", "Python, pandas, numpy, scikit-learn, PyTorch, Hugging Face "
             "Transformers, sentence-transformers, spaCy, SQL, MLflow, Weights & Biases, "
             "Docker, FastAPI para servir modelos, Jupyter."),
            ("Formación", "Máster en Ciencia de Datos, Universitat de Barcelona (2020-2022). "
             "Grado en Matemáticas, Universitat Autònoma de Barcelona (2016-2020)."),
            ("Logros", "Reducción del coste de anotación manual a la mitad mediante "
             "aprendizaje activo: el modelo propone los casos dudosos y el equipo clínico "
             "solo revisa esos, en lugar de muestrear al azar. "
             "Establecimiento del protocolo de evaluación de modelos de la unidad, con "
             "conjunto de control congelado y revisión obligatoria de sesgos por grupo "
             "demográfico antes de cualquier promoción a producción. "
             "Formación interna sobre embeddings y búsqueda vectorial para el equipo de "
             "producto, con material propio que se sigue usando."),
            ("Publicaciones y divulgación", "Ponencia en el congreso SEPLN 2024 sobre "
             "desambiguación de siglas médicas en informes de alta. Artículo divulgativo "
             "sobre evaluación de buscadores semánticos en el blog de ingeniería de la "
             "empresa. Colaborador ocasional en un grupo de lectura de artículos de "
             "procesamiento de lenguaje natural."),
            ("Otros datos", "Disponibilidad inmediata. Preferencia por modelo híbrido en "
             "Barcelona o remoto con visitas periódicas. Interés declarado en puestos "
             "donde el modelo llegue a producción y no se quede en prueba de concepto."),
            ("Idiomas", "Español y catalán nativos. Inglés C1. Francés B1."),
        ],
    },
    {
        "archivo": "lucia_fernandez_frontend.pdf",
        "nombre": "Lucía Fernández Prado",
        "puesto": "Frontend Developer",
        "detalle": "React y TypeScript",
        "contacto": "Madrid · lucia.fernandez@correo-ficticio.es · 600 000 003",
        "secciones": [
            ("Perfil", "Desarrolladora frontend centrada en interfaces accesibles y en el "
             "rendimiento percibido en navegador. Cuido el diseño de sistemas de "
             "componentes reutilizables y trabajo codo con codo con producto y diseño. "
             "Me tomo la accesibilidad como un requisito y no como un extra, y he llevado "
             "dos productos a cumplimiento WCAG AA."),
            ("Experiencia", "Frontend Developer sénior en Cabify (2022-2026). Desarrollo del "
             "panel de operaciones en React y TypeScript, usado a diario por los equipos "
             "de ciudad en once mercados. Implantación de un design system propio con "
             "Storybook que unificó tres interfaces heredadas y recortó a la mitad el "
             "tiempo de construcción de pantallas nuevas. Mejora de Core Web Vitals en un "
             "35% mediante división de código, carga diferida de rutas y sustitución de "
             "una librería de gráficos pesada por SVG a medida. Auditoría y corrección de "
             "accesibilidad con lectores de pantalla. "
             "Frontend Developer en agencia Kaizen (2020-2022). Desarrollo de tiendas en "
             "Next.js para clientes de retail, con renderizado en servidor e "
             "internacionalización en cuatro idiomas. "
             "Maquetadora web en Estudio Nueve (2019-2020)."),
            ("Proyectos", "Migración incremental de una aplicación de Angular 1 a React sin "
             "congelar el desarrollo de producto, conviviendo ambos frameworks durante "
             "ocho meses mediante web components como frontera. "
             "Charla en la Madrid JS sobre pruebas de accesibilidad automatizadas."),
            ("Tecnologías", "JavaScript, TypeScript, React, Next.js, Redux Toolkit, React "
             "Query, Vite, HTML5, CSS3, Sass, Tailwind, Storybook, Jest, Testing Library, "
             "Playwright, Figma, Lighthouse, axe-core."),
            ("Formación", "Grado Superior en Desarrollo de Aplicaciones Web (2017-2019). "
             "Bootcamp intensivo de React avanzado, 2021."),
            ("Logros", "Reducción del peso del paquete inicial de la aplicación de 1,2 MB "
             "a 380 KB, lo que bajó el tiempo hasta interactivo en conexiones móviles "
             "lentas de once a cuatro segundos. "
             "Definición de la política de accesibilidad de producto y de su lista de "
             "verificación previa a publicación, hoy obligatoria en cada entrega. "
             "Reducción de los errores en producción del frontend un 60% tras introducir "
             "TypeScript en modo estricto en una base de código que era JavaScript puro."),
            ("Formación complementaria", "Curso avanzado de accesibilidad web y WCAG 2.2, "
             "2024. Formación en arquitectura de micro frontends, 2023. Taller de "
             "rendimiento web impartido por Google Developer Experts, 2022."),
            ("Otros datos", "Disponibilidad para incorporación en quince días. Preferencia "
             "por remoto con encuentros presenciales trimestrales. Participo como "
             "ponente ocasional en meetups de desarrollo frontend en Madrid y colaboro en "
             "la traducción al español de documentación de código abierto."),
            ("Idiomas", "Español nativo. Inglés B2. Portugués A2."),
        ],
    },
    {
        "archivo": "david_ortega_devops.pdf",
        "nombre": "David Ortega Benítez",
        "puesto": "DevOps / SRE",
        "detalle": "Kubernetes e infraestructura como código",
        "contacto": "Sevilla · david.ortega@correo-ficticio.es · 600 000 004",
        "secciones": [
            ("Perfil", "Ingeniero de fiabilidad con siete años gestionando plataformas en "
             "producción. Automatizo despliegues, observabilidad y respuesta a incidentes. "
             "Creo en la infraestructura como código sin excepciones y en los postmortem "
             "sin culpables como la única forma de que un fallo se pague una sola vez."),
            ("Experiencia", "Site Reliability Engineer en Glovo (2021-2026). Gestión de "
             "clústeres Kubernetes multirregión que sostienen la plataforma de pedidos. "
             "Pipelines de despliegue continuo con ArgoCD y despliegue progresivo por "
             "porcentaje de tráfico. Reducción del tiempo medio de recuperación de 45 a 12 "
             "minutos mediante alertas basadas en presupuesto de error en lugar de "
             "umbrales fijos, que eran ruido y nadie miraba. Diseño del plan de guardias y "
             "de la rotación entre once personas. Coordinador de incidentes en cuatro "
             "caídas mayores. "
             "Administrador de sistemas en Everis (2019-2021). Automatización de "
             "aprovisionamiento con Ansible, monitorización con Zabbix y migración de un "
             "centro de datos propio a la nube para tres clientes del sector seguros. "
             "Técnico de soporte de sistemas en Ayesa (2018-2019)."),
            ("Proyectos", "Módulos de Terraform reutilizables para el alta de servicios "
             "nuevos, que bajaron el tiempo de puesta en marcha de un servicio de tres "
             "días a una tarde. "
             "Sistema de detección de secretos en commits integrado en el pipeline, tras "
             "una fuga de credenciales en un repositorio interno."),
            ("Tecnologías", "Kubernetes, Docker, Terraform, Ansible, ArgoCD, Helm, "
             "Prometheus, Grafana, Loki, OpenTelemetry, Linux, Bash, Python, Go básico, "
             "GitHub Actions, GitLab CI."),
            ("Formación", "Ingeniería Técnica en Telecomunicaciones, Universidad de Sevilla "
             "(2013-2017)."),
            ("Logros", "Reducción del gasto de infraestructura un 28% mediante "
             "dimensionado automático por demanda real y apagado de entornos de prueba "
             "fuera de horario. "
             "Implantación de la cultura de postmortem sin culpables, con veintitrés "
             "documentos publicados internamente y seguimiento de acciones correctoras. "
             "Reducción del número de alertas nocturnas de ciento veinte a nueve al mes "
             "revisando una por una cuáles eran accionables y borrando el resto."),
            ("Formación complementaria", "Formación en ingeniería del caos y pruebas de "
             "resiliencia, 2024. Curso de observabilidad con OpenTelemetry, 2023. "
             "Formación interna en gestión de incidentes y comunicación de crisis, 2022."),
            ("Otros datos", "Disponibilidad para incorporación en un mes. Acostumbrado a "
             "guardias rotativas. Modelo híbrido en Sevilla o remoto. Carné de conducir B. "
             "Mantengo un blog técnico sobre fiabilidad de sistemas con publicación "
             "mensual."),
            ("Certificaciones", "Certified Kubernetes Administrator (CKA), 2022. "
             "HashiCorp Certified Terraform Associate, 2023."),
            ("Idiomas", "Español nativo. Inglés B2."),
        ],
    },
    {
        "archivo": "beatriz_nogales_rrhh.pdf",
        "nombre": "Beatriz Nogales Cuesta",
        "puesto": "Técnica de Recursos Humanos",
        "detalle": "Selección y desarrollo",
        "contacto": "Valencia · beatriz.nogales@correo-ficticio.es · 600 000 005",
        "secciones": [
            ("Perfil", "Profesional de recursos humanos con ocho años en selección, "
             "acogida y planes de formación. Experiencia en entornos industriales y de "
             "gran distribución, con procesos de alto volumen y fuerte componente de "
             "relación con el comité de empresa."),
            ("Experiencia", "Responsable de selección en Mercadona (2020-2026). Gestión de "
             "procesos de alto volumen para tiendas y bloques logísticos, con más de "
             "cuatrocientas incorporaciones al año. Rediseño del proceso de acogida, que "
             "redujo la rotación en los primeros noventa días un 18%. Implantación de "
             "entrevistas por competencias estructuradas y formación de los mandos "
             "intermedios que entrevistan. "
             "Técnica de recursos humanos en Grupo Antolín (2018-2020). Administración de "
             "personal, nóminas, control de absentismo y apoyo en la negociación del "
             "convenio de centro. "
             "Consultora de selección en Adecco (2016-2018). Cobertura de vacantes de "
             "perfil administrativo y de producción para clientes de la comarca."),
            ("Proyectos", "Puesta en marcha del plan de igualdad de centro, incluido el "
             "diagnóstico previo y el registro retributivo. "
             "Programa de desarrollo de mandos intermedios con itinerario formativo propio "
             "y evaluación a los seis meses."),
            ("Competencias", "Entrevista por competencias, evaluación del desempeño, planes "
             "de carrera, negociación colectiva, prevención de riesgos laborales nivel "
             "básico, SAP SuccessFactors, SAP HCM, Excel avanzado."),
            ("Formación", "Grado en Psicología, Universitat de València (2011-2015). "
             "Máster en Dirección de Recursos Humanos, ESIC (2015-2016)."),
            ("Logros", "Reducción del tiempo medio de cobertura de vacante de treinta y "
             "cuatro a diecinueve días mediante una cantera propia de candidaturas y "
             "entrevistas en bloque. "
             "Puesta en marcha del canal de denuncias interno y de su protocolo de "
             "tramitación, con formación a toda la plantilla del centro. "
             "Mejora de doce puntos en el índice de clima laboral del área logística tras "
             "un plan de acción construido a partir de grupos de discusión."),
            ("Formación complementaria", "Curso de compensación y beneficios, 2024. "
             "Formación en gestión del cambio, 2022. Actualización anual en normativa "
             "laboral y jurisprudencia social."),
            ("Otros datos", "Disponibilidad para incorporación en quince días. "
             "Disponibilidad para desplazamientos entre centros de la provincia. Carné de "
             "conducir B y vehículo propio. Voluntaria en un programa de orientación "
             "laboral para personas mayores de cuarenta y cinco años en situación de "
             "desempleo de larga duración."),
            ("Idiomas", "Español nativo. Inglés B1."),
        ],
    },
    {
        "archivo": "kwame_osei_data_engineer.pdf",
        "nombre": "Kwame Osei",
        "puesto": "Data Engineer",
        "detalle": "Batch and streaming pipelines",
        "contacto": "Manchester · kwame.osei@correo-ficticio.uk · +44 7700 000006",
        "secciones": [
            ("Profile", "Data engineer with five years of experience building reliable data "
             "pipelines. I focus on data modelling, orchestration and making analytics "
             "datasets trustworthy enough that downstream teams stop maintaining their own "
             "shadow copies. I care more about clear contracts between producers and "
             "consumers than about any particular tool."),
            ("Experience", "Data Engineer at Monzo (2022-2026). Built and maintained batch "
             "pipelines in Airflow feeding the analytics warehouse, covering roughly two "
             "hundred daily tasks. Designed dimensional models in dbt and introduced a "
             "layered structure separating raw ingestion from business logic. Introduced "
             "data quality tests and freshness checks that cut data incident reports by "
             "half in two quarters. Led the migration from a nightly full reload to "
             "incremental models, taking the warehouse refresh from four hours to twenty "
             "minutes. "
             "Junior Data Engineer at Deliveroo (2021-2022). Ingestion jobs in Python and "
             "Spark for order and rider event streams, plus backfills for historical data. "
             "Analytics intern at the Co-operative Group (2020-2021)."),
            ("Projects", "Streaming pipeline consuming Kafka topics into near real time "
             "tables for the operations dashboard, replacing a fifteen minute polling job. "
             "Internal catalogue of dataset ownership and service level expectations, "
             "which made it possible to route data incidents to the right team "
             "automatically."),
            ("Technologies", "Python, SQL, Apache Airflow, dbt, Apache Spark, Kafka, "
             "Snowflake, BigQuery, Postgres, Docker, Terraform, Git, Great Expectations, "
             "Looker."),
            ("Education", "BSc Computer Science, University of Manchester (2017-2020)."),
            ("Achievements", "Cut the monthly warehouse compute bill by 31% by rewriting "
             "the three most expensive models and partitioning the largest fact table. "
             "Wrote the team handbook on data modelling conventions, which is now the "
             "reference used in code review and onboarding. "
             "Reduced onboarding time for new analysts from three weeks to five days by "
             "documenting the core datasets and their known caveats."),
            ("Additional training", "Advanced dbt modelling workshop, 2024. Course on "
             "streaming systems and exactly once semantics, 2023. Internal training on "
             "data privacy and handling of personal data under GDPR, 2022."),
            ("Other", "Available at one month notice. Open to hybrid work in Manchester or "
             "fully remote within the United Kingdom or Spain. Maintainer of a small open "
             "source package for Airflow sensors, with around four hundred monthly "
             "downloads. Occasional speaker at the Manchester data engineering meetup."),
            ("Languages", "English native. Spanish B1. Twi native."),
        ],
    },
    {
        "archivo": "sergio_ibanez_fullstack.pdf",
        "nombre": "Sergio Ibáñez Rojo",
        "puesto": "Desarrollador Full Stack",
        "detalle": "Java y Angular",
        "contacto": "Zaragoza · sergio.ibanez@correo-ficticio.es · 600 000 007",
        "secciones": [
            ("Perfil", "Desarrollador full stack con nueve años en aplicaciones de gestión "
             "empresarial. Trabajo el ciclo completo, del modelo de datos a la pantalla, "
             "sobre todo en banca y seguros. Estoy cómodo en bases de código grandes y "
             "antiguas, que es donde suele estar el trabajo de verdad."),
            ("Experiencia", "Desarrollador sénior en Ibercaja (2020-2026). Desarrollo y "
             "evolución de la banca electrónica de empresas con Spring Boot en el servidor "
             "y Angular en el cliente. Refactorización del módulo de firma delegada, que "
             "acumulaba diez años de parches, subiendo la cobertura de pruebas del 15% al "
             "78%. Integración con el bus corporativo de servicios y con pasarelas de "
             "firma electrónica. Participación en el comité de arquitectura de "
             "aplicaciones. "
             "Analista programador en Hiberus (2017-2020). Aplicaciones a medida en Java "
             "para clientes de logística y distribución. "
             "Programador en Grupo Oesía (2015-2017). Mantenimiento de aplicaciones "
             "heredadas en Struts y JSP y su migración progresiva a Spring MVC."),
            ("Proyectos", "Motor de reglas configurable para la validación de operaciones, "
             "que sacó del código las condiciones de negocio y permitió a negocio "
             "cambiarlas sin desplegar. "
             "Migración de una base de datos Oracle a PostgreSQL con doble escritura "
             "durante la transición y verificación de consistencia."),
            ("Tecnologías", "Java 8 a 21, Spring Boot, Spring Security, Hibernate, JPA, "
             "Maven, JUnit, Mockito, Angular, TypeScript, RxJS, Oracle, PostgreSQL, "
             "Jenkins, SonarQube, Docker, Kafka."),
            ("Logros", "Reducción del tiempo de compilación y despliegue del proyecto "
             "principal de cincuenta minutos a doce, al modularizar el proyecto Maven y "
             "paralelizar las pruebas. "
             "Eliminación de una familia de fallos de concurrencia en la firma de "
             "operaciones que se reproducía una vez al mes y nadie había conseguido "
             "aislar en dos años. "
             "Redacción de la guía de estilo de código Java del departamento y de las "
             "reglas de SonarQube asociadas, hoy aplicadas en catorce proyectos."),
            ("Formación", "Ingeniería Informática, Universidad de Zaragoza (2010-2015)."),
            ("Formación complementaria", "Curso de arquitectura hexagonal y pruebas en "
             "sistemas heredados, 2023. Formación en Spring Boot 3 y migración desde "
             "Java 8, 2023. Curso de seguridad en aplicaciones bancarias y normativa "
             "PSD2, 2021."),
            ("Otros datos", "Disponibilidad para incorporación en un mes por preaviso. "
             "Modelo híbrido en Zaragoza. Experiencia acreditada trabajando en entornos "
             "regulados con auditorías periódicas del Banco de España. Carné de conducir "
             "B. Formador interno de nuevas incorporaciones desde 2022."),
            ("Idiomas", "Español nativo. Inglés B2."),
        ],
    },
    {
        "archivo": "nadia_belkacem_ml_engineer.pdf",
        "nombre": "Nadia Belkacem",
        "puesto": "Machine Learning Engineer",
        "detalle": "MLOps y puesta en producción de modelos",
        "contacto": "Bilbao · nadia.belkacem@correo-ficticio.es · 600 000 008",
        "secciones": [
            ("Perfil", "Ingeniera de aprendizaje automático centrada en llevar modelos a "
             "producción y mantenerlos vivos. Mi trabajo empieza donde acaba el cuaderno "
             "de experimentos: empaquetado, servicio, monitorización de deriva y "
             "reentrenamiento. He visto suficientes modelos excelentes morir en un "
             "portátil como para insistir en esto."),
            ("Experiencia", "Machine Learning Engineer en Ternua Group (2023-2026). Diseño "
             "de la plataforma interna de modelos: registro con MLflow, servicio con "
             "FastAPI sobre Kubernetes y despliegue en sombra antes de cada promoción. "
             "Sistema de recomendación de producto basado en embeddings de catálogo y "
             "comportamiento de sesión, que subió la conversión del bloque de "
             "recomendados un 12%. Monitorización de deriva de datos con alertas cuando "
             "la distribución de entrada se aleja de la de entrenamiento. "
             "Data Scientist en Sngular (2021-2023). Modelos de previsión de demanda con "
             "gradient boosting y series temporales para clientes de retail. "
             "Ingeniera de datos junior en Idom (2020-2021)."),
            ("Proyectos", "Marco de reentrenamiento automático con validación previa: un "
             "modelo nuevo solo sustituye al anterior si gana en el conjunto de control y "
             "no empeora en ningún segmento de usuario vigilado. "
             "Reducción del coste de inferencia a la tercera parte mediante cuantización "
             "y agrupación de peticiones."),
            ("Tecnologías", "Python, PyTorch, scikit-learn, XGBoost, MLflow, DVC, FastAPI, "
             "Docker, Kubernetes, Airflow, Feast, Prometheus, Grafana, SQL, Spark."),
            ("Formación", "Máster en Inteligencia Artificial, Universidad de Deusto "
             "(2018-2020). Grado en Ingeniería en Tecnologías de Telecomunicación, "
             "Universidad del País Vasco (2014-2018)."),
            ("Logros", "Reducción del tiempo entre un experimento validado y su llegada a "
             "producción de seis semanas a cuatro días, al estandarizar el empaquetado y "
             "automatizar la promoción entre entornos. "
             "Detección temprana de una deriva de datos causada por un cambio silencioso "
             "en un proveedor externo, gracias a la monitorización de distribuciones de "
             "entrada, antes de que afectara a las recomendaciones. "
             "Definición del registro de modelos de la compañía, con trazabilidad de qué "
             "datos y qué código produjeron cada versión desplegada."),
            ("Formación complementaria", "Curso de sistemas de recomendación a escala, "
             "2024. Formación en aprendizaje automático responsable y evaluación de "
             "sesgos, 2023. Taller de optimización de inferencia y cuantización, 2022."),
            ("Otros datos", "Disponibilidad para incorporación en un mes. Modelo híbrido "
             "en Bilbao o remoto. Interés explícito en equipos con cultura de revisión de "
             "código y de experimentación medida. Coorganizadora de un grupo local de "
             "aprendizaje automático con encuentros mensuales."),
            ("Idiomas", "Español nativo. Euskera B2. Francés nativo. Inglés C1. Árabe B2."),
        ],
    },
    {
        "archivo": "pablo_arriaga_android.pdf",
        "nombre": "Pablo Arriaga Sanz",
        "puesto": "Desarrollador Android",
        "detalle": "Kotlin y Jetpack Compose",
        "contacto": "Málaga · pablo.arriaga@correo-ficticio.es · 600 000 009",
        "secciones": [
            ("Perfil", "Desarrollador móvil con seis años dedicados a Android. Trabajo con "
             "Kotlin y arquitectura limpia, y me preocupa especialmente el consumo de "
             "batería y el comportamiento en gama baja, que es donde vive buena parte de "
             "los usuarios reales y casi nunca se prueba."),
            ("Experiencia", "Android Developer sénior en Freenow (2022-2026). Desarrollo de "
             "la aplicación de pasajero, con seis millones de instalaciones. Migración "
             "progresiva de vistas XML a Jetpack Compose pantalla a pantalla, sin "
             "congelar producto. Rediseño del seguimiento de viaje en tiempo real, que "
             "bajó el consumo de batería en trayecto un 30% cambiando la estrategia de "
             "actualización de ubicación. Reducción del tiempo de arranque en frío de 2,8 "
             "a 1,4 segundos. "
             "Android Developer en Bnext (2019-2022). Aplicación de banca móvil: alta de "
             "cliente con verificación de identidad, biometría y notificaciones push "
             "transaccionales. Cumplimiento de requisitos de seguridad PSD2. "
             "Desarrollador junior en Vector ITC (2018-2019)."),
            ("Proyectos", "Librería interna de pruebas de interfaz sobre dispositivos "
             "reales en granja, que detectó tres fallos específicos de fabricante que el "
             "emulador no reproducía. "
             "Modo sin conexión con cola de operaciones y resolución de conflictos para "
             "zonas de cobertura pobre."),
            ("Tecnologías", "Kotlin, Java, Jetpack Compose, Coroutines, Flow, Hilt, Room, "
             "Retrofit, WorkManager, MVVM, Clean Architecture, JUnit, Espresso, Mockk, "
             "Gradle, Firebase, Google Play Console."),
            ("Logros", "Subida de la valoración en Google Play de 3,4 a 4,5 estrellas en "
             "año y medio, atacando por orden las causas concretas que aparecían en las "
             "reseñas negativas en lugar de rediseñar a ciegas. "
             "Reducción de la tasa de cierres inesperados del 1,8% al 0,2% de sesiones "
             "mediante instrumentación fina y corrección de fugas de memoria en la "
             "pantalla de mapa. "
             "Definición de la política de soporte de versiones de Android del equipo, "
             "equilibrando alcance de usuarios y coste de mantenimiento."),
            ("Formación", "Grado en Ingeniería del Software, Universidad de Málaga "
             "(2014-2018)."),
            ("Formación complementaria", "Curso avanzado de Jetpack Compose y animaciones, "
             "2024. Formación en rendimiento y consumo de batería en Android, 2023. "
             "Curso de arquitectura modular en proyectos móviles grandes, 2022."),
            ("Otros datos", "Disponibilidad para incorporación en quince días. Modelo "
             "remoto con base en Málaga. Experiencia trabajando en equipo distribuido en "
             "tres husos horarios. Carné de conducir B. Mantengo una pequeña aplicación "
             "propia en Google Play con unas dos mil instalaciones activas."),
            ("Idiomas", "Español nativo. Inglés B2."),
        ],
    },
    {
        "archivo": "irene_vidal_qa.pdf",
        "nombre": "Irene Vidal Company",
        "puesto": "QA Engineer",
        "detalle": "Automatización de pruebas",
        "contacto": "Castellón · irene.vidal@correo-ficticio.es · 600 000 010",
        "secciones": [
            ("Perfil", "Ingeniera de calidad con siete años en automatización de pruebas y "
             "estrategia de testing. Me interesa más prevenir el defecto que encontrarlo, "
             "así que trabajo pegada a desarrollo desde el refinamiento y no al final del "
             "sprint. Defiendo pirámides de test con base ancha y poca punta."),
            ("Experiencia", "QA Automation Engineer en Flywire (2021-2026). Diseño de la "
             "estrategia de pruebas de la plataforma de pagos internacionales. Suite de "
             "regresión en Playwright que sustituyó a un plan manual de dos días y ahora "
             "corre en veinte minutos en cada pull request. Pruebas de contrato entre "
             "servicios con Pact, que eliminaron una familia recurrente de fallos de "
             "integración en preproducción. Introducción de pruebas de carga con k6 en el "
             "flujo de cobro. Formación al equipo de desarrollo para que escriban sus "
             "propias pruebas de integración. "
             "QA Engineer en Zeleros (2019-2021). Validación de software de control y "
             "documentación de trazabilidad de requisitos. "
             "Tester manual en Grupo Gimeno (2017-2019)."),
            ("Proyectos", "Entorno de datos de prueba reproducible con contenedores y "
             "semillas versionadas, que acabó con el clásico 'en mi entorno funciona'. "
             "Panel de salud de la suite que marca los tests inestables por tasa de fallo "
             "intermitente y los pone en cuarentena automáticamente."),
            ("Tecnologías", "Playwright, Cypress, Selenium, pytest, Jest, Pact, k6, JMeter, "
             "Python, TypeScript, SQL, Docker, GitHub Actions, Jira, Xray, Postman."),
            ("Formación", "Grado en Ingeniería Informática, Universitat Jaume I (2013-2017)."),
            ("Certificaciones", "ISTQB Foundation Level, 2018. ISTQB Advanced Test Analyst, "
             "2021."),
            ("Logros", "Reducción de los defectos que llegaban a producción un 45% en un "
             "año, medido sobre incidencias reportadas por cliente y no sobre defectos "
             "encontrados internamente. "
             "Recorte del tiempo de la suite de regresión de dos horas a veinte minutos "
             "mediante paralelización y eliminación de pruebas redundantes que "
             "verificaban lo mismo por caminos distintos. "
             "Implantación de la definición de terminado del equipo, que incluye criterios "
             "de prueba explícitos acordados en refinamiento."),
            ("Formación complementaria", "Curso de pruebas de rendimiento con k6 y análisis "
             "de resultados, 2024. Formación en pruebas de seguridad para equipos de QA, "
             "2023. Taller de pruebas basadas en propiedades, 2022."),
            ("Otros datos", "Disponibilidad para incorporación en un mes. Modelo híbrido "
             "en Castellón o València, o remoto. Carné de conducir B. Participo en el "
             "grupo de testing de la comunidad técnica valenciana y he impartido dos "
             "charlas sobre pruebas de contrato."),
            ("Idiomas", "Español nativo. Valenciano nativo. Inglés B2."),
        ],
    },
    {
        "archivo": "tomas_bravo_ciberseguridad.pdf",
        "nombre": "Tomás Bravo Linares",
        "puesto": "Analista de Ciberseguridad",
        "detalle": "Pentesting y respuesta a incidentes",
        "contacto": "Madrid · tomas.bravo@correo-ficticio.es · 600 000 011",
        "secciones": [
            ("Perfil", "Analista de seguridad ofensiva y defensiva con cinco años de "
             "experiencia. Hago pruebas de intrusión sobre aplicaciones web e "
             "infraestructura, y participo en la respuesta a incidentes. Escribo informes "
             "que un equipo de desarrollo puede accionar, no listados de herramienta "
             "pegados sin criterio."),
            ("Experiencia", "Pentester en S2 Grupo (2022-2026). Auditorías de aplicaciones "
             "web y APIs para clientes de banca, sanidad y administración pública. "
             "Ejercicios de red team con simulación de adversario y evasión de controles "
             "en entorno autorizado. Participación en el equipo de respuesta ante dos "
             "incidentes de ransomware, con contención, análisis forense y reconstrucción "
             "de la línea temporal del ataque. Revisión de código en busca de patrones "
             "vulnerables. "
             "Analista SOC de nivel 2 en Telefónica Tech (2020-2022). Triaje de alertas, "
             "creación de reglas de correlación en el SIEM y caza de amenazas sobre "
             "registros de red y de endpoint. "
             "Técnico de sistemas en Grupo Ibérica (2019-2020)."),
            ("Proyectos", "Descubrimiento y reporte responsable de una vulnerabilidad de "
             "control de acceso roto en un portal público, con su correspondiente CVE. "
             "Laboratorio interno de entrenamiento con máquinas vulnerables preparadas "
             "para formar a los analistas de nivel 1."),
            ("Tecnologías", "Burp Suite, Nmap, Metasploit, OWASP ZAP, Wireshark, Volatility, "
             "Splunk, Elastic Security, Sysmon, Python, Bash, PowerShell, Kali Linux, "
             "Active Directory, OWASP Top 10, MITRE ATT&CK."),
            ("Formación", "Máster en Ciberseguridad, Universidad Carlos III (2018-2019). "
             "Grado en Ingeniería Informática, Universidad Politécnica de Madrid "
             "(2014-2018)."),
            ("Logros", "Reducción del tiempo medio de detección de un incidente de "
             "catorce horas a cuarenta minutos, tras reescribir las reglas de correlación "
             "que generaban más ruido que señal. "
             "Corrección del 90% de los hallazgos críticos de la primera auditoría en el "
             "plazo acordado, gracias a informes con reproducción paso a paso y ejemplo "
             "de corrección en el lenguaje de cada equipo. "
             "Diseño del programa de concienciación en seguridad con campañas simuladas "
             "de phishing, que bajó la tasa de clic del 22% al 6%."),
            ("Certificaciones", "OSCP (Offensive Security Certified Professional), 2021. "
             "CEH, 2020."),
            ("Formación complementaria", "Curso de seguridad en entornos de contenedores y "
             "Kubernetes, 2024. Formación en análisis forense de memoria, 2023. Curso de "
             "seguridad en la nube y configuraciones erróneas frecuentes, 2022."),
            ("Otros datos", "Disponibilidad para incorporación en un mes. Modelo híbrido "
             "en Madrid. Disponibilidad para viajar a instalaciones de cliente. "
             "Habilitación de seguridad para trabajo con administración pública. Participo "
             "en competiciones de captura la bandera con un equipo estable desde 2019."),
            ("Idiomas", "Español nativo. Inglés C1."),
        ],
    },
    {
        "archivo": "sofia_marchetti_producto.pdf",
        "nombre": "Sofía Marchetti",
        "puesto": "Product Designer",
        "detalle": "Investigación y diseño de producto digital",
        "contacto": "Valencia · sofia.marchetti@correo-ficticio.es · 600 000 012",
        "secciones": [
            ("Perfil", "Diseñadora de producto con seis años entre investigación con "
             "usuarios y diseño de interfaz. Trabajo en equipos de producto junto a "
             "desarrollo, y disfruto especialmente de los problemas de flujo complejos "
             "donde la solución bonita no es la solución correcta."),
            ("Experiencia", "Product Designer en Jeff (2022-2026). Rediseño completo del "
             "flujo de reserva, con investigación previa mediante entrevistas y pruebas "
             "de usabilidad moderadas. La versión nueva subió la finalización de reserva "
             "un 22% en test A/B. Construcción y mantenimiento del sistema de diseño en "
             "Figma, con documentación de componentes y trabajo conjunto con frontend "
             "para que el código y el diseño no divergieran. "
             "Diseñadora UX/UI en Sngular (2019-2022). Proyectos de banca y seguros: "
             "arquitectura de información, prototipado y validación con usuarios reales. "
             "Diseñadora junior en estudio Tresmas (2018-2019)."),
            ("Proyectos", "Programa continuo de investigación con usuarios: seis "
             "entrevistas al mes con panel propio, cuyos hallazgos alimentan directamente "
             "el refinamiento del backlog. "
             "Revisión de accesibilidad del sistema de diseño con corrección de contraste "
             "y de orden de foco en veinte componentes."),
            ("Herramientas", "Figma, FigJam, Maze, Hotjar, Dovetail, Miro, Notion, "
             "Principle, nociones de HTML y CSS suficientes para hablar con desarrollo y "
             "revisar implementaciones."),
            ("Formación", "Grado en Diseño y Desarrollo de Videojuegos, Universitat Jaume I "
             "(2013-2017). Máster en Diseño de Interacción, ELISAVA (2017-2018)."),
            ("Logros", "Reducción de las consultas al servicio de atención al cliente "
             "relacionadas con el flujo de reserva un 31%, al reescribir los mensajes de "
             "error y los estados vacíos con lenguaje que explica qué hacer. "
             "Implantación de la práctica de que cada persona del equipo de producto "
             "asista a una sesión de usuario al trimestre, lo que cambió más decisiones "
             "que cualquier informe escrito. "
             "Unificación de tres bibliotecas de componentes divergentes en un único "
             "sistema con dueño y proceso de contribución definido."),
            ("Formación complementaria", "Curso de investigación cuantitativa aplicada a "
             "producto, 2024. Formación en diseño de servicios, 2023. Certificado de "
             "accesibilidad digital, 2022."),
            ("Otros datos", "Disponibilidad para incorporación en quince días. Modelo "
             "híbrido en Valencia o remoto. Interés en productos con complejidad "
             "operativa real más que en escaparates comerciales. Mentora en un programa "
             "de acompañamiento a diseñadoras junior."),
            ("Idiomas", "Español nativo. Italiano nativo. Inglés C1."),
        ],
    },
    {
        "archivo": "hugo_delgado_analista_bi.pdf",
        "nombre": "Hugo Delgado Ferrer",
        "puesto": "Analista de Datos y BI",
        "detalle": "Power BI y modelado analítico",
        "contacto": "Murcia · hugo.delgado@correo-ficticio.es · 600 000 013",
        "secciones": [
            ("Perfil", "Analista de datos con cinco años convirtiendo preguntas de negocio "
             "en modelos y cuadros de mando que se usan de verdad. Trabajo sobre todo con "
             "SQL y Power BI. Mi criterio es que un informe que nadie abre es trabajo "
             "perdido, así que empiezo siempre por la decisión que hay que tomar."),
            ("Experiencia", "Analista de datos sénior en Hero España (2022-2026). Modelo "
             "analítico de ventas y de cadena de suministro sobre el almacén corporativo, "
             "con capa semántica en Power BI compartida por comercial, operaciones y "
             "finanzas. Sustitución de un ecosistema de treinta ficheros Excel enviados "
             "por correo por seis cuadros de mando con datos certificados. Automatización "
             "del cierre mensual de indicadores, que pasó de cinco días a uno. Formación "
             "interna en autoservicio de datos para veinte personas de negocio. "
             "Analista de BI en Grupo Fuertes (2020-2022). Informes de producción y de "
             "mermas, y modelado dimensional en SQL Server Analysis Services. "
             "Becario de control de gestión en El Pozo (2019-2020)."),
            ("Proyectos", "Diccionario de métricas compartido que zanjó tres definiciones "
             "distintas de 'cliente activo' que convivían entre departamentos. "
             "Modelo de detección de anomalías en precios de compra que destapó "
             "desviaciones de proveedor por valor de 80.000 euros anuales."),
            ("Tecnologías", "SQL, T-SQL, Power BI, DAX, Power Query, SSAS, SSIS, Excel "
             "avanzado, Python para análisis con pandas, Snowflake, dbt básico, Git."),
            ("Logros", "Reducción del tiempo de respuesta a preguntas de negocio de una "
             "semana a menos de un día, al montar una capa de autoservicio con métricas "
             "ya validadas en lugar de atender cada petición a medida. "
             "Retirada de veintidós informes obsoletos tras un inventario de uso real, lo "
             "que liberó capacidad de mantenimiento y acabó con cifras contradictorias en "
             "circulación. "
             "Diseño del cuadro de mando de dirección que hoy se revisa en el comité "
             "semanal, con definición acordada de cada indicador."),
            ("Formación", "Grado en Administración y Dirección de Empresas, Universidad de "
             "Murcia (2015-2019). Máster en Business Intelligence y Big Data, EOI "
             "(2019-2020)."),
            ("Formación complementaria", "Curso avanzado de DAX y optimización de modelos "
             "tabulares, 2024. Formación en modelado dimensional según Kimball, 2023. "
             "Curso de storytelling con datos y diseño de cuadros de mando, 2022."),
            ("Otros datos", "Disponibilidad para incorporación en quince días. Modelo "
             "híbrido en Murcia o remoto. Carné de conducir B y vehículo propio. "
             "Acostumbrado a trabajar como puente entre negocio y equipos técnicos, "
             "traduciendo requisitos en ambas direcciones."),
            ("Idiomas", "Español nativo. Inglés B2."),
        ],
    },
    {
        "archivo": "priya_raghunathan_cloud.pdf",
        "nombre": "Priya Raghunathan",
        "puesto": "Cloud Architect",
        "detalle": "Platform design and governance",
        "contacto": "Dublin · priya.raghunathan@correo-ficticio.ie · +353 80 000 014",
        "secciones": [
            ("Profile", "Cloud architect with eleven years in infrastructure, the last six "
             "designing platforms for large migrations. I work between engineering teams "
             "and finance, which means I am as accountable for the monthly bill as for the "
             "architecture diagram. I favour boring, well understood building blocks."),
            ("Experience", "Principal Cloud Architect at Workhuman (2021-2026). Owned the "
             "target architecture for the migration of a monolithic estate across three "
             "regions, delivered in eighteen months with no customer facing downtime. "
             "Designed the landing zone, account structure and guardrails, including "
             "tagging policy and automated cost attribution per team. Drove a cost "
             "optimisation programme that cut monthly platform spend by 34% through right "
             "sizing, committed use discounts and shutting down forgotten environments. "
             "Chaired the architecture review board. "
             "Cloud Engineer at Version 1 (2017-2021). Infrastructure as code for public "
             "sector clients, mostly regulated workloads with strict data residency. "
             "Systems Engineer at Eircom (2014-2017). Virtualisation and storage."),
            ("Projects", "Multi account governance model with automated compliance checks, "
             "so that a new team gets a compliant account in under an hour instead of "
             "waiting three weeks for review. "
             "Disaster recovery design and quarterly game days with real failover, not "
             "tabletop exercises."),
            ("Technologies", "Terraform, Terragrunt, Kubernetes, Docker, Python, Go, "
             "networking and identity design, Datadog, well architected reviews, FinOps "
             "practices."),
            ("Education", "MSc Distributed Systems, Trinity College Dublin (2012-2013). "
             "BEng Electronic Engineering, Anna University (2008-2012)."),
            ("Certifications", "Certified Kubernetes Administrator, 2021. "
             "Professional level cloud architecture certification, 2022."),
            ("Achievements", "Brought platform provisioning time for a new product team "
             "from three weeks to under an hour through self service templates with "
             "policy built in. "
             "Ran the migration programme with zero customer facing downtime across "
             "eighteen months and forty two services, using a phased cutover with "
             "rollback rehearsed for each wave. "
             "Established the internal architecture decision record practice, so that the "
             "reasoning behind a choice survives the person who made it."),
            ("Additional training", "FinOps practitioner training, 2024. Course on zero "
             "trust network design, 2023. Training on regulated workloads and data "
             "residency requirements in the European Union, 2022."),
            ("Other", "Available at three months notice due to contractual terms. Open to "
             "hybrid work in Dublin or remote within the European Union. Regular speaker "
             "at cloud architecture meetups and mentor in a programme supporting women "
             "moving into infrastructure engineering."),
            ("Languages", "English native. Tamil native. Spanish A2."),
        ],
    },
    {
        "archivo": "elena_cortes_data_junior.pdf",
        "nombre": "Elena Cortés Rubio",
        "puesto": "Ingeniera de Datos Junior",
        "detalle": "Primer año de experiencia",
        "contacto": "Valladolid · elena.cortes@correo-ficticio.es · 600 000 015",
        "secciones": [
            ("Perfil", "Ingeniera de datos junior con un año de experiencia profesional y "
             "muchas ganas de crecer en el área. Vengo de un máster con proyecto aplicado "
             "y busco un equipo donde haya revisión de código y alguien de quien "
             "aprender. Me interesa especialmente la calidad del dato y la orquestación."),
            ("Experiencia", "Data Engineer junior en Grupo Norte (2025-2026). Mantenimiento "
             "y ampliación de pipelines en Airflow que alimentan el almacén analítico. "
             "Desarrollo de modelos en dbt para el área comercial bajo revisión de una "
             "persona sénior. Documentación de los orígenes de datos, que no existía, y "
             "creación de las primeras pruebas de frescura. "
             "Prácticas de análisis de datos en Michelin (2024-2025). Informes de "
             "producción en Power BI y limpieza de datos de sensores de planta."),
            ("Proyectos", "Proyecto de fin de máster: canalización completa de ingesta, "
             "modelado y visualización sobre datos abiertos de calidad del aire, con "
             "Airflow, Postgres y Metabase, desplegada con Docker Compose. "
             "Contribución menor a la documentación de un paquete de código abierto de "
             "utilidades para dbt."),
            ("Tecnologías", "Python, SQL, pandas, Apache Airflow, dbt, PostgreSQL, Docker, "
             "Git, Power BI. Nociones de Spark obtenidas en formación, sin experiencia en "
             "producción todavía."),
            ("Logros", "Documentación de los catorce orígenes de datos del almacén, que "
             "hasta entonces solo conocía una persona del equipo, y creación del glosario "
             "de campos asociado. "
             "Detección de un error silencioso de zona horaria en la ingesta que "
             "desplazaba un día los pedidos de madrugada, corregido con recarga histórica "
             "de dos años. "
             "Automatización del informe semanal de calidad de datos, que antes se "
             "montaba a mano cada lunes."),
            ("Formación", "Máster en Ingeniería de Datos, Universidad de Valladolid "
             "(2023-2024). Grado en Estadística, Universidad de Valladolid (2019-2023)."),
            ("Formación complementaria", "Curso de dbt de nivel intermedio, 2025. "
             "Formación en modelado dimensional, 2025. Curso de fundamentos de Docker y "
             "contenedores, 2024. Trabajo actualmente en la certificación de Airflow."),
            ("Otros datos", "Disponibilidad inmediata. Modelo híbrido en Valladolid o "
             "remoto. Disponibilidad para trasladarme por un proyecto interesante. Carné "
             "de conducir B. Busco explícitamente un puesto con acompañamiento técnico: "
             "me interesa más aprender bien que asumir responsabilidad pronto."),
            ("Idiomas", "Español nativo. Inglés B2."),
        ],
    },
    {
        "archivo": "javier_montes_contabilidad.pdf",
        "nombre": "Javier Montes Aliaga",
        "puesto": "Contable Sénior",
        "detalle": "Contabilidad financiera y fiscalidad",
        "contacto": "Alicante · javier.montes@correo-ficticio.es · 600 000 016",
        "secciones": [
            ("Perfil", "Contable con doce años de experiencia en contabilidad financiera, "
             "cierre y obligaciones fiscales. He trabajado en asesoría y en empresa, y "
             "estoy acostumbrado a cerrar con plazos ajustados y a defender los números "
             "ante auditoría externa."),
            ("Experiencia", "Responsable de contabilidad en Grupo Marjal (2019-2026). "
             "Cierre mensual y anual de tres sociedades del grupo, elaboración de cuentas "
             "anuales y memoria. Presentación de impuestos: IVA, retenciones, impuesto de "
             "sociedades y operaciones intracomunitarias. Interlocución con auditoría "
             "externa en seis ejercicios sin salvedades. Supervisión de un equipo de dos "
             "personas. Implantación de un nuevo plan analítico por centro de coste. "
             "Contable en asesoría Ruiz y Asociados (2014-2019). Cartera de cuarenta "
             "clientes de pequeña empresa y autónomos, con contabilidad completa, nóminas "
             "y asesoramiento fiscal básico. "
             "Auxiliar administrativo en Cerámicas Levante (2012-2014)."),
            ("Proyectos", "Migración del sistema contable de A3 a SAP Business One, "
             "incluida la conversión de saldos históricos y la formación del equipo. "
             "Automatización de la conciliación bancaria mediante importación de "
             "extractos normalizados, que ahorró dos días de trabajo al mes."),
            ("Competencias", "Plan General Contable, consolidación, fiscalidad de "
             "sociedades, IVA intracomunitario, SAP Business One, A3ASESOR, Sage, Excel "
             "avanzado con tablas dinámicas y macros básicas."),
            ("Formación", "Licenciatura en Administración y Dirección de Empresas, "
             "Universidad de Alicante (2007-2012). Curso superior de fiscalidad, Centro "
             "de Estudios Financieros (2016)."),
            ("Logros", "Reducción del plazo de cierre mensual de doce a cuatro días "
             "laborables, mediante calendario de tareas repartido y conciliaciones "
             "automáticas. "
             "Recuperación de 45.000 euros en cuotas de IVA soportado no deducidas en "
             "ejercicios anteriores, detectadas en una revisión sistemática de facturas "
             "de proveedor extranjero. "
             "Diseño del cuadro de indicadores financieros que la dirección revisa "
             "mensualmente, con margen por línea de negocio y previsión de tesorería a "
             "noventa días."),
            ("Formación complementaria", "Actualización anual en cierre contable y "
             "novedades fiscales, Centro de Estudios Financieros. Curso de consolidación "
             "de estados financieros, 2022. Formación en normativa de facturación "
             "electrónica y sistema Verifactu, 2025."),
            ("Otros datos", "Disponibilidad para incorporación en un mes por preaviso. "
             "Presencial o híbrido en Alicante. Carné de conducir B y vehículo propio. "
             "Acostumbrado a los picos de carga de los cierres trimestrales y de la "
             "campaña del impuesto de sociedades."),
            ("Idiomas", "Español nativo. Inglés A2."),
        ],
    },
]


def construir_pdf(perfil: dict) -> Path:
    """Escribe el PDF de un perfil.

    El orden de las dos primeras lineas no es estetico, es contractual:
    extract_text.py toma la linea 0 como nombre y la 1 como puesto para componer
    el nombre que se muestra en el ranking. Los datos de contacto van en tercer
    lugar precisamente para no ocupar ninguno de esos dos sitios.
    """
    ruta = CVS_DIR / perfil["archivo"]
    doc = SimpleDocTemplate(
        str(ruta),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=perfil["nombre"],
    )

    base = getSampleStyleSheet()
    estilo_nombre = ParagraphStyle(
        "nombre", parent=base["Title"], fontSize=17, spaceAfter=2, alignment=0
    )
    estilo_titular = ParagraphStyle(
        "titular", parent=base["Normal"], fontSize=10.5, textColor="#333333",
        spaceAfter=3,
    )
    estilo_contacto = ParagraphStyle(
        "contacto", parent=base["Normal"], fontSize=8.5, textColor="#666666",
        spaceAfter=12,
    )
    estilo_seccion = ParagraphStyle(
        "seccion", parent=base["Heading2"], fontSize=10.5, spaceBefore=9, spaceAfter=3
    )
    estilo_cuerpo = ParagraphStyle(
        "cuerpo", parent=base["Normal"], fontSize=9, leading=12.5
    )

    flujo = [
        Paragraph(perfil["nombre"], estilo_nombre),
        Paragraph(f"{perfil['puesto']} | {perfil['detalle']}", estilo_titular),
        Paragraph(perfil["contacto"], estilo_contacto),
    ]
    for titulo, cuerpo in perfil["secciones"]:
        flujo.append(Paragraph(titulo.upper(), estilo_seccion))
        flujo.append(Paragraph(cuerpo, estilo_cuerpo))
    flujo.append(Spacer(1, 0.4 * cm))

    doc.build(flujo)
    return ruta


def main() -> None:
    CVS_DIR.mkdir(exist_ok=True)
    total = 0
    for perfil in PERFILES:
        ruta = construir_pdf(perfil)
        caracteres = sum(len(c) for _, c in perfil["secciones"])
        total += caracteres
        print(f"  {ruta.name:<38} {caracteres:>5} caracteres")
    print(f"\n{len(PERFILES)} CVs ficticios en {CVS_DIR}")
    print(f"Longitud media: {total // len(PERFILES)} caracteres")


if __name__ == "__main__":
    main()
