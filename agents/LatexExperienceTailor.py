import re
import json
from google import genai

class LatexResumeTailor:
    """
    Module for updating only the experience section in a LaTeX resume
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def update_experience_section(self, original_latex, structured_bullets):
        """
        Update only the experience section of a LaTeX resume with selected bullets
        
        Args:
            original_latex (str): Original LaTeX resume content
            structured_bullets (dict): Structured bullet points data from structure_selected_bullets
            
        Returns:
            str: LaTeX code for the updated experience section only
        """
        prompt = self._create_experience_update_prompt(original_latex, structured_bullets)
        
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        return response.text.strip()
    
    def _create_experience_update_prompt(self, original_latex, structured_bullets):
        """Create a prompt for updating only the experience section"""
        prompt = f"""
        You are an expert LaTeX resume editor. Your task is to update ONLY the experience section
        of the original LaTeX resume with the new bullet points while preserving all LaTeX formatting.
        
        ORIGINAL LATEX RESUME:
        ```
        {original_latex}
        ```
        
        NEW BULLET POINTS (STRUCTURED):
        {json.dumps(structured_bullets, indent=2)}
        
        Please generate ONLY the updated experience section of the resume with the following changes:
        
        1. Start with the \\section{{Experience}} tag (or equivalent if differently named in original)
        2. Include all the formatting and structure from the original LaTeX for the experience section
        3. Replace ONLY the bullet points with the new ones from the structured data
        4. For each work experience, use the company and title from the structured data
        5. Preserve all LaTeX formatting, commands, and environments exactly as they appear in the original
        
        Important guidelines:
        - DO NOT include any other sections (skills, education, etc.)
        - DO NOT modify any formatting commands or environments
        - Output ONLY the experience section, starting with \\section{{Experience}} (or equivalent)
        - Maintain all original LaTeX syntax, spacing, and structure
        - Make sure all \\begin and \\end tags are properly paired
        - Return ONLY the LaTeX code with no additional text or explanation
        """
        return prompt