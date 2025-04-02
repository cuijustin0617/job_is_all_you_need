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
    initial_sidebar_state="collapsed",
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

# Redesigned function to parse adaptations into a more robust UI data format
def parse_adaptations_for_ui(adaptation_results):
    ui_data = {}
    
    # Handle the case where adaptation_results is None or empty
    if not adaptation_results:
        return ui_data
    
    try:
        for exp_key, adaptations in adaptation_results.items():
                # Skip if adaptations is not a dictionary
                if not isinstance(adaptations, dict):
                    continue
                    
                # Get experience data safely
                if exp_key in st.session_state.parsed_resume and isinstance(st.session_state.parsed_resume[exp_key], dict):
                    exp_data = st.session_state.parsed_resume[exp_key]
                    position_key = f"{exp_data.get('title', 'Position')} at {exp_data.get('company', 'Company')}"
                else:
                    position_key = f"Experience {exp_key}"
                
                # Initialize with empty lists to avoid None values
                ui_data[position_key] = {
                    "position": position_key,
                    "title_suggestions": [],
                    "to_keep": [],
                    "to_adjust": [],
                    "to_add": []
                }
                
                # Safely add title suggestions
                if "title_suggestions" in adaptations and isinstance(adaptations["title_suggestions"], list):
                    ui_data[position_key]["title_suggestions"] = adaptations["title_suggestions"]
                
                # Safely add bullets to keep
                if "to_keep" in adaptations and isinstance(adaptations["to_keep"], list):
                    ui_data[position_key]["to_keep"] = adaptations["to_keep"]
                
                # Safely add bullets to adjust
                if "to_adjust" in adaptations and isinstance(adaptations["to_adjust"], list):
                    ui_data[position_key]["to_adjust"] = adaptations["to_adjust"]
                
                # Safely add bullets to add
                if "to_add" in adaptations and isinstance(adaptations["to_add"], list):
                    ui_data[position_key]["to_add"] = adaptations["to_add"]
    except Exception as e:
        st.error(f"Error parsing adaptations: {str(e)}")
    
    return ui_data

# Redesigned function to convert UI data back to a string
def ui_data_to_string(ui_data):
    formatted_text = ""
    
    # Handle the case where ui_data is None or not a dictionary
    if not ui_data or not isinstance(ui_data, dict):
        return formatted_text
    
    try:
        for position_key, data in ui_data.items():
            # Skip if data is not a dictionary
            if not isinstance(data, dict):
                continue
                
            # Add position header
            formatted_text += f"Position: {position_key}\n\n"
            
            # Format title suggestions if available
            if "title_suggestions" in data and isinstance(data["title_suggestions"], list) and len(data["title_suggestions"]) > 0:
                title_sugg = data["title_suggestions"][0]
                if isinstance(title_sugg, dict):
                    formatted_text += "TITLES:\n"
                    
                    # Use the selected title if available, otherwise use the current title
                    selected_title = title_sugg.get('selected', title_sugg.get('current', ''))
                    formatted_text += f"- Selected: {selected_title}\n"
                    
                    # Include other titles for reference
                    formatted_text += f"# - Current: {title_sugg.get('current', '')}\n"
                    formatted_text += f"# - Suggested 1: {title_sugg.get('suggested1', '')}\n"
                    formatted_text += f"# - Suggested 2: {title_sugg.get('suggested2', '')}\n\n"
            
            # Format bullets to keep
            formatted_text += "TO KEEP:\n"
            if "to_keep" in data and isinstance(data["to_keep"], list) and data["to_keep"]:
                for bullet in data["to_keep"]:
                    if bullet:  # Ensure bullet is not empty
                        formatted_text += f"- {bullet}\n"
            else:
                formatted_text += "None\n"
            formatted_text += "\n"
            
            # Format bullets to adjust
            formatted_text += "TO ADJUST:\n"
            if "to_adjust" in data and isinstance(data["to_adjust"], list) and data["to_adjust"]:
                for adj in data["to_adjust"]:
                    if isinstance(adj, dict):
                        formatted_text += f"- Original: {adj.get('original', '')}\n"
                        formatted_text += f"- Tailored: {adj.get('tailored', '')}\n\n"
            else:
                formatted_text += "None\n"
            formatted_text += "\n"
            
            # Format bullets to add
            formatted_text += "TO ADD:\n"
            if "to_add" in data and isinstance(data["to_add"], list) and data["to_add"]:
                for bullet in data["to_add"]:
                    if bullet:  # Ensure bullet is not empty
                        formatted_text += f"- {bullet}\n"
            else:
                formatted_text += "None\n"
            
            formatted_text += "\n---\n\n"
    except Exception as e:
        st.error(f"Error formatting data: {str(e)}")
    
    return formatted_text

# Completely redesigned interactive adaptation editor
def interactive_adaptation_editor(adaptation_results):
    # Initialize empty result if no adaptations
    if not adaptation_results:
        st.warning("No adaptation results available.")
        return None
    
    # Create a fresh UI data structure if not already in session state
    if "ui_adaptations" not in st.session_state:
        st.session_state.ui_adaptations = parse_adaptations_for_ui(adaptation_results)
    
    # Create a deep copy of the data to work with
    if "working_adaptations" not in st.session_state:
        st.session_state.working_adaptations = {}
        for position_key, data in st.session_state.ui_adaptations.items():
            st.session_state.working_adaptations[position_key] = {
                "position": position_key,
                "title_suggestions": data.get("title_suggestions", []).copy() if isinstance(data.get("title_suggestions"), list) else [],
                "to_keep": data.get("to_keep", []).copy() if isinstance(data.get("to_keep"), list) else [],
                "to_adjust": data.get("to_adjust", []).copy() if isinstance(data.get("to_adjust"), list) else [],
                "to_add": data.get("to_add", []).copy() if isinstance(data.get("to_add"), list) else []
            }
    
    # Add CSS for the bubble UI with hover effects for editing
    st.markdown("""
    <style>
    .bubble-container {
        display: flex;
        flex-wrap: wrap;
        gap: 3px;
        margin-bottom: 8px;
    }
    .section-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #555;
        margin-bottom: 4px;
        margin-top: 10px;
        text-transform: uppercase;
    }
    .sub-label {
        font-size: 0.65rem;
        color: #777;
        margin-bottom: 2px;
        margin-top: 5px;
    }
    .bullet-bubble {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #f0f7ff;
        border-radius: 12px;
        padding: 4px 10px;
        margin-bottom: 3px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.08);
        transition: box-shadow 0.2s ease, background-color 0.2s ease;
    }
    .bullet-bubble:hover {
        box-shadow: 0 2px 5px rgba(0,0,0,0.12);
        background-color: #e6f2ff;
    }
    .bullet-text {
        flex-grow: 1;
        padding-right: 8px;
        font-size: 0.8rem;
        line-height: 1.2;
    }
    .delete-btn {
        color: #ff4b4b;
        background: none;
        border: none;
        cursor: pointer;
        font-weight: bold;
        font-size: 11px;
        opacity: 0.6;
        transition: opacity 0.2s ease;
        padding: 0 3px;
    }
    .delete-btn:hover {
        opacity: 1;
    }
    .position-header {
        background-color: #e7f5ff;
        padding: 6px 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #4361ee;
    }
    .position-header h4 {
        margin: 0;
        font-size: 0.95rem;
    }
    .original-bubble {
        background-color: #fff3e0;
    }
    .original-bubble:hover {
        background-color: #ffe0b2;
    }
    .tailored-bubble {
        background-color: #e8f5e9;
    }
    .tailored-bubble:hover {
        background-color: #c8e6c9;
    }
    .adjust-pair {
        border-left: 3px solid #7986cb;
        padding-left: 6px;
        margin-bottom: 8px;
        background-color: #f5f7ff;
        padding: 6px;
        border-radius: 5px;
    }
    .empty-state {
        font-style: italic;
        color: #888;
        padding: 3px 0;
        font-size: 0.75rem;
    }
    /* Floating job description section */
    .floating-job-container {
        position: sticky;
        top: 5rem;
        max-height: calc(100vh - 6rem);
        overflow-y: auto;
        padding-right: 1rem;
    }
    .add-buttons-container {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 10px;
    }
    .add-button {
        font-size: 0.7rem;
        padding: 3px 8px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        cursor: pointer;
    }
    .add-button:hover {
        background-color: #e9ecef;
    }
    .title-input {
        font-size: 0.75rem;
        padding: 2px 6px;
        height: 25px !important;
        min-height: 25px !important;
    }
    .stButton button {
        font-size: 0.7rem;
        padding: 2px 6px;
        height: auto !important;
    }
    .title-option {
        border: 1px solid #dee2e6;
        border-radius: 15px;
        padding: 3px 8px;
        margin: 0 3px;
        font-size: 0.7rem;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-block;
    }
    .title-option:hover {
        background-color: #e9ecef;
    }
    .title-option.selected {
        background-color: #cfe8ff;
        border-color: #4361ee;
        font-weight: bold;
    }
    /* Compact inputs */
    div.stTextInput > div {
        padding-bottom: 0px !important;
    }
    div.stTextInput > div > div > input {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        height: 30px !important;
        min-height: 30px !important;
        font-size: 0.8rem !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    /* Fix text wrapping for text inputs */
    .stTextInput textarea, .stTextInput input {
        white-space: normal !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        word-break: break-word !important;
    }
    .st-emotion-cache-q8sbsg p {
        white-space: normal !important;
        overflow-wrap: break-word !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize title selection in session state if not exists
    if "title_selections" not in st.session_state:
        st.session_state.title_selections = {}
    
    # Use a flag to track if any changes were made that require saving
    changes_made = False
    
    # Process each position in the working adaptations
    for position_key in list(st.session_state.working_adaptations.keys()):
        # Create a safe reference to the data
        data = st.session_state.working_adaptations[position_key]
        
        with st.expander(f"Position: {position_key}", expanded=True):
            st.markdown(f"<div class='position-header'><h4>{position_key}</h4></div>", unsafe_allow_html=True)
            
            # --- TITLE SUGGESTIONS ---
            if "title_suggestions" in data and isinstance(data["title_suggestions"], list) and len(data["title_suggestions"]) > 0:
                st.markdown("<div class='section-label'>Title Suggestions (Click to Select)</div>", unsafe_allow_html=True)
                
                # Get the title suggestion safely
                title_sugg = data["title_suggestions"][0] if isinstance(data["title_suggestions"][0], dict) else {"current": "", "suggested1": "", "suggested2": ""}
                
                # Check if there's already a selection for this position
                title_selection_key = f"title_selection_{position_key}"
                if title_selection_key not in st.session_state:
                    st.session_state[title_selection_key] = None
                
                # Create clickable title options
                title_options = [
                    {"label": "Current", "value": title_sugg.get('current', '')},
                    {"label": "Suggestion 1", "value": title_sugg.get('suggested1', '')},
                    {"label": "Suggestion 2", "value": title_sugg.get('suggested2', '')}
                ]
                
                # Display title options as clickable buttons
                cols = st.columns(3)
                for i, option in enumerate(title_options):
                    with cols[i]:
                        is_selected = st.session_state[title_selection_key] == option["value"]
                        button_label = f"{option['label']}: {option['value']}"
                        if st.button(
                            button_label, 
                            key=f"title_opt_{position_key}_{i}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"
                        ):
                            st.session_state[title_selection_key] = option["value"]
                            # Update the title suggestion in the data
                            title_sugg['selected'] = option["value"]
                            data["title_suggestions"][0] = title_sugg
                            changes_made = True
                            st.rerun()
                
                # Display the selected title
                if st.session_state[title_selection_key]:
                    st.success(f"Selected title: {st.session_state[title_selection_key]}")
                    # Store the selection in the data
                    title_sugg['selected'] = st.session_state[title_selection_key]
                    data["title_suggestions"][0] = title_sugg
                else:
                    st.info("Click on a title to select it for your resume")
            
            # --- TO KEEP SECTION ---
            if "to_keep" in data and isinstance(data["to_keep"], list):
                keep_bullets = data["to_keep"]
                if keep_bullets:
                    st.markdown("<div class='section-label'>To Keep</div>", unsafe_allow_html=True)
                    
                    # Track bullets to remove (can't modify list while iterating)
                    bullets_to_remove = []
                    bullets_to_update = {}
                    
                    # Display existing bullets as editable bubbles
                    for i, bullet in enumerate(keep_bullets):
                        # Skip if the bullet is None or not a string
                        if bullet is None or not isinstance(bullet, str):
                            bullets_to_remove.append(i)
                            continue
                            
                        col1, col2 = st.columns([20, 1])
                        with col1:
                            edited_bullet = st.text_input(
                                f"Keep bullet {i} for {position_key}",
                                value=bullet,
                                label_visibility="collapsed",
                                key=f"keep_{position_key}_{i}",
                                help=None
                            )
                            if edited_bullet != bullet:
                                bullets_to_update[i] = edited_bullet
                        
                        with col2:
                            if st.button("❌", key=f"del_keep_{position_key}_{i}", help=None):
                                bullets_to_remove.append(i)
                                changes_made = True
                    
                    # Process updates outside the loop
                    for i, value in bullets_to_update.items():
                        if i < len(keep_bullets):
                            keep_bullets[i] = value
                            changes_made = True
                    
                    # Remove bullets that were deleted
                    for i in sorted(bullets_to_remove, reverse=True):
                        if i < len(keep_bullets):
                            del keep_bullets[i]
                            changes_made = True
            
            # --- TO ADJUST SECTION ---
            if "to_adjust" in data and isinstance(data["to_adjust"], list):
                adjust_bullets = data["to_adjust"]
                if adjust_bullets:
                    st.markdown("<div class='section-label'>To Adjust</div>", unsafe_allow_html=True)
                    
                    # Track pairs to remove
                    pairs_to_remove = []
                    pairs_to_update = {}
                    
                    # Display existing adjustment pairs as editable bubbles
                    for i, adj in enumerate(adjust_bullets):
                        # Skip if the adjustment is not a dictionary
                        if not isinstance(adj, dict):
                            pairs_to_remove.append(i)
                            continue
                            
                        st.markdown(f"<div class='adjust-pair'>", unsafe_allow_html=True)
                        
                        # Original bullet
                        st.markdown("<div class='sub-label'>Original</div>", unsafe_allow_html=True)
                        col1, col2 = st.columns([20, 1])
                        with col1:
                            edited_original = st.text_input(
                                f"Original {i} for {position_key}",
                                value=adj.get("original", ""),
                                label_visibility="collapsed",
                                key=f"orig_{position_key}_{i}",
                                help=None
                            )
                        
                        with col2:
                            # When deleting original, keep the tailored version
                            if st.button("❌", key=f"del_orig_{position_key}_{i}", help=None):
                                # Get the tailored version
                                tailored_bullet = adj.get("tailored", "")
                                if tailored_bullet and "to_keep" in data:
                                    data["to_keep"].append(tailored_bullet)
                                pairs_to_remove.append(i)
                                changes_made = True
                        
                        # Tailored bullet
                        st.markdown("<div class='sub-label'>Tailored</div>", unsafe_allow_html=True)
                        col3, col4 = st.columns([20, 1])
                        with col3:
                            edited_tailored = st.text_input(
                                f"Tailored {i} for {position_key}",
                                value=adj.get("tailored", ""),
                                label_visibility="collapsed",
                                key=f"tail_{position_key}_{i}",
                                help=None
                            )
                        
                        with col4:
                            # When deleting tailored, keep the original version
                            if st.button("❌", key=f"del_tail_{position_key}_{i}", help=None):
                                # Get the original version
                                original_bullet = adj.get("original", "")
                                if original_bullet and "to_keep" in data:
                                    data["to_keep"].append(original_bullet)
                                pairs_to_remove.append(i)
                                changes_made = True
                        
                        # Capture edits for later processing
                        if edited_original != adj.get("original", "") or edited_tailored != adj.get("tailored", ""):
                            pairs_to_update[i] = {"original": edited_original, "tailored": edited_tailored}
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Process updates outside the loop
                    for i, value in pairs_to_update.items():
                        if i < len(adjust_bullets):
                            adjust_bullets[i] = value
                            changes_made = True
                    
                    # Remove pairs that were deleted
                    for i in sorted(pairs_to_remove, reverse=True):
                        if i < len(adjust_bullets):
                            del adjust_bullets[i]
                            changes_made = True
            
            # --- TO ADD SECTION ---
            if "to_add" in data and isinstance(data["to_add"], list):
                add_bullets = data["to_add"]
                if add_bullets:
                    st.markdown("<div class='section-label'>To Add</div>", unsafe_allow_html=True)
                    
                    # Track bullets to remove
                    bullets_to_remove = []
                    bullets_to_update = {}
                    
                    # Display existing bullets as editable bubbles
                    for i, bullet in enumerate(add_bullets):
                        # Skip if the bullet is None or not a string
                        if bullet is None or not isinstance(bullet, str):
                            bullets_to_remove.append(i)
                            continue
                            
                        col1, col2 = st.columns([20, 1])
                        with col1:
                            edited_bullet = st.text_input(
                                f"Add bullet {i} for {position_key}",
                                value=bullet,
                                label_visibility="collapsed",
                                key=f"add_{position_key}_{i}",
                                help=None
                            )
                            if edited_bullet != bullet:
                                bullets_to_update[i] = edited_bullet
                        
                        with col2:
                            if st.button("❌", key=f"del_add_{position_key}_{i}", help=None):
                                bullets_to_remove.append(i)
                                changes_made = True
                    
                    # Process updates outside the loop
                    for i, value in bullets_to_update.items():
                        if i < len(add_bullets):
                            add_bullets[i] = value
                            changes_made = True
                    
                    # Remove bullets that were deleted
                    for i in sorted(bullets_to_remove, reverse=True):
                        if i < len(add_bullets):
                            del add_bullets[i]
                            changes_made = True
            
            # Add buttons at the bottom to add new items to each section
            st.markdown("<div class='add-buttons-container'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("+ Add to keep", key=f"add_keep_btn_{position_key}", help=None):
                    # Initialize to_keep if it doesn't exist
                    if "to_keep" not in data:
                        data["to_keep"] = []
                    data["to_keep"].append("New bullet point")
                    changes_made = True
                    st.rerun()
            
            with col2:
                if st.button("+ Add adjustment", key=f"add_adj_btn_{position_key}", help=None):
                    # Initialize to_adjust if it doesn't exist
                    if "to_adjust" not in data:
                        data["to_adjust"] = []
                    data["to_adjust"].append({"original": "Original bullet", "tailored": "Tailored bullet"})
                    changes_made = True
                    st.rerun()
            
            with col3:
                if st.button("+ Add new bullet", key=f"add_new_btn_{position_key}", help=None):
                    # Initialize to_add if it doesn't exist
                    if "to_add" not in data:
                        data["to_add"] = []
                    data["to_add"].append("New bullet point")
                    changes_made = True
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Format the data for the agent
    return ui_data_to_string(st.session_state.working_adaptations)

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
    
    # Step 2: Update the adaptation editor section
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
        
        # Apply CSS for the floating job description container
        st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:nth-child(2) {
            position: sticky;
            top: 3rem;
            background-color: white;
            z-index: 999;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            max-height: calc(100vh - 6rem);
            overflow-y: auto;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with col1:
            st.subheader("Edit Adaptation Suggestions")
            
            # Use the interactive bubble editor instead of the text area
            selected_bullets = interactive_adaptation_editor(st.session_state.adaptation_results)
        
        with col2:
            st.markdown("<div class='floating-job-container'>", unsafe_allow_html=True)
            st.subheader("Job Requirements")
            
            # Apply styling for job description container
            st.markdown("""
            <style>
            .job-container {
                border: 1px solid #e6e6e6;
                border-radius: 5px;
                background-color: #f9f9f9;
                padding: 10px;
                margin-bottom: 10px;
                width: 100%;
                font-size: 0.9rem;
                line-height: 1.4;
            }
            .job-header {
                background-color: #f0f5ff;
                border-left: 5px solid #4361ee;
                padding: 8px 10px;
                border-radius: 5px;
                margin-bottom: 10px;
                color: #1e40af;
                font-size: 0.9rem;
            }
            .job-content {
                padding: 10px 15px;
                background-color: #f9f9f9;
                border-radius: 5px;
                margin-bottom: 10px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                font-size: 0.85rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Show condensed job description if available
            if hasattr(st.session_state, 'condensed_job_description') and st.session_state.condensed_job_description:
                # Replace newlines with <br> tags before using in the HTML
                formatted_job_description = st.session_state.condensed_job_description.replace('\n', '<br>')
                
                # Wrap the job description in the container
                st.markdown(f"""
                <div class="job-container">
                    <div class="job-header">
                        <h4 style="margin:0;font-size:0.95rem;">🎯 Key Requirements & Qualifications</h4>
                    </div>
                    <div class="job-content">
                        <p>{formatted_job_description}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("No condensed job description available. Please go back to Step 1.")
        
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Update the button for compiling selected bullets
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