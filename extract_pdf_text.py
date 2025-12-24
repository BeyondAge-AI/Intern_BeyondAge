import PyPDF2
import sys

def extract_pdf_text(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page_text
            return text
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "pdfs/Lifestyle Questionnaire for Teenage Boys - Google Forms.pdf"
    text = extract_pdf_text(pdf_path)
    print(text)
    # Save to file for easier inspection
    with open("pdf_text_sample.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\n\nText saved to pdf_text_sample.txt")



