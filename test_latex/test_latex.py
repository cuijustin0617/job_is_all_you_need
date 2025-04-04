import os
from latex import latex_to_pdf

def test_latex_conversion():
    # Create a simple LaTeX document
    latex_content = r"""
\documentclass{article}
\begin{document}
\title{Test Document}
\author{LaTeX Converter Test}
\maketitle

\section{Introduction}
This is a test document to verify the LaTeX to PDF conversion utility.

\section{Test Section}
If you can see this text in a PDF, the conversion worked successfully!

\end{document}
"""
    
    # Define output path
    output_path = "test_document.pdf"
    
    # Convert to PDF
    try:
        pdf_path = latex_to_pdf(latex_content, output_path)
        print(f"✅ Success! PDF created at: {pdf_path}")
        print(f"File exists: {os.path.exists(pdf_path)}")
        print(f"File size: {os.path.getsize(pdf_path)} bytes")
    except Exception as e:
        print(f"❌ Conversion failed: {str(e)}")

if __name__ == "__main__":
    test_latex_conversion() 