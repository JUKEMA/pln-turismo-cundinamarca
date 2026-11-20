"""
Dashboard: análisis de sentimiento y tópicos en reseñas turísticas de Cundinamarca.
Curso de Procesamiento de Lenguaje Natural, Universidad de Cundinamarca (grupo 901).

Adaptado de la estructura de la plantilla "personal-finance-dashboard"
(pestañas Inicio / Dashboard / Datos / Documentación + filtros en la barra lateral),
pero sin base de datos ni Docker: lee directamente los CSV de la carpeta data/
generados por el cuaderno de Colab, para poder desplegarlo en Streamlit Community Cloud.

Ejecutar en local:  streamlit run app.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL (se puede ajustar sin tocar el resto del código)
# ----------------------------------------------------------------------------
DATA = Path(__file__).parent.parent / "data"
MIN_RESENAS = 200          # mínimo de reseñas para interpretar un grupo
MIN_LUGAR = 50             # por debajo de esto un lugar se marca "muestra pequeña"
MIN_N_ANIO = 30            # un año con menos reseñas no se grafica
FECHA_EXTRACCION = "2026-11-20"

# Términos poco informativos que salen en las alertas; se pueden ocultar desde la barra lateral
GENERICAS = {"parque", "niño", "pequeño", "malo", "subir", "entrar", "faltar",
             "privado", "permitir", "problema", "hora", "animal", "comida"}

# Las etiquetas automáticas de los tópicos son débiles. Si el grupo las renombra a mano,
# se escriben aquí, por ejemplo {0: "Compras y museo", 3: "Zoológico"}.
ETIQUETAS_MANUALES: dict[int, str] = {}

COLORES_SENT = {"positivo": "#2E8B57", "neutro": "#9AA0A6", "negativo": "#C0392B"}

st.set_page_config(page_title="Reseñas turísticas · Cundinamarca",
                   page_icon="🗺️", layout="wide")


# ----------------------------------------------------------------------------
# CARGA DE DATOS
# ----------------------------------------------------------------------------
@st.cache_data
def leer_csv(nombre: str) -> pd.DataFrame:
    return pd.read_csv(DATA / nombre)


@st.cache_data
def cargar_config() -> dict:
    with open(DATA / "config_ejecucion.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def cargar_resenas() -> pd.DataFrame:
    df = leer_csv("resenas_procesadas.csv")
    df["anio"] = pd.to_datetime(df["fecha"]).dt.year
    return df


@st.cache_data
def ic95_bootstrap(valores: np.ndarray, B: int = 2000, seed: int = 42):
    """Intervalo de confianza del 95% para la media por bootstrap percentil."""
    n = len(valores)
    if n < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    medias = valores[rng.integers(0, n, size=(B, n))].mean(axis=1)
    return (float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5)))


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


try:
    df = cargar_resenas()
    cfg = cargar_config()
except FileNotFoundError as e:
    st.error(f"No se encontró un archivo en la carpeta data/: {e}")
    st.stop()

# Etiquetas de tópicos (automáticas del cuaderno, con posibilidad de sobrescribir)
ETIQ = {int(k): v for k, v in cfg["etiquetas_topicos"].items()}
ETIQ.update(ETIQUETAS_MANUALES)
TCOLS = sorted([c for c in df.columns if c.startswith("topico_") and c[7:].isdigit()],
               key=lambda c: int(c[7:]))

# ----------------------------------------------------------------------------
# BARRA LATERAL: filtros
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")
    provincias = ["Todas"] + sorted(df["provincia"].unique())
    prov = st.selectbox("Provincia", provincias)
    base_mun = df if prov == "Todas" else df[df["provincia"] == prov]
    mun = st.selectbox("Municipio", ["Todos"] + sorted(base_mun["municipio_nombre"].unique()))
    a_min, a_max = int(df["anio"].min()), int(df["anio"].max())
    rango = st.slider("Años de la reseña (aproximados)", a_min, a_max, (a_min, a_max))
    sin_trunc = st.checkbox("Excluir reseñas truncadas por Google Maps", value=False,
                            help="Sirve para ver cuánto cambia el resultado sin los comentarios cortados.")
    st.divider()
    st.subheader("Alertas")
    min_apar = st.slider("Mínimo de oraciones negativas", 4, 15, 5)
    ocultar_gen = st.checkbox("Ocultar términos genéricos", value=True)
    st.caption("Los paneles de TF-IDF, alertas, temas de queja, reglas de decisión y RNT "
               "vienen precalculados con todo el corpus; no responden a los filtros de año ni de truncadas.")

# Aplicar filtros
dff = df.copy()
if prov != "Todas":
    dff = dff[dff["provincia"] == prov]
if mun != "Todos":
    dff = dff[dff["municipio_nombre"] == mun]
dff = dff[dff["anio"].between(*rango)]
if sin_trunc:
    dff = dff[~dff["truncada"]]

municipios_sel = sorted(dff["municipio_nombre"].unique())

# ----------------------------------------------------------------------------
# ENCABEZADO + NOTA DE LIMITACIONES (siempre visible)
# ----------------------------------------------------------------------------
st.title("Sentimiento y tópicos en reseñas turísticas de Cundinamarca")
st.caption("Sabana Centro (Zipaquirá, Nemocón, Guatavita) y Tequendama (La Mesa, San Antonio del Tequendama, Cachipay)")

pct_trunc = df["truncada"].mean()
pct_guat = (df["municipio_nombre"] == "Guatavita").mean()
st.warning(
    f"**Lee esto antes de interpretar.** Corpus de {len(df):,} reseñas reales de Google Maps recogidas por lugar "
    f"(muestra **no aleatoria**, sesgada hacia sitios muy turísticos). No traen estrellas, las fechas son "
    f"**aproximadas** (se calcularon desde «hace X años» con extracción al {FECHA_EXTRACCION}), "
    f"{pct(pct_trunc)} de los comentarios están truncados y Guatavita pesa {pct(pct_guat)} del corpus. "
    "La validación del sentimiento es concordancia entre métodos, **no** exactitud contra etiquetas humanas. "
    "Uso académico, citando la fuente."
)

if dff.empty:
    st.error("Los filtros no dejan ninguna reseña. Amplía el rango de años o quita filtros.")
    st.stop()

tab_inicio, tab_dash, tab_datos, tab_doc = st.tabs(["Inicio", "Dashboard", "Datos", "Documentación"])

# ----------------------------------------------------------------------------
# INICIO
# ----------------------------------------------------------------------------
with tab_inicio:
    st.subheader("¿Qué es este tablero?")
    st.markdown(
        """
        Convierte reseñas turísticas en texto libre en tres indicadores para la gestión pública:

        1. **Polaridad del sentimiento**, de −1 (muy negativo) a +1 (muy positivo).
        2. **Distribución de tópicos** con LDA (modelo probabilístico no supervisado).
        3. **Términos relevantes y alertas** con TF-IDF y *lift* sobre oraciones negativas.

        Además se contrasta, de forma descriptiva, con el Registro Nacional de Turismo (RNT) de datos.gov.co.
        """
    )
    st.subheader("Cómo usarlo")
    st.markdown(
        """
        - Elige provincia, municipio y rango de años en la barra lateral.
        - Ve a **Dashboard** y recorre las secciones: sentimiento, términos, tópicos, alertas y reglas, lugares y RNT.
        - En **Datos** están las tablas y en **Documentación** el pipeline, la configuración y las limitaciones.
        """
    )
    st.info("Lectura rápida: el sentimiento es mayoritariamente positivo, como es de esperar en parques, plazas y "
            "atractivos. Lo útil para decidir está en la minoría de reseñas con crítica y en sus temas, "
            "que son pocas en número; por eso cada gráfico muestra su n.")

# ----------------------------------------------------------------------------
# DASHBOARD
# ----------------------------------------------------------------------------
with tab_dash:
    # ---- Indicadores principales ----
    n = len(dff)
    media = dff["sentimiento"].mean()
    ic_inf, ic_sup = ic95_bootstrap(dff["sentimiento"].to_numpy())
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Reseñas", f"{n:,}")
    c2.metric("Polaridad media", f"{media:.3f}")
    c3.metric("IC 95% de la media", f"{ic_inf:.3f} a {ic_sup:.3f}")
    c4.metric("% positivas / negativas",
              f"{pct((dff['sent_label'] == 'positivo').mean())} / {pct((dff['sent_label'] == 'negativo').mean())}")
    c5.metric("% con alguna crítica", pct(dff["tiene_critica"].mean()))
    if n < MIN_RESENAS:
        st.warning(f"Solo hay {n} reseñas con estos filtros (mínimo recomendado: {MIN_RESENAS}). "
                   "Interpreta con mucha cautela.")

    sec = st.tabs(["Sentimiento", "Términos (TF-IDF)", "Tópicos (LDA)", "Alertas y reglas",
                   "Lugares", "RNT"])

    # ---- SENTIMIENTO ----
    with sec[0]:
        a, b = st.columns(2)
        with a:
            fig = px.histogram(dff, x="sentimiento", color="sent_label", nbins=40,
                               color_discrete_map=COLORES_SENT,
                               category_orders={"sent_label": ["negativo", "neutro", "positivo"]},
                               labels={"sentimiento": "Polaridad (P(pos) − P(neg))", "sent_label": "Clase"},
                               title="Distribución de la polaridad")
            fig.update_layout(yaxis_title="Reseñas")
            st.plotly_chart(fig, width="stretch")
            st.caption("La distribución es bimodal: la media resume mal una masa muy positiva y una cola negativa.")
        with b:
            comp = (dff.groupby(["municipio_nombre", "sent_label"]).size()
                    .unstack(fill_value=0).reindex(columns=["positivo", "neutro", "negativo"], fill_value=0))
            tot = comp.sum(axis=1)
            comp_pct = comp.div(tot, axis=0).reset_index().melt(
                id_vars="municipio_nombre", var_name="clase", value_name="porcentaje")
            comp_pct["n"] = comp_pct["municipio_nombre"].map(tot)
            fig = px.bar(comp_pct, x="porcentaje", y="municipio_nombre", color="clase", orientation="h",
                         color_discrete_map=COLORES_SENT, hover_data={"n": True},
                         labels={"municipio_nombre": "", "porcentaje": "% de reseñas"},
                         title="Clases de sentimiento por municipio")
            fig.update_xaxes(tickformat=".0%")
            st.plotly_chart(fig, width="stretch")

        # Media con IC por municipio
        filas = []
        for m, g in dff.groupby("municipio_nombre"):
            lo, hi = ic95_bootstrap(g["sentimiento"].to_numpy())
            filas.append({"municipio": m, "media": g["sentimiento"].mean(), "n": len(g),
                          "mas": hi - g["sentimiento"].mean(), "menos": g["sentimiento"].mean() - lo})
        tm = pd.DataFrame(filas).sort_values("media")
        fig = px.scatter(tm, x="media", y="municipio", error_x="mas", error_x_minus="menos",
                         hover_data={"n": True}, title="Polaridad media por municipio (IC 95% bootstrap)",
                         labels={"media": "Polaridad media", "municipio": ""})
        fig.update_traces(marker=dict(size=10))
        st.plotly_chart(fig, width="stretch")
        st.caption("Si los intervalos se traslapan, no hay evidencia clara de diferencia entre municipios. "
                   "Además, parte de la diferencia refleja qué lugares se recolectaron (ver pestaña Lugares).")

        # Evolución por año
        ya = (dff.groupby(["provincia", "anio"]).agg(n=("sentimiento", "size"), media=("sentimiento", "mean"))
              .reset_index())
        ya = ya[ya["n"] >= MIN_N_ANIO]
        if not ya.empty:
            fig = px.line(ya, x="anio", y="media", color="provincia", markers=True, hover_data={"n": True},
                          title=f"Polaridad media por año aproximado (años con al menos {MIN_N_ANIO} reseñas)",
                          labels={"anio": "Año", "media": "Polaridad media"})
            st.plotly_chart(fig, width="stretch")
            st.caption("Las fechas se reconstruyeron desde «hace X años», por eso solo se muestra el año.")

    # ---- TF-IDF ----
    with sec[1]:
        tfidf = leer_csv("tfidf_terminos_municipio.csv")
        tfidf = tfidf[tfidf["municipio"].isin(municipios_sel)]
        top_n = st.slider("Términos por municipio", 5, 20, 10)
        top = (tfidf.sort_values(["municipio", "tfidf"], ascending=[True, False])
               .groupby("municipio").head(top_n))
        if top.empty:
            st.info("No hay términos para los filtros elegidos.")
        else:
            fig = px.bar(top, x="tfidf", y="termino", facet_col="municipio", facet_col_wrap=3,
                         labels={"tfidf": "TF-IDF", "termino": ""},
                         title="Términos más característicos de cada municipio",
                         height=320 * ((top["municipio"].nunique() - 1) // 3 + 1))
            fig.update_yaxes(matches=None, showticklabels=True, categoryorder="total ascending")
            fig.update_xaxes(matches=None)
            fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
            st.plotly_chart(fig, width="stretch")
            st.caption("TF-IDF resalta lo que distingue a un municipio de los demás; con pocos lugares por municipio "
                       "(2 o 3), suele salir el nombre de atracciones concretas más que una queja.")

    # ---- TÓPICOS ----
    with sec[2]:
        dt = dff.dropna(subset=TCOLS[:1])
        sin_topico = 1 - len(dt) / len(dff)
        k = cfg["k_lda"]
        cv = cfg["coherencia_cv"][str(k)]
        st.caption(f"LDA con k = {k} (coherencia c_v = {cv:.3f}, valor bajo y casi plano entre k = 3 y 12). "
                   f"{pct(sin_topico)} de las reseñas filtradas no tienen tópico (texto vacío tras la limpieza). "
                   "Las etiquetas son automáticas: tómalas como exploratorias.")
        if dt.empty:
            st.info("No hay reseñas con tópico para estos filtros.")
        else:
            nombres = {c: ETIQ[int(c[7:])] for c in TCOLS}
            por_mun = dt.groupby("municipio_nombre")[TCOLS].mean().rename(columns=nombres)
            fig = px.imshow(por_mun, text_auto=".0%", aspect="auto", color_continuous_scale="Blues",
                            labels=dict(color="Peso medio"), title="Peso medio de cada tópico por municipio")
            fig.update_xaxes(tickangle=-40)
            fig.update_layout(height=420)
            st.plotly_chart(fig, width="stretch")

            por_prov = (dt.groupby("provincia")[TCOLS].mean().rename(columns=nombres)
                        .reset_index().melt(id_vars="provincia", var_name="topico", value_name="peso"))
            fig = px.bar(por_prov, x="peso", y="topico", color="provincia", barmode="group", orientation="h",
                         labels={"peso": "Peso medio", "topico": ""}, title="Tópicos por provincia")
            fig.update_xaxes(tickformat=".0%")
            fig.update_layout(height=520)
            st.plotly_chart(fig, width="stretch")

            # Sentimiento por tópico dominante
            dt = dt.assign(topico_nombre=dt["topico_dominante"].astype(int).map(ETIQ))
            tt = (dt.groupby("topico_nombre").agg(reseñas=("sentimiento", "size"),
                                                  polaridad_media=("sentimiento", "mean"),
                                                  pct_negativo=("sent_label", lambda s: (s == "negativo").mean()))
                  .sort_values("polaridad_media").reset_index().rename(columns={"topico_nombre": "tópico dominante"}))
            st.markdown("**Sentimiento según el tópico dominante de cada reseña**")
            st.dataframe(tt, hide_index=True, width="stretch",
                         column_config={"polaridad_media": st.column_config.NumberColumn(format="%.3f"),
                                        "pct_negativo": st.column_config.NumberColumn("% negativo", format="percent")})

            palabras = leer_csv("topicos_palabras.csv")
            palabras["etiqueta_vista"] = palabras["topico"].map(ETIQ)
            elegido = st.selectbox("Palabras principales de un tópico", [ETIQ[i] for i in sorted(ETIQ)])
            pw = palabras[palabras["etiqueta_vista"] == elegido].sort_values("rank").head(15)
            fig = px.bar(pw, x="peso", y="palabra", orientation="h", labels={"peso": "Peso", "palabra": ""})
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, width="stretch")

    # ---- ALERTAS Y REGLAS ----
    with sec[3]:
        st.markdown("#### Alertas: términos en oraciones negativas")
        st.caption("Con pocas apariciones (4 a 15 oraciones), el *lift* se infla: úsalo para ubicar ejemplos, "
                   "no como indicador. La tabla se ordena por número de oraciones, no por lift.")

        def mostrar_alertas(tabla: pd.DataFrame, titulo: str):
            t = tabla[tabla["n_oraciones_neg"] >= min_apar].copy()
            if ocultar_gen:
                t = t[~t["termino"].isin(GENERICAS)]
            t = t.sort_values(["n_oraciones_neg", "lift"], ascending=False)
            st.markdown(f"**{titulo}**")
            if t.empty:
                st.info("Sin términos que cumplan los criterios (prueba bajar el mínimo en la barra lateral).")
                return
            st.dataframe(t[["termino", "n_oraciones_neg", "lift", "ejemplo"]], hide_index=True, width="stretch",
                         column_config={"termino": "Término", "n_oraciones_neg": "Oraciones negativas",
                                        "lift": st.column_config.NumberColumn("Lift", format="%.1f"),
                                        "ejemplo": st.column_config.TextColumn("Ejemplo", width="large")})

        alert_p = leer_csv("alertas_negativas_provincia.csv")
        alert_m = leer_csv("alertas_negativas_municipio.csv")
        if mun != "Todos":
            mostrar_alertas(alert_m[alert_m["municipio_nombre"] == mun], f"Alertas en {mun}")
        else:
            for p in ([prov] if prov != "Todas" else sorted(alert_p["provincia"].unique())):
                mostrar_alertas(alert_p[alert_p["provincia"] == p], f"Alertas en {p}")
            with st.expander("Ver alertas por municipio"):
                for m in municipios_sel:
                    mostrar_alertas(alert_m[alert_m["municipio_nombre"] == m], m)

        st.divider()
        st.markdown("#### Temas de queja (% de reseñas que mencionan cada tema)")
        pt = leer_csv("problemas_por_tema.csv")
        pt = pt[pt["tema"] != "Sin tema identificado"]
        if mun != "Todos":
            pt = pt[(pt["nivel"] == "municipio") & (pt["grupo"] == mun)]
        elif prov != "Todas":
            pt = pt[(pt["nivel"] == "provincia") & (pt["grupo"] == prov)]
        else:
            pt = pt[pt["nivel"] == "provincia"]
        pt = pt.assign(mas=pt["ic95_sup"] - pt["pct_resenas"], menos=pt["pct_resenas"] - pt["ic95_inf"])
        fig = px.bar(pt, x="pct_resenas", y="tema", color="grupo", barmode="group", orientation="h",
                     error_x="mas", error_x_minus="menos", hover_data={"n_resenas_tema": True},
                     labels={"pct_resenas": "% de reseñas", "tema": "", "grupo": ""},
                     title="Temas de queja con IC 95%")
        fig.update_xaxes(tickformat=".1%")
        fig.update_yaxes(categoryorder="total ascending")
        fig.update_layout(height=520)
        st.plotly_chart(fig, width="stretch")
        st.caption("Cada tema agrupa pocas reseñas (pasa el cursor para ver el n). Los intervalos son anchos.")

        st.divider()
        st.markdown("#### Reglas de decisión: ¿se sostienen con los datos?")
        reglas = leer_csv("reglas_decision.csv")
        sig = reglas[reglas["significativa"]]
        if sig.empty:
            st.info("Ningún tema muestra diferencia significativa entre provincias tras corregir por comparaciones múltiples.")
        else:
            txt = "; ".join(f"{r.tema} (mayor en {r.provincia_mayor}, {abs(r.diferencia_pp):.2f} pp)"
                            for r in sig.itertuples())
            st.success(f"Diferencias significativas entre provincias (p ajustado < 0,05): {txt}.")
        st.dataframe(
            reglas[["tema", "pct_sabana_centro", "pct_tequendama", "diferencia_pp", "n_sabana_centro",
                    "n_tequendama", "p_ajustada", "significativa", "solidez", "accion_sugerida"]],
            hide_index=True, width="stretch",
            column_config={"pct_sabana_centro": st.column_config.NumberColumn("% Sabana Centro", format="percent"),
                           "pct_tequendama": st.column_config.NumberColumn("% Tequendama", format="percent"),
                           "diferencia_pp": st.column_config.NumberColumn("Dif. (pp)", format="%.2f"),
                           "p_ajustada": st.column_config.NumberColumn("p ajustado", format="%.3f"),
                           "accion_sugerida": st.column_config.TextColumn("Acción sugerida", width="large")})
        st.caption("Solo se sugiere acción donde la diferencia es significativa y hay suficientes reseñas. "
                   "Vías, precios y atención no cumplen ese criterio con esta muestra.")

    # ---- LUGARES ----
    with sec[4]:
        lugares = (dff.groupby(["municipio_nombre", "lugar_nombre"])
                   .agg(n=("sentimiento", "size"), polaridad_media=("sentimiento", "mean"),
                        pct_negativo=("sent_label", lambda s: (s == "negativo").mean()),
                        pct_con_critica=("tiene_critica", "mean"))
                   .reset_index())
        lugares["muestra_pequena"] = lugares["n"] < MIN_LUGAR
        lugares["lugar"] = lugares["lugar_nombre"] + np.where(lugares["muestra_pequena"], " *", "")
        lugares = lugares.sort_values("polaridad_media")
        fig = px.bar(lugares, x="polaridad_media", y="lugar", color="municipio_nombre", orientation="h",
                     hover_data={"n": True, "lugar": False}, text="n",
                     labels={"polaridad_media": "Polaridad media", "lugar": "", "municipio_nombre": "Municipio"},
                     title="Polaridad media por lugar (el número es la cantidad de reseñas)")
        fig.update_layout(height=max(380, 28 * len(lugares)))
        st.plotly_chart(fig, width="stretch")
        st.caption(f"* Muestra pequeña (menos de {MIN_LUGAR} reseñas): no es comparable con los demás lugares.")
        st.dataframe(lugares[["municipio_nombre", "lugar_nombre", "n", "polaridad_media", "pct_negativo",
                              "pct_con_critica", "muestra_pequena"]],
                     hide_index=True, width="stretch",
                     column_config={"municipio_nombre": "Municipio", "lugar_nombre": "Lugar",
                                    "polaridad_media": st.column_config.NumberColumn("Polaridad media", format="%.3f"),
                                    "pct_negativo": st.column_config.NumberColumn("% negativo", format="percent"),
                                    "pct_con_critica": st.column_config.NumberColumn("% con crítica", format="percent")})

    # ---- RNT ----
    with sec[5]:
        rnt = leer_csv("rnt_por_categoria.csv")
        rnt = rnt[rnt["municipio_nombre"].isin(municipios_sel)]
        fig = px.bar(rnt, x="prestadores", y="municipio_nombre", color="categoria", orientation="h",
                     labels={"prestadores": "Prestadores activos", "municipio_nombre": "", "categoria": "Categoría"},
                     title="Prestadores activos en el RNT por municipio y categoría")
        fig.update_layout(height=420)
        st.plotly_chart(fig, width="stretch")
        met = leer_csv("metricas_municipio.csv")[["municipio_nombre", "prestadores_rnt"]]
        cmp_ = (dff.groupby("municipio_nombre").agg(reseñas=("sentimiento", "size"),
                                                    polaridad_media=("sentimiento", "mean"))
                .reset_index().merge(met, on="municipio_nombre", how="left"))
        st.dataframe(cmp_, hide_index=True, width="stretch",
                     column_config={"municipio_nombre": "Municipio", "prestadores_rnt": "Prestadores RNT",
                                    "polaridad_media": st.column_config.NumberColumn("Polaridad media", format="%.3f")})
        st.caption("Cruce solo descriptivo: son 6 municipios y las reseñas corresponden a lugares públicos "
                   "(parques, embalses, minas), no a los prestadores registrados. No se calcula correlación.")

# ----------------------------------------------------------------------------
# DATOS
# ----------------------------------------------------------------------------
with tab_datos:
    st.subheader("Tablas de salida")
    met_mun = (dff.groupby(["provincia", "municipio_nombre"])
               .agg(reseñas=("sentimiento", "size"), polaridad_media=("sentimiento", "mean"),
                    pct_positivo=("sent_label", lambda s: (s == "positivo").mean()),
                    pct_neutro=("sent_label", lambda s: (s == "neutro").mean()),
                    pct_negativo=("sent_label", lambda s: (s == "negativo").mean()),
                    pct_con_critica=("tiene_critica", "mean"),
                    pct_truncadas=("truncada", "mean")).reset_index())
    with st.expander("Métricas por municipio (según filtros)", expanded=True):
        st.dataframe(met_mun, hide_index=True, width="stretch")
        st.download_button("Descargar métricas (CSV)", met_mun.to_csv(index=False).encode("utf-8-sig"),
                           file_name="metricas_municipio_filtradas.csv", mime="text/csv")
    with st.expander("Muestra de reseñas procesadas"):
        cols = ["municipio_nombre", "lugar_nombre", "anio", "sentimiento", "sent_label", "tiene_critica",
                "truncada", "etiqueta_topico", "texto_resena"]
        st.dataframe(dff[cols].head(300), hide_index=True, width="stretch")
        st.caption("Se muestran las primeras 300 reseñas del filtro. Los textos son reseñas públicas de "
                   "Google Maps, solo para análisis académico.")
    with st.expander("Palabras de los tópicos"):
        st.dataframe(leer_csv("topicos_palabras.csv"), hide_index=True, width="stretch")

# ----------------------------------------------------------------------------
# DOCUMENTACIÓN
# ----------------------------------------------------------------------------
with tab_doc:
    st.subheader("Pipeline")
    st.markdown(
        f"""
        1. **Recolección:** reseñas de Google Maps lugar por lugar con la extensión Instant Data Scraper
           (17 archivos CSV), extracción al {FECHA_EXTRACCION}.
        2. **Limpieza:** HTML, duplicados, longitud mínima (15 caracteres y 3 palabras) y filtro de español
           con `langdetect`. Quedan **{cfg['n_resenas']:,}** reseñas.
        3. **Lingüística:** spaCy `{cfg['config']['SPACY_MODELO']}` (nota: el documento de planificación decía
           `es_core_news_sm`), solo sustantivos, adjetivos y verbos lematizados, sin stopwords ni topónimos, con bigramas de gensim.
        4. **Sentimiento:** `pysentimiento`, polaridad = P(positivo) − P(negativo), con reseñas largas partidas por oraciones
           ({cfg['n_oraciones']:,} oraciones).
        5. **TF-IDF** por municipio y **alertas** por *lift* en oraciones negativas.
        6. **LDA** con gensim, k elegido por coherencia c_v entre {cfg['config']['LDA_K_MIN']} y {cfg['config']['LDA_K_MAX']}.
        7. **Cruce descriptivo** con el RNT (solo prestadores en estado ACTIVO).
        """
    )
    coh = pd.DataFrame({"k": [int(k) for k in cfg["coherencia_cv"]],
                        "coherencia_cv": list(cfg["coherencia_cv"].values())})
    fig = px.line(coh, x="k", y="coherencia_cv", markers=True, title="Coherencia c_v según el número de tópicos")
    fig.update_yaxes(range=[0, 0.5])
    st.plotly_chart(fig, width="stretch")

    st.subheader("Limitaciones de los datos")
    st.markdown(
        """
        - Las reseñas **no traen estrellas**; no hay verdad de referencia para el sentimiento.
        - Las **fechas son aproximadas**, calculadas desde «hace 2 años» y similares.
        - Google Maps **trunca** una parte de los comentarios (columna `truncada`).
        - **Muestra no aleatoria**, sesgada hacia lugares muy turísticos; cada municipio tiene entre 2 y 3 lugares.
        - **Guatavita pesa mucho** en el corpus, y la diferencia entre provincias se mezcla con la composición de lugares.
        - La **validación** del sentimiento es concordancia entre métodos, no exactitud frente a etiquetas humanas.
        - Los temas de queja y las alertas se basan en **pocas reseñas**; son pistas para revisar, no mediciones precisas.
        - Las reseñas de Google tienen restricciones de uso: solo análisis académico y citando la fuente.
        """
    )
    st.subheader("Equipo y referencias")
    st.markdown(
        """
        Brandon Iván Castiblanco Castro, Juan Miguel Pérez Gil, Kevin Leandro Ramírez Poveda y Luigy Camilo Arias Torres.
        Procesamiento de Lenguaje Natural, grupo 901, Universidad de Cundinamarca. Docente: Ing. Freddy Orlando Martínez Bernal.

        Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet allocation. *Journal of Machine Learning Research, 3*, 993–1022.

        Ministerio de Comercio, Industria y Turismo (2026). Registro Nacional de Turismo (RNT) de Cundinamarca. Datos Abiertos Colombia (datos.gov.co).
        """
    )
