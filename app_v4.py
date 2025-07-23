import json
import os
import shutil
from agents_master.ResumeParser import LLMResumeParser
from agents_master.JobCondenser import JobCondenser
from agents_master.BlockRanker import BlockRanker
from agents_master.ResumeBuilder import ResumeBuilder
from agents_master.ResumeReformatter import ResumeReformatter

def main():
    api_key = "AIzaSyD3fnGbKojcbSYiD2eKJQvum0oF4N5iWlA"
    
    # Create and clean intermediate_dev folder for logging intermediate results
    intermediate_dir = "v4_intermediate_dev"
    if os.path.exists(intermediate_dir):
        shutil.rmtree(intermediate_dir)  # Clear existing directory
    os.makedirs(intermediate_dir, exist_ok=True)
    
    # Create results folder for final outputs
    results_dir = "v4_results"
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
    print("1. Parsing resume...")
    parser = LLMResumeParser(api_key=api_key)
    with open("resumes/master_resume.txt", "r") as file:
        latex_content = file.read()
    parse_result = parser.parse_latex(latex_content)
    parsed_resume = parse_result["result"]
    save_intermediate(parsed_resume, "1_parsed_resume.json")
    save_intermediate(parse_result["prompt"], "1_prompt_parse_resume.txt")
    
    # 2. Condense job
    print("2. Condensing job...")
    job_condenser = JobCondenser(api_key=api_key)
    with open("jobs/llm+rag.txt", "r") as file:
        job_description = file.read()
    condense_result = job_condenser.condense(job_description)
    job_requirements = condense_result["result"]
    save_intermediate(job_requirements, "2_job_requirements.json")
    save_intermediate(condense_result["prompt"], "2_prompt_condense_job.txt")
    
    # 3. Rank blocks
    print("3. Ranking blocks...")
    block_ranker = BlockRanker(api_key=api_key)
    ranking_result = block_ranker.rank_resume_blocks(parsed_resume, job_requirements)
    save_intermediate(ranking_result, "3_ranking_result.json")
    save_intermediate(ranking_result["prompt"], "3_prompt_rank_blocks.txt")
    
    # 4. Determine inclusion threshold
    print("4. Determining inclusion threshold...")
    threshold_result = block_ranker.determine_inclusion_threshold(ranking_result, parsed_resume)
    save_intermediate(threshold_result, "4_threshold_result.json")
    save_intermediate(threshold_result["threshold_prompt"], "4_prompt_determine_threshold.txt")
    
    # 5. Build resume and generate PDF using original template
    print("5. Building resume and generating PDF using original template...")
    resume_builder = ResumeBuilder(api_key=api_key)
    original_output_path = os.path.join(results_dir, "tailored_resume_original")
    latex_path, pdf_path = resume_builder.build_resume_pdf(
        parsed_resume, latex_content, threshold_result, original_output_path
    )
    
    # Save the original template and extracted latex prompt
    save_intermediate(latex_content, "5a_original_template.tex")
    
    # 6. Save the generated LaTeX and its prompt
    print("6. Saving the generated LaTeX...")
    with open(latex_path, "r") as file:
        generated_latex = file.read()
    save_intermediate(generated_latex, "5b_generated_resume_original.tex")
    
    # We need to re-run _generate_latex to get the prompt since build_resume_pdf doesn't return it
    filtered_resume = resume_builder._filter_resume_by_threshold(parsed_resume, threshold_result)
    generate_result = resume_builder._generate_latex(filtered_resume, latex_content, False)
    save_intermediate(generate_result["prompt"], "5_prompt_build_resume.txt")
    
    if pdf_path:
        print(f"Tailored resume generated: {latex_path} and PDF: {pdf_path}")
    else:
        print(f"Tailored resume generated: {latex_path} but PDF conversion failed.")
    
    # 7. Analyze the resume to ensure it fits on one page
    print("7. Analyzing the resume to ensure it fits on one page...")
    if pdf_path:
        reformatter = ResumeReformatter(api_key=api_key)
        
        # Get blocks just within the threshold and just below the threshold using enhanced_ranked_list
        threshold = threshold_result["threshold"]
        enhanced_ranked_list = threshold_result["enhanced_ranked_list"]
        
        # Get the last block within threshold (at the threshold position)
        last_block_within = None
        if threshold > 0 and threshold <= len(enhanced_ranked_list):
            # The block at the threshold position (index threshold-1 since ranks start at 1)
            last_block_info = enhanced_ranked_list[threshold-1]
            last_block_within = {
                "id": last_block_info["block_id"],
                "title": last_block_info["description"].split(": ", 1)[1] if ": " in last_block_info["description"] else last_block_info["description"],
                "type": last_block_info["type"]
            }
        
        # Get the first block outside threshold
        first_block_outside = None
        if threshold < len(enhanced_ranked_list):
            # The block just after the threshold (index threshold since ranks start at 1)
            first_block_info = enhanced_ranked_list[threshold]
            first_block_outside = {
                "id": first_block_info["block_id"],
                "title": first_block_info["description"].split(": ", 1)[1] if ": " in first_block_info["description"] else first_block_info["description"],
                "type": first_block_info["type"]
            }
        
        # Create lists for the reformatter
        blocks_within_threshold_tail = [last_block_within] if last_block_within else []
        blocks_below_threshold_head = [first_block_outside] if first_block_outside else []
        
        # 2. Get formatting recommendations
        print("8. Getting formatting recommendations...")
        recommendations = reformatter.reformat_resume(
            pdf_path, 
            generated_latex, 
            blocks_within_threshold_tail, 
            blocks_below_threshold_head
        )
        
        # Save the recommendations and vision prompt
        save_intermediate(recommendations, "6a_format_recommendations.json")
        save_intermediate(recommendations["vision_prompt"], "6_prompt_vision_analysis.txt")
        save_intermediate(f"NOTE: This prompt was used with {recommendations['num_images']} PDF images of the resume", "6_prompt_vision_analysis_note.txt")
        print("Resume formatting analysis completed")
        
        # 3. Regenerate the resume with the recommended changes
        print("9. Regenerating the resume with the recommended changes...")
        regenerate_result = reformatter.regenerate_resume(
            generated_latex,
            parsed_resume,
            recommendations
        )
        regenerated_latex = regenerate_result["latex"]
        
        # Save the regenerated LaTeX and its prompt
        save_intermediate(regenerated_latex, "6b_regenerated_resume.tex")
        save_intermediate(regenerate_result["regeneration_prompt"], "7_prompt_regenerate_resume.txt")
        
        # Generate PDF from the regenerated LaTeX
        regenerated_output_path = os.path.join(results_dir, "tailored_resume_regenerated")
        with open(f"{regenerated_output_path}.tex", "w") as file:
            file.write(regenerated_latex)
        
        # Convert to PDF using the ResumeBuilder's latex_to_pdf method
        regenerated_pdf_path = resume_builder.latex_to_pdf(
            regenerated_latex, 
            f"{regenerated_output_path}.pdf"
        )
        
        if regenerated_pdf_path:
            print(f"Regenerated resume created: {regenerated_output_path}.tex and PDF: {regenerated_pdf_path}")
        else:
            print(f"Regenerated resume created: {regenerated_output_path}.tex but PDF conversion failed.")
    
    # 8. Example with gold standard template (same as v3)
    try:
        # 1. Load the gold standard template
        with open("gold_standard_resumes/research_resume.txt", "r") as file:
            gold_template = file.read()
        save_intermediate(gold_template, "7a_gold_standard_template.tex")
            
        # 2. Build resume using the gold standard template
        print("9. Building resume using the gold standard template...")
        gold_output_path = os.path.join(results_dir, "tailored_resume_gold")
        gold_latex_path, gold_pdf_path = resume_builder.build_resume_pdf(
            parsed_resume, gold_template, threshold_result, 
            gold_output_path, use_gold_standard=True
        )
        
        # Save the generated gold standard LaTeX and its prompt
        with open(gold_latex_path, "r") as file:
            generated_gold_latex = file.read()
        save_intermediate(generated_gold_latex, "7b_generated_resume_gold.tex")
        
        # We need to re-run _generate_latex to get the prompt
        filtered_resume = resume_builder._filter_resume_by_threshold(parsed_resume, threshold_result)
        gold_generate_result = resume_builder._generate_latex(filtered_resume, gold_template, True)
        save_intermediate(gold_generate_result["prompt"], "8_prompt_build_gold_resume.txt")
        
        # 3. Analyze and reformat the gold standard resume
        print("10. Analyzing and reformatting the gold standard resume...")
        if gold_pdf_path:
            gold_recommendations = reformatter.reformat_resume(
                gold_pdf_path,
                generated_gold_latex,
                blocks_within_threshold_tail,
                blocks_below_threshold_head
            )
            
            # Save the recommendations and vision prompt
            save_intermediate(gold_recommendations, "8a_gold_format_recommendations.json")
            save_intermediate(gold_recommendations["vision_prompt"], "9_prompt_gold_vision_analysis.txt")
            save_intermediate(f"NOTE: This prompt was used with {gold_recommendations['num_images']} PDF images of the resume", "9_prompt_gold_vision_analysis_note.txt")
            print("Gold standard resume formatting analysis completed")
            
            # 4. Regenerate the gold standard resume with the recommended changes
            print("11. Regenerating the gold standard resume with the recommended changes...")
            gold_regenerate_result = reformatter.regenerate_resume(
                generated_gold_latex,
                parsed_resume,
                gold_recommendations
            )
            regenerated_gold_latex = gold_regenerate_result["latex"]
            
            # Save the regenerated gold LaTeX and its prompt
            save_intermediate(regenerated_gold_latex, "8b_regenerated_gold_resume.tex")
            save_intermediate(gold_regenerate_result["regeneration_prompt"], "10_prompt_regenerate_gold_resume.txt")
            
            # Generate PDF from the regenerated gold LaTeX
            regenerated_gold_output_path = os.path.join(results_dir, "tailored_resume_gold_regenerated")
            with open(f"{regenerated_gold_output_path}.tex", "w") as file:
                file.write(regenerated_gold_latex)
            
            # Convert to PDF
            regenerated_gold_pdf_path = resume_builder.latex_to_pdf(
                regenerated_gold_latex, 
                f"{regenerated_gold_output_path}.pdf"
            )
            
            if regenerated_gold_pdf_path:
                print(f"Regenerated gold resume created: {regenerated_gold_output_path}.tex and PDF: {regenerated_gold_pdf_path}")
            else:
                print(f"Regenerated gold resume created: {regenerated_gold_output_path}.tex but PDF conversion failed.")
        
        if gold_pdf_path:
            print(f"Gold standard resume generated: {gold_latex_path} and PDF: {gold_pdf_path}")
        else:
            print(f"Gold standard resume generated: {gold_latex_path} but PDF conversion failed.")
    except FileNotFoundError as e:
        print(f"Gold standard template not found: {e}. Using original template only.")
        save_intermediate(f"Error: {str(e)}", "7_gold_standard_error.txt")

if __name__ == "__main__":
    main() 