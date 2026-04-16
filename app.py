# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from collections import defaultdict

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Cobros Yom", page_icon="\U0001F49C", layout="wide")

# ============================================================
# AUTH: Clave de acceso
# ============================================================
def check_password():
    """Retorna True si el usuario ingresa la clave correcta."""
    CLAVE = st.secrets.get("CLAVE", "yom2026")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("### Cobros Yom")
    st.caption("Ingresa la clave para acceder.")
    pwd = st.text_input("Clave", type="password", key="pwd_input")
    if st.button("Entrar"):
        if pwd == CLAVE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Clave incorrecta.")
    return False

if not check_password():
    st.stop()

# ============================================================
# DATA: Catalogo de reglas de cobro
# ============================================================
CATALOGO = [
    # Dicalla
    dict(cliente="Dicalla", concepto="SaaS Growth Digital (hasta 1.000 comercios)",
         tipo="proporcional", precio_base=40, incluido=1000, adicional=6.9, unidad=1000,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable="Comercios Growth", variable_hint="Comercios Growth activos",
         notas="PRECIO INVENTADO UF 40 - confirmar. Adicional UF 6,9/1000.", placeholder=True),
    dict(cliente="Dicalla", concepto="SaaS Sales Intelligence (hasta 1.000 comercios)",
         tipo="proporcional", precio_base=25, incluido=1000, adicional=4.3, unidad=1000,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable="Comercios SI", variable_hint="Comercios Sales Intelligence",
         notas="PRECIO INVENTADO UF 25 - confirmar. Adicional UF 4,3/1000.", placeholder=True),
    dict(cliente="Dicalla", concepto="Vendedores adicionales (App Venta)",
         tipo="proporcional", precio_base=0, incluido=25, adicional=0.8, unidad=1,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable="Vendedores activos", variable_hint="Vendedores en App Venta (25 incluidos)",
         notas="Fase 2. UF 0,8 por vendedor sobre 25 base.", placeholder=False),
    # El Muneco
    dict(cliente="El Muneco", concepto="Cuota setup (UF 132 en 6 cuotas)",
         tipo="cuota", precio_base=22, incluido=None, adicional=None, unidad=None,
         moneda="UF", mes_desde=1, mes_hasta=6,
         variable=None, variable_hint=None,
         notas="Ajustar mes desde/hasta segun fecha real de inicio.", placeholder=False),
    dict(cliente="El Muneco", concepto="SaaS base mensual",
         tipo="fijo", precio_base=30, incluido=None, adicional=None, unidad=None,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable=None, variable_hint=None,
         notas="PRECIO INVENTADO UF 30 - confirmar.", placeholder=True),
    # Bastien
    dict(cliente="Bastien", concepto="SaaS + Consultoria (piloto)",
         tipo="cuota", precio_base=172, incluido=None, adicional=None, unidad=None,
         moneda="UF", mes_desde=1, mes_hasta=4,
         variable=None, variable_hint=None,
         notas="4 meses piloto. Incluye 25 vendedores, 1.000 clientes.", placeholder=False),
    dict(cliente="Bastien", concepto="SaaS + Operacion",
         tipo="cuota", precio_base=125, incluido=None, adicional=None, unidad=None,
         moneda="UF", mes_desde=5, mes_hasta=6,
         variable=None, variable_hint=None,
         notas="2 meses post-piloto.", placeholder=False),
    dict(cliente="Bastien", concepto="B2B transacciones",
         tipo="variable_puro", precio_base=0, incluido=None, adicional=0.02, unidad=1,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable="Transacciones B2B", variable_hint="Transacciones B2B del mes",
         notas="UF 0,02 por transaccion.", placeholder=False),
    dict(cliente="Bastien", concepto="LLM Commerce (tokens)",
         tipo="manual", precio_base=0, incluido=None, adicional=None, unidad=None,
         moneda="CLP", mes_desde=None, mes_hasta=None,
         variable="Consumo LLM CLP", variable_hint="Monto directo en CLP",
         notas="Si modulo instalado. Ingresar monto directo.", placeholder=False),
    # Codelpa
    dict(cliente="Codelpa", concepto="SaaS YOM base",
         tipo="fijo", precio_base=100, incluido=None, adicional=None, unidad=None,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable=None, variable_hint=None,
         notas="IVA INCLUIDO. Contrato 2019.", placeholder=False),
    dict(cliente="Codelpa", concepto="Modulo Recomendacion A",
         tipo="fijo", precio_base=120, incluido=None, adicional=None, unidad=None,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable=None, variable_hint=None,
         notas="IVA INCLUIDO. Canasta Base + OOS.", placeholder=False),
    dict(cliente="Codelpa", concepto="Modulo Recomendacion B",
         tipo="fijo", precio_base=80, incluido=None, adicional=None, unidad=None,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable=None, variable_hint=None,
         notas="PRECIO INVENTADO UF 80 - confirmar.", placeholder=True),
    dict(cliente="Codelpa", concepto="Ordenes B2B e-commerce",
         tipo="variable_puro", precio_base=0, incluido=None, adicional=0.02, unidad=1,
         moneda="UF", mes_desde=None, mes_hasta=None,
         variable="Ordenes B2B", variable_hint="Ordenes B2B procesadas en el mes",
         notas="UF 0,02 por orden procesada.", placeholder=False),
]

MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
TIPO_LABELS = {
    "fijo": "Fijo mensual",
    "cuota": "Cuota fija",
    "proporcional": "Proporcional",
    "redondeado": "Por bloque",
    "variable_puro": "Variable puro",
    "manual": "Monto manual",
}

# ============================================================
# CALCULO
# ============================================================
def calc_monto(item, mes, var_values):
    t = item["tipo"]
    val = var_values.get(item["variable"], 0) if item["variable"] else 0

    if t == "fijo":
        return item["precio_base"]

    if t == "cuota":
        d, h = item.get("mes_desde"), item.get("mes_hasta")
        if d is not None and h is not None:
            return item["precio_base"] if d <= mes <= h else 0
        return item["precio_base"]

    if t == "proporcional":
        extra = max(0, val - (item["incluido"] or 0))
        return (item["precio_base"] or 0) + (extra / (item["unidad"] or 1)) * (item["adicional"] or 0)

    if t == "redondeado":
        import math
        extra = max(0, val - (item["incluido"] or 0))
        return (item["precio_base"] or 0) + math.ceil(extra / (item["unidad"] or 1)) * (item["adicional"] or 0)

    if t == "variable_puro":
        return (val / (item["unidad"] or 1)) * (item["adicional"] or 0)

    if t == "manual":
        return val

    return 0


# ============================================================
# UI
# ============================================================
st.markdown("""
<style>
    .block-container { max-width: 1000px; }
    div[data-testid="stMetric"] { background: #f0fdf4; padding: 12px 16px; border-radius: 10px; border: 1px solid #bbf7d0; }
    div[data-testid="stMetric"] label { color: #065f46 !important; font-weight: 600 !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #059669 !important; }
    .placeholder-tag { background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("Cobros Yom")
st.caption("Elige un cliente, ingresa las variables del mes y listo.")

tab_facturar, tab_catalogo = st.tabs(["Facturar", "Catalogo completo"])

# ============================================================
# TAB 1: FACTURAR
# ============================================================
with tab_facturar:
    clientes = list(dict.fromkeys(item["cliente"] for item in CATALOGO))

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        cliente = st.selectbox("Cliente", clientes)
    with col2:
        mes = st.selectbox("Mes", range(1, 13), format_func=lambda m: f"{m} - {MESES[m-1]}", index=3)
    with col3:
        ano = st.number_input("Ano", min_value=2024, max_value=2030, value=2026)

    # Filtrar items del cliente
    items = [it for it in CATALOGO if it["cliente"] == cliente]
    variables = [it for it in items if it["variable"]]

    # Variables del mes
    var_values = {}
    if variables:
        st.markdown(f"### Variables de {cliente} -- {MESES[mes-1]} {ano}")
        cols = st.columns(min(len(variables), 3))
        for i, it in enumerate(variables):
            with cols[i % 3]:
                var_values[it["variable"]] = st.number_input(
                    it["variable"],
                    min_value=0,
                    value=0,
                    step=1,
                    help=it["variable_hint"],
                    key=f"var_{cliente}_{it['variable']}"
                )
    else:
        st.info(f"**{cliente}** no tiene conceptos variables. Todo es fijo.")

    # Calcular resultados
    st.markdown("---")

    rows = []
    totals_by_currency = defaultdict(float)

    for it in items:
        monto = calc_monto(it, mes, var_values)
        # Ocultar cuotas fuera de rango
        if it["tipo"] == "cuota" and monto == 0:
            continue
        totals_by_currency[it["moneda"]] += monto
        rows.append({
            "concepto": it["concepto"],
            "tipo": it["tipo"],
            "monto": monto,
            "moneda": it["moneda"],
            "placeholder": it["placeholder"],
            "notas": it["notas"],
        })

    if rows:
        # Totales por moneda
        metric_cols = st.columns(len(totals_by_currency))
        for i, (moneda, total) in enumerate(totals_by_currency.items()):
            with metric_cols[i]:
                if moneda == "CLP":
                    st.metric(f"Total {MESES[mes-1]} -- {cliente}", f"${total:,.0f} CLP")
                else:
                    st.metric(f"Total {MESES[mes-1]} -- {cliente}", f"{total:,.2f} {moneda}")

        st.markdown("")

        # Tabla de detalle
        for row in rows:
            c1, c2, c3, c4 = st.columns([3, 1.2, 1.5, 3])
            with c1:
                label = row["concepto"]
                if row["placeholder"]:
                    label += " [!]"
                st.markdown(f"**{label}**")
                st.caption(TIPO_LABELS.get(row["tipo"], row["tipo"]))
            with c2:
                mon = row["moneda"]
                monto = row["monto"]
                if mon == "CLP":
                    display = f"${monto:,.0f}"
                else:
                    display = f"{monto:,.2f}"
                st.markdown(f"`{display}` **{mon}**")
            with c3:
                st.empty()
            with c4:
                if row["placeholder"]:
                    st.markdown(f"<span class='placeholder-tag'>INVENTADO</span> {row['notas']}", unsafe_allow_html=True)
                else:
                    st.caption(row["notas"])
            st.markdown("<hr style='margin:4px 0; border:none; border-top:1px solid #eee;'>", unsafe_allow_html=True)
    else:
        st.warning(f"No hay cobros para {cliente} en {MESES[mes-1]}.")


# ============================================================
# TAB 2: CATALOGO COMPLETO
# ============================================================
with tab_catalogo:
    st.markdown("Todas las reglas de cobro. Las filas con [!] tienen precios inventados por confirmar.")

    cat_rows = []
    for it in CATALOGO:
        cat_rows.append({
            "Cliente": it["cliente"],
            "Concepto": it["concepto"],
            "Tipo": TIPO_LABELS.get(it["tipo"], it["tipo"]),
            "Precio base": it["precio_base"] if it["precio_base"] else "-",
            "Incluido": it["incluido"] if it["incluido"] else "-",
            "Adicional": it["adicional"] if it["adicional"] else "-",
            "Unidad": it["unidad"] if it["unidad"] else "-",
            "Moneda": it["moneda"],
            "Meses": f"{it['mes_desde']}-{it['mes_hasta']}" if it["mes_desde"] and it["mes_hasta"] else "Todo",
            "Variable": it["variable"] or "-",
            "Notas": ("[!] " if it["placeholder"] else "") + it["notas"],
        })

    df = pd.DataFrame(cat_rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Cliente": st.column_config.TextColumn(width="small"),
            "Concepto": st.column_config.TextColumn(width="medium"),
            "Tipo": st.column_config.TextColumn(width="small"),
            "Notas": st.column_config.TextColumn(width="large"),
        }
    )

