import os
import subprocess
import tempfile
import shutil
from pathlib import Path


def latex_to_pdf(latex_content: str, output_path: str = None) -> str:
    """
    Convert a string of LaTeX code to a PDF file.
    
    Args:
        latex_content: String containing valid LaTeX code
        output_path: Optional path where the PDF should be saved.
                    If not provided, a temporary file will be created.
    
    Returns:
        Path to the generated PDF file
    
    Raises:
        RuntimeError: If conversion fails
    """
    # Create a temporary directory to work in
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary tex file
        tex_file_path = os.path.join(temp_dir, "document.tex")
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        # Get the base filename without extension
        pdf_filename = "document.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        # Call pdflatex to convert LaTeX to PDF
        try:
            # Run pdflatex in the temp directory
            process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, tex_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"PDF conversion failed: {process.stderr}")
            
            # Check if PDF was created
            if not os.path.exists(pdf_path):
                raise RuntimeError("PDF file was not created")
            
            # Copy to output location if specified
            if output_path:
                # Create directory if it doesn't exist
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # Copy the file to the requested location
                shutil.copy(pdf_path, output_path)
                return output_path
            else:
                # If no output path specified, copy to current directory
                current_dir = os.getcwd()
                final_path = os.path.join(current_dir, pdf_filename)
                shutil.copy(pdf_path, final_path)
                return final_path
                
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Error running pdflatex: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to convert LaTeX to PDF: {str(e)}")


def save_latex_as_pdf(tex_file_path: str, dst_path: str) -> str:
    """
    Convert an existing .tex file to PDF.
    
    Args:
        tex_file_path: Path to the existing .tex file
        dst_path: Path where the PDF should be saved
    
    Returns:
        Path to the generated PDF file
    
    Raises:
        FileNotFoundError: If the tex file doesn't exist
        RuntimeError: If conversion fails
    """
    if not os.path.exists(tex_file_path):
        raise FileNotFoundError(f"TeX file {tex_file_path} does not exist")
    
    try:
        # Get the directory and filename
        tex_dir = os.path.dirname(tex_file_path)
        tex_filename = os.path.basename(tex_file_path)
        
        # Remember current directory
        prev_dir = os.getcwd()
        
        try:
            # Change to the directory of the tex file
            if tex_dir:
                os.chdir(tex_dir)
            
            # Run pdflatex
            process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"PDF conversion failed: {process.stderr}")
            
            # Get the PDF path (same name as tex file but .pdf extension)
            pdf_filename = os.path.splitext(tex_filename)[0] + ".pdf"
            pdf_path = os.path.join(tex_dir, pdf_filename) if tex_dir else pdf_filename
            
            # Check if PDF was created
            if not os.path.exists(pdf_path):
                raise RuntimeError("PDF file was not created")
            
            # Copy to destination if specified
            if dst_path:
                # Create directory if it doesn't exist
                dst_dir = os.path.dirname(dst_path)
                if dst_dir and not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                
                # Copy the file to the requested location
                shutil.copy(pdf_path, dst_path)
                return dst_path
            else:
                return pdf_path
            
        finally:
            # Always change back to the original directory
            os.chdir(prev_dir)
            
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Error running pdflatex: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to convert LaTeX to PDF: {str(e)}")


if __name__ == "__main__":
    # Example usage
    latex_content = r"""
    \documentclass{article}
    \begin{document}
    Hello, world!
    \end{document}
    """
    
    pdf_path = latex_to_pdf(latex_content, "output.pdf")
    print(f"PDF created at: {pdf_path}")
