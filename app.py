import streamlit as st
import pdfplumber
import re
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="HBL Extractor V3.3", page_icon="🏥", layout="centered")

st.title("🏥 Extractor HBLT - Exámenes de Laboratorio")
st.markdown("### Sube tu PDF del Barros Luco y obtén los resultados.")

# --- DICCIONARIO DE ABREVIACIONES Y CORRECCIONES ---
ABREVIACIONES = {
    # Hematología
    "Hemoglobina": "Hb", "Hematocrito": "Hto", "Recuento De Leucocitos": "GB", 
    "Plaquetas": "Plaq", "Recuento De Plaquetas": "Plaq", 
    "Vcm": "VCM", "Recuento De Eritrocitos": "GR", "Hcm": "HCM", "Chcm": "CHCM",
    
    # Coagulación
    "Tiempo De Protrombina": "TP", 
    "Tiempo De Protrombina Seg": "TP seg", # <--- NUEVO
    "Tiempo De Tromboplastina": "TTPA", "Inr": "INR",
    
    # Bioquímica / Función Renal / Hepática
    "Nitrogeno Ureico": "BUN", "Urea": "Urea", "Creatinina": "Crea", 
    "Sodio": "Na", "Potasio": "K", "Cloro": "Cl", "Proteina C Reactiva": "PCR", 
    "Acido Urico": "Ac.Urico", "Calcio": "Ca", "Fosforo": "P", 
    "Proteinas Totales": "Prot T", "Albumina": "Alb", "Ldh": "LDH", 
    "Fosfatasa Alcalina": "FA", "Got": "GOT", "Ast": "GOT", "Got/Ast": "GOT",
    "Gpt": "GPT", "Alt": "GPT", "Gpt/Alt": "GPT", "Ggt": "GGT", "Gama Glutamil": "GGT",
    "Colesterol Total": "Col T", "Bilirrubina Total": "BT", "Bilirrubina Directa": "BD", "Bilirrubina Indirecta": "BI", "Procalcitonina": "Procalcitonina",
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
    with pdfplumber.open(archivo_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text: continue
            lines = text.split('\n')
            
            for line in lines:
                line = line.replace('*', '').strip()
                if not line: continue
                
                # --- 1. FILTROS DE BASURA ADMINISTRATIVA ---
                ignorar = ["Avda", "Carrera", "Teléfono", "Miguel", "Ministerio", "Salud", 
                           "Hospital", "Barros", "Luco", "RUT", "Paciente", "Solicitante", 
                           "Validado", "Fecha", "Hora", "Página", "Bioquimico", 
                           "Hematologia", "Coagulacion", "Gases", "Orina Completa", "Urocultivo",
                           "Inmunoquimica", "Quimica Sanguinea"]
                
                # --- 2. FILTROS CLÍNICOS ---
                basura_clinica = ["Septico", "Sepsis", "Choque", "Riesgo", "Representa", "Bajo", "Alto", "Severa"]

                if any(x.upper() in line.upper() for x in ignorar): continue
                if any(x.upper() in line.upper() for x in basura_clinica): continue
                
                if re.search(r'\d{2}/\d{2}/\d{4}', line): continue
                palabras_rango = ["Día", "Dia", "Mes", "Año", "Adulto", "Niño", "Semanas"]
                if any(p in line for p in palabras_rango): continue

                nombre = ""
                valor = ""

                # --- 3. BÚSQUEDA DEL DATO ---
                match_num = re.search(r'^(.+?)[:\s]+([<>]?-?\d+[.,]?\d*)', line)
                palabras_clave = r'(Positivo|Negativo|Normal|Amarillo|Ambar|Turbio|Limpido|Escaso|Regular|Abundante|Indeterminado|Reactivo|No Reactivo)'
                match_text = re.search(r'^(.+?)[:\s]+(' + palabras_clave + r'.*)$', line, re.IGNORECASE)

                if match_num:
                    nombre = match_num.group(1).strip()
                    valor = match_num.group(2).strip()
                    if re.match(r'^\d', nombre): continue 
                elif match_text:
                    nombre = match_text.group(1).strip()
                    valor = match_text.group(2).strip()
                else:
                    continue

                if len(nombre) < 2: continue
                if ":" in nombre and len(nombre) < 5: continue

                # --- 4. FORMATEO Y ABREVIACIÓN ---
                es_porcentaje = "%" in line
                
                nombre_limpio = nombre.replace("%", "").replace(":", "").strip().title()
                nombre_final = ABREVIACIONES.get(nombre_limpio, nombre_limpio)
                
                if es_porcentaje and "%" not in valor:
                    valor = f"{valor}%"
                
                resultados.append(f"{nombre_final} {valor}")
    
    return " - ".join(resultados)

# --- INTERFAZ ---
archivo = st.file_uploader("📂Arrastra tu PDF aquí", type="pdf")
st.info("ℹ️ Nota: Resultados NO numéricos (ej: orina) pueden no aparecer o estar erroneos. Digítalos manualmente de ser necesario.")

if archivo:
    try:
        with st.spinner("Procesando documento..."):
            texto = procesar_pdf(archivo)
        
        if len(texto) > 0:
            st.success("✅ ¡Extracción exitosa!")
            
            st.caption("1️⃣ Revisa y edita:")
            texto_final = st.text_area("Edición", value=texto, height=100, label_visibility="collapsed")
            
            st.caption("2️⃣ Copia aquí 👇")
            st.code(texto_final, language=None)
            
            st.warning("⚠️ IMPORTANTE: Verifica siempre que los resultados correspondan a tu paciente.")
        else:
            st.warning("⚠️ El PDF se procesó, pero no encontré exámenes legibles.")
    except Exception as e:
        st.error(f"Error técnico: {e}")

st.write("---")
