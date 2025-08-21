channelColor = "\033[38;5;51m"

white = "\033[38;5;255m"
resetColor = "\033[38;5;244m"
red = "\033[38;5;196m"
green = "\033[38;5;48m"
azul = "\033[38;5;69m"
rosa = "\033[38;5;213m"
morado = "\033[38;5;99m"
dorado = "\033[38;5;221m"

userColors = {
    "regularUserColor": "\033[38;5;95m",
    "userSubColor": "\033[38;5;69m",
    "userVipColor": "\033[38;5;207m",
    "userModColor": "\033[38;5;121m",
}

def colorConvert(hex_color: str) -> str:
    """
    Convierte un color hexadecimal a un código ANSI 256-color para foreground.
    """
    if  hex_color.startswith("#"):
        hex_color = hex_color.lstrip("#")

    if len(hex_color) != 6:
        # raise ValueError("Color hexadecimal inválido")
        return white    

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Conversión a índice de la tabla ANSI de 256 colores
    def rgb_to_ansi_index(r, g, b):
        if r == g == b:
            if r < 8:
                return 16
            if r > 248:
                return 231
            return round(((r - 8) / 247) * 24) + 232
        return 16 + (36 * round(r / 255 * 5)) + (6 * round(g / 255 * 5)) + round(b / 255 * 5)

    ansi_code = rgb_to_ansi_index(r, g, b)
    return f"\033[38;5;{ansi_code}m"
