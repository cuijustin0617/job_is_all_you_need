import json
import os
import shutil
from agents_master.ResumeParser import LLMResumeParser
from agents_master.JobCondenser import JobCondenser
from agents_master.BlockRanker import BlockRanker
from agents_master.ResumeBuilder import ResumeBuilder

def main():
    api_key = "AIzaSyD3fnGbKojcbSYiD2eKJQvum0oF4N5iWlA"
    
    # Create and clean intermediate_dev folder for logging intermediate results
    intermediate_dir = "v3_intermediate_dev"
    if os.path.exists(intermediate_dir):
        shutil.rmtree(intermediate_dir)  # Clear existing directory
    os.makedirs(intermediate_dir, exist_ok=True)
    
    # Create results folder for final outputs
    results_dir = "v3_results"
    if os.path.exists(results_dir):
        shutil.rmtree(results_dir)  # Clear existing directory
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
    
    # 1. Parse resume
    parser = LLMResumeParser(api_key=api_key)
    with open("resumes/master_resume.txt", "r") as file:
        latex_content = file.read()
    parsed_resume = parser.parse_latex(latex_content)
    save_intermediate(parsed_resume, "1_parsed_resume.json")
    
    # 2. Condense job
    job_condenser = JobCondenser(api_key=api_key)
    with open("jobs/llm+rag.txt", "r") as file:
        job_description = file.read()
    job_requirements = job_condenser.condense(job_description)
    save_intermediate(job_requirements, "2_job_requirements.json")
    
    # 3. Rank blocks
    block_ranker = BlockRanker(api_key=api_key)
    ranking_result = block_ranker.rank_resume_blocks(parsed_resume, job_requirements)
    save_intermediate(ranking_result, "3_ranking_result.json")
    
    # 4. Determine inclusion threshold
    threshold_result = block_ranker.determine_inclusion_threshold(ranking_result, parsed_resume)
    save_intermediate(threshold_result, "4_threshold_result.json")
    
    # 5. Build resume and generate PDF using original template
    resume_builder = ResumeBuilder(api_key=api_key)
    original_output_path = os.path.join(results_dir, "tailored_resume_original")
    latex_path, pdf_path = resume_builder.build_resume_pdf(
        parsed_resume, latex_content, threshold_result, original_output_path
    )
    save_intermediate(latex_content, "5a_original_template.tex")
    
    # 6. Save the generated LaTeX
    with open(latex_path, "r") as file:
        generated_latex = file.read()
    save_intermediate(generated_latex, "5b_generated_resume_original.tex")
    
    if pdf_path:
        print(f"Tailored resume generated: {latex_path} and PDF: {pdf_path}")
    else:
        print(f"Tailored resume generated: {latex_path} but PDF conversion failed.")
    
    # 7. Example with gold standard template
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

if __name__ == "__main__":
    main() 