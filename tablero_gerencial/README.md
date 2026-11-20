# Tablero gerencial - Turismo Cundinamarca

    pip install -r requirements.txt
    streamlit run app.py

Lee los CSV de `data/` generados por el notebook. Despliegue: Streamlit Community Cloud (archivo principal `app.py`).

## Estructura
- `app.py` → **Tablero gerencial** (página principal): prioridades, plan de acción, fortalezas, límites.
- `pages/2_Analisis_detallado.py` → dashboard técnico original (sentimiento, TF-IDF, tópicos LDA, datos).
- `data/` → CSV generados por el notebook.
