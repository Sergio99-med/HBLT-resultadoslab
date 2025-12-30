import streamlit as st
import pdfplumber
import re
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="HBL Extractor V4.0", page_icon="🏥", layout="centered")

st.title("🏥 Extractor HBLT - V4.0 (Infecto-Uro)")
st.markdown("### Sube tu PDF (Sangre, Orina o Cultivos).")

# --- LISTAS DE DETECCIÓN INTELIGENTE ---
ANTIBIOTICOS = [
    "Amikacina", "Ampicilina", "Amoxicilina", "Azitromicina", "Cefazolina", "Cefepime", 
    "Ceftriaxona", "Cefuroximo", "Ciprofloxacino", "Clindamicina", "Cotrimoxazol", 
    "Dalbavancina", "Daptomicina", "Eritromicina", "Gentamicina", "Imipenem", 
    "Levofloxacino", "Linezolid", "Meropenem", "Nitrofurantoina", "Oxacilina", 
    "Penicilina", "Rifampicina", "Trimetoprim", "Vancomicina", "Piperacilina"
]

MICROBIO_KEYWORDS = [
    "Cocaceas", "Bacilos", "Levaduras", "Staphylococcus", "Streptococcus", 
    "Escherichia", "Klebsiella", "Pseudomonas", "Enterococcus", "Candida", 
    "Tincion", "Colonia", "UFC", "Recuento", "Vial", "Aerobio", "Anaerobio"
]

# --- DICCIONARIO DE ABREVIACIONES ---
ABREVIACIONES = {
    # Hematología
    "Hemoglobina": "Hb", "Hematocrito": "Hto", "Recuento De Leucocitos": "GB", 
    "Plaquetas": "Plaq", "Recuento De Plaquetas": "Plaq", 
    "Vcm": "VCM", "Hcm": "HCM", "Chcm": "CHCM",
    
    # Coagulación
    "Tiempo De Protrombina": "TP", "Tiempo De Protrombina Seg": "TP seg",
    "Tiempo De Tromboplastina": "TTPA", "Inr": "INR",
    
    # Bioquímica
    "Nitrogeno Ureico": "BUN", "Urea": "Urea", "Creatinina": "Crea", 
    "Sodio": "Na", "Potasio": "K", "Cloro": "Cl", "Proteina C Reactiva": "PCR", 
    "Acido Urico": "Ac.Urico", "Calcio": "Ca", "Fosforo": "P", 
    "Proteinas Totales": "Prot.Tot", "Albumina": "Alb", "Ldh": "LDH", 
    "Fosfatasa Alcalina": "FA", "Got": "GOT", "Ast": "GOT", "Got/Ast": "GOT",
    "Gpt": "GPT", "Alt": "GPT", "Gpt/Alt": "GPT", "Ggt": "GGT", "Gama Glutamil": "GGT",
    "Colesterol Total": "Col.Tot", "Bilirrubina Total": "Bili.T", "Procalcitonina": "Procalcitonina",
    "Troponina T": "Troponina T", "Ck-Total": "CK-Total", "Ck-Mb": "CK-MB",
    
    # Gases
    "Ph": "pH", "Po2": "pO2", "Pco2": "pCO2", "So2": "SatO2", "Hco3": "HCO3", 
    "Exceso De Base": "BE", "Acido Lactico": "Lactato", "Tco2": "tCO2", 
    
    # Orina Completa (NUEVO)
    "Glucosuria": "Glu.Orina", "Proteinuria": "Prot.Orina", 
    "Cuerpos Cetonicos": "Cetonas", "Eritrocitohemoglobina": "Hb.Orina",
    "Leucocitos": "Leucocitos", "Eritrocito": "Eritrocitos", 
    "Celulas Epiteliales": "Cel.Epit", "Bacterias": "Bacterias", 
    "Cristales": "Cristales", "Cilindros": "Cilindros",
    "Ph Urinario": "pH", "Densidad": "Densidad",
    "Aspecto": "Aspecto", "Color": "Color", "Nitritos": "Nitritos",
    "Urobilinogeno": "Urob", "Bilirrubina": "Bili"
}

def procesar_pdf(archivo_bytes):
    resultados = []
    with pdfplumber.open(archivo_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text: continue
            lines = text.split('\n')
            
            for line in lines:
                line_clean = line.replace('*', '').strip()
                if not line_clean: continue
                
                # --- 1. FILTROS DE BASURA ---
                ignorar = ["Avda", "Carrera", "Teléfono", "Miguel", "Ministerio", "Salud", 
                           "Hospital", "Barros", "Luco", "RUT", "Paciente", "Solicitante", 
                           "Validado", "Fecha", "Hora", "Página", "Bioquimico", 
                           "Hematologia", "Coagulacion", "Gases", "Orina Completa", "Urocultivo",
                           "Inmunoquimica", "Quimica Sanguinea", "Informe Microbiologico"]
                
                basura_clinica = ["Septico", "Sepsis", "Choque", "Riesgo", "Representa", "Bajo", "Alto", "Severa", "Valores de Referencia"]

                if any(x.upper() in line_clean.upper() for x in ignorar): continue
                if any(x.upper() in line_clean.upper() for x in basura_clinica): continue
                if re.search(r'\d{2}/\d{2}/\d{4}', line_clean): continue
                
                palabras_rango = ["Día", "Dia", "Mes", "Año", "Adulto", "Niño", "Semanas"]
                if any(p in line_clean for p in palabras_rango): continue

                # --- 2. DETECTOR DE ANTIBIOGRAMA (PRIORIDAD) ---
                # Detecta si la línea contiene un antibiótico conocido
                antibiotico_detectado = next((ab for ab in ANTIBIOTICOS if ab.upper() in line_clean.upper()), None)
                if antibiotico_detectado:
                    # Busca S, I, R al final de la línea o aislado
                    match_sir = re.search(r'\b(S|I|R)\b', line_clean)
                    if match_sir:
                        sir = match_sir.group(1)
                        resultados.append(f"{antibiotico_detectado} ({sir})")
                        continue

                # --- 3. DETECTOR MICROBIOLÓGICO (TEXTO LIBRE) ---
                if any(k.upper() in line_clean.upper() for k in MICROBIO_KEYWORDS):
                    # Limpiamos exceso de espacios y guardamos la frase relevante
                    frase = re.sub(r'\s+', ' ', line_clean).strip()
                    # Filtramos headers vacíos
                    if len(frase) > 3 and "Resultado" not in frase:
                        resultados.append(frase)
                    continue

                # --- 4. PARSEO ESTÁNDAR (SANGRE / ORINA) ---
                nombre = ""
                valor = ""

                # Patrón A: Nombre + Número (Soporta rangos como 0-3)
                # Regex: Nombre + Espacio/: + (Numero o Rango 0-3 o <Numero)
                match_num = re.search(r'^(.+?)[:\s]+([<>]?\d+(?:-\d+)?[.,]?\d*)', line_clean)
                
                # Patrón B: Cualitativos (Positivo, Amarillo, etc.)
                palabras_clave = r'(Positivo|Negativo|Normal|Amarillo|Ambar|Turbio|Limpido|Escaso|Regular|Abundante|Indeterminado|Reactivo|No Reactivo|Claro|Ligero)'
                match_text = re.search(r'^(.+?)[:\s]+(' + palabras_clave + r'.*)$', line_clean, re.IGNORECASE)

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

                # Abreviación y Limpieza
                es_porcentaje = "%" in line_clean
                nombre_limpio = nombre.replace("%", "").replace(":", "").strip().title()
                nombre_final = ABREVIACIONES.get(nombre_limpio, nombre_limpio)
                
                if es_porcentaje and "%" not in valor:
                    valor = f"{valor}%"
                
                # Evitar duplicados exactos en orina (ej: Leucocitos sale 2 veces)
                dato_formateado = f"{nombre_final} {valor}"
                if dato_formateado not in resultados:
                    resultados.append(dato_formateado)
    
    return " - ".join(resultados)

# --- INTERFAZ ---
archivo = st.file_uploader("Arrastra tu PDF aquí", type="pdf")
st.info("ℹ️ Nota: Resultados NO numéricos (ej: orina) pueden no aparecer automáticamente. Digítalos manual si faltan.")

if archivo:
    try:
        with st.spinner("Procesando documento..."):
            texto = procesar_pdf(archivo)
        
        if len(texto) > 0:
            st.success("✅ ¡Extracción exitosa!")
            st.caption("1️⃣ Revisa y edita:")
            texto_final = st.text_area("Edición", value=texto, height=150, label_visibility="collapsed")
            st.caption("2️⃣ Copia aquí 👇")
            st.code(texto_final, language=None)
            st.warning("⚠️ IMPORTANTE: Verifica siempre que los resultados correspondan a tu paciente.")
        else:
            st.warning("⚠️ El PDF se procesó, pero no encontré exámenes legibles.")
    except Exception as e:
        st.error(f"Error técnico: {e}")

st.write("---")
