def get_color_from_funkyfuture_palette(select_color: int = 0) -> tuple[int, int, int]:
    # LOSPEC: FUNKYFUTURE 8 PALETTE
    color = [
        (43, 15, 84),
        (171, 31, 101),
        (255, 79, 105),
        (255, 247, 248),
        (255, 129, 66),
        (255, 218, 69),
        (51, 104, 220),
        (73, 231, 236),
    ]
    if select_color >= len(color):
        return color[len(color) - 1]
    else:
        return color[select_color]

def get_color_from_sodacap_palette(select_color: int = 0) -> tuple[int, int, int]:
    # LOSPEC: SODA-CAP PALETTE
    color = [
        (33, 118, 204),
        (255, 125, 110),
        (252, 166, 172),
        (232, 231, 203),
    ]
    if select_color >= len(color):
        return color[len(color) - 1]
    else:
        return color[select_color]
    
def get_color_from_moonlightgb_palette(select_color: int = 0) -> tuple[int, int, int]:
    # LOSPEC: MOONLIGHT GB PALETTE
    color = [
        (15, 5, 45),
        (32, 54, 113),
        (54, 134, 143),
        (95, 199, 93),
    ]
    if select_color >= len(color):
        return color[len(color) - 1]
    else:
        return color[select_color]