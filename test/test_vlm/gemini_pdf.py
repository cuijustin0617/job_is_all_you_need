import google.generativeai as genai
from dotenv import load_dotenv
import os
import PyPDF2

load_dotenv()

# Function to count pages in a PDF
def count_pdf_pages(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        return len(pdf_reader.pages)

# Path to the PDF resume
pdf_path = 'test/test_vlm/test_resume_1.pdf'

# Get the actual page count
page_count = count_pdf_pages(pdf_path)
print(f"Actual page count: {page_count}")

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create a model
model = genai.GenerativeModel('gemini-2.0-flash')

# Create content parts for the prompt and PDF
prompt = "Tell me whether this PDF resume is over or under a page and by how much. Be specific about the length and measure how much content exceeds a page or how much space is left if under a page."

# Read the PDF for analysis
with open(pdf_path, 'rb') as f:
    pdf_data = f.read()

# Generate a response from the model
response = model.generate_content([
    prompt,
    {"mime_type": "application/pdf", "data": pdf_data}
])

print("\nGemini's analysis:")
print(response.text)

# Compare with actual page count
if page_count > 1:
    print(f"\nConfirmation: Resume is {page_count} pages, which is {page_count-1} page(s) over the 1-page target.")
elif page_count == 1:
    print("\nConfirmation: Resume is exactly 1 page.")
else:
    print("\nError: Unable to determine page count correctly.")
