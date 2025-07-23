import json
import os
import shutil
import streamlit as st
from datetime import datetime
import pandas as pd
from PIL import Image
from google import genai
import time
import functools

# Import agents
from agents_master.ResumeParser import LLMResumeParser
from agents_master.JobCondenser import JobCondenser
from agents_master.BlockRanker import BlockRanker
from agents_master.ResumeBuilder import ResumeBuilder
from agents_master.ResumeReformatter import ResumeReformatter

# Retry decorator for LLM calls
def retry_on_error(max_retries=3, initial_delay=1):
    """
    Decorator that retries a function call if it raises an exception.
    
    Args:
        max_retries (int): Maximum number of retries
        initial_delay (int): Initial delay in seconds, doubled after each retry
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Wait before retrying
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                        st.warning(f"Error in {func.__name__}: {str(e)}. Retrying... (Attempt {attempt+1}/{max_retries})")
                    else:
                        st.error(f"Failed after {max_retries} retries: {str(e)}")
                        raise last_exception
        return wrapper
    return decorator

# Custom styling for a high-end, elegant UI
def setup_page():
    """Configure page settings and custom CSS"""
    st.set_page_config(
        page_title="Resume Tailor - Gold Standard",
        page_icon="📄",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for an elegant UI
    st.markdown("""
    <style>
    .main {
        padding: 2rem 3rem;
        max-width: 1000px;
    }
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 300;
        color: #1E3A8A;
    }
    h1 {
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 0.5rem;
    }
    h2 {
        font-size: 1.8rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stButton button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: none;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #2563EB;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    div.stProgress > div > div > div {
        background-color: #1E3A8A;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
    }
    .json-viewer {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        overflow-x: auto;
        border: 1px solid #eaeaea;
    }
    .success-box {
        background-color: #f0fff4;
        border-left: 4px solid #68d391;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #ebf8ff;
        border-left: 4px solid #63b3ed;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper functions
def create_output_directories():
    """Create and clean directories for storing intermediate results and outputs"""
    intermediate_dir = "v5_intermediate"
    results_dir = "v5_results"
    
    for directory in [intermediate_dir, results_dir]:
        if os.path.exists(directory):
            shutil.rmtree(directory)  # Clear existing directory
        os.makedirs(directory, exist_ok=True)
    
    return intermediate_dir, results_dir

def save_intermediate(data, filename, intermediate_dir):
    """Save intermediate result to file and return file path"""
    file_path = os.path.join(intermediate_dir, filename)
    with open(file_path, "w") as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, indent=2)
    return file_path

def display_json(data, expanded=True):
    """Display JSON data in a clean, formatted way"""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            st.text(data)
            return
    
    st.json(data, expanded=expanded)

def display_info_box(title, content):
    """Display information in a nicely formatted box"""
    st.markdown(f"""
    <div class="info-box">
        <strong>{title}</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)

def display_success_box(title, content):
    """Display success message in a nicely formatted box"""
    st.markdown(f"""
    <div class="success-box">
        <strong>{title}</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)

# Core processing functions
@retry_on_error(max_retries=3, initial_delay=1)
def parse_resume(api_key, resume_content, intermediate_dir):
    """Parse resume using LLMResumeParser agent"""
    parser = LLMResumeParser(api_key=api_key, model_name="gemini-2.5-flash-preview-04-17")
    parse_result = parser.parse_latex(resume_content)
    
    # Save intermediate results
    parsed_resume = parse_result["result"]
    save_intermediate(parsed_resume, "1_parsed_resume.json", intermediate_dir)
    save_intermediate(parse_result["prompt"], "1_prompt_parse_resume.txt", intermediate_dir)
    
    return parsed_resume, parse_result["prompt"]

@retry_on_error(max_retries=3, initial_delay=1)
def condense_job(api_key, job_description, intermediate_dir):
    """Condense job description using JobCondenser agent"""
    job_condenser = JobCondenser(api_key=api_key, model_name="gemini-2.5-flash-preview-04-17")
    condense_result = job_condenser.condense(job_description)
    
    # Save intermediate results
    job_requirements = condense_result["result"]
    save_intermediate(job_requirements, "2_job_requirements.json", intermediate_dir)
    save_intermediate(condense_result["prompt"], "2_prompt_condense_job.txt", intermediate_dir)
    
    return job_requirements, condense_result["prompt"]

@retry_on_error(max_retries=3, initial_delay=1)
def rank_resume_blocks(api_key, parsed_resume, job_requirements, intermediate_dir):
    """Rank resume blocks using BlockRanker agent"""
    block_ranker = BlockRanker(api_key=api_key, model_name="gemini-2.5-flash-preview-04-17")
    ranking_result = block_ranker.rank_resume_blocks(parsed_resume, job_requirements)
    
    # Save intermediate results
    save_intermediate(ranking_result, "3_ranking_result.json", intermediate_dir)
    save_intermediate(ranking_result["prompt"], "3_prompt_rank_blocks.txt", intermediate_dir)
    
    return ranking_result

@retry_on_error(max_retries=3, initial_delay=1)
def determine_threshold(api_key, ranking_result, parsed_resume, intermediate_dir):
    """Determine inclusion threshold using BlockRanker agent"""
    block_ranker = BlockRanker(api_key=api_key, model_name="gemini-2.5-flash-preview-04-17")
    threshold_result = block_ranker.determine_inclusion_threshold(ranking_result, parsed_resume)
    
    # Save intermediate results
    save_intermediate(threshold_result, "4_threshold_result.json", intermediate_dir)
    save_intermediate(threshold_result["threshold_prompt"], "4_prompt_determine_threshold.txt", intermediate_dir)
    
    return threshold_result

@retry_on_error(max_retries=3, initial_delay=1)
def build_gold_resume(api_key, parsed_resume, gold_template, threshold_result, 
                     output_path, intermediate_dir):
    """Build resume using gold standard template"""
    resume_builder = ResumeBuilder(api_key=api_key, model_name="gemini-2.5-flash-preview-04-17")
    
    # Save the gold standard template
    save_intermediate(gold_template, "5_gold_standard_template.tex", intermediate_dir)
    
    # Build resume using gold standard template
    gold_latex_path, gold_pdf_path = resume_builder.build_resume_pdf(
        parsed_resume, gold_template, threshold_result, 
        output_path, use_gold_standard=True
    )
    
    # Save the generated gold standard LaTeX
    with open(gold_latex_path, "r") as file:
        generated_gold_latex = file.read()
    save_intermediate(generated_gold_latex, "6_generated_resume_gold.tex", intermediate_dir)
    
    # Get the prompt used (need to re-run _generate_latex)
    filtered_resume = resume_builder._filter_resume_by_threshold(parsed_resume, threshold_result)
    gold_generate_result = resume_builder._generate_latex(filtered_resume, gold_template, True)
    save_intermediate(gold_generate_result["prompt"], "7_prompt_build_gold_resume.txt", intermediate_dir)
    
    return gold_latex_path, gold_pdf_path, generated_gold_latex, gold_generate_result["prompt"]

@retry_on_error(max_retries=3, initial_delay=1)
def analyze_and_reformat(api_key, gold_pdf_path, generated_gold_latex, threshold_result, 
                        parsed_resume, intermediate_dir, results_dir):
    """Analyze and reformat the resume for optimal presentation"""
    reformatter = ResumeReformatter(api_key=api_key, model_name="gemini-2.5-flash-preview-04-17")
    
    # Get blocks just within the threshold and just below the threshold
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
    
    # Get formatting recommendations
    gold_recommendations = reformatter.reformat_resume(
        gold_pdf_path,
        generated_gold_latex,
        blocks_within_threshold_tail,
        blocks_below_threshold_head
    )
    
    # Save the recommendations and vision prompt
    save_intermediate(gold_recommendations, "8_gold_format_recommendations.json", intermediate_dir)
    save_intermediate(gold_recommendations["vision_prompt"], "8_prompt_gold_vision_analysis.txt", intermediate_dir)
    save_intermediate(f"NOTE: This prompt was used with {gold_recommendations['num_images']} PDF images of the resume", 
                      "8_prompt_gold_vision_analysis_note.txt", intermediate_dir)
    
    # Regenerate the gold standard resume with the recommended changes
    gold_regenerate_result = reformatter.regenerate_resume(
        generated_gold_latex,
        parsed_resume,
        gold_recommendations
    )
    regenerated_gold_latex = gold_regenerate_result["latex"]
    
    # Save the regenerated gold LaTeX and its prompt
    save_intermediate(regenerated_gold_latex, "9_regenerated_gold_resume.tex", intermediate_dir)
    save_intermediate(gold_regenerate_result["regeneration_prompt"], "9_prompt_regenerate_gold_resume.txt", intermediate_dir)
    
    # Generate PDF from the regenerated gold LaTeX
    regenerated_gold_output_path = os.path.join(results_dir, "tailored_resume_gold_regenerated")
    with open(f"{regenerated_gold_output_path}.tex", "w") as file:
        file.write(regenerated_gold_latex)
    
    # Convert to PDF
    resume_builder = ResumeBuilder(api_key=api_key, model_name="gemini-2.5-flash-preview-04-17")
    regenerated_gold_pdf_path = resume_builder.latex_to_pdf(
        regenerated_gold_latex, 
        f"{regenerated_gold_output_path}.pdf"
    )
    
    return (regenerated_gold_output_path, regenerated_gold_pdf_path, 
            gold_recommendations, gold_regenerate_result["regeneration_prompt"])

# Main app
def main():
    # Set up the page
    setup_page()
    
    # App header
    st.title("Resume Tailor - Gold Standard")
    st.markdown("""
    Create a tailored resume focused on the most relevant experience for a specific job,
    using our gold standard template format for optimal presentation.
    """)
    
    # Add persistent progress bar at the top
    if 'progress_status' not in st.session_state:
        st.session_state.progress_status = 0
    
    top_progress_bar = st.progress(st.session_state.progress_status)
    
    # Create directories
    intermediate_dir, results_dir = create_output_directories()
    
    # API Key input
    api_key = st.text_input("Enter your Google API Key", type="password")
    if not api_key:
        st.warning("Please enter your Google API Key to proceed.")
        st.stop()
    
    # File upload section
    st.header("Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Master Resume (LaTeX)")
        resume_file = st.file_uploader("Upload your master resume LaTeX file", type=["txt", "tex"])
        if resume_file:
            resume_content = resume_file.read().decode("utf-8")
            st.success(f"Resume uploaded: {resume_file.name}")
        else:
            if st.checkbox("Use sample resume"):
                try:
                    with open("resumes/master_resume.txt", "r") as file:
                        resume_content = file.read()
                    st.success("Sample resume loaded")
                except FileNotFoundError:
                    st.error("Sample resume file not found")
                    resume_content = None
            else:
                resume_content = None
    
    with col2:
        st.subheader("Job Description")
        job_file = st.file_uploader("Upload job description text file", type=["txt"])
        if job_file:
            job_description = job_file.read().decode("utf-8")
            st.success(f"Job description uploaded: {job_file.name}")
        else:
            if st.checkbox("Use sample job description"):
                try:
                    with open("jobs/llm+rag.txt", "r") as file:
                        job_description = file.read()
                    st.success("Sample job description loaded")
                except FileNotFoundError:
                    st.error("Sample job description file not found")
                    job_description = None
            else:
                job_description = None
    
    # Gold standard template selection
    st.subheader("Gold Standard Template")
    
    try:
        template_files = [f for f in os.listdir("gold_standard_resumes") if f.endswith((".txt", ".tex"))]
        if template_files:
            selected_template = st.selectbox(
                "Select a gold standard template",
                template_files,
                index=0
            )
            with open(os.path.join("gold_standard_resumes", selected_template), "r") as file:
                gold_template = file.read()
            st.success(f"Template loaded: {selected_template}")
        else:
            st.warning("No gold standard templates found")
            gold_template = None
    except (FileNotFoundError, OSError):
        st.warning("Gold standard templates directory not found")
        gold_template = None
    
    # Process button
    process_btn = st.button("Generate Tailored Resume", disabled=not (resume_content and job_description and gold_template))
    
    if process_btn:
        # Reset progress bar for new process
        st.session_state.progress_status = 0
        top_progress_bar.progress(st.session_state.progress_status)
        
        # Create a session state to track progress
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
            
        with st.spinner("Processing your resume..."):
            # Create progress bar
            progress_bar = st.progress(0)
            
            # Set timestamp for output files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Parse Resume
            st.header("1. Resume Parsing")
            progress_bar.progress(10)
            # Update top progress bar
            st.session_state.progress_status = 0.10
            top_progress_bar.progress(st.session_state.progress_status)
            parsed_resume, parse_prompt = parse_resume(api_key, resume_content, intermediate_dir)
            
            with st.expander("View Parsed Resume Structure", expanded=False):
                display_json(parsed_resume)
                
            display_info_box("Parsing Complete", f"Successfully parsed {parsed_resume.get('total_blocks', 0)} resume blocks")
            
            # 2. Condense Job
            st.header("2. Job Description Analysis")
            progress_bar.progress(25)
            # Update top progress bar
            st.session_state.progress_status = 0.25
            top_progress_bar.progress(st.session_state.progress_status)
            job_requirements, condense_prompt = condense_job(api_key, job_description, intermediate_dir)
            
            with st.expander("View Job Requirements", expanded=True):
                display_json(job_requirements)
            
            # 3. Rank Resume Blocks
            st.header("3. Resume Block Ranking")
            progress_bar.progress(40)
            # Update top progress bar
            st.session_state.progress_status = 0.40
            top_progress_bar.progress(st.session_state.progress_status)
            ranking_result = rank_resume_blocks(api_key, parsed_resume, job_requirements, intermediate_dir)
            
            with st.expander("View Block Rankings", expanded=True):
                # Create a more readable table of rankings
                if "ranked_list" in ranking_result:
                    ranked_list = ranking_result["ranked_list"]
                    if ranked_list:
                        # Create enhanced ranked list with block details
                        enhanced_ranked = []
                        for item in ranked_list:
                            block_id = item["block_id"]
                            rank = item["rank"]
                            
                            # Get block details from parsed resume
                            block_data = parsed_resume.get(block_id, {})
                            
                            # Create description based on block type
                            description = ""
                            if block_data:
                                block_type = block_data.get("block_type", "").lower()
                                
                                if block_type == "work experience":
                                    title = block_data.get("title", "")
                                    company = block_data.get("company", "")
                                    description = f"{company} - {title}" if company and title else (company or title)
                                elif block_type == "project":
                                    description = block_data.get("title", "")
                                elif block_type == "publication":
                                    description = block_data.get("title", "")
                                else:
                                    description = block_data.get("name", "")
                            
                            enhanced_ranked.append({
                                "Rank": rank,
                                "Block ID": block_id,
                                "Type": block_data.get("block_type", "Unknown"),
                                "Description": description
                            })
                        
                        # Create DataFrame and display as table
                        df = pd.DataFrame(enhanced_ranked)
                        st.table(df)
                    else:
                        st.info("No ranked blocks available")
                else:
                    display_json(ranking_result)
            
            # 4. Determine Threshold
            st.header("4. Inclusion Threshold")
            progress_bar.progress(55)
            # Update top progress bar
            st.session_state.progress_status = 0.55
            top_progress_bar.progress(st.session_state.progress_status)
            threshold_result = determine_threshold(api_key, ranking_result, parsed_resume, intermediate_dir)
            
            threshold = threshold_result.get("threshold", 0)
            st.markdown(f"**Selected Threshold:** Include top {threshold} ranked blocks")
            
            with st.expander("View Threshold Analysis", expanded=False):
                display_json(threshold_result)
            
            # 5. Build Resume with Gold Standard
            st.header("5. Gold Standard Resume Generation")
            progress_bar.progress(70)
            # Update top progress bar
            st.session_state.progress_status = 0.70
            top_progress_bar.progress(st.session_state.progress_status)
            
            output_path = os.path.join(results_dir, f"tailored_resume_gold_{timestamp}")
            gold_latex_path, gold_pdf_path, generated_gold_latex, gold_prompt = build_gold_resume(
                api_key, parsed_resume, gold_template, threshold_result, 
                output_path, intermediate_dir
            )
            
            if gold_pdf_path:
                display_success_box("Initial Resume Created", f"Generated gold standard resume saved as {os.path.basename(gold_pdf_path)}")
            else:
                st.error("Gold standard resume PDF generation failed")
            
            # 6. Analyze and Reformat
            st.header("6. Resume Analysis & Optimization")
            progress_bar.progress(85)
            # Update top progress bar
            st.session_state.progress_status = 0.85
            top_progress_bar.progress(st.session_state.progress_status)
            
            if gold_pdf_path:
                result = analyze_and_reformat(
                    api_key, gold_pdf_path, generated_gold_latex, 
                    threshold_result, parsed_resume, 
                    intermediate_dir, results_dir
                )
                
                regenerated_gold_output_path, regenerated_gold_pdf_path, gold_recommendations, regeneration_prompt = result
                
                with st.expander("View Format Recommendations", expanded=False):
                    display_json(gold_recommendations)
                
                if regenerated_gold_pdf_path:
                    display_success_box(
                        "Final Resume Created", 
                        f"Optimized resume saved as {os.path.basename(regenerated_gold_pdf_path)}"
                    )
                else:
                    st.error("Final resume PDF generation failed")
            
            # Complete
            progress_bar.progress(100)
            # Update top progress bar
            st.session_state.progress_status = 1.0
            top_progress_bar.progress(st.session_state.progress_status)
            st.session_state.processing_complete = True
            
            # Display results section
            st.header("Tailored Resume")
            
            if st.session_state.processing_complete and regenerated_gold_pdf_path:
                st.markdown("### Your tailored resume is ready!")
                
                # Button to open PDF
                pdf_btn_col1, pdf_btn_col2 = st.columns([1, 1])
                
                with pdf_btn_col1:
                    with open(regenerated_gold_pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="Download Final Resume PDF",
                            data=pdf_file,
                            file_name=f"Tailored_Resume_{timestamp}.pdf",
                            mime="application/pdf"
                        )
                
                with pdf_btn_col2:
                    with open(f"{regenerated_gold_output_path}.tex", "rb") as tex_file:
                        st.download_button(
                            label="Download LaTeX Source",
                            data=tex_file,
                            file_name=f"Tailored_Resume_{timestamp}.tex",
                            mime="text/plain"
                        )
                
                # Display a preview if possible
                try:
                    import PyPDF2
                    from pdf2image import convert_from_path
                    
                    # Convert first page of PDF to image
                    images = convert_from_path(regenerated_gold_pdf_path, dpi=150, first_page=1, last_page=1)
                    if images:
                        st.image(images[0], caption="Resume Preview", use_column_width=True)
                except ImportError:
                    st.info("Install pdf2image package for PDF preview")
                except Exception as e:
                    st.warning(f"Could not generate preview: {str(e)}")

if __name__ == "__main__":
    main() 