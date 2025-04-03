import unicodedata

def normalize_text(text):
    """
    Normalizuje vstupní text pro porovnání:
    - odstraní diakritiku
    - převede na malá písmena
    - odstraní mezery
    """
    text = text.strip().lower().replace(" ", "")
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    return text
