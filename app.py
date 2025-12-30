import streamlit as st
import pdfplumber
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Extractor Labs Sergio", page_icon="🧪", layout="centered")

st.title("Extractor de Exámenes Médicos 🏥")
st.markdown("---")

# --- FUNCIONES DE EXTRACCIÓN (LA MAGIA) ---

def clean_text(text):
    """Limpieza básica de espacios y saltos de línea."""
    return re.sub(r'\s+', ' ', text).strip()

def parse_blood_exams(text):
    """
    Lógica 'Estándar de Oro' para exámenes de sangre.
    Busca patrones estrictos: Nombre del examen seguido de números.
    Ejemplo: 'Hemoglobina 10.1', 'PCR 57.09'
    """
    # Esta regex busca: Palabras (nombre examen) + Espacio + Número (con decimales opcionales)
    # Ignora textos largos que no terminan en número.
    pattern = r"([a-zA-Z\s\.\(\)\%\^]+?)\s+(\d+[\.,]?\d*)"
    matches = re.findall(pattern, text)
    
    formatted_results = []
    for match in matches:
        name = match[0].strip()
        value = match[1]
        
        # Filtros para limpiar basura común en PDFs médicos
        if len(name) > 2 and len(name) < 40: 
            formatted_results.append(f"{name} {value}")
            
    return " - ".join(formatted_results)

def parse_complex_exams(text):
    """
    Lógica Experimental para Orina, Cultivos y Gram.
    Intenta capturar todo el texto relevante, incluyendo palabras como 'Negativo', 'Claro', 'S', 'R'.
    """
    # 1. Intentamos capturar pares Clave: Valor textual (Ej: Aspecto Claro, Nitritos Negativo)
    # Busca palabras seguidas de 'Negativo', 'Positivo', 'Claro', 'Ambar', etc.
    textual_pattern = r"([a-zA-Z\s\.]+)\s+(Negativo|Positivo|Claro|Ambar|Escasa|Abundante)"
    textual_matches = re.findall(textual_pattern, text, re.IGNORECASE)
    
    # 2. Para Antibiogramas (S/R)
    # Busca nombre antibiótico + (R) o (S) o I
    abx_pattern = r"([a-zA-Z\s]+)\s+(\([RS]\)|[RS])"
    abx_matches = re.findall(abx_pattern, text)

    results = []
    
    # Agregamos hallazgos textuales (Orina)
    for match in textual_matches:
        results.append(f"{match[0].strip()} {match[1]}")

    # Agregamos antibióticos (Cultivos)
    if abx_matches:
        results.append("ANTIBIOGRAMA: " + " - ".join([f"{m[0].strip()} {m[1]}" for m in abx_matches]))
    
    # Si no encontró patrones específicos, devolvemos el texto limpio general (fallback)
    if not results:
        # Eliminamos encabezados comunes para limpiar un poco
        text = text.replace("Informe de Resultados", "").replace("Validado por", "")
        return text
        
    return " - ".join(results)

# --- INTERFAZ CON PESTAÑAS (TABS) ---

tab1, tab2 = st.tabs(["🩸 Sangre (Estándar)", "🧫 Orina y Cultivos (Beta)"])

# === PESTAÑA 1: SANGRE (La que debe funcionar perfecto) ===
with tab1:
    st.header("Exámenes de Sangre / Numéricos")
    st.info("Sube aquí: Hemogramas, Perfiles Bioquímicos, Gases, Electrolitos.")
    
    uploaded_file_blood = st.file_uploader("Arrastra tu PDF de Sangre aquí", type="pdf", key="blood_uploader")

    if uploaded_file_blood:
        with pdfplumber.open(uploaded_file_blood) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        
        # Procesamiento
        raw_text = clean_text(full_text)
        final_output = parse_blood_exams(raw_text)

        st.success("¡Extracción de Sangre exitosa!")
        
        # Área de edición
        text_area = st.text_area("Revisa y edita:", value=final_output, height=150, key="blood_text")
        
        # Botón de copiado visual
        st.code(text_area, language="text")
        st.caption("👆 Haz clic en el icono de copiar a la derecha.")

# === PESTAÑA 2: ORINA Y CULTIVOS (La zona de pruebas) ===
with tab2:
    st.header("Orina, Cultivos y Gram")
    st.warning("⚠️ Módulo en desarrollo: Verifica bien los resultados cualitativos.")
    st.info("Sube aquí: Orina completa, Urocultivos, Gram, Antibiogramas.")

    uploaded_file_complex = st.file_uploader("Arrastra tu PDF complejo aquí", type="pdf", key="complex_uploader")

    if uploaded_file_complex:
        with pdfplumber.open(uploaded_file_complex) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        
        # Procesamiento distinto
        raw_text = clean_text(full_text)
        final_output = parse_complex_exams(raw_text)

        st.success("¡Extracción Compleja realizada!")
        
        # Área de edición
        text_area_complex = st.text_area("Revisa y edita (puede requerir más ajustes):", value=final_output, height=150, key="complex_text")
        
        st.code(text_area_complex, language="text")
