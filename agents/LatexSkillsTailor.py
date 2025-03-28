import json
from google import genai

class LatexSkillsTailor:
    """
    Module for tailoring the skills section of a LaTeX resume based on job descriptions
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def tailor_skills_section(self, original_latex, condensed_job_description):
        """
        Generate an updated skills section based on the job description
        
        Args:
            original_latex (str): Original LaTeX resume content
            condensed_job_description (str): Condensed job description
            
        Returns:
            str: Updated LaTeX skills section only
        """
        prompt = self._create_skills_tailoring_prompt(original_latex, condensed_job_description)
        
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        return response.text.strip()
    
    def _create_skills_tailoring_prompt(self, original_latex, condensed_job_description):
        """Create a prompt for tailoring the skills section"""
        prompt = f"""
        You are an expert LaTeX resume editor. Your task is to update ONLY the skills section
        of a resume to better match a specific job description while preserving the LaTeX formatting.
        
        ORIGINAL LATEX RESUME:
        ```
        {original_latex}
        ```
        
        CONDENSED JOB DESCRIPTION:
        {condensed_job_description}
        
        Please generate ONLY the updated skills section in LaTeX format. The updated section should:
        
        1. Start with the \\section{{Skills}} tag (or equivalent if named differently in original)
        2. Maintain the original structure and LaTeX formatting/environments
        3. Prioritize skills mentioned in the job description by:
           - Reordering categories and skills to highlight the most relevant ones first
           - Making sure the most relevant skills appear at the beginning of their respective lists
           - Not removing any skills from the original resume
        4. Keep the same layout style (columns, spacing, bullet points style, etc.)
        
        IMPORTANT:
        - DO NOT include any other resume sections
        - DO NOT add skills not present in the original resume
        - DO NOT modify any LaTeX formatting commands
        - Output ONLY the skills section, starting with \\section{{Skills}} (or equivalent)
        - Return ONLY the LaTeX code with no additional text or explanation
        """
        return prompt