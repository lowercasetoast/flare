"""
flare.charsets — pre-defined character sets and palette utilities.

Import any charset string and pass it as the *charset* argument to
:class:`~flare.core.Canvas`.
"""

# ── single-bit charsets (on/off, best for braille/block) ────────────────────

BRAILLE = "braille"      # default: 2×4 braille cells
BLOCK   = "block"        # 2×2 quarter-block elements

# ── grayscale ramps (ordered light → dark) ───────────────────────────────────

ASCII_RAMP      = " .:-=+*#%@"
EXTENDED_RAMP   = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
SHADE_RAMP      = " ░▒▓█"
DOTS_RAMP       = " .:;!I#@"
NUMBERS_RAMP    = " 123456789"
HEX_RAMP        = " 0123456789ABCDEF"
MATRIX_RAMP     = " 01"
STAR_RAMP       = " .*#"
EMOJI_RAMP      = "  ░▒▓"       # safe subset for terminals

# ── custom symbol sets ────────────────────────────────────────────────────────

BRAILLE_RAMP = (
    "⠀⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏"
    "⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟"
    "⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯"
    "⠰⠱⠲⠳⠴⠵⠶⠷⠸⠹⠺⠻⠼⠽⠾⠿"
    "⡀⡁⡂⡃⡄⡅⡆⡇⡈⡉⡊⡋⡌⡍⡎⡏"
    "⡐⡑⡒⡓⡔⡕⡖⡗⡘⡙⡚⡛⡜⡝⡞⡟"
    "⡠⡡⡢⡣⡤⡥⡦⡧⡨⡩⡪⡫⡬⡭⡮⡯"
    "⡰⡱⡲⡳⡴⡵⡶⡷⡸⡹⡺⡻⡼⡽⡾⡿"
    "⢀⢁⢂⢃⢄⢅⢆⢇⢈⢉⢊⢋⢌⢍⢎⢏"
    "⢐⢑⢒⢓⢔⢕⢖⢗⢘⢙⢚⢛⢜⢝⢞⢟"
    "⢠⢡⢢⢣⢤⢥⢦⢧⢨⢩⢪⢫⢬⢭⢮⢯"
    "⢰⢱⢲⢳⢴⢵⢶⢷⢸⢹⢺⢻⢼⢽⢾⢿"
    "⣀⣁⣂⣃⣄⣅⣆⣇⣈⣉⣊⣋⣌⣍⣎⣏"
    "⣐⣑⣒⣓⣔⣕⣖⣗⣘⣙⣚⣛⣜⣝⣞⣟"
    "⣠⣡⣢⣣⣤⣥⣦⣧⣨⣩⣪⣫⣬⣭⣮⣯"
    "⣰⣱⣲⣳⣴⣵⣶⣷⣸⣹⣺⣻⣼⣽⣾⣿"
)

BOX_DRAWING = "─│┌┐└┘├┤┬┴┼"
ARROWS      = "←→↑↓↔↕⇐⇒⇑⇓"
MATH        = "∑∏∫∂∆∇±×÷≤≥≠≈∞"

__all__ = [
    "BRAILLE", "BLOCK",
    "ASCII_RAMP", "EXTENDED_RAMP", "SHADE_RAMP", "DOTS_RAMP",
    "NUMBERS_RAMP", "HEX_RAMP", "MATRIX_RAMP", "STAR_RAMP",
    "BRAILLE_RAMP", "BOX_DRAWING", "ARROWS", "MATH",
]
