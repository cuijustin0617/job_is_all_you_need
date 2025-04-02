import streamlit as st
import json
from google import genai

import os

# Import our agent classes
from agents.ResumeParser import LLMResumeParser
from agents.JobDescriptionCondenser import JobDescriptionCondenser
from agents.BulletAdapter import BulletAdapter
from agents.LatexExperienceTailor import LatexResumeTailor
from agents.LatexSkillsTailor import LatexSkillsTailor

# Set page config
st.set_page_config(
    page_title="Resume Tailor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Set up the API client function - moved before it's called
def setup_api_client(api_key):
    # Initialize all the agents directly with the API key
    # No need to set environment variables or use genai.configure()
    st.session_state.resume_parser = LLMResumeParser(api_key=api_key)
    st.session_state.job_condenser = JobDescriptionCondenser(api_key=api_key)
    st.session_state.bullet_adapter = BulletAdapter(api_key=api_key)
    st.session_state.latex_experience_tailor = LatexResumeTailor(api_key=api_key)
    st.session_state.skills_tailor = LatexSkillsTailor(api_key=api_key)
    st.success("API key set successfully!")
    st.session_state.api_key = api_key

# Function to initialize session state variables
def initialize_session_state():
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "api_key" not in st.session_state:
        # Set default API key for development
        st.session_state.api_key = "AIzaSyD3fnGbKojcbSYiD2eKJQvum0oF4N5iWlA"
    if "latex_resume" not in st.session_state:
        st.session_state.latex_resume = None
    if "parsed_resume" not in st.session_state:
        st.session_state.parsed_resume = None
    if "job_description" not in st.session_state:
        st.session_state.job_description = None
    if "condensed_job_description" not in st.session_state:
        st.session_state.condensed_job_description = None
    if "adaptation_results" not in st.session_state:
        st.session_state.adaptation_results = None
    if "structured_bullets" not in st.session_state:
        st.session_state.structured_bullets = None
    if "tailored_experience_latex" not in st.session_state:
        st.session_state.tailored_experience_latex = None
    if "tailored_skills_latex" not in st.session_state:
        st.session_state.tailored_skills_latex = None
    if "active_section" not in st.session_state:
        st.session_state.active_section = None

# Initialize session state
initialize_session_state()

# Set up the API client if not already set up
if st.session_state.api_key and not hasattr(st.session_state, 'resume_parser'):
    setup_api_client(st.session_state.api_key)

# Sidebar for navigation and API key
with st.sidebar:
    st.title("Resume Tailor")
    st.write("Adapt your resume to specific job descriptions")
    
    # API key input with default value shown
    api_key = st.text_input("Enter your Google AI API key:", 
                           value="•••••••••••••••••••••••••••••", 
                           type="password")
    if st.button("Set API Key") and api_key and api_key != "•••••••••••••••••••••••••••••":
        setup_api_client(api_key)
    
    # Navigation
    st.subheader("Navigation")
    st.write("Current step: ", st.session_state.step)
    
    # Step buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous Step") and st.session_state.step > 1:
            st.session_state.step -= 1
            st.rerun()
    with col2:
        if st.button("Next Step") and st.session_state.step < 5:
            st.session_state.step += 1
            st.rerun()

# Function to format adaptation results into text format with all details
def format_detailed_adaptations(adaptation_results):
    formatted_text = ""
    
    for exp_key, adaptations in adaptation_results.items():
        exp_data = st.session_state.parsed_resume[exp_key]
        
        # Add position header
        formatted_text += f"Position: {exp_data.get('title', '')} at {exp_data.get('company', '')}\n\n"
        
        # Display title suggestions if available
        if "title_suggestions" in adaptations and adaptations["title_suggestions"]:
            title_sugg = adaptations["title_suggestions"][0]
            formatted_text += "TITLES:\n"
            formatted_text += f"- Current: {title_sugg.get('current', '')}\n"
            formatted_text += f"- Suggested 1: {title_sugg.get('suggested1', '')}\n"
            formatted_text += f"- Suggested 2: {title_sugg.get('suggested2', '')}\n\n"
        
        # Display bullets to keep
        formatted_text += "TO KEEP:\n"
        if "to_keep" in adaptations and adaptations["to_keep"]:
            for bullet in adaptations["to_keep"]:
                formatted_text += f"- {bullet}\n"
        else:
            formatted_text += "None\n"
        formatted_text += "\n"
        
        # Display bullets to adjust
        formatted_text += "TO ADJUST:\n"
        if "to_adjust" in adaptations and adaptations["to_adjust"]:
            for adj in adaptations["to_adjust"]:
                formatted_text += f"- Original: {adj.get('original', '')}\n"
                formatted_text += f"- Tailored: {adj.get('tailored', '')}\n\n"
        else:
            formatted_text += "None\n"
        formatted_text += "\n"
        
        # Display bullets to add
        formatted_text += "TO ADD:\n"
        if "to_add" in adaptations and adaptations["to_add"]:
            for bullet in adaptations["to_add"]:
                formatted_text += f"- {bullet}\n"
        else:
            formatted_text += "None\n"
        
        formatted_text += "\n---\n\n"
    
    return formatted_text

# Function to display formatted bullet suggestions
def display_formatted_adaptation_results(adaptation_results):
    st.subheader("Adaptation Suggestions")
    for exp_key, adaptations in adaptation_results.items():
        exp_data = st.session_state.parsed_resume[exp_key]
        st.markdown(f"### Job: {exp_data.get('title')} at {exp_data.get('company')}")
        
        # Display title suggestions if available
        if "title_suggestions" in adaptations and adaptations["title_suggestions"]:
            title_sugg = adaptations["title_suggestions"][0]
            st.markdown("#### Titles:")
            st.markdown(f"- Current: {title_sugg.get('current', '')}")
            st.markdown(f"- Suggestion 1: {title_sugg.get('suggested1', '')}")
            st.markdown(f"- Suggestion 2: {title_sugg.get('suggested2', '')}")
        
        # Display bullets to keep
        if "to_keep" in adaptations and adaptations["to_keep"]:
            st.markdown("#### To Keep:")
            for bullet in adaptations["to_keep"]:
                st.markdown(f"- {bullet}")
        else:
            st.markdown("#### To Keep: None")
        
        # Display bullets to adjust
        if "to_adjust" in adaptations and adaptations["to_adjust"]:
            st.markdown("#### To Adjust:")
            for idx, adj in enumerate(adaptations["to_adjust"]):
                st.markdown(f"- Original: {adj.get('original', '')}")
                st.markdown(f"- Tailored: {adj.get('tailored', '')}")
                st.markdown("---")
        else:
            st.markdown("#### To Adjust: None")
        
        # Display bullets to add
        if "to_add" in adaptations and adaptations["to_add"]:
            st.markdown("#### To Add:")
            for bullet in adaptations["to_add"]:
                st.markdown(f"- {bullet}")
        else:
            st.markdown("#### To Add: None")
        
        st.markdown("---")
    
    # Add copy button for all adaptations
    formatted_text = format_detailed_adaptations(adaptation_results)
    
    # We'll use a container to place the button and instructions together
    copy_container = st.container()
    copy_container.markdown("### Copy All Suggestions for Next Step")
    copy_container.text_area("Copy this formatted text", formatted_text, height=150)
    copy_container.info("This formatted text contains all the suggested titles and bullet points organized for easy pasting into the next step.")

# Main content based on current step
if not hasattr(st.session_state, 'resume_parser'):
    with st.spinner("Setting up API connection..."):
        setup_api_client(st.session_state.api_key)
    st.success("API connection established with default key")

if st.session_state.api_key is None:
    st.warning("Please set your Google AI API key in the sidebar to continue.")
else:
    # Step 1: Remove the duplicate button and add keys to all buttons
    if st.session_state.step == 1:
        st.header("Step 1: Parse Resume & Condense Job Description")
        
        # Create two columns for inputs
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Your LaTeX Resume")
            resume_input = st.text_area(
                "Enter your LaTeX resume code:", 
                height=300,
                placeholder="Paste your LaTeX resume code here",
                key="resume_input"
            )
        
        with col2:
            st.subheader("Job Description")
            job_description_input = st.text_area(
                "Enter the job description:",
                height=300,
                placeholder="Paste the job description here",
                key="job_description_input"
            )
        
        # Center the Process button between columns
        st.markdown("""
            <style>
            div.stButton > button {
                display: block;
                margin: 0 auto;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Single process button with a unique key
        if st.button("Process Resume & Job Description", key="process_button"):
            if not resume_input or not job_description_input:
                st.error("Please provide both your LaTeX resume and the job description.")
            else:
                with st.spinner("Processing resume and job description..."):
                    try:
                        # Parse resume
                        st.session_state.latex_resume = resume_input
                        st.session_state.parsed_resume = st.session_state.resume_parser.parse_latex(resume_input)
                        
                        # Condense job description
                        st.session_state.job_description = job_description_input
                        st.session_state.condensed_job_description = st.session_state.job_condenser.condense(job_description_input)
                        
                        st.success("Resume parsed and job description condensed successfully!")
                        
                        # Initialize the active section if not exists
                        if "active_section" not in st.session_state:
                            # Default to first work experience if available
                            work_exp_keys = [k for k in st.session_state.parsed_resume.keys() if k.startswith("work_experience_")]
                            if work_exp_keys:
                                st.session_state.active_section = work_exp_keys[0]
                            elif "skills" in st.session_state.parsed_resume:
                                st.session_state.active_section = "skills"
                            else:
                                st.session_state.active_section = None  # No valid section found
                        else:
                            # Verify that the active section still exists in the current parsed resume
                            if st.session_state.active_section not in st.session_state.parsed_resume:
                                # If not, reset to a valid section
                                work_exp_keys = [k for k in st.session_state.parsed_resume.keys() if k.startswith("work_experience_")]
                                if work_exp_keys:
                                    st.session_state.active_section = work_exp_keys[0]
                                elif "skills" in st.session_state.parsed_resume:
                                    st.session_state.active_section = "skills"
                                else:
                                    st.session_state.active_section = None  # No valid section found
                        
                        # Display results after processing
                        if "parsed_resume" in st.session_state and st.session_state.parsed_resume and "condensed_job_description" in st.session_state and st.session_state.condensed_job_description:
                            # Display the results in two columns
                            result_col1, result_col2 = st.columns(2)
                            
                            with result_col1:
                                st.subheader("Parsed Resume Sections")
                                
                                # Create a scrollable container with fixed height for the resume sections
                                # Apply styling directly to the container with custom CSS
                                st.markdown("""
                                <style>
                                .scrollable-container {
                                    height: 500px;
                                    overflow-y: auto;
                                    padding: 15px;
                                    border: 1px solid #e6e6e6;
                                    border-radius: 5px;
                                    background-color: #f9f9f9;
                                    margin-bottom: 20px;
                                    width: 100%;
                                }
                                .section-header {
                                    background-color: #f0f0f0;
                                    padding: 8px;
                                    margin-top: 12px;
                                    margin-bottom: 8px;
                                    border-radius: 4px;
                                    border-left: 4px solid #4361ee;
                                }
                                .bullet-item {
                                    margin-bottom: 3px; /* Reduced line spacing */
                                }
                                .resume-content {
                                    padding: 5px;
                                    width: 100%;
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                # Extract all work experience sections
                                work_exp_keys = sorted([k for k in st.session_state.parsed_resume.keys() 
                                                      if k.startswith("work_experience_") or k.startswith("Work_Experience_")])
                                
                                # Create consolidated HTML content for all sections
                                html_content = '<div class="resume-content">'
                                
                                # Display all work experiences
                                for exp_key in work_exp_keys:
                                    section_data = st.session_state.parsed_resume[exp_key]
                                    company = section_data.get('company', 'Company')
                                    title = section_data.get('title', 'Position')
                                    
                                    html_content += f'<div class="section-header"><strong>{company} - {title}</strong></div>'
                                    
                                    if 'location' in section_data:
                                        html_content += f'<p><strong>Location:</strong> {section_data.get("location", "N/A")}</p>'
                                    if 'duration' in section_data:
                                        html_content += f'<p><strong>Duration:</strong> {section_data.get("duration", "N/A")}</p>'
                                    
                                    html_content += '<p><strong>Bullet Points:</strong></p>'
                                    if 'bullets' in section_data and section_data['bullets']:
                                        html_content += '<ul style="padding-left: 20px; margin-top: 5px;">'
                                        for bullet in section_data['bullets']:
                                            html_content += f'<li class="bullet-item">{bullet}</li>'
                                        html_content += '</ul>'
                                    else:
                                        html_content += '<p>No bullet points found.</p>'
                                    
                                    html_content += '<hr style="margin: 10px 0;">'
                                
                                # Display skills section if present
                                if "skills" or "Skills" in st.session_state.parsed_resume:
                                    if "skills" in st.session_state.parsed_resume:
                                        skills_data = st.session_state.parsed_resume["skills"]
                                    else:
                                        skills_data = st.session_state.parsed_resume["Skills"]
                                    html_content += '<div class="section-header"><strong>Skills</strong></div>'
                                    
                                    for category, skills in skills_data.items():
                                        html_content += f'<p><strong>{category}:</strong> {", ".join(skills)}</p>'
                                
                                # Close the content div
                                html_content += '</div>'
                                
                                # Wrap the entire content in a scrollable container
                                st.markdown(f'<div class="scrollable-container">{html_content}</div>', unsafe_allow_html=True)
                            
                            with result_col2:
                                st.subheader("Job Description Summary")
                                
                                # Update the styling for job description container
                                st.markdown("""
                                <style>
                                .job-container {
                                    height: 500px;
                                    overflow-y: auto;
                                    border: 1px solid #e6e6e6;
                                    border-radius: 5px;
                                    background-color: #f9f9f9;
                                    padding: 10px;
                                    margin-bottom: 20px;
                                    width: 100%;
                                }
                                .job-header {
                                    background-color: #f0f5ff;
                                    border-left: 5px solid #4361ee;
                                    padding: 10px;
                                    border-radius: 5px;
                                    margin-bottom: 10px;
                                    color: #1e40af;
                                }
                                .job-content {
                                    padding: 20px;
                                    background-color: #f9f9f9;
                                    border-radius: 5px;
                                    margin-bottom: 10px;
                                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                # Replace newlines with <br> tags before using in the HTML
                                formatted_job_description = st.session_state.condensed_job_description.replace('\n', '<br>')
                                
                                # Wrap the job description in the scrollable container
                                st.markdown(f"""
                                <div class="job-container">
                                    <div class="job-header">
                                        <h4>🎯 Job Requirements </h4>
                                    </div>
                                    <div class="job-content">
                                        <p>{formatted_job_description}</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Move the proceed button outside of the columns but still inside the try block
                        st.markdown("<div style='text-align: center; padding: 1rem;'>", unsafe_allow_html=True)
                        if st.button("Proceed to Bullet Adaptation", 
                                    on_click=lambda: setattr(st.session_state, 'step', 2),
                                    key="proceed_to_bullets_button"):
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"Error processing: {str(e)}")
    
    # Step 2: Add keys to buttons
    elif st.session_state.step == 2:
        st.header("Step 2: Adapt Resume Bullets")
        
        # Automatically generate adaptation results if they don't exist
        if "adaptation_results" not in st.session_state or not st.session_state.adaptation_results:
            with st.spinner("Generating adaptation suggestions..."):
                try:
                    st.session_state.adaptation_results = st.session_state.bullet_adapter.adapt_all_experiences(
                        st.session_state.parsed_resume, 
                        st.session_state.condensed_job_description
                    )
                except Exception as e:
                    st.error(f"Error generating adaptations: {str(e)}")
        
        # Create two columns layout
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("Edit Adaptation Suggestions")
            
            # Pre-populate the text area with adaptation results
            initial_text = format_detailed_adaptations(st.session_state.adaptation_results) if st.session_state.adaptation_results else ""
            
            # Text area for editing adaptations
            selected_bullets = st.text_area(
                "Review and edit the suggested bullet points:",
                value=initial_text,
                height=500,
                placeholder="Position: Software Engineer at Amazon\n\nTITLES:\n- Current: Software Engineer\n- Suggested 1: AWS Cloud Engineer\n\nTO KEEP:\n- Implemented CI/CD pipeline\n\nTO ADJUST:\n- Original: Developed backend APIs\n- Tailored: Developed RESTful APIs using AWS Lambda\n\nTO ADD:\n- Optimized AWS costs by 30%"
            )
        
        with col2:
            st.subheader("Job Description Summary")
            
            # Apply styling for job description container
            st.markdown("""
            <style>
            .job-container {
                height: 500px;
                overflow-y: auto;
                border: 1px solid #e6e6e6;
                border-radius: 5px;
                background-color: #f9f9f9;
                padding: 10px;
                margin-bottom: 20px;
                width: 100%;
            }
            .job-header {
                background-color: #f0f5ff;
                border-left: 5px solid #4361ee;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
                color: #1e40af;
            }
            .job-content {
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
                margin-bottom: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Show condensed job description if available
            if hasattr(st.session_state, 'condensed_job_description') and st.session_state.condensed_job_description:
                # Replace newlines with <br> tags before using in the HTML
                formatted_job_description = st.session_state.condensed_job_description.replace('\n', '<br>')
                
                # Wrap the job description in the scrollable container
                st.markdown(f"""
                <div class="job-container">
                    <div class="job-header">
                        <h4>🎯 Key Requirements & Qualifications</h4>
                    </div>
                    <div class="job-content">
                        <p>{formatted_job_description}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("No condensed job description available. Please go back to Step 1.")
        
        # Single button to compile selected bullets
        if st.button("Compile Selected Bullet Points", key="compile_bullets_button") and selected_bullets:
            with st.spinner("Processing selected bullets..."):
                try:
                    st.session_state.structured_bullets = st.session_state.bullet_adapter.structure_selected_bullets(
                        selected_bullets,
                        st.session_state.parsed_resume
                    )
                    
                    # Generate LaTeX for experience section
                    st.session_state.tailored_experience_latex = st.session_state.latex_experience_tailor.update_experience_section(
                        st.session_state.latex_resume,
                        st.session_state.structured_bullets
                    )
                    
                    # Generate skills section immediately
                    st.session_state.tailored_skills_latex = st.session_state.skills_tailor.tailor_skills_section(
                        st.session_state.latex_resume,
                        st.session_state.condensed_job_description
                    )
                    
                    # Move to step 3 automatically
                    st.session_state.step = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing bullets: {str(e)}")
    
    # Step 3: Display final results
    elif st.session_state.step == 3:
        st.header("Step 3: Final Tailored Sections")
        
        if st.session_state.tailored_experience_latex and st.session_state.tailored_skills_latex:
            tab1, tab2 = st.tabs(["Experience Section", "Skills Section"])
            
            with tab1:
                st.code(st.session_state.tailored_experience_latex, language="latex")
                st.download_button(
                    label="Download Experience Section",
                    data=st.session_state.tailored_experience_latex,
                    file_name="tailored_experience.tex",
                    mime="text/plain",
                    key="download_experience_button"
                )
            
            with tab2:
                st.code(st.session_state.tailored_skills_latex, language="latex")
                st.download_button(
                    label="Download Skills Section",
                    data=st.session_state.tailored_skills_latex,
                    file_name="tailored_skills.tex",
                    mime="text/plain",
                    key="download_skills_button"
                )
            
            # Option to download both sections
            combined_sections = f"{st.session_state.tailored_experience_latex}\n\n{st.session_state.tailored_skills_latex}"
            st.download_button(
                label="Download Both Sections",
                data=combined_sections,
                file_name="tailored_resume_sections.tex",
                mime="text/plain",
                key="download_combined_button"
            )
            
            st.success("Resume tailoring complete! You can now download the tailored sections and incorporate them into your resume.")
        else:
            st.error("No tailored sections available. Please go back and complete the previous steps.")