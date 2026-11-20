# Documento Maestro de Planificación, Contexto y Ejecución
## Proyecto de Procesamiento de Lenguaje Natural (PLN)

---

### 1. Identificación Institucional y Académica
* **Título del Proyecto:** Análisis de Sentimiento y Modelado de Tópicos mediante Procesamiento de Lenguaje Natural sobre Reseñas Ciudadanas y Turísticas en Municipios Prioritarios de Cundinamarca.
* **Institución:** Universidad de Cundinamarca – Facultad de Ingeniería.
* **Asignatura:** Procesamiento de Lenguaje Natural (PLN) – Grupo 91.
* **Docente:** Ing. Freddy Orlando Martinez Bernal.
* **Integrantes del Equipo:**
  * Brandon Ivan Castiblanco Castro
  * Juan Miguel Perez Gil
  * Kevin Leandro Ramírez Poveda
  * Luigy Camilo Arias Torres

---

### 2. Planteamiento del Problema y Justificación
* **Área de Estudio:** Desarrollo económico regional, competitividad turística y análisis de retroalimentación ciudadana no estructurada en Cundinamarca.
* **Situación Actual:** Los municipios turísticos de Cundinamarca reciben un volumen masivo de comentarios, opiniones y quejas en plataformas digitales (Google Places, TripAdvisor) en formato de texto libre (*unstructured text*). Las alcaldías y entidades departamentales carecen de sistemas automatizados para procesar estos datos, haciendo que el análisis manual sea costoso e inviable.
* **Justificación Técnica:** El uso de técnicas de PLN permite transformar opiniones cualitativas dispersas en indicadores cuantitativos accionables para la gestión pública y empresarial.

---

### 3. Delimitación Geográfica y Vocación Turística
El análisis se focaliza en seis (6) municipios estratégicos divididos en dos provincias con perfiles diferenciados:

| Provincia | Municipios Focales | Enfoque y Perfil Turístico |
| :--- | :--- | :--- |
| **Sabana Centro** | Zipaquirá, Nemocón, Guatavita | Turismo patrimonial, histórico, cultural y de grandes atractivos (Catedral de Sal, Mina, Embalse). |
| **Tequendama** | La Mesa, San Antonio del Tequendama, Cachipay | Ecoturismo, agroturismo, clima cálido, fincas de descanso y naturaleza. |

---

### 4. Factores e Índices a Rastrear
El sistema extraerá y calculará tres métricas fundamentales a partir del corpus textual:
1. **Polaridad del Sentimiento (*Sentiment Score*):** Cuantificación continua de la carga emocional en un rango de **$-1.0$** (extremadamente negativo) a **$+1.0$** (extremadamente positivo).
2. **Distribución de Tópicos Ocultos (*Topic Ratio*):** Agrupación probabilística no supervisada mediante LDA para descubrir problemáticas o virtudes latentes (vías, sobrecostos, atención al cliente, parqueaderos, seguridad).
3. **Frecuencia y Relevancia de Términos (TF-IDF):** Ponderación estadística para detectar términos críticos o alertas recurrentes específicas de cada municipio.

---

### 5. Arquitectura de Datos y Fuentes
Para garantizar auditabilidad, rigor y velocidad de ejecución, el proyecto integra dos fuentes complementarias:

1. **Corpus Textual No Estructurado (Reseñas Digitales):**
   * **Volumen objetivo:** Entre $5,000$ y $15,000$ reseñas en español.
   * **Origen:** Reseñas de Google Places y TripAdvisor, respaldadas mediante datasets públicos validados en **Kaggle** y extracción controlada con Python.
   * **Variables:** Texto del comentario, calificación en estrellas ($1$ a $5$), fecha y municipio.
2. **Registro Oficial Estructurado (Datos Abiertos Colombia):**
   * **Origen:** Registro Nacional de Turismo (RNT) del Ministerio de Comercio, Industria y Turismo (MinCIT), descargado desde `datos.gov.co`.
   * **Propósito:** Cruzar y correlacionar la satisfacción turística percibida con el nivel de formalización comercial de los prestadores de servicios en cada municipio.

---

### 6. Pipeline Técnico de PLN (Arquitectura del Software)
El flujo de procesamiento de datos en Python seguirá estrictamente cinco etapas secuenciales:

1. **Ingesta y Limpieza:** Estandarización a minúsculas, remoción de signos de puntuación, caracteres especiales, URLs, emojis y eliminación de *stopwords* en español.
2. **Lematización:** Normalización morfológica utilizando la librería `spaCy` con su modelo en español (`es_core_news_sm`) para reducir palabras a su raíz canónica.
3. **Vectorización:** Transformación del texto lematizado a una representación matricial numérica mediante **TF-IDF** (*Term Frequency - Inverse Document Frequency*).
4. **Modelado de Tópicos:** Entrenamiento de un modelo **LDA** (*Latent Dirichlet Allocation*) para extraer los temas dominantes por provincia y municipio.
5. **Análisis de Sentimiento:** Cálculo automatizado de la polaridad emocional ($-1.0$ a $+1.0$) utilizando modelos preentrenados o enfoques léxicos adaptados al español.

---

### 7. Plan de Ejecución Ágil (Asistido por IA)
Debido a la prioridad de entrega rápida, el desarrollo no se rige por fechas rígidas, sino por un **flujo secuencial de hitos entregables**, optimizando el tiempo mediante generación de código modular con IA:

* **Hito 1: Preparación y Estructuración de Datos (`data/`)**
  * *Objetivo:* Consolidar el dataset de reseñas y el CSV del RNT filtrados para los 6 municipios.
  * *Entregable:* Carpeta `data/` con archivos `.csv` limpios y listos para ingesta.
* **Hito 2: Desarrollo del Motor de PLN (`notebooks/`)**
  * *Objetivo:* Implementar el pipeline completo (SpaCy, TF-IDF, LDA y Sentimiento) en Python / Google Colab.
  * *Entregable:* Notebook ejecutable (`.ipynb`) que exporte las métricas procesadas y los modelos entrenados.
* **Hito 3: Despliegue de Interfaz Visual (`app.py`)**
  * *Objetivo:* Construir un *dashboard* interactivo ligero utilizando **Streamlit**.
  * *Funcionalidad:* Filtros por provincia y municipio, visualización de polaridad promedio, nubes de palabras / términos TF-IDF y distribución de tópicos LDA.
  * *Entregable:* Aplicación web desplegada en la nube (Streamlit Community Cloud o Hugging Face Spaces).
* **Hito 4: Documentación Técnica y Cierre (`docs/` y `README.md`)**
  * *Objetivo:* Redactar el informe final académico con análisis de resultados, conclusiones e impacto, junto con la documentación del repositorio en GitHub.
  * *Entregable:* Documento final en formato académico y repositorio estructurado.

---

### 8. Grupos de Interés (*Stakeholders*) y Decisiones Prácticas
Los resultados del sistema están diseñados para orientar decisiones institucionales reales:
* **Entidades Beneficiarias:** Secretaría de Competitividad y Desarrollo Económico de Cundinamarca, Alcaldías y Secretarías de Turismo de los 6 municipios focales, Instituto Departamental de Cultura y Turismo (IDECUT) y Cámaras de Comercio regionales.
* **Acciones Derivadas:**
  * *Infraestructura:* Priorizar inversión vial y señalización si en la provincia del Tequendama predominan tópicos negativos asociados a tráfico o estado de vías.
  * *Competitividad Comercial:* Focalizar capacitaciones en servicio al cliente y regulación de tarifas si Sabana Centro arroja alertas de sobrecostos o mala atención.

---

### 9. Referencias Base y Recursos Técnicos
* Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). *Latent Dirichlet allocation.* Journal of Machine Learning Research, 3, 993–1022.
* Ministerio de Comercio, Industria y Turismo - MinCIT. (2026). *Registro Nacional de Turismo (RNT) de Cundinamarca.* Datos Abiertos Colombia (`datos.gov.co`).
* SpaCy. (2026). *Industrial-strength Natural Language Processing in Python: Spanish Models (`es_core_news_sm`).* Explosion AI.