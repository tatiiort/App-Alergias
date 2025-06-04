import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json

df = pd.read_csv("ingredientes_acrylgel_base_actualizado.csv", sep=';', encoding='latin1', quotechar='"')

st.title("Consulta de Ingredientes para Alergias")

# Inicializar estados si no existen
if 'last_search' not in st.session_state:
    st.session_state.last_search = None
if 'input_individual' not in st.session_state:
    st.session_state.input_individual = ""
if 'select_ingrediente' not in st.session_state:
    st.session_state.select_ingrediente = "-- Selecciona un ingrediente --"
if 'text_area' not in st.session_state:
    st.session_state.text_area = ""

ingredientes_lista = df['Ingrediente'].tolist()
opciones_desplegable = ["-- Selecciona un ingrediente --"] + ingredientes_lista

def guardar_no_encontrados(no_encontrados):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    # Cargar las credenciales desde st.secrets
    creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],  # aquí ya es dict, no string JSON
    scopes=scope
)
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)

    # Abrir la hoja de cálculo
    sheet = client.open("Ingredientes no encontrados").sheet1

    for ing in no_encontrados:
        sheet.append_row([str(datetime.datetime.now()), ing])

def on_input_change():
    st.session_state.select_ingrediente = "-- Selecciona un ingrediente --"
    st.session_state.text_area = ""
    st.session_state.last_search = 'input'

def on_select_change():
    st.session_state.input_individual = ""
    st.session_state.text_area = ""
    st.session_state.last_search = 'select'

def on_button_click():
    if st.session_state.text_area.strip():
        st.session_state.input_individual = ""
        st.session_state.select_ingrediente = "-- Selecciona un ingrediente --"
        st.session_state.last_search = 'text_area'
    else:
        st.warning("Por favor pega la fórmula antes de buscar.")

ingrediente_input = st.text_input(
    "Escribe el nombre del ingrediente (opcional):",
    value=st.session_state.input_individual,
    key="input_individual",
    on_change=on_input_change
)

ingrediente_seleccionado = st.selectbox(
    "Selecciona un ingrediente",
    opciones_desplegable,
    index=opciones_desplegable.index(st.session_state.select_ingrediente) if st.session_state.select_ingrediente in opciones_desplegable else 0,
    key="select_ingrediente",
    on_change=on_select_change
)

st.write("### Pega la fórmula completa (separada por comas):")
ingredientes_formula = st.text_area(
    "Pega aquí la fórmula",
    value=st.session_state.text_area,
    key="text_area"
)

st.button("Buscar ingredientes en fórmula", on_click=on_button_click)

def mostrar_detalle(detalles):
    categoria = detalles["Categoria"].strip().lower()
    color = (
        "green" if categoria == "tolerable" else
        "red" if categoria == "prohibido" else
        "orange" if "precaución" in categoria else
        "black"
    )
    st.subheader(detalles["Ingrediente"])
    st.markdown(f"**Categoría:** <span style='color:{color}'>{detalles['Categoria']}</span>", unsafe_allow_html=True)
    st.write(f"**Notas:** {detalles['Notas']}")
    st.write(f"**Alternativas:** {detalles['Alternativas']}")
    st.write(f"**Fuente:** {detalles['Fuente']}")

if st.session_state.last_search == 'select' and st.session_state.select_ingrediente != "-- Selecciona un ingrediente --":
    detalles = df[df['Ingrediente'].str.strip().str.lower() == st.session_state.select_ingrediente.strip().lower()]
    if not detalles.empty:
        mostrar_detalle(detalles.iloc[0])

elif st.session_state.last_search == 'input' and st.session_state.input_individual.strip():
    matches = df[df['Ingrediente'].str.contains(st.session_state.input_individual.strip(), case=False, na=False)]
    if not matches.empty:
        mostrar_detalle(matches.iloc[0])
    else:
        st.info("Ingrediente no encontrado.")

elif st.session_state.last_search == 'text_area' and st.session_state.text_area.strip():
    ingredientes_pegados = [i.strip() for i in st.session_state.text_area.split(",") if i.strip()]
    encontrados = []
    no_encontrados = []

    for ing in ingredientes_pegados:
        match = df[df['Ingrediente'].str.contains(ing, case=False, na=False)]
        if not match.empty:
            encontrados.append(match.iloc[0])
        else:
            no_encontrados.append(ing)

    if encontrados:
        st.write(f"### Ingredientes encontrados ({len(encontrados)}):")
        for detalle in encontrados:
            mostrar_detalle(detalle)

    if no_encontrados:
        guardar_no_encontrados(no_encontrados)
        st.warning(f"No se encontraron {len(no_encontrados)} ingredientes y se han guardado para revisión:")
        st.write(", ".join(no_encontrados))
