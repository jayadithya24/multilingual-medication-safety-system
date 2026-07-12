import easyocr

reader = easyocr.Reader(['en'])

def extract_text(file_path):
    result = reader.readtext(file_path)

    detected_text = [item[1] for item in result]

    medicine_name = "Medicine Not Found"

    for text in detected_text:
        if "dolo" in text.lower():
            medicine_name = text
            break

    return {
        "medicine": medicine_name,
        "all_text": detected_text
    }