import streamlit as st
import pdfplumber
import re

# Configuración de la página
st.set_page_config(page_title="HBL Extractor", page_icon="🏥", layout="centered")

# Título y descripción
st.title("🏥 Extractor HBL - Resultados de Exámenes de Laboratorio")
st.markdown("Sube tu PDF del Barros Luco y obtén los resultados al instante.")
st.caption("Sube el PDF, revisa el texto y copialo a la ficha.")

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
    "Exceso De Base": "BE", "Acido Lactico": "Lactato", "Tco2": "tCO2", "Glucosa": "Glu",
    "Sedimento Urinario": "Sedimento", "Aspecto": "Aspecto", "Color": "Color",
    "Cetonas": "Cetonas", "Nitritos": "Nitritos", "Glucosa En Orina": "Glu.Orina"
}

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
                
                # --- FILTROS DE BASURA ---
                ignorar = ["Avda", "Carrera", "Teléfono", "Miguel", "Ministerio", "Salud", 
                           "Hospital", "Barros", "Luco", "RUT", "Paciente", "Solicitante", 
                           "Validado", "Fecha", "Hora", "Página", "Nota", "Valor", "Critico", 
                           "Método", "Anterior", "Referencia", "Unidad", "Medida", "Edad", 
                           "Sexo", "Procedencia", "Bioquimico", "Hematologia", "Coagulacion", "Gases",
                           "Orina Completa", "Urocultivo"]
                
                if any(x.upper() in line.upper() for x in ignorar): continue
                if re.search(r'\d{2}/\d{2}/\d{4}', line): continue
                palabras_rango = ["Día", "Dia", "Mes", "Año", "Adulto", "Niño", "Semanas"]
                if any(p in line for p in palabras_rango): continue

                nombre = ""
                valor = ""

                # Estrategias de búsqueda
                match_num = re.search(r'^(.+?)\s+([<>]?-?\d+[.,]?\d*)', line)
                palabras_clave = r'(Positivo|Negativo|Normal|Amarillo|Ambar|Turbio|Limpido|Escaso|Regular|Abundante|Indeterminado|Reactivo|No Reactivo)'
                match_text = re.search(r'^(.+?)\s+(' + palabras_clave + r'.*)$', line, re.IGNORECASE)

                if match_num:
                    nombre = match_num.group(1).strip()
                    valor = match_num.group(2).strip()
                    if re.match(r'^\d', nombre): continue 
                elif match_text:
                    nombre = match_text.group(1).strip()
                    valor = match_text.group(2).strip()
                else:
                    continue

                if len(nombre) < 3: continue
                if ":" in nombre and len(nombre) < 5: continue

                # Abreviar
                es_porcentaje = "%" in line
                nombre_limpio = nombre.replace("%", "").replace(":", "").strip().title()
                nombre_final = ABREVIACIONES.get(nombre_limpio, nombre_limpio)
                
                if es_porcentaje:
                    valor = f"{valor}%"
                
                resultados.append(f"{nombre_final} {valor}")
    
    return " - ".join(resultados)

# --- INTERFAZ ---
st.write("---")
archivo = st.file_uploader("📂 Cargar PDF (Arrastra aquí)", type="pdf")

if archivo:
    with st.spinner('Analizando documento...'):
        try:
            texto = procesar_pdf(archivo)
            if texto:
                st.success("✅ ¡Extracción exitosa!")
                
                # AQUI ESTÁ EL CAMBIO MAGICO: st.text_area
                # height=150 define qué tan alto es el cuadro inicialmente
                st.text_area("📋 ¡Listo! Copia el texto de abajo y recuerda siempre revisar que esten los datos correctos:", value=texto, height=150)
                
                st.caption("Tip: Puedes editar el texto dentro del cuadro antes de copiarlo si hay algún error.")
            else:
                st.warning("⚠️ No encontré resultados legibles. Verifica el PDF.")
    except Exception as e:
        st.error(f"Error técnico: {e}")
