"""Tablero gerencial: reseñas turísticas de Cundinamarca (Sabana Centro y Tequendama).
Responde: ¿dónde estamos mal?, ¿por qué?, ¿qué hacemos y quién lo hace?
Ejecutar:  streamlit run app.py
"""
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).parent / "data"
MIN_TEMA = 8  # reseñas mínimas para considerar un tema como evidencia sólida
st.set_page_config(page_title="Tablero gerencial · Turismo Cundinamarca", page_icon="📊", layout="wide")

# Acción recomendada y responsable por tema de queja
ACCIONES = {
    "Limpieza y mantenimiento": ("Plan de aseo: puntos de residuos, baños y mantenimiento de espacios públicos", "Alcaldía / Sec. Servicios Públicos", "0-3 meses"),
    "Infraestructura y comodidad": ("Mejorar sombra, asientos, accesibilidad y señalización interna", "Sec. Turismo / Obras", "3-6 meses"),
    "Vías y acceso": ("Priorizar mantenimiento vial y señalización de accesos a atractivos", "Sec. Infraestructura / Gobernación", "6-12 meses"),
    "Precios y cobros": ("Transparentar tarifas y vigilar sobrecostos con el sector comercial", "Cámara de Comercio / Sec. Turismo", "0-3 meses"),
    "Atención y servicio": ("Capacitación en servicio al cliente a prestadores", "IDECUT / Cámara de Comercio", "3-6 meses"),
    "Parqueadero, filas y aglomeración": ("Ordenar parqueo, reserva de cupos y control de aforo", "Sec. Movilidad / Turismo", "3-6 meses"),
    "Seguridad": ("Presencia de apoyo turístico y vigilancia en puntos críticos", "Alcaldía / Policía de Turismo", "0-3 meses"),
    "Horarios y restricciones": ("Publicar horarios y reglas de ingreso de forma clara", "Operadores de atractivos", "0-3 meses"),
    "Comida y gastronomía": ("Estandarizar calidad y precios de oferta gastronómica", "Cámara de Comercio", "6-12 meses"),
    "Ruido y ambiente": ("Normas de ruido y convivencia en zonas turísticas", "Alcaldía", "3-6 meses"),
    "Obras y diseño del espacio": ("Coordinar obras para no afectar la experiencia del visitante", "Sec. Obras", "6-12 meses"),
    "Bienestar animal": ("Revisar condiciones de atracciones con animales", "Autoridad ambiental", "6-12 meses"),
}
COL = {"Alta": "#C0392B", "Media": "#E6A23C", "Baja": "#2E8B57"}


@st.cache_data
def csv(n):
    return pd.read_csv(DATA / n)


met, prov = csv("metricas_municipio.csv"), None
res = csv("resenas_procesadas.csv")
temas = csv("problemas_por_tema.csv")
temas = temas[(temas.nivel == "municipio") & (temas.tema != "Sin tema identificado")]
reglas = csv("reglas_decision.csv")
alert = csv("alertas_negativas_municipio.csv")
cfg = json.load(open(DATA / "config_ejecucion.json", encoding="utf-8"))

# ---- Indicadores globales y semáforo ----
N = met.n_resenas.sum()
g_sent = (met.sent_medio * met.n_resenas).sum() / N
g_neg = (met.pct_negativo * met.n_resenas).sum() / N
g_crit = (met.pct_con_critica * met.n_resenas).sum() / N
met["idx_riesgo"] = 100 * (0.5 * met.pct_negativo / g_neg + 0.5 * met.pct_con_critica / g_crit) / 2
met["prioridad"] = pd.cut(met.idx_riesgo, [-1, 45, 60, 1e9], labels=["Baja", "Media", "Alta"])
met = met.sort_values("idx_riesgo", ascending=False).reset_index(drop=True)
top_tema = (temas[temas.n_resenas_tema >= 1].sort_values("pct_resenas", ascending=False)
            .groupby("grupo").head(3))


def plan():
    filas = []
    for _, m in met.iterrows():
        t = top_tema[top_tema.grupo == m.municipio_nombre]
        for i, (_, r) in enumerate(t.iterrows()):
            a, resp, plz = ACCIONES[r.tema]
            filas.append(dict(Municipio=m.municipio_nombre, Prioridad=str(m.prioridad), Rank=i + 1, Tema=r.tema,
                              **{"% reseñas que lo mencionan": f"{r.pct_resenas:.1%}", "Reseñas": int(r.n_resenas_tema)},
                              Evidencia="Sólida" if r.n_resenas_tema >= MIN_TEMA else "Preliminar",
                              Acción=a, Responsable=resp, Plazo=plz))
    return pd.DataFrame(filas)


PLAN = plan()

# ---- Encabezado ----
st.title("📊 Tablero gerencial · Turismo en Cundinamarca")
st.caption(f"Qué dicen {int(N):,} reseñas de Google Maps sobre 6 municipios (Sabana Centro y Tequendama) "
           f"y qué decisiones se derivan. Datos extraídos el 2026-11-20.")

peor = met.iloc[0]
c = st.columns(4)
c[0].metric("Percepción global (−1 a +1)", f"{g_sent:.2f}", help="Promedio de polaridad de las reseñas")
c[1].metric("Reseñas negativas", f"{g_neg:.1%}")
c[2].metric("Reseñas con alguna crítica", f"{g_crit:.1%}", help="Incluso reseñas positivas pueden traer una queja puntual")
c[3].metric("Municipio prioritario", peor.municipio_nombre, f"{peor.pct_negativo:.1%} negativas", delta_color="inverse")

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Resumen ejecutivo", "🛠️ Plan de acción", "💪 Fortalezas a potenciar", "🔎 Evidencia y límites"])

# =============== TAB 1 ===============
with tab1:
    sc, tq = met[met.provincia == "Sabana Centro"], met[met.provincia == "Tequendama"]
    pn = lambda d: (d.pct_negativo * d.n_resenas).sum() / d.n_resenas.sum()
    pc = lambda d: (d.pct_con_critica * d.n_resenas).sum() / d.n_resenas.sum()
    sig = reglas[reglas.significativa]
    st.subheader("Hallazgos clave")
    h = [f"**La percepción es buena en general**: {g_sent:.2f} de 1.00 y {1 - g_neg:.0%} de reseñas no negativas. "
         f"El problema no es la imagen sino puntos específicos de la experiencia.",
         f"**Tequendama requiere más atención**: {pn(tq):.1%} de reseñas negativas frente a {pn(sc):.1%} en Sabana Centro, "
         f"y {pc(tq):.1%} con crítica frente a {pc(sc):.1%}."]
    for _, r in sig.iterrows():
        h.append(f"**{r.tema}** es una queja significativamente mayor en {r.provincia_mayor} "
                 f"({abs(r.diferencia_pp):.1f} puntos porcentuales de diferencia, validado estadísticamente).")
    h.append(f"**Prioridad de intervención**: {', '.join(met[met.prioridad == 'Alta'].municipio_nombre) or 'ninguno en nivel alto'} "
             f"(alto riesgo); {', '.join(met[met.prioridad == 'Media'].municipio_nombre) or 'ninguno'} (vigilancia).")
    for x in h:
        st.markdown(f"- {x}")

    st.subheader("Semáforo de prioridad por municipio")
    st.caption("Índice de riesgo = promedio de % negativas y % con crítica, relativo al promedio global (100 = promedio).")
    fig = px.bar(met.sort_values("idx_riesgo"), x="idx_riesgo", y="municipio_nombre", color="prioridad",
                 color_discrete_map=COL, orientation="h", text=met.sort_values("idx_riesgo").idx_riesgo.round(0),
                 labels={"idx_riesgo": "Índice de riesgo", "municipio_nombre": "", "prioridad": "Prioridad"})
    fig.add_vline(x=100, line_dash="dot", annotation_text="promedio global")
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width='stretch')

    t = met[["municipio_nombre", "provincia", "prioridad", "n_resenas", "sent_medio", "pct_negativo", "pct_con_critica"]].copy()
    t.columns = ["Municipio", "Provincia", "Prioridad", "Reseñas", "Sentimiento", "% negativas", "% con crítica"]
    st.dataframe(t.style.format({"Sentimiento": "{:.2f}", "% negativas": "{:.1%}", "% con crítica": "{:.1%}"}),
                 hide_index=True, width='stretch')

# =============== TAB 2 ===============
with tab2:
    st.subheader("¿Qué mejorar, dónde y quién lo ejecuta?")
    sel = st.multiselect("Municipios", list(met.municipio_nombre), default=list(met.municipio_nombre))
    st.markdown("**Mapa de calor: % de reseñas que mencionan cada problema**")
    hm = temas.pivot_table(index="tema", columns="grupo", values="pct_resenas", fill_value=0)
    hm = hm[[m for m in met.municipio_nombre if m in sel]] if sel else hm
    hm = hm.loc[hm.max(axis=1).sort_values().index]
    fig = px.imshow(hm * 100, color_continuous_scale="Reds", aspect="auto", text_auto=".1f",
                    labels=dict(color="% reseñas", x="", y=""))
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width='stretch')

    st.markdown("**Plan de acción priorizado** (3 principales problemas por municipio)")
    p = PLAN[PLAN.Municipio.isin(sel)]
    for mun, d in p.groupby("Municipio", sort=False):
        pri = d.Prioridad.iloc[0]
        with st.expander(f"{'🔴' if pri == 'Alta' else '🟡' if pri == 'Media' else '🟢'} {mun} · prioridad {pri}", expanded=pri == "Alta"):
            st.dataframe(d.drop(columns=["Municipio", "Prioridad", "Rank"]), hide_index=True, width='stretch')
            ej = alert[alert.municipio_nombre == mun].sort_values("lift", ascending=False)
            ej = ej[ej.n_oraciones_neg >= 3].head(2)
            for _, e in ej.iterrows():
                st.markdown(f"> 🗣️ _«{str(e.ejemplo)[:230]}…»_")
    st.download_button("⬇️ Descargar plan de acción (CSV)", PLAN.to_csv(index=False).encode("utf-8-sig"),
                       "plan_de_accion.csv", "text/csv")

    st.markdown("**Brechas entre provincias (prueba estadística corregida)**")
    r = reglas.sort_values("diferencia_pp")[["tema", "pct_sabana_centro", "pct_tequendama", "diferencia_pp", "significativa"]]
    r.columns = ["Tema", "Sabana Centro", "Tequendama", "Dif. (pp)", "¿Significativa?"]
    st.dataframe(r.style.format({"Sabana Centro": "{:.1%}", "Tequendama": "{:.1%}", "Dif. (pp)": "{:+.2f}"}),
                 hide_index=True, width='stretch')

# =============== TAB 3 ===============
with tab3:
    st.subheader("Lo que el turista valora: ventajas para promocionar")
    pos = res[res.sent_label == "positivo"].groupby("municipio_nombre").size() / res.groupby("municipio_nombre").size()
    lug = csv("sentimiento_por_lugar.csv")
    lug = lug[~lug.muestra_pequena].sort_values("sent_medio", ascending=False)
    a, b = st.columns(2)
    with a:
        st.markdown("**Atractivos mejor valorados** (n ≥ 50)")
        l = lug[["lugar_nombre", "municipio_nombre", "n", "sent_medio", "pct_negativo"]].head(6)
        l.columns = ["Atractivo", "Municipio", "Reseñas", "Sentimiento", "% neg."]
        st.dataframe(l.style.format({"Sentimiento": "{:.2f}", "% neg.": "{:.1%}"}), hide_index=True, width='stretch')
    with b:
        st.markdown("**Atractivos que requieren intervención** (n ≥ 50)")
        l = lug.sort_values("sent_medio")[["lugar_nombre", "municipio_nombre", "n", "sent_medio", "pct_negativo"]].head(6)
        l.columns = ["Atractivo", "Municipio", "Reseñas", "Sentimiento", "% neg."]
        st.dataframe(l.style.format({"Sentimiento": "{:.2f}", "% neg.": "{:.1%}"}), hide_index=True, width='stretch')

    st.markdown("**Temas dominantes en las conversaciones por provincia**")
    tprov = csv("topicos_por_provincia.csv").set_index("provincia")
    for pv, row in tprov.iterrows():
        top = row.sort_values(ascending=False).head(3)
        st.markdown(f"- **{pv}**: " + "; ".join(f"{k} ({v:.0%})" for k, v in top.items()))
    st.info("Sugerencia: con base en estos temas, orientar la promoción de Sabana Centro al turismo patrimonial/cultural "
            "y la de Tequendama a naturaleza, familia y fauna, corrigiendo antes los problemas de limpieza.")

    st.markdown("**Formalización comercial (RNT) vs. volumen de reseñas**")
    f = met[["municipio_nombre", "prestadores_rnt", "n_resenas", "resenas_por_prestador"]].copy()
    fig = px.scatter(f, x="prestadores_rnt", y="n_resenas", size="n_resenas", text="municipio_nombre",
                     labels={"prestadores_rnt": "Prestadores registrados (RNT)", "n_resenas": "Reseñas analizadas"})
    fig.update_traces(textposition="top center")
    fig.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width='stretch')
    low = f.sort_values("resenas_por_prestador").head(2)
    st.caption(f"{', '.join(low.municipio_nombre)} tienen muchos prestadores registrados pero pocas reseñas por prestador: "
               "oportunidad de visibilidad digital y de formalización/promoción.")

# =============== TAB 4 ===============
with tab4:
    st.subheader("Cómo leer estos resultados")
    st.markdown(f"""
- **Base**: {cfg['n_resenas']:,} reseñas de Google Maps; sentimiento con *{cfg['metodo_sentimiento']}*; {cfg['k_lda']} tópicos LDA.
- Las quejas son una **minoría** (≈{g_crit:.0%} de reseñas): cada tema agrupa pocas reseñas, por eso se marca la evidencia como *Sólida* (≥{MIN_TEMA} reseñas) o *Preliminar*.
- Solo las diferencias marcadas como significativas resisten la corrección por comparaciones múltiples; el resto son **pistas para revisar**, no conclusiones.
- Los datos no incluyen TripAdvisor y el RNT cuenta prestadores, no calidad del servicio.
- Antes de invertir, validar en campo los temas con evidencia *Preliminar*.
""")
    mun = st.selectbox("Leer reseñas negativas reales", list(met.municipio_nombre))
    neg = res[(res.municipio_nombre == mun) & (res.sent_label == "negativo")].sort_values("sentimiento").head(5)
    for _, r in neg.iterrows():
        st.markdown(f"> _{str(r.texto_resena)[:350]}_  \n> — {r.lugar_nombre}, {str(r.fecha)[:4]}")
