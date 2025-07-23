# Resume Tailor (Still in Progress)

An AI-powered tool that automatically tailors LaTeX resumes to specific job descriptions using LLMs.

## What it does

- Parses your master LaTeX resume into structured blocks
- Analyzes job descriptions to extract key requirements  
- Ranks and selects the most relevant resume content
- Generates a tailored one-page resume using gold standard templates
- Uses vision feedback to optimize formatting and layout

## Setup

1. Install dependencies:
```bash
pip install -r requirements_v5.txt
```

2. Get a Google AI API key from [Google AI Studio](https://aistudio.google.com/)

3. Install LaTeX (for PDF generation):
   - macOS: `brew install basictex`
   - Linux: `sudo apt-get install texlive`

## Usage

### Streamlit App (v5)
```bash
streamlit run app_v5.py
```

### Command Line (v3/v4)
```bash
python app_v3.py  # Basic version
python app_v4.py  # With visual feedback
```

## File Structure

- `resumes/` - Sample master resume templates
- `jobs/` - Sample job descriptions  
- `gold_standard_resumes/` - Professional resume templates
- `agents_master/` - Core LLM modules for parsing, ranking, building
- `v*_results/` - Generated outputs by version

## Requirements

- Python 3.8+
- Google AI API key
- LaTeX installation
- Streamlit (for web interface) 