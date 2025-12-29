import streamlit as st
import pdfplumber
import re
import requests
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="HBL Extractor", page_icon="🏥", layout="centered")

st.title("🏥 Extractor HBLT - Resultados de Exámenes de Laboratorio")
st.markdown("### Sube tu PDF del Barros Luco y obtén los resultados al instante.")
st.caption("Recuerda siempre revisar que sea el PDF de tu paciente")

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

def procesar_pdf(archivo_bytes):
    resultados = []
    # Abrimos el archivo desde los bytes en memoria
    with pdfplumber.open(archivo_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text: continue
            lines = text.split('\n')
            
            for line in lines:
                line = line.replace('*', '').strip()
                if not line: continue
                
                # --- FILTROS ---
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

                # Busquedas
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

# --- INTERFAZ CON PESTAÑAS ---
tab1, tab2 = st.tabs(["📂 Subir Archivo", "🔗 Pegar Link"])

# --- OPCIÓN 1: ARCHIVO ---
with tab1:
    archivo = st.file_uploader("Arrastra tu PDF aquí", type="pdf")
    if archivo:
        try:
            texto = procesar_pdf(archivo)
            if texto:
            st.success("✅ ¡Extracción exitosa!")
            st.text_area("📋 Copia los resultados aquí:", value=texto, height=150)
            st.caption("Tip: Puedes editar el texto de arriba antes de copiar. Recuerda siempre asegurarte que sean los resultados correctos y de tu paciente!")
            else:
                st.warning("⚠️ Sin resultados legibles.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- OPCIÓN 2: LINK (EXPERIMENTAL) ---
with tab2:
    url = st.text_input("Pega el link del PDF aquí:")
    st.caption("Nota: Si el link es de la Intranet del hospital, puede que no funcione por seguridad.")
    
    if url:
        if st.button("Extraer desde Link"):
            try:
                with st.spinner("Intentando descargar..."):
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        # Convertimos la respuesta web en un archivo virtual
                        archivo_virtual = io.BytesIO(response.content)
                        texto_url = procesar_pdf(archivo_virtual)
                        
                        if texto_url:
                            st.success("✅ ¡Leído desde Link!")
                            st.text_area("📋 Copia aquí (Link):", value=texto_url, height=150)
                            st.caption("Tip Pro: Si el Link falla, presiona Ctrl+S en el PDF y arrástralo a la primera pestaña.")
                        else:
                            st.warning("⚠️ El link abrió, pero no detecté datos.")
                    else:
                        st.error(f"❌ Error al acceder al link (Código {response.status_code}). Probablemente es una red privada.")
            except Exception as e:
                st.error(f"❌ No se pudo conectar. El servidor no tiene acceso a la red del hospital. Error: {e}")

st.write("---")
