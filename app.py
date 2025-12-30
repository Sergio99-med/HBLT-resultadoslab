import streamlit as st
import pdfplumber
import re
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="HBL Extractor V3.3", page_icon="🏥", layout="centered")

st.title("🏥 Extractor HBLT - Exámenes de laboratorio")
st.markdown("### Sube el PDF del Barros Luco y obtén los resultados al instante.")

# --- DICCIONARIO DE ABREVIACIONES Y CORRECCIONES ---
ABREVIACIONES = {
    # Hematología
    "Hemoglobina": "Hb", "Hematocrito": "Hto", "Recuento De Leucocitos": "GB",
    "Plaquetas": "Plaq", "Recuento De Plaquetas": "Plaq",
    "Vcm": "VCM", "Hcm": "HCM", "Chcm": "CHCM",
    
    # Coagulación
    "Tiempo De Protrombina": "TP",
    "Tiempo De Protrombina Seg": "TP seg", # <--- NUEVO
    "Tiempo De Tromboplastina": "TTPA", "Inr": "INR",
    
    # Bioquímica / Función Renal / Hepática
    "Nitrogeno Ureico": "BUN", "Urea": "Urea", "Creatinina": "Crea",
    "Sodio": "Na", "Potasio": "K", "Cloro": "Cl", "Proteina C Reactiva": "PCR",
    "Acido Urico": "Ac.Urico", "Calcio": "Ca", "Fosforo": "P",
    "Proteinas Totales": "Prot.Tot", "Albumina": "Alb", "Ldh": "LDH",
    "Fosfatasa Alcalina": "FA", "Got": "GOT", "Ast": "GOT", "Got/Ast": "GOT",
    "Gpt": "GPT", "Alt": "GPT", "Gpt/Alt": "GPT", "Ggt": "GGT", "Gama Glutamil": "GGT",
    "Colesterol Total": "Col.Tot", "Bilirrubina Total": "Bili.T", "Procalcitonina": "Procalcitonina",
    "Troponina T": "Troponina T", "Ck-Total": "CK-Total", "Ck-Mb": "CK-MB",
    
    # Gases
    "Ph": "pH", # <--- NUEVO
    "Po2": "pO2", "Pco2": "pCO2", "So2": "SatO2", "Hco3": "HCO3",
    "Exceso De Base": "BE", "Acido Lactico": "Lactato", "Tco2": "tCO2",
    
    # Orina / Otros
    "Glucosa": "Glu", "Sedimento Urinario": "Sedimento",
    "Aspecto": "Aspecto", "Color": "Color", "Cetonas": "Cetonas",
    "Nitritos": "Nitritos", "Glucosa En Orina": "Glu.Orina"
}

def procesar_pdf(archivo_bytes):
    resultados = []
    seen = set() # <--- NUEVO: Conjunto para detectar duplicados
    
    with pdfplumber.open(archivo_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text: continue
            lines = text.split('\n')
            
            for line in lines:
                line = line.replace('*', '').strip()
                if not line: continue

                # --- NUEVO: PRE-PROCESAMIENTO DE ABREVIACIONES ---
                # Reemplaza antes de filtrar, ignorando mayúsculas/minúsculas
                for nombre_largo, abreviacion in ABREVIACIONES.items():
                    pattern = re.compile(re.escape(nombre_largo), re.IGNORECASE)
                    line = pattern.sub(abreviacion, line)

                # --- 1. FILTROS DE BASURA ADMINISTRATIVA ---
                ignorar = ["Avda", "Carrera", "Teléfono", "Miguel", "Ministerio", "Salud",
                           "Hospital", "Barros", "Luco", "RUT", "Paciente", "Solicitante",
                           "Validado", "Fecha", "Hora", "Página", "Bioquimico",
                           "Hematologia", "Coagulacion", "Gases", "Orina Completa", "Urocultivo",
                           "Inmunoquimica", "Quimica Sanguinea"]
                
                # --- 2.
