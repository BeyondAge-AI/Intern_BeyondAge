from PyPDF2 import PdfReader

def pdf_to_text(pdf_path, output_txt_path):
    reader = PdfReader(pdf_path)
    
    with open(output_txt_path, "w", encoding="utf-8") as f:
        for page in reader.pages:
            text = page.extract_text()
            if text:
                f.write(text + "\n")

# Example usage
pdf_to_text("input.pdf", "output.txt")
