
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json

# 🔐 Inicializa Firebase con credenciales desde st.secrets
if not firebase_admin._apps:
    cred_dict = json.loads(st.secrets["firebase_credentials"])
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def guardar_usuario(usuario):
    db.collection("usuarios").document(usuario["email"]).set(usuario)

def guardar_match(email1, email2):
    db.collection("matches").add({
        "user1_email": email1,
        "user2_email": email2,
        "timestamp": datetime.datetime.now()
    })

def usuario_ya_tiene_match(email):
    m1 = db.collection("matches").where("user1_email", "==", email).stream()
    m2 = db.collection("matches").where("user2_email", "==", email).stream()
    return any(m1) or any(m2)

def signos_compatibles(signo1, signo2):
    compat = {
        "Aries": ["Leo", "Sagitario", "Géminis", "Acuario"],
        "Tauro": ["Virgo", "Capricornio", "Cáncer", "Piscis"],
        "Géminis": ["Libra", "Acuario", "Aries", "Leo"],
        "Cáncer": ["Escorpio", "Piscis", "Tauro", "Virgo"],
        "Leo": ["Aries", "Sagitario", "Géminis", "Libra"],
        "Virgo": ["Tauro", "Capricornio", "Cáncer", "Escorpio"],
        "Libra": ["Géminis", "Acuario", "Leo", "Sagitario"],
        "Escorpio": ["Cáncer", "Piscis", "Virgo", "Capricornio"],
        "Sagitario": ["Aries", "Leo", "Libra", "Acuario"],
        "Capricornio": ["Tauro", "Virgo", "Escorpio", "Piscis"],
        "Acuario": ["Géminis", "Libra", "Aries", "Sagitario"],
        "Piscis": ["Cáncer", "Escorpio", "Tauro", "Capricornio"]
    }
    return signo2 in compat.get(signo1, [])

def buscar_match(usuario):
    usuarios = db.collection("usuarios").stream()
    for doc in usuarios:
        otro = doc.to_dict()
        if otro["email"] == usuario["email"]:
            continue
        if usuario_ya_tiene_match(usuario["email"]) or usuario_ya_tiene_match(otro["email"]):
            continue
        if otro["interes_en_genero"] not in [usuario["genero"], "ambos"]:
            continue
        if usuario["interes_en_genero"] not in [otro["genero"], "ambos"]:
            continue
        if otro["tipo_relacion"] != usuario["tipo_relacion"]:
            continue
        if otro["creencia"] != usuario["creencia"]:
            continue
        if otro["quiere_hijos"] != usuario["quiere_hijos"]:
            continue
        if not signos_compatibles(usuario["signo"], otro["signo"]):
            continue
        if set(usuario["hobbies"]).isdisjoint(otro["hobbies"]):
            continue
        return otro
    return None

# INTERFAZ STREAMLIT
st.title("💘 App de Match por Afinidad")

with st.form("formulario"):
    nombre = st.text_input("Nombre")
    edad = st.number_input("Edad", min_value=18, max_value=100)
    genero = st.selectbox("Género", ["femenino", "masculino", "no binario"])
    email = st.text_input("Correo electrónico")
    universidad = st.text_input("Universidad")
    cumpleaños = st.date_input("Cumpleaños")
    tipo_relacion = st.radio("Tipo de relación", ["seria", "casual"])
    creencia = st.radio("Creencia", ["creyente", "ateo", "agnóstico"])
    signo = st.selectbox("Signo zodiacal", [
        "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
        "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"])
    altura = st.number_input("Altura (m)", min_value=1.0, max_value=2.5)
    hobbies = st.multiselect("Hobbies", ["leer", "cine", "viajar", "música", "deportes", "dibujar"])
    quiere_hijos = st.radio("¿Quieres hijos?", ["sí", "no"])
    interes_en_genero = st.radio("¿Te interesa?", ["hombre", "mujer", "ambos"])

    enviar = st.form_submit_button("Enviar")

if enviar:
    usuario = {
        "nombre": nombre,
        "edad": edad,
        "genero": genero,
        "email": email,
        "universidad": universidad,
        "cumpleaños": str(cumpleaños),
        "tipo_relacion": tipo_relacion,
        "creencia": creencia,
        "signo": signo,
        "altura": altura,
        "hobbies": hobbies,
        "quiere_hijos": quiere_hijos,
        "interes_en_genero": interes_en_genero,
    }

    guardar_usuario(usuario)
    match = buscar_match(usuario)

    if match:
        guardar_match(usuario["email"], match["email"])
        st.success(f"🎉 ¡Hiciste match con {match['nombre']}!")
    else:
        st.warning("😢 No se encontró pareja compatible por ahora.")
