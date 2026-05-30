import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import hashlib
import os

# ─────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PLACCA.CO — Sistema ERP",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = os.path.join(os.path.dirname(__file__), "erp_system.db")

# ─────────────────────────────────────────────
# CSS PERSONALIZADO
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* Paleta de colores corporativa */
:root {
    --primary: #1a1a2e;
    --accent: #e94560;
    --card-bg: #16213e;
    --text: #eaeaea;
}

/* Fondo general */
.stApp {
    background-color: #0f0f1a;
    color: #eaeaea;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    border-right: 1px solid #e94560;
}
[data-testid="stSidebar"] .stMarkdown, 
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #eaeaea !important;
}

/* Tarjetas métricas */
.metric-card {
    background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
    border: 1px solid #e94560;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin: 5px 0;
}
.metric-card h2 { color: #e94560; font-size: 2rem; margin: 0; }
.metric-card p { color: #aaa; font-size: 0.85rem; margin: 5px 0 0 0; }

/* Semáforo de cartera */
.semaforo-verde { background-color: #1a4a2e; border-left: 5px solid #27ae60; border-radius: 8px; padding: 8px 12px; margin: 4px 0; }
.semaforo-amarillo { background-color: #4a3a0a; border-left: 5px solid #f39c12; border-radius: 8px; padding: 8px 12px; margin: 4px 0; }
.semaforo-rojo { background-color: #4a1a1a; border-left: 5px solid #e74c3c; border-radius: 8px; padding: 8px 12px; margin: 4px 0; }

/* Botones */
.stButton > button {
    background: linear-gradient(135deg, #e94560, #c0392b);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 20px;
    transition: all 0.3s;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(233, 69, 96, 0.4);
}

/* Títulos */
h1, h2, h3 { color: #eaeaea !important; }
.section-title {
    color: #e94560;
    font-size: 1.3rem;
    font-weight: 700;
    border-bottom: 2px solid #e94560;
    padding-bottom: 8px;
    margin-bottom: 20px;
}

/* Tablas */
.stDataFrame { border-radius: 10px; overflow: hidden; }
thead tr th { background-color: #1a1a2e !important; color: #e94560 !important; }

/* Login */
.login-container {
    max-width: 420px;
    margin: 0 auto;
    padding: 40px;
    background: linear-gradient(135deg, #16213e, #1a1a2e);
    border-radius: 16px;
    border: 1px solid #e94560;
    box-shadow: 0 20px 60px rgba(233, 69, 96, 0.2);
}

/* Alertas */
.alert-success { background: #1a4a2e; border: 1px solid #27ae60; border-radius: 8px; padding: 12px; color: #2ecc71; }
.alert-warning { background: #4a3a0a; border: 1px solid #f39c12; border-radius: 8px; padding: 12px; color: #f39c12; }
.alert-danger { background: #4a1a1a; border: 1px solid #e74c3c; border-radius: 8px; padding: 12px; color: #e74c3c; }

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background-color: #1a1a2e !important;
    color: #eaeaea !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #1a1a2e;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #aaa;
    border-radius: 8px;
}
.stTabs [aria-selected="true"] {
    background-color: #e94560 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FUNCIONES DE BASE DE DATOS
# ─────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def run_query(query, params=(), fetch=True):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            cols = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            return pd.DataFrame(rows, columns=cols)
        else:
            conn.commit()
            conn.close()
            return cursor.lastrowid
    except Exception as e:
        conn.close()
        raise e

def run_many(query, data):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.executemany(query, data)
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        raise e


# ─────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────
def check_login(username, password):
    df = run_query("SELECT username, role FROM users WHERE username=? AND password=?", (username, password))
    if not df.empty:
        return df.iloc[0]['role']
    return None

def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="login-container">
            <h2 style="text-align:center; color:#e94560; margin-bottom:8px;">🏭 PLACCA.CO</h2>
            <p style="text-align:center; color:#aaa; margin-bottom:30px; font-size:0.9rem;">Sistema ERP · CRM · Bodega</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### Iniciar Sesión")
            username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
            submitted = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
            
            if submitted:
                role = check_login(username.strip(), password.strip())
                if role:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username.strip()
                    st.session_state['role'] = role
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos.")
        
        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#666; font-size:0.8rem;">
            <b>Usuarios de prueba:</b><br>
            admin / admin123 · ventas / ventas123 · bodega / bodega123
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÓDULO: DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────
def dashboard():
    st.markdown('<p class="section-title">📊 Dashboard Comercial — Resumen Ejecutivo</p>', unsafe_allow_html=True)
    
    # KPIs principales
    total_ventas = run_query("SELECT COALESCE(SUM(total_price), 0) as total FROM sales WHERE status='Completado'")
    total_pedidos = run_query("SELECT COUNT(DISTINCT order_number) as total FROM sales WHERE status='Completado'")
    total_clientes = run_query("SELECT COUNT(*) as total FROM clients")
    total_productos = run_query("SELECT COUNT(*) as total FROM inventory")
    
    col1, col2, col3, col4 = st.columns(4)
    
    tv = total_ventas.iloc[0]['total']
    tp = total_pedidos.iloc[0]['total']
    tc = total_clientes.iloc[0]['total']
    tprod = total_productos.iloc[0]['total']
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>💰 ${tv:,.0f}</h2>
            <p>Ventas Totales (COP)</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2>🛒 {tp}</h2>
            <p>Pedidos Completados</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h2>👥 {tc}</h2>
            <p>Clientes Activos</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h2>📦 {tprod}</h2>
            <p>Referencias en Catálogo</p>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1.3, 1])
    
    with col_left:
        st.markdown('<p class="section-title">🏆 Ranking de Productos Más Vendidos</p>', unsafe_allow_html=True)
        
        ranking_df = run_query("""
        SELECT 
            s.id_sku as "Referencia (SKU)",
            COALESCE(i.name, s.id_sku) as "Nombre del Producto",
            SUM(s.quantity) as "Unidades Vendidas",
            SUM(s.total_price) as "Ingresos Totales (COP)"
        FROM sales s
        LEFT JOIN inventory i ON s.id_sku = i.id_sku
        WHERE s.status = 'Completado' AND s.id_sku != ''
        GROUP BY s.id_sku
        ORDER BY SUM(s.quantity) DESC
        LIMIT 15
        """)
        
        if not ranking_df.empty:
            ranking_df["Ingresos Totales (COP)"] = ranking_df["Ingresos Totales (COP)"].apply(lambda x: f"${x:,.0f}")
            
            fig_ranking = px.bar(
                ranking_df,
                x="Unidades Vendidas",
                y="Referencia (SKU)",
                orientation='h',
                color="Unidades Vendidas",
                color_continuous_scale=["#16213e", "#e94560"],
                title="Top 15 Referencias por Unidades Vendidas",
                text="Unidades Vendidas"
            )
            fig_ranking.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#eaeaea',
                title_font_color='#e94560',
                showlegend=False,
                coloraxis_showscale=False,
                yaxis={'categoryorder': 'total ascending'},
                height=420
            )
            fig_ranking.update_traces(textposition='outside', textfont_color='#eaeaea')
            st.plotly_chart(fig_ranking, use_container_width=True)
            
            st.dataframe(ranking_df, use_container_width=True, hide_index=True)
    
    with col_right:
        st.markdown('<p class="section-title">📈 Ventas por Canal</p>', unsafe_allow_html=True)
        
        canal_df = run_query("""
        SELECT channel as Canal, 
               SUM(total_price) as Total,
               COUNT(DISTINCT order_number) as Pedidos
        FROM sales 
        WHERE status='Completado' AND channel != ''
        GROUP BY channel
        ORDER BY Total DESC
        """)
        
        if not canal_df.empty:
            fig_canal = px.pie(
                canal_df,
                names="Canal",
                values="Total",
                color_discrete_sequence=px.colors.sequential.RdBu,
                hole=0.4
            )
            fig_canal.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#eaeaea',
                height=280,
                showlegend=True,
                legend=dict(font=dict(color='#eaeaea'))
            )
            st.plotly_chart(fig_canal, use_container_width=True)
        
        st.markdown('<p class="section-title">📅 Ventas por Mes</p>', unsafe_allow_html=True)
        
        mes_df = run_query("""
        SELECT substr(date, 1, 7) as Mes,
               SUM(total_price) as Total
        FROM sales
        WHERE status='Completado'
        GROUP BY substr(date, 1, 7)
        ORDER BY Mes
        """)
        
        if not mes_df.empty:
            fig_mes = px.line(
                mes_df,
                x="Mes",
                y="Total",
                markers=True,
                color_discrete_sequence=["#e94560"]
            )
            fig_mes.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#eaeaea',
                height=220,
                xaxis=dict(gridcolor='#333'),
                yaxis=dict(gridcolor='#333')
            )
            st.plotly_chart(fig_mes, use_container_width=True)


# ─────────────────────────────────────────────
# MÓDULO: CRM Y CARTERA
# ─────────────────────────────────────────────
def crm_cartera():
    tab1, tab2 = st.tabs(["👥 Directorio CRM", "💳 Control de Cartera"])
    
    with tab1:
        st.markdown('<p class="section-title">👥 Directorio CRM — Clientes Activos</p>', unsafe_allow_html=True)
        st.caption("El CRM se construye automáticamente desde el historial de ventas. Todos los clientes aquí han realizado al menos una compra.")
        
        # Búsqueda
        search = st.text_input("🔍 Buscar cliente por nombre o ciudad...", "")
        
        query = """
        SELECT 
            c.name as "Nombre Cliente",
            c.client_id as "Cédula / NIT",
            c.phone as "Teléfono",
            c.city as "Ciudad",
            c.total_orders as "N° Pedidos",
            c.total_spent as "LTV Total ($)",
            c.last_purchase as "Última Compra"
        FROM clients c
        """
        
        if search:
            query += f" WHERE c.name LIKE '%{search}%' OR c.city LIKE '%{search}%'"
        
        query += " ORDER BY c.total_spent DESC"
        
        crm_df = run_query(query)
        
        if not crm_df.empty:
            crm_df["LTV Total ($)"] = crm_df["LTV Total ($)"].apply(lambda x: f"${x:,.0f}")
            st.dataframe(crm_df, use_container_width=True, hide_index=True)
            st.caption(f"Total de clientes: **{len(crm_df)}**")
        else:
            st.info("No se encontraron clientes.")
        
        st.markdown("---")
        st.markdown('<p class="section-title">➕ Agregar / Actualizar Cliente</p>', unsafe_allow_html=True)
        
        with st.form("add_client_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("Nombre Completo / Razón Social *")
                c_id = st.text_input("Cédula / NIT")
                c_phone = st.text_input("Teléfono")
            with col2:
                c_address = st.text_input("Dirección")
                c_city = st.text_input("Ciudad")
            
            if st.form_submit_button("💾 Guardar Cliente", use_container_width=True):
                if c_name:
                    try:
                        run_query("""
                        INSERT OR REPLACE INTO clients (name, client_id, phone, address, city, total_spent, total_orders, last_purchase)
                        VALUES (?, ?, ?, ?, ?, 
                            COALESCE((SELECT total_spent FROM clients WHERE name=?), 0),
                            COALESCE((SELECT total_orders FROM clients WHERE name=?), 0),
                            COALESCE((SELECT last_purchase FROM clients WHERE name=?), date('now'))
                        )
                        """, (c_name, c_id, c_phone, c_address, c_city, c_name, c_name, c_name), fetch=False)
                        st.success(f"✅ Cliente **{c_name}** guardado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("El nombre del cliente es obligatorio.")
    
    with tab2:
        st.markdown('<p class="section-title">💳 Panel de Control de Cartera — Ventas a Crédito</p>', unsafe_allow_html=True)
        
        # Obtener ventas a crédito
        credito_df = run_query("""
        SELECT 
            s.date as fecha_venta,
            s.order_number as pedido,
            s.client_name as cliente,
            s.client_phone as telefono,
            s.client_city as ciudad,
            s.id_sku as sku,
            s.total_price as total,
            s.payment_method as medio_pago
        FROM sales s
        WHERE LOWER(s.payment_method) LIKE '%crédito%' 
           OR LOWER(s.payment_method) LIKE '%credito%'
           OR LOWER(s.payment_method) LIKE '%credit%'
        ORDER BY s.date DESC
        """)
        
        today = date.today()
        
        if credito_df.empty:
            # Si no hay ventas con "crédito" en el medio de pago, mostrar todas las ventas para demo
            credito_df = run_query("""
            SELECT 
                s.date as fecha_venta,
                s.order_number as pedido,
                s.client_name as cliente,
                s.client_phone as telefono,
                s.client_city as ciudad,
                s.id_sku as sku,
                s.total_price as total,
                s.payment_method as medio_pago
            FROM sales s
            ORDER BY s.date DESC
            LIMIT 20
            """)
            st.info("ℹ️ Mostrando ventas recientes como referencia. Para activar el control de cartera, registra ventas con 'Crédito' como medio de pago.")
        
        if not credito_df.empty:
            # Calcular semáforo
            verde = amarillo = rojo = 0
            
            st.markdown("#### 🚦 Semáforo de Mora")
            
            for _, row in credito_df.iterrows():
                try:
                    fecha_venta = datetime.strptime(str(row['fecha_venta'])[:10], '%Y-%m-%d').date()
                    fecha_venc = fecha_venta + timedelta(days=15)
                    dias_restantes = (fecha_venc - today).days
                    
                    if dias_restantes > 3:
                        estado = "🟢 Al día"
                        clase = "semaforo-verde"
                        verde += 1
                    elif dias_restantes >= 0:
                        estado = "🟡 Próximo a vencer"
                        clase = "semaforo-amarillo"
                        amarillo += 1
                    else:
                        estado = f"🔴 En mora ({abs(dias_restantes)} días)"
                        clase = "semaforo-rojo"
                        rojo += 1
                    
                    st.markdown(f"""
                    <div class="{clase}">
                        <strong>{row['cliente']}</strong> — Pedido: {row['pedido']} — 
                        Total: ${row['total']:,.0f} COP — 
                        Vence: {fecha_venc.strftime('%d/%m/%Y')} — 
                        <strong>{estado}</strong>
                        <br><small>📞 {row['telefono']} | 🏙️ {row['ciudad']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception:
                    pass
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Resumen semáforo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card" style="border-color:#27ae60;">
                    <h2 style="color:#27ae60;">✅ {verde}</h2>
                    <p>Al día</p>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card" style="border-color:#f39c12;">
                    <h2 style="color:#f39c12;">⚠️ {amarillo}</h2>
                    <p>Próximos a vencer</p>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="metric-card" style="border-color:#e74c3c;">
                    <h2 style="color:#e74c3c;">🚨 {rojo}</h2>
                    <p>En mora</p>
                </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÓDULO: VENTAS
# ─────────────────────────────────────────────
def ventas():
    tab1, tab2 = st.tabs(["📋 Historial de Ventas", "➕ Registrar Nueva Venta"])
    
    with tab1:
        st.markdown('<p class="section-title">📋 Historial de Ventas</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_cliente = st.text_input("🔍 Filtrar por cliente", "")
        with col2:
            filtro_sku = st.text_input("🔍 Filtrar por SKU", "")
        with col3:
            filtro_estado = st.selectbox("Estado", ["Todos", "Completado", "Pendiente", "Cancelado"])
        
        query = """
        SELECT 
            s.date as "Fecha",
            s.order_number as "N° Pedido",
            s.client_name as "Cliente",
            s.client_city as "Ciudad",
            s.id_sku as "SKU",
            COALESCE(i.name, s.id_sku) as "Producto",
            s.quantity as "Cantidad",
            s.unit_price as "Precio Unit.",
            s.total_price as "Total (COP)",
            s.payment_method as "Medio de Pago",
            s.channel as "Canal",
            s.status as "Estado"
        FROM sales s
        LEFT JOIN inventory i ON s.id_sku = i.id_sku
        WHERE 1=1
        """
        
        params = []
        if filtro_cliente:
            query += " AND s.client_name LIKE ?"
            params.append(f'%{filtro_cliente}%')
        if filtro_sku:
            query += " AND s.id_sku LIKE ?"
            params.append(f'%{filtro_sku}%')
        if filtro_estado != "Todos":
            query += " AND s.status = ?"
            params.append(filtro_estado)
        
        query += " ORDER BY s.date DESC"
        
        ventas_df = run_query(query, tuple(params))
        
        if not ventas_df.empty:
            ventas_df["Total (COP)"] = ventas_df["Total (COP)"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
            ventas_df["Precio Unit."] = ventas_df["Precio Unit."].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
            st.dataframe(ventas_df, use_container_width=True, hide_index=True)
            st.caption(f"Total registros: **{len(ventas_df)}**")
        else:
            st.info("No se encontraron ventas con los filtros aplicados.")
    
    with tab2:
        st.markdown('<p class="section-title">➕ Registrar Nueva Venta</p>', unsafe_allow_html=True)
        
        # Obtener listas para selectores
        productos_df = run_query("SELECT id_sku, name, variant, current_stock FROM inventory ORDER BY name")
        clientes_df = run_query("SELECT name, client_id, phone, city FROM clients ORDER BY name")
        
        with st.form("nueva_venta_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📅 Información del Pedido**")
                fecha_venta = st.date_input("Fecha de Venta", value=date.today())
                
                # Generar número de pedido automático
                ultimo_pedido = run_query("SELECT order_number FROM sales ORDER BY id DESC LIMIT 1")
                if not ultimo_pedido.empty:
                    try:
                        num = int(ultimo_pedido.iloc[0]['order_number'].replace('PED-', '')) + 1
                        sugerido = f"PED-{num:03d}"
                    except:
                        sugerido = "PED-001"
                else:
                    sugerido = "PED-001"
                
                order_number = st.text_input("N° Pedido / Factura", value=sugerido)
                payment_method = st.selectbox("Medio de Pago", 
                    ["Bancolombia", "Nequi", "Efectivo", "Crédito 15 días", "PSE", "Tarjeta Crédito", "Otro"])
                status = st.selectbox("Estado", ["Completado", "Pendiente", "Cancelado"])
                channel = st.selectbox("Canal de Venta", 
                    ["WhatsApp", "Web Shopify", "Mercado Libre", "Rappi", "Falabella", "Otro"])
            
            with col2:
                st.markdown("**👤 Información del Cliente**")
                
                # Selector de cliente existente o nuevo
                opciones_clientes = ["-- Nuevo Cliente --"] + list(clientes_df['name'].values) if not clientes_df.empty else ["-- Nuevo Cliente --"]
                cliente_sel = st.selectbox("Seleccionar Cliente Existente", opciones_clientes)
                
                if cliente_sel != "-- Nuevo Cliente --" and not clientes_df.empty:
                    cliente_info = clientes_df[clientes_df['name'] == cliente_sel].iloc[0]
                    client_name = cliente_sel
                    client_id = st.text_input("Cédula / NIT", value=str(cliente_info['client_id']))
                    client_phone = st.text_input("Teléfono", value=str(cliente_info['phone']))
                    client_city = st.text_input("Ciudad", value=str(cliente_info['city']))
                    client_address = st.text_input("Dirección", "")
                else:
                    client_name = st.text_input("Nombre Completo / Razón Social *")
                    client_id = st.text_input("Cédula / NIT")
                    client_phone = st.text_input("Teléfono")
                    client_city = st.text_input("Ciudad")
                    client_address = st.text_input("Dirección")
            
            st.markdown("---")
            st.markdown("**📦 Información del Producto**")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                if not productos_df.empty:
                    opciones_prod = [f"{row['id_sku']} — {row['name']} ({row['variant']}) | Stock: {row['current_stock']}" 
                                    for _, row in productos_df.iterrows()]
                    prod_sel = st.selectbox("Producto / SKU *", opciones_prod)
                    id_sku = prod_sel.split(" — ")[0] if prod_sel else ""
                else:
                    id_sku = st.text_input("ID SKU *")
            
            with col4:
                quantity = st.number_input("Cantidad *", min_value=1, value=1, step=1)
            
            with col5:
                unit_price = st.number_input("Precio Unitario (COP) *", min_value=0.0, value=0.0, step=100.0)
            
            total_calc = quantity * unit_price
            st.markdown(f"**💰 Total calculado: ${total_calc:,.0f} COP**")
            
            submitted = st.form_submit_button("💾 Registrar Venta", use_container_width=True)
            
            if submitted:
                if not client_name or not id_sku or quantity <= 0:
                    st.error("⚠️ Complete los campos obligatorios: Cliente, SKU y Cantidad.")
                else:
                    try:
                        # Verificar stock disponible
                        stock_check = run_query("SELECT current_stock FROM inventory WHERE id_sku=?", (id_sku,))
                        
                        if not stock_check.empty:
                            stock_actual = stock_check.iloc[0]['current_stock']
                            if stock_actual < quantity:
                                st.warning(f"⚠️ Stock insuficiente. Disponible: {stock_actual} unidades.")
                            else:
                                # Insertar venta
                                run_query("""
                                INSERT INTO sales (date, order_number, payment_method, status, client_name, 
                                    client_id, client_phone, client_address, client_city, id_sku, 
                                    quantity, channel, unit_price, total_price)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (str(fecha_venta), order_number, payment_method, status, client_name,
                                      client_id, client_phone, client_address, client_city, id_sku,
                                      quantity, channel, unit_price, total_calc), fetch=False)
                                
                                # Descontar del inventario si está completado
                                if status == "Completado":
                                    run_query("""
                                    UPDATE inventory SET current_stock = current_stock - ? WHERE id_sku = ?
                                    """, (quantity, id_sku), fetch=False)
                                
                                # Actualizar CRM
                                run_query("""
                                INSERT INTO clients (name, client_id, phone, address, city, total_spent, total_orders, last_purchase)
                                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                                ON CONFLICT(name) DO UPDATE SET
                                    total_spent = total_spent + excluded.total_spent,
                                    total_orders = total_orders + 1,
                                    last_purchase = excluded.last_purchase
                                """, (client_name, client_id, client_phone, client_address, client_city, 
                                      total_calc, str(fecha_venta)), fetch=False)
                                
                                fecha_venc = fecha_venta + timedelta(days=15)
                                st.success(f"""
                                ✅ **Venta registrada exitosamente.**  
                                - Pedido: **{order_number}**  
                                - Cliente: **{client_name}**  
                                - Total: **${total_calc:,.0f} COP**  
                                - Fecha de Vencimiento (crédito): **{fecha_venc.strftime('%d/%m/%Y')}**
                                """)
                                st.rerun()
                        else:
                            st.error("SKU no encontrado en el inventario.")
                    except Exception as e:
                        st.error(f"Error al registrar la venta: {e}")


# ─────────────────────────────────────────────
# MÓDULO: BODEGA E INVENTARIO
# ─────────────────────────────────────────────
def bodega():
    tab1, tab2, tab3 = st.tabs(["📦 Maestro de Inventario", "📥 Registrar Entrada", "📤 Registrar Salida"])
    
    with tab1:
        st.markdown('<p class="section-title">📦 Maestro de Inventario — Stock Actual</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            filtro_tipo = st.text_input("🔍 Filtrar por tipo o nombre de producto", "")
        with col2:
            solo_stock = st.checkbox("Solo productos con stock > 0", value=False)
        
        query = """
        SELECT 
            id_sku as "SKU / Referencia",
            name as "Nombre del Producto",
            variant as "Variante",
            type as "Tipo",
            provider as "Proveedor",
            initial_stock as "Stock Inicial",
            current_stock as "Stock Actual",
            CASE 
                WHEN current_stock <= 0 THEN '🔴 Sin Stock'
                WHEN current_stock <= 5 THEN '🟡 Stock Bajo'
                ELSE '🟢 Disponible'
            END as "Estado"
        FROM inventory
        WHERE 1=1
        """
        
        params = []
        if filtro_tipo:
            query += " AND (type LIKE ? OR name LIKE ? OR id_sku LIKE ?)"
            params.extend([f'%{filtro_tipo}%', f'%{filtro_tipo}%', f'%{filtro_tipo}%'])
        if solo_stock:
            query += " AND current_stock > 0"
        
        query += " ORDER BY current_stock DESC, name"
        
        inv_df = run_query(query, tuple(params))
        
        if not inv_df.empty:
            # Colorear según estado
            def color_estado(val):
                if '🔴' in str(val):
                    return 'background-color: #4a1a1a; color: #e74c3c'
                elif '🟡' in str(val):
                    return 'background-color: #4a3a0a; color: #f39c12'
                elif '🟢' in str(val):
                    return 'background-color: #1a4a2e; color: #27ae60'
                return ''
            
            st.dataframe(
                inv_df.style.map(color_estado, subset=["Estado"]),
                use_container_width=True,
                hide_index=True
            )
            
            # Resumen rápido
            sin_stock = len(inv_df[inv_df["Stock Actual"] <= 0])
            stock_bajo = len(inv_df[(inv_df["Stock Actual"] > 0) & (inv_df["Stock Actual"] <= 5)])
            disponible = len(inv_df[inv_df["Stock Actual"] > 5])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""<div class="metric-card" style="border-color:#27ae60;">
                    <h2 style="color:#27ae60;">{disponible}</h2><p>Con Stock Disponible</p></div>""", 
                    unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="metric-card" style="border-color:#f39c12;">
                    <h2 style="color:#f39c12;">{stock_bajo}</h2><p>Stock Bajo (≤5)</p></div>""", 
                    unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class="metric-card" style="border-color:#e74c3c;">
                    <h2 style="color:#e74c3c;">{sin_stock}</h2><p>Sin Stock</p></div>""", 
                    unsafe_allow_html=True)
        else:
            st.info("No se encontraron productos.")
    
    with tab2:
        st.markdown('<p class="section-title">📥 Registrar Entrada de Mercancía</p>', unsafe_allow_html=True)
        
        productos_df = run_query("SELECT id_sku, name, variant, current_stock FROM inventory ORDER BY name")
        
        with st.form("entrada_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                if not productos_df.empty:
                    opciones_prod = [f"{row['id_sku']} — {row['name']} ({row['variant']}) | Stock actual: {row['current_stock']}" 
                                    for _, row in productos_df.iterrows()]
                    prod_sel = st.selectbox("Producto / SKU *", opciones_prod)
                    id_sku_entrada = prod_sel.split(" — ")[0]
                else:
                    id_sku_entrada = st.text_input("ID SKU *")
                
                cantidad_entrada = st.number_input("Cantidad a Ingresar *", min_value=1, value=1, step=1)
            
            with col2:
                proveedor_entrada = st.text_input("Proveedor / Origen")
                fecha_entrada = st.date_input("Fecha de Entrada", value=date.today())
                notas_entrada = st.text_area("Notas / Observaciones", height=80)
            
            if st.form_submit_button("📥 Registrar Entrada", use_container_width=True):
                try:
                    run_query("""
                    UPDATE inventory SET current_stock = current_stock + ? WHERE id_sku = ?
                    """, (cantidad_entrada, id_sku_entrada), fetch=False)
                    
                    stock_nuevo = run_query("SELECT current_stock FROM inventory WHERE id_sku=?", (id_sku_entrada,))
                    nuevo_stock = stock_nuevo.iloc[0]['current_stock'] if not stock_nuevo.empty else "N/A"
                    
                    st.success(f"""
                    ✅ **Entrada registrada exitosamente.**  
                    - SKU: **{id_sku_entrada}**  
                    - Cantidad ingresada: **+{cantidad_entrada}**  
                    - Stock nuevo: **{nuevo_stock}** unidades  
                    - Proveedor: **{proveedor_entrada or 'No especificado'}**
                    """)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar entrada: {e}")
    
    with tab3:
        st.markdown('<p class="section-title">📤 Registrar Salida / Despacho</p>', unsafe_allow_html=True)
        st.caption("Las salidas asociadas a un cliente descuentan automáticamente el inventario disponible.")
        
        productos_df = run_query("SELECT id_sku, name, variant, current_stock FROM inventory WHERE current_stock > 0 ORDER BY name")
        clientes_df = run_query("SELECT name FROM clients ORDER BY name")
        
        with st.form("salida_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                if not productos_df.empty:
                    opciones_prod = [f"{row['id_sku']} — {row['name']} ({row['variant']}) | Stock: {row['current_stock']}" 
                                    for _, row in productos_df.iterrows()]
                    prod_sel = st.selectbox("Producto / SKU *", opciones_prod)
                    id_sku_salida = prod_sel.split(" — ")[0]
                    stock_disp = int(prod_sel.split("Stock: ")[1]) if "Stock: " in prod_sel else 0
                else:
                    id_sku_salida = st.text_input("ID SKU *")
                    stock_disp = 0
                
                cantidad_salida = st.number_input(f"Cantidad a Despachar * (Disponible: {stock_disp})", 
                                                   min_value=1, max_value=max(1, stock_disp), value=1, step=1)
            
            with col2:
                tipo_salida = st.selectbox("Tipo de Salida", ["Venta / Despacho", "Muestra", "Pérdida / Daño", "Devolución a Proveedor", "Otro"])
                
                opciones_clientes = ["Sin cliente asociado"] + (list(clientes_df['name'].values) if not clientes_df.empty else [])
                cliente_salida = st.selectbox("Cliente Asociado (opcional)", opciones_clientes)
                
                fecha_salida = st.date_input("Fecha de Salida", value=date.today())
                notas_salida = st.text_area("Notas / Observaciones", height=80)
            
            if st.form_submit_button("📤 Registrar Salida", use_container_width=True):
                try:
                    stock_check = run_query("SELECT current_stock FROM inventory WHERE id_sku=?", (id_sku_salida,))
                    
                    if not stock_check.empty:
                        stock_actual = stock_check.iloc[0]['current_stock']
                        
                        if stock_actual < cantidad_salida:
                            st.error(f"❌ Stock insuficiente. Disponible: {stock_actual} unidades.")
                        else:
                            run_query("""
                            UPDATE inventory SET current_stock = current_stock - ? WHERE id_sku = ?
                            """, (cantidad_salida, id_sku_salida), fetch=False)
                            
                            stock_nuevo = run_query("SELECT current_stock FROM inventory WHERE id_sku=?", (id_sku_salida,))
                            nuevo_stock = stock_nuevo.iloc[0]['current_stock'] if not stock_nuevo.empty else "N/A"
                            
                            st.success(f"""
                            ✅ **Salida registrada exitosamente.**  
                            - SKU: **{id_sku_salida}**  
                            - Cantidad despachada: **-{cantidad_salida}**  
                            - Stock restante: **{nuevo_stock}** unidades  
                            - Tipo: **{tipo_salida}**  
                            - Cliente: **{cliente_salida}**
                            """)
                            st.rerun()
                    else:
                        st.error("SKU no encontrado.")
                except Exception as e:
                    st.error(f"Error al registrar salida: {e}")


# ─────────────────────────────────────────────
# MÓDULO: AGREGAR PRODUCTO AL CATÁLOGO
# ─────────────────────────────────────────────
def agregar_producto():
    st.markdown('<p class="section-title">➕ Agregar Nuevo Producto al Catálogo</p>', unsafe_allow_html=True)
    
    with st.form("nuevo_producto_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            p_sku = st.text_input("ID SKU / Referencia *", placeholder="Ej: IMAD17X")
            p_name = st.text_input("Nombre del Producto *")
            p_variant = st.text_input("Variante", placeholder="Ej: Pack 100")
            p_type = st.text_input("Tipo / Categoría", placeholder="Ej: Imánes, Gafetes...")
        
        with col2:
            p_provider = st.text_input("Proveedor")
            p_stock = st.number_input("Stock Inicial", min_value=0, value=0, step=1)
            p_price = st.number_input("Precio de Venta (COP)", min_value=0.0, value=0.0, step=100.0)
        
        if st.form_submit_button("💾 Guardar Producto", use_container_width=True):
            if p_sku and p_name:
                try:
                    run_query("""
                    INSERT OR REPLACE INTO inventory (id_sku, name, variant, type, provider, initial_stock, current_stock, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (p_sku, p_name, p_variant, p_type, p_provider, p_stock, p_stock, p_price), fetch=False)
                    st.success(f"✅ Producto **{p_name}** ({p_sku}) agregado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("SKU y Nombre son obligatorios.")


# ─────────────────────────────────────────────
# NAVEGACIÓN PRINCIPAL
# ─────────────────────────────────────────────
def main():
    # Inicializar session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        login_page()
        return
    
    # Sidebar de navegación
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding: 20px 0 10px 0;">
            <h2 style="color:#e94560; margin:0;">🏭 PLACCA.CO</h2>
            <p style="color:#aaa; font-size:0.8rem; margin:4px 0 0 0;">Sistema ERP v1.0</p>
        </div>
        <hr style="border-color:#333; margin:10px 0;">
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background:#1a1a2e; border-radius:8px; padding:10px; margin-bottom:15px; text-align:center;">
            <p style="color:#e94560; margin:0; font-weight:600;">👤 {st.session_state['username'].upper()}</p>
            <p style="color:#aaa; margin:0; font-size:0.75rem;">{st.session_state['role']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        menu_options = {
            "📊 Dashboard": "dashboard",
            "🛒 Ventas": "ventas",
            "👥 CRM & Cartera": "crm",
            "📦 Bodega / Inventario": "bodega",
            "➕ Agregar Producto": "producto"
        }
        
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 'dashboard'
        
        for label, page_id in menu_options.items():
            is_active = st.session_state['current_page'] == page_id
            btn_style = "background: #e94560; color: white;" if is_active else ""
            if st.button(label, use_container_width=True, key=f"nav_{page_id}"):
                st.session_state['current_page'] = page_id
                st.rerun()
        
        st.markdown("<hr style='border-color:#333; margin:20px 0 10px 0;'>", unsafe_allow_html=True)
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ''
            st.session_state['role'] = ''
            st.rerun()
        
        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#555; font-size:0.7rem;">
            PLACCA.CO ERP v1.0<br>
            Desarrollado con Streamlit
        </div>
        """, unsafe_allow_html=True)
    
    # Renderizar página activa
    page = st.session_state.get('current_page', 'dashboard')
    
    if page == 'dashboard':
        dashboard()
    elif page == 'ventas':
        ventas()
    elif page == 'crm':
        crm_cartera()
    elif page == 'bodega':
        bodega()
    elif page == 'producto':
        agregar_producto()


if __name__ == "__main__":
    main()
