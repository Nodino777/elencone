import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

# Configurazione della pagina
st.set_page_config(
    page_title="Analisi Timeseries",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Analisi Dati Timeseries")
st.markdown("---")

# Caricamento del file
@st.cache_data
def load_data():
    """Carica i dati dal file Excel"""
    try:
        # Carica il file Excel
        df = pd.read_excel('Domande.xlsx')
        
        # Cerca una colonna di date/timestamp
        date_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['data', 'date', 'time', 'timestamp', 'giorno', 'mese', 'anno']):
                date_columns.append(col)
        
        # Se non trova colonne di date, usa l'indice come timeline
        if not date_columns and len(df) > 0:
            df['Timeline'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
            date_columns = ['Timeline']
        
        # Converti le colonne di date in datetime
        for col in date_columns:
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass
        
        return df, date_columns
    except Exception as e:
        st.error(f"Errore nel caricamento del file: {str(e)}")
        return None, []

# Carica i dati
df, date_columns = load_data()

if df is not None:
    st.success(f"File caricato con successo! Dimensioni: {df.shape[0]} righe x {df.shape[1]} colonne")
    
    # Sidebar per i filtri
    st.sidebar.header("🔧 Filtri e Configurazioni")
    
    # Selezione della colonna temporale
    if date_columns:
        time_column = st.sidebar.selectbox(
            "Seleziona colonna temporale:",
            options=date_columns,
            index=0
        )
    else:
        st.sidebar.warning("Nessuna colonna temporale trovata")
        time_column = None
    
    # Identifica le colonne numeriche
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Rimuovi la colonna temporale dalle opzioni numeriche se presente
    if time_column in numeric_columns:
        numeric_columns.remove(time_column)
    
    st.sidebar.subheader("📊 Selezione Colonne da Visualizzare")
    
    # Limita a massimo 10 colonne
    max_columns = min(10, len(numeric_columns))
    
    if numeric_columns:
        selected_columns = st.sidebar.multiselect(
            f"Seleziona fino a {max_columns} colonne numeriche:",
            options=numeric_columns,
            default=numeric_columns[:max_columns],
            max_selections=max_columns
        )
    else:
        st.sidebar.warning("Nessuna colonna numerica trovata")
        selected_columns = []
    
    # Filtro per intervallo di date
    if time_column and not df.empty:
        st.sidebar.subheader("📅 Filtro Temporale")
        
        min_date = df[time_column].min()
        max_date = df[time_column].max()
        
        date_range = st.sidebar.date_input(
            "Seleziona intervallo di date:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Applica il filtro temporale
        if len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df[(df[time_column] >= pd.Timestamp(start_date)) & 
                           (df[time_column] <= pd.Timestamp(end_date))]
        else:
            df_filtered = df
    else:
        df_filtered = df
    
    # Opzioni di visualizzazione
    st.sidebar.subheader("🎨 Opzioni Grafico")
    
    chart_type = st.sidebar.selectbox(
        "Tipo di grafico:",
        options=["Linee", "Linee + Punti", "Area", "Barre"]
    )
    
    show_legend = st.sidebar.checkbox("Mostra legenda", value=True)
    
    # Normalizzazione dei dati
    normalize_data = st.sidebar.checkbox("Normalizza i dati (0-1)", value=False)
    
    # Layout principale
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("📋 Informazioni Dataset")
        st.write(f"**Righe totali:** {len(df)}")
        st.write(f"**Righe filtrate:** {len(df_filtered)}")
        st.write(f"**Colonne numeriche:** {len(numeric_columns)}")
        
        if selected_columns:
            st.write("**Colonne selezionate:**")
            for col in selected_columns:
                st.write(f"• {col}")
    
    with col1:
        if selected_columns and time_column:
            # Prepara i dati per il grafico
            plot_data = df_filtered[[time_column] + selected_columns].copy()
            
            # Normalizzazione se richiesta
            if normalize_data:
                for col in selected_columns:
                    min_val = plot_data[col].min()
                    max_val = plot_data[col].max()
                    if max_val != min_val:
                        plot_data[col] = (plot_data[col] - min_val) / (max_val - min_val)
            
            # Crea il grafico
            fig = go.Figure()
            
            for col in selected_columns:
                if chart_type == "Linee":
                    fig.add_trace(go.Scatter(
                        x=plot_data[time_column],
                        y=plot_data[col],
                        mode='lines',
                        name=col,
                        line=dict(width=2)
                    ))
                elif chart_type == "Linee + Punti":
                    fig.add_trace(go.Scatter(
                        x=plot_data[time_column],
                        y=plot_data[col],
                        mode='lines+markers',
                        name=col,
                        line=dict(width=2),
                        marker=dict(size=4)
                    ))
                elif chart_type == "Area":
                    fig.add_trace(go.Scatter(
                        x=plot_data[time_column],
                        y=plot_data[col],
                        mode='lines',
                        name=col,
                        fill='tonexty' if col != selected_columns[0] else 'tozeroy',
                        line=dict(width=2)
                    ))
                elif chart_type == "Barre":
                    fig.add_trace(go.Bar(
                        x=plot_data[time_column],
                        y=plot_data[col],
                        name=col,
                        opacity=0.7
                    ))
            
            # Configurazione del layout
            fig.update_layout(
                title=f"Grafico Timeseries - {chart_type}",
                xaxis_title="Data/Tempo",
                yaxis_title="Valori" + (" (Normalizzati)" if normalize_data else ""),
                hovermode='x unified',
                showlegend=show_legend,
                height=600,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            # Personalizzazione degli assi
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiche descrittive
            st.subheader("📊 Statistiche Descrittive")
            
            stats_data = df_filtered[selected_columns].describe()
            st.dataframe(stats_data.round(3))
            
            # Correlazione tra variabili
            if len(selected_columns) > 1:
                st.subheader("🔗 Matrice di Correlazione")
                
                corr_matrix = df_filtered[selected_columns].corr()
                
                fig_corr = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale='RdBu',
                    title="Correlazione tra le variabili selezionate"
                )
                
                st.plotly_chart(fig_corr, use_container_width=True)
            
        else:
            st.warning("Seleziona almeno una colonna numerica e una colonna temporale per visualizzare il grafico")
    
    # Visualizzazione dei dati grezzi
    if st.checkbox("Mostra dati grezzi"):
        st.subheader("📋 Dati Grezzi")
        if selected_columns and time_column:
            st.dataframe(df_filtered[[time_column] + selected_columns])
        else:
            st.dataframe(df_filtered)

else:
    st.error("Impossibile caricare il file. Assicurati che il file 'Domande.xlsx' sia presente nella directory dell'app.")
    
    # Istruzioni per l'uso
    st.markdown("""
    ### 📝 Istruzioni per l'uso:
    
    1. Assicurati che il file `Domande.xlsx` sia nella stessa directory di questo script
    2. Il file deve contenere almeno una colonna con dati numerici
    3. Se presente, verrà automaticamente rilevata una colonna temporale
    4. Utilizza i filtri nella sidebar per personalizzare la visualizzazione
    5. Puoi selezionare fino a 10 colonne da visualizzare contemporaneamente
    
    ### 🔧 Funzionalità disponibili:
    - Selezione colonne numeriche (max 10)
    - Filtro temporale
    - Diversi tipi di grafico (linee, area, barre)
    - Normalizzazione dei dati
    - Statistiche descrittive
    - Matrice di correlazione
    - Visualizzazione dati grezzi
    """)
