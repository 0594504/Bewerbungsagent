import fitz  # PyMuPDF


def extract_text_from_pdf(filepath):
    """Liest den Text aus einer PDF-Datei und gibt ihn als String zurück."""

    try:
        doc = fitz.open(filepath)
    except FileNotFoundError:
        print(f"Datei nicht gefunden: {filepath}")
        return None

    # Text aus allen Seiten zusammensammeln
    text = ""
    for seite in doc:
        text += seite.get_text()

    doc.close()

    # Prüfen ob überhaupt Text vorhanden ist
    if not text.strip():
        print("Kein lesbarer Text in der PDF gefunden. Möglicherweise ist es eine gescannte Datei.")
        return None

    return text