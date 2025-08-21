# Lista de categoria
"""
    Fuerza
    Resistencia
    Habilidad
    Carisma
    Empatia
    Oscuridad
    Voluntad
    Astucia
"""

# Definir roles principales según combinaciones de habilidades

role_emojis = {
    "Fuerza": "💪",
    "Resistencia": "🛡️",
    "Habilidad": "🎯",
    "Carisma": "✨",
    "Empatia": "❤️",
    "Oscuridad": "🌑",
    "Voluntad": "🪨",
    "Astucia": "🦊",
    "Bromista": "🤡",
}

role_rules = {
    # Combinaciones con Fuerza
    ("Fuerza", "Resistencia"): "🛡️ Guerrero Blindado",
    ("Resistencia", "Fuerza"): "⚒️ Titan de Hierro",
    ("Fuerza", "Habilidad"): "💥 Berserker Ágil",
    ("Habilidad", "Fuerza"): "🏹 Cazador Implacable",
    ("Fuerza", "Carisma"): "💫 Paladín Inspirador",
    ("Carisma", "Fuerza"): "🦸‍♂️ Comandante Heroico",
    ("Fuerza", "Voluntad"): "🔥 Campeón del Valor",
    ("Voluntad", "Fuerza"): "💪 Luchador Indomable",
    ("Fuerza", "Astucia"): "🧠 Guardián Astuto",
    ("Astucia", "Fuerza"): "⚔️ Táctico Salvaje",
    ("Fuerza", "Oscuridad"): "🌑 Guerrero Sombrío",
    ("Oscuridad", "Fuerza"): "💀 Asesino Brutal",
    ("Fuerza", "Empatia"): "🛡️ Defensor del Pueblo",
    ("Empatia", "Fuerza"): "🤝 Protector Noble",
    ("Fuerza", "Bromista"): "🎭 Guerrero Arlequín",
    ("Bromista", "Fuerza",): "🎪 Arlequín Formidable",

    # Combinaciones con Resistencia
    ("Resistencia", "Habilidad"): "💪 Luchador Experimentado",
    ("Habilidad", "Resistencia"): "🛡️ Guardia Intrépido",
    ("Resistencia", "Carisma"): "🗣️ Líder Inquebrantable",
    ("Carisma", "Resistencia"): "🎤 Sargento Carismático",
    ("Resistencia", "Voluntad"): "⚔️ Héroe Inmortal",
    ("Voluntad", "Resistencia"): "💀 Defensor Resistente",
    ("Resistencia", "Astucia"): "🧠 Táctico de Acero",
    ("Astucia", "Resistencia"): "♟️ Estratégico Imparable",
    ("Resistencia", "Oscuridad"): "🌘 Sombra Inquebrantable",
    ("Oscuridad", "Resistencia"): "🖤 Guerrero de las Sombras",
    ("Resistencia", "Empatia"): "💖 Guerrero Compasivo",
    ("Empatia", "Resistencia"): "🤗 Defensor Empático",
    ("Resistencia", "Bromista"): "🎭 Arlequín solitario",
    ("Bromista", "Resistencia"): "🤡 Defensor Arlequín",

    # Combinaciones con Habilidad
    ("Habilidad", "Carisma"): "🕵️‍♂️ Espía Astuto",
    ("Carisma", "Habilidad"): "🎯 Líder Excepcional",
    ("Habilidad", "Voluntad"): "🔪 Asesino Determinado",
    ("Voluntad", "Habilidad"): "🧗‍♂️ Maestro de la Supervivencia",
    ("Habilidad", "Astucia"): "🧳 Ladrón Ingenioso",
    ("Astucia", "Habilidad"): "🦸 Rastreador Ágil",
    ("Habilidad", "Oscuridad"): "🌒 Asesino Sigiloso",
    ("Oscuridad", "Habilidad"): "🌑 Sombra Mortal",
    ("Habilidad", "Empatia"): "🩺 Sanador Preciso",
    ("Empatia", "Habilidad"): "💉 Curandero Ágil",
    ("Habilidad", "Bromista"): "🎭 Ladrón Bromista",
    ("Bromista", "Habilidad"): "🤡 Arlequín Ágil",

    # Combinaciones con Carisma
    ("Carisma", "Voluntad"): "💡 Inspirador Inquebrantable",
    ("Voluntad", "Carisma"): "🧠 Líder Visionario",
    ("Carisma", "Astucia"): "🎭 Embajador Astuto",
    ("Astucia", "Carisma"): "🎩 Líder Manipulador",
    ("Carisma", "Oscuridad"): "🌑 Tirano Sombrío",
    ("Oscuridad", "Carisma"): "👑 Líder Oscuro",
    ("Carisma", "Empatia"): "💖 Guía Compasiva",
    ("Empatia", "Carisma"): "🌟 Líder Benévolo",
    ("Carisma", "Bromista"): "🎪 Arlequín Embajador",
    ("Bromista", "Carisma"): "🤡 Líder Bromista",

    # Combinaciones con Voluntad
    ("Voluntad", "Astucia"): "🔧 Superviviente Ingenioso",
    ("Astucia", "Voluntad"): "🏆 Maestro de la Resiliencia",
    ("Voluntad", "Oscuridad"): "🖤 Campeón Oscuro",
    ("Oscuridad", "Voluntad"): "💀 Luchador Sin Piedad",
    ("Voluntad", "Empatia"): "🤝 Defensor Resiliente",
    ("Empatia", "Voluntad"): "💪 Vigilante Compasivo",
    ("Voluntad", "Bromista"): "🎪 Líder Bromista",
    ("Bromista", "Voluntad"): "🤡 Arlequín Campeón",

    # Combinaciones con Astucia
    ("Astucia", "Oscuridad"): "🌒 Espía Nocturno",
    ("Oscuridad", "Astucia"): "🕵️‍♂️ Ladrón Oscuro",
    ("Astucia", "Empatia"): "🧠 Estratégico Altruista",
    ("Empatia", "Astucia"): "🤝 Táctico Empático",
    ("Astucia", "Bromista"): "🤡 Táctico Bromista",
    ("Bromista", "Astucia"): "🎭 Ladrón Bromista",

    # Combinaciones con Oscuridad
    ("Oscuridad", "Empatia"): "🌑 Vigilante de las Sombras",
    ("Empatia", "Oscuridad"): "🖤 Defensor Oscuro",
    ("Oscuridad", "Bromista"): "🎭 Ladrón arlequín",
    ("Bromista", "Oscuridad"): "🌑 Guerrero Sombrío"
}


# Rol complementario basado en la tercera habilidad
complemento_roles = {
    "Fuerza": "Coloso",
    "Resistencia": "Guardián",
    "Habilidad": "Maestro",
    "Carisma": "Inspirador",
    "Voluntad": "Inquebrantable",
    "Astucia": "Genio",
    "Oscuridad": "Misterio",
    "Empatia": "Sanador",
    "Bromista": "Burlón",
}
