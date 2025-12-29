import streamlit as st
import pdfplumber
import re
import requests
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="HBL Extractor", page_icon="🏥", layout="centered")

st.title("🏥 Extractor HBLT - Exámenes de Laboratorio")
st.markdown("### Sube tu PDF del Barros Luco y obtén los resultados.")

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
    
    # AVISO AZUL (MÁS VISIBLE)
    st.info("ℹ️ Nota: Resultados NO numéricos pueden no aparecer. Digítalos manualmente si faltan.")
    
    if archivo:
        try:
            with st.spinner("Procesando documento..."):
                texto = procesar_pdf(archivo)
            
            if len(texto) > 0:
                st.success("✅ ¡Extracción exitosa!")
                
                # 1. ÁREA DE EDICIÓN
                st.caption("1️⃣ Revisa y edita el texto si es necesario:")
                texto_final = st.text_area("Edición", value=texto, height=100, label_visibility="collapsed")
                
                # 2. BOTÓN DE COPIADO
                st.caption("2️⃣ Copia el resultado final con un click aquí 👇")
                st.code(texto_final, language=None)
                
                # AVISO AMARILLO AL FINAL
                st.warning("⚠️ IMPORTANTE: Verifica siempre que los resultados correspondan a tu paciente.")
                
            else:
                st.warning("⚠️ El PDF se procesó, pero no encontré exámenes legibles.")
                st.info("Posibles causas: \n1. Es un PDF escaneado (imagen).\n2. El formato es muy distinto al estándar.\n3. Intenta subir un PDF original del sistema.")
                
        except Exception as e:
            st.error(f"Error técnico: {e}")

# --- OPCIÓN 2: LINK ---
with tab2:
    url = st.text_input("Pega el link del PDF aquí:")
    
    # AVISO
    st.info("ℹ️Nota: Si el link es de la Intranet y no funciona, usa Ctrl+S para guardarlo y súbelo en la otra pestaña.")
    
    if url:
        if st.button("Extraer desde Link"):
            try:
                with st.spinner("Descargando..."):
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        archivo_virtual = io.BytesIO(response.content)
                        texto_url = procesar_pdf(archivo_virtual)
                        
                        if len(texto_url) > 0:
                            st.success("✅ ¡Leído desde Link!")
                            
                            # 1. EDICIÓN
                            st.caption("1️⃣ Revisa y edita:")
                            texto_url_final = st.text_area("Edición Link", value=texto_url, height=100, label_visibility="collapsed")
                            
                            # 2. COPIADO
                            st.caption("2️⃣ Copia con un click 👇")
                            st.code(texto_url_final, language=None)
                            
                            # AVISO AMARILLO AL FINAL
                            st.warning("⚠️ IMPORTANTE: Verifica siempre que los resultados correspondan a tu paciente.")
                        else:
                            st.warning("⚠️ El link abrió, pero no detecté datos.")
                    else:
                        st.error(f"❌ Error al acceder al link (Código {response.status_code}). Probablemente es una red privada.")
            except Exception as e:
                st.error(f"❌ No se pudo conectar. El servidor no tiene acceso a la red del hospital. Error: {e}")

st.write("---")
