import json
import os
import subprocess
import requests
import base64
import tempfile
import shutil
from google import genai

class ResumeBuilder:
    """
    Module for building a one-page resume from filtered resume sections
    using either the original LaTeX template's formatting or a gold standard template.
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None, gold_standard_template=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.gold_standard_template = gold_standard_template
    
    def build_resume(self, parsed_resume, template, ranking_result, use_gold_standard=False):
        """
        Build a one-page resume from the parsed resume, using only blocks within the threshold.
        
        Args:
            parsed_resume (dict): The parsed resume from ResumeParser
            template (str): Either the original LaTeX code from the master resume 
                            or a gold standard template if use_gold_standard is True
            ranking_result (dict): Result from BlockRanker with threshold
            use_gold_standard (bool): Whether to use the gold standard template instead of original LaTeX
            
        Returns:
            str: LaTeX code for the one-page resume
        """
        # Filter the parsed resume based on the threshold
        filtered_resume = self._filter_resume_by_threshold(parsed_resume, ranking_result)
        
        # Generate new LaTeX code using the filtered resume and chosen template
        latex_code = self._generate_latex(filtered_resume, template, use_gold_standard)
        
        return latex_code
    
    def build_resume_pdf(self, parsed_resume, template, ranking_result, output_file="tailored_resume", use_gold_standard=False):
        """
        Build a one-page resume from the parsed resume and convert it to PDF.
        
        Args:
            parsed_resume (dict): The parsed resume from ResumeParser
            template (str): Either the original LaTeX code from the master resume 
                           or a gold standard template if use_gold_standard is True
            ranking_result (dict): Result from BlockRanker with threshold
            output_file (str): Base name for the output files (without extension)
            use_gold_standard (bool): Whether to use the gold standard template instead of original LaTeX
            
        Returns:
            tuple: (latex_path, pdf_path) paths to the generated LaTeX and PDF files
        """
        # Generate LaTeX code
        latex_code = self.build_resume(parsed_resume, template, ranking_result, use_gold_standard)
        
        # Save LaTeX to file
        latex_path = f"{output_file}.tex"
        with open(latex_path, "w") as file:
            file.write(latex_code)
        
        # Convert to PDF
        pdf_path = self.latex_to_pdf(latex_code, f"{output_file}.pdf")
        
        return latex_path, pdf_path
    
    def latex_to_pdf(self, latex_content: str, output_path: str = None) -> str:
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
                pdflatex_path = "/Library/TeX/texbin/pdflatex"  # Use full path for macOS with BasicTeX
                
                print(f"Running pdflatex from: {pdflatex_path}")
                print(f"Temp directory: {temp_dir}")
                print(f"TeX file: {tex_file_path}")
                
                # Check if pdflatex exists
                if not os.path.exists(pdflatex_path):
                    print(f"ERROR: pdflatex not found at {pdflatex_path}")
                    # Try finding it on the PATH
                    try:
                        alt_path = shutil.which("pdflatex")
                        if alt_path:
                            print(f"Found pdflatex at alternative path: {alt_path}")
                            pdflatex_path = alt_path
                        else:
                            print("pdflatex not found in PATH")
                    except Exception as e:
                        print(f"Error finding pdflatex: {e}")
                
                # Run pdflatex twice to resolve references
                for i in range(2):
                    process = subprocess.run(
                        [pdflatex_path, "-interaction=nonstopmode", "-output-directory", temp_dir, tex_file_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                    )
                    
                    if i == 1:  # Only print output on second run
                        print(f"pdflatex return code: {process.returncode}")
                        print(f"pdflatex stdout: {process.stdout[:200]}...")
                        
                        # Print error details if there was an error
                        if process.returncode != 0:
                            print(f"pdflatex stderr: {process.stderr}")
                            print(f"Full stdout: {process.stdout}")
                
                # List files in temp directory to see what was created
                print(f"Files in temp directory: {os.listdir(temp_dir)}")
                
                # Check if PDF was created, regardless of return code
                if os.path.exists(pdf_path):
                    print(f"PDF file was created with size: {os.path.getsize(pdf_path)} bytes")
                    
                    # Copy to output location if specified
                    if output_path:
                        # Create directory if it doesn't exist
                        output_dir = os.path.dirname(output_path)
                        if output_dir and not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        
                        # Copy the file to the requested location
                        shutil.copy(pdf_path, output_path)
                        print(f"Successfully generated PDF: {output_path}")
                        return output_path
                    else:
                        # If no output path specified, copy to current directory
                        current_dir = os.getcwd()
                        final_path = os.path.join(current_dir, pdf_filename)
                        shutil.copy(pdf_path, final_path)
                        print(f"Successfully generated PDF: {final_path}")
                        return final_path
                else:
                    print(f"PDF file was not created. Files in temp directory: {os.listdir(temp_dir)}")
                    # Try to read the log file for more information
                    log_path = os.path.join(temp_dir, "document.log")
                    if os.path.exists(log_path):
                        with open(log_path, 'r') as f:
                            log_content = f.read()
                            log_lines = log_content.split('\n')[-30:]
                            print(f"LaTeX log file (last 30 lines):")
                            for line in log_lines:
                                print(line)
                    
                    raise RuntimeError("PDF file was not created")
                    
            except subprocess.SubprocessError as e:
                print(f"Subprocess error: {e}")
                raise RuntimeError(f"Error running pdflatex: {str(e)}")
            except Exception as e:
                print(f"Exception: {type(e).__name__}: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                raise RuntimeError(f"Failed to convert LaTeX to PDF: {str(e)}")
    
    def _filter_resume_by_threshold(self, parsed_resume, ranking_result):
        """
        Filter the parsed resume to only include blocks that must be included
        and blocks within the threshold rank.
        
        Args:
            parsed_resume (dict): The parsed resume from ResumeParser
            ranking_result (dict): Result from BlockRanker with threshold
            
        Returns:
            dict: Filtered parsed resume
        """
        threshold = ranking_result.get("threshold", 2)
        must_include = set(ranking_result.get("must_include", []))
        
        # Find blocks to include based on threshold
        blocks_to_include = must_include.copy()
        
        # Add blocks from ranked list up to threshold
        for item in ranking_result.get("ranked_list", []):
            if item["rank"] <= threshold:
                blocks_to_include.add(item["block_id"])
        
        # Filter the parsed resume
        filtered_resume = {
            "total_blocks": len(blocks_to_include)
        }
        
        # Add blocks to the filtered resume
        for block_id, block_data in parsed_resume.items():
            if block_id == "total_blocks":
                continue
                
            if block_id in blocks_to_include:
                filtered_resume[block_id] = block_data
                
        # Add always-included sections like education and skills if they exist
        for block_id, block_data in parsed_resume.items():
            if block_id == "total_blocks":
                continue
                
            if "block_type" in block_data:
                block_type = block_data["block_type"].lower()
                if block_type in ["education", "skills", "professional summary"]:
                    filtered_resume[block_id] = block_data
        
        return filtered_resume
    
    def _generate_latex(self, filtered_resume, template, use_gold_standard=False):
        """
        Generate LaTeX code for the one-page resume using the filtered resume
        and the formatting from the chosen template.
        
        Args:
            filtered_resume (dict): Filtered parsed resume
            template (str): The template LaTeX code (either original or gold standard)
            use_gold_standard (bool): Whether the template is a gold standard template
            
        Returns:
            str: LaTeX code for the one-page resume
        """
        prompt = self._create_latex_prompt(filtered_resume, template, use_gold_standard)
        
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        # Extract the LaTeX code
        latex_code = self._extract_latex_code(response.text)
        return latex_code
    
    def _create_latex_prompt(self, filtered_resume, template, use_gold_standard=False):
        """
        Create a prompt for generating the LaTeX code.
        
        Args:
            filtered_resume (dict): Filtered parsed resume
            template (str): The template LaTeX code (either original or gold standard)
            use_gold_standard (bool): Whether the template is a gold standard template
            
        Returns:
            str: Prompt for the LLM
        """
        template_description = "gold standard" if use_gold_standard else "original"
        
        prompt = f"""
        You are an expert LaTeX resume builder. Your task is to generate a one-page resume using:
        
        1. The content from this parsed resume data:
        {json.dumps(filtered_resume, indent=2)}
        
        2. The formatting and style from this {template_description} LaTeX template:
        ```latex
        {template}
        ```
        
        INSTRUCTIONS:
        - Create a complete, compilable LaTeX document
        - Use ONLY the information included in the parsed resume data
        - IMPORTANT: Replace the placeholder contact information in the template with the actual contact information(name, location, email, phone, linkedin..) from parsed resume, while maintaining the same formatting style. the name is usually in the author field on latex template.
        - Maintain the exact same structure, formatting, fonts, margins, and style as the template
        - Include sections in the same order as the template
        - If a section type doesn't exist in the filtered data, skip it entirely
        - Make sure bullet points are properly formatted
        - Ensure the result is exactly one page (remove content if necessary)
        - Keep the exact same LaTeX packages and document class
        
        
        BULLET POINT SELECTION GUIDELINES:
        - For each experience section, select only the most relevant and impactful bullet points
        - The number of bullet points should match the importance and length of the experience, but also consider the remaining space on the page:
          * For primary/recent/important experiences: 4-8 bullet points
          * For secondary experiences: 3-5 bullet points
          * For minor/older experiences: 1-3 bullet points
        - For project sections: 2-4 bullet points maximum
        - For publication sections: typically just 1 entry 
        - When selecting bullet points, prioritize those that:
          * Demonstrate quantifiable achievements and results
          * Showcase relevant skills for the target position
          * Highlight leadership, initiative, and impact
          * Use strong action verbs
        - Preserve the original wording of selected bullet points
        - If a bullet point is too long, keep it intact rather than editing it
        
        Return ONLY the complete LaTeX code with no additional explanations or markdown.
        """
        return prompt
    
    def _extract_latex_code(self, response_text):
        """
        Extract the LaTeX code from the model's response.
        
        Args:
            response_text (str): Response from the LLM
            
        Returns:
            str: Extracted LaTeX code
        """
        # If the response is clean LaTeX, return it directly
        if response_text.strip().startswith("\\documentclass"):
            return response_text.strip()
        
        # Try to extract LaTeX from code blocks
        import re
        latex_match = re.search(r'```(?:latex)?\s*([\s\S]*?)\s*```', response_text)
        if latex_match:
            return latex_match.group(1).strip()
        
        # If no code block, look for document class and try to extract the LaTeX
        doc_match = re.search(r'(\\documentclass.*?\\end{document})', response_text, re.DOTALL)
        if doc_match:
            return doc_match.group(1).strip()
        
        # If all extraction attempts fail, return the raw response
        return response_text.strip()

    def set_gold_standard_template(self, template):
        """
        Set a gold standard LaTeX template to use for formatting.
        
        Args:
            template (str): The LaTeX code of the gold standard template
        """
        self.gold_standard_template = template


if __name__ == "__main__":
    api_key = "AIzaSyD3fnGbKojcbSYiD2eKJQvum0oF4N5iWlA"
    
    # Create and clean intermediate_dev folder for logging intermediate results
    intermediate_dir = "intermediate_dev"
    if os.path.exists(intermediate_dir):
        shutil.rmtree(intermediate_dir)  # Clear existing directory
    os.makedirs(intermediate_dir, exist_ok=True)
    
    # Create results folder for final outputs
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)
    
    def save_intermediate(data, filename):
        """Save intermediate result to file in intermediate_dev folder"""
        file_path = os.path.join(intermediate_dir, filename)
        with open(file_path, "w") as f:
            if isinstance(data, str):
                f.write(data)
            else:
                json.dump(data, f, indent=2)
        print(f"Saved intermediate result to {file_path}")
    
    # Example test
    from ResumeParser import LLMResumeParser
    from JobCondenser import JobCondenser
    from BlockRanker import BlockRanker
    
    # Parse resume
    parser = LLMResumeParser(api_key=api_key)
    with open("resumes/master_resume.txt", "r") as file:
        latex_content = file.read()
    parsed_resume = parser.parse_latex(latex_content)
    save_intermediate(parsed_resume, "1_parsed_resume.json")
    
    # Condense job
    job_condenser = JobCondenser(api_key=api_key)
    with open("jobs/llm+rag.txt", "r") as file:
        job_description = file.read()
    job_requirements = job_condenser.condense(job_description)
    save_intermediate(job_requirements, "2_job_requirements.json")
    
    # Rank blocks
    block_ranker = BlockRanker(api_key=api_key)
    ranking_result = block_ranker.rank_resume_blocks(parsed_resume, job_requirements)
    save_intermediate(ranking_result, "3_ranking_result.json")
    threshold_result = block_ranker.determine_inclusion_threshold(ranking_result, parsed_resume)
    save_intermediate(threshold_result, "4_threshold_result.json")
    
    # Build resume and generate PDF using original template
    resume_builder = ResumeBuilder(api_key=api_key)
    original_output_path = os.path.join(results_dir, "tailored_resume_original")
    latex_path, pdf_path = resume_builder.build_resume_pdf(
        parsed_resume, latex_content, threshold_result, original_output_path
    )
    save_intermediate(latex_content, "5a_original_template.tex")
    
    # Save the generated LaTeX
    with open(latex_path, "r") as file:
        generated_latex = file.read()
    save_intermediate(generated_latex, "5b_generated_resume_original.tex")
    
    if pdf_path:
        print(f"Tailored resume generated: {latex_path} and PDF: {pdf_path}")
    else:
        print(f"Tailored resume generated: {latex_path} but PDF conversion failed.")
    
    # Example with gold standard template
    try:
        # 1. Load the gold standard template
        with open("gold_standard_resumes/research_resume.txt", "r") as file:
            gold_template = file.read()
        save_intermediate(gold_template, "6a_gold_standard_template.tex")
            
        # 2. Build resume using the gold standard template
        gold_output_path = os.path.join(results_dir, "tailored_resume_gold")
        gold_latex_path, gold_pdf_path = resume_builder.build_resume_pdf(
            parsed_resume, gold_template, threshold_result, 
            gold_output_path, use_gold_standard=True
        )
        
        # Save the generated gold standard LaTeX
        with open(gold_latex_path, "r") as file:
            generated_gold_latex = file.read()
        save_intermediate(generated_gold_latex, "6b_generated_resume_gold.tex")
        
        if gold_pdf_path:
            print(f"Gold standard resume generated: {gold_latex_path} and PDF: {gold_pdf_path}")
        else:
            print(f"Gold standard resume generated: {gold_latex_path} but PDF conversion failed.")
    except FileNotFoundError as e:
        print(f"Gold standard template not found: {e}. Using original template only.")
        save_intermediate(f"Error: {str(e)}", "6_gold_standard_error.txt")
