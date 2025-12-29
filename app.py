import streamlit as st
import pdfplumber
import re

# Configuración básica de la página
st.set_page_config(page_title="HBL Extractor", page_icon="🏥")

st.title("🏥 Extractor HBL - Sergio")
st.markdown("Sube tu PDF del Barros Luco y obtén la evolución lista.")

# --- DICCIONARIO DE ABREVIACIONES ---
ABREVIACIONES = {
    "Hemoglobina": "Hb", "Hematocrito": "Hto", "Recuento De Leucocitos": "GB", 
    "Plaquetas": "Plaq", "Tiempo De Protrombina": "TP", "Tiempo De Tromboplastina": "TTPA", 
    "Inr": "INR", "Nitrogeno Ureico": "BUN", "Urea": "Urea", "Creatinina": "Crea", 
    "Sodio": "Na", "Potasio": "K", "Cloro": "Cl", "Proteina C Reactiva": "PCR", 
    "Acido Urico": "Ac.Urico", "Calcio": "Ca", "Fosforo": "P", "Proteinas Totales": "Prot.Tot", 
    "Albumina": "Alb", "Ldh": "LDH", "Fosfatasa Alcalina": "FA", "Got/Ast": "GOT", 
    "Gpt/Alt": "GPT", "Colesterol Total": "Col.Tot", "Bilirrubina Total": "Bili.T", 
    "Po2": "pO2", "Pco2": "pCO2", "So2": "SatO2", "Hco3": "HCO3", 
    "Exceso De Base": "BE", "Acido Lactico": "Lactato", "Tco2": "tCO2", "Glucosa": "Glu"
}

# --- FUNCIÓN INTELIGENTE DE LECTURA ---
def procesar_pdf(uploaded_file):
    resultados = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text: continue
            lines = text.split('\n')
            
            for line in lines:
                line = line.replace('*', '').strip()
                if not line: continue
                
                # Filtros de basura
                ignorar = ["Avda", "Carrera", "Teléfono", "Miguel", "Ministerio", "Salud", 
                           "Hospital", "Barros", "Luco", "RUT", "Paciente", "Solicitante", 
                           "Validado", "Fecha", "Hora", "Página", "Nota", "Valor", "Critico", 
                           "Método", "Anterior", "Referencia", "Unidad", "Medida", "Edad", 
                           "Sexo", "Procedencia", "Bioquimico", "Hematologia", "Coagulacion", "Gases"]
                
                if any(x.upper() in line.upper() for x in ignorar): continue
                if re.search(r'\d{2}/\d{2}/\d{4}', line): continue
                palabras_rango = ["Día", "Dia", "Mes", "Año", "Adulto", "Niño", "Semanas"]
                if any(p in line for p in palabras_rango): continue

                # Extracción del dato
                match = re.search(r'^(.+?)\s+([<>]?-?\d+[.,]?\d*)', line)
                if match:
                    nombre = match.group(1).strip()
                    valor = match.group(2).strip()
                    
                    if len(nombre) < 3: continue
                    if ":" in nombre and len(nombre) < 5: continue
                    if re.match(r'^\d', nombre): continue 

                    # Abreviar
                    es_porcentaje = "%" in line
                    nombre_limpio = nombre.replace("%", "").replace(":", "").strip().title()
                    nombre_final = ABREVIACIONES.get(nombre_limpio, nombre_limpio)
                    valor_final = f"{valor}%" if es_porcentaje else valor
                    
                    resultados.append(f"{nombre_final} {valor_final}")
    
    return " - ".join(resultados)

# --- LO QUE SE VE EN PANTALLA ---
archivo = st.file_uploader("Sube el PDF aquí", type="pdf")

if archivo:
    try:
        texto = procesar_pdf(archivo)
        if texto:
            st.success("✅ ¡Listo! Copia el texto de abajo:")
            st.code(texto, language=None)
        else:
            st.warning("No pude leer datos. ¿Es un PDF original?")
    except Exception as e:
        st.error(f"Error: {e}")
