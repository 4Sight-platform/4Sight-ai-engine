
class PixelWidthCalculator:
    """
    Calculates pixel width of text strings to simulate Google SERP truncation.
    Based on Arial font metrics (Title: ~18px, Desc: ~13px).
    """
    
    # Approximate widths for Arial 18px (Title)
    CHAR_WIDTHS_TITLE = {
        'a': 10, 'b': 11, 'c': 10, 'd': 11, 'e': 10, 'f': 6, 'g': 11, 'h': 11, 'i': 4, 'j': 4,
        'k': 10, 'l': 4, 'm': 16, 'n': 11, 'o': 11, 'p': 11, 'q': 11, 'r': 7, 's': 9, 't': 5,
        'u': 11, 'v': 10, 'w': 15, 'x': 10, 'y': 10, 'z': 9,
        'A': 12, 'B': 12, 'C': 13, 'D': 13, 'E': 12, 'F': 11, 'G': 13, 'H': 13, 'I': 5, 'J': 9,
        'K': 12, 'L': 10, 'M': 16, 'N': 13, 'O': 13, 'P': 12, 'Q': 13, 'R': 13, 'S': 12, 'T': 11,
        'U': 13, 'V': 12, 'W': 18, 'X': 12, 'Y': 12, 'Z': 11,
        '0': 11, '1': 11, '2': 11, '3': 11, '4': 11, '5': 11, '6': 11, '7': 11, '8': 11, '9': 11,
        ' ': 5, '.': 4, ',': 4, '-': 6, '|': 4
    }
    
    @staticmethod
    def get_pixel_width(text: str, is_title: bool = True) -> int:
        if not text:
            return 0
            
        width = 0
        scale = 1.0 if is_title else 0.75  # Description is smaller (~13.5px)
        
        for char in text:
            # Default to avg width (10) if unknown
            w = PixelWidthCalculator.CHAR_WIDTHS_TITLE.get(char, PixelWidthCalculator.CHAR_WIDTHS_TITLE.get(char.lower(), 10))
            width += w
            
        return int(width * scale)

    @staticmethod
    def check_truncation(text: str, limit_px: int, is_title: bool = True) -> dict:
        width = PixelWidthCalculator.get_pixel_width(text, is_title)
        is_truncated = width > limit_px
        return {
            "width": width,
            "limit": limit_px,
            "truncated": is_truncated,
            "status": "needs_attention" if is_truncated else "optimal",
            "message": f"{width}px / {limit_px}px"
        }
