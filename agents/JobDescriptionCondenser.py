import json
from google import genai

class JobDescriptionCondenser:
    """
    Module for condensing job descriptions to extract only relevant information
    for resume tailoring.
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def condense(self, job_description):
        """
        Extract only the relevant parts of a job description that would affect
        resume adaptation.
        
        Args:
            job_description (str): The full job description
            
        Returns:
            str: Condensed job description with only relevant information
        """
        prompt = self._create_condensing_prompt(job_description)
        
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        return response.text.strip()
    
    def _create_condensing_prompt(self, job_description):
        """Create a prompt for condensing job descriptions"""
        prompt = f"""
        You are an expert resume tailoring assistant. Your task is to analyze a job description
        and extract ONLY the most relevant information that would affect how someone would tailor
        their resume for this position.
        
        Focus on extracting:
        1. Required skills, technologies, frameworks, and tools
        2. Required types of experience 
        3. Required knowledge domains or subject matter expertise
        4. Essential responsibilities and duties that indicate what skills to highlight
        5. Performance expectations or metrics that could guide achievements to highlight
        
        IGNORE:
        - Generic company information
        - Cultural fit statements that don't mention specific skills
        - Benefits, perks, and compensation details
        - Generic statements like "good communication skills" unless specifically technical
        - Application process details
        
        JOB DESCRIPTION:
        {job_description}
        
        Return ONLY the condensed essential information in a clear, organized format.
        Maintain the key technical terms, phrases about required experience, and specific knowledge domains.
        Use bullet points for easier readability.
        """
        return prompt