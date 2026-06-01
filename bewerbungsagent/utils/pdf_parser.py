import pymupdf as fitz  # PyMuPDF


def extrahiere_text(dateipfad):
    """Liest den Text aus einer PDF-Datei und gibt ihn als String zurück.

    Gibt leeren String zurück wenn die PDF nur Bilder enthält (kein Text).
    """
    try:
        doc = fitz.open(dateipfad)
    except FileNotFoundError:
        print(f"Datei nicht gefunden: {dateipfad}")
        return ""

    # Text aus allen Seiten sammeln
    text = ""
    for seite in doc:
        text += seite.get_text()

    doc.close()

    # Warnung wenn kein Text gefunden (z.B. Bild-PDF)
    if not text.strip():
        print("Warnung: Kein lesbarer Text in der PDF (möglicherweise Bild-PDF ohne OCR).")
        return ""

    return text
