import json
import re
from google import genai

class JobCondenser:
    """
    Module for condensing job descriptions into structured categories
    for targeted resume tailoring.
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        """
        Initialize the JobCondenser.
        
        Args:
            model_name (str): Name of the Gemini model to use
            api_key (str): API key for Google AI
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def condense(self, job_description):
        """
        Extract and categorize relevant parts of a job description for resume adaptation.
        
        Args:
            job_description (str): The full job description
            
        Returns:
            dict: Structured dictionary with categorized job requirements
        """
        prompt = self._create_condensing_prompt(job_description)
        
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        response_text = response.text.strip()
        
        try:
            # First try direct JSON parsing
            result = json.loads(response_text)
            return {"result": result, "prompt": prompt}
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from markdown code blocks
            try:
                # Extract content between code fences if present
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
                if json_match:
                    json_str = json_match.group(1).strip()
                    result = json.loads(json_str)
                    return {"result": result, "prompt": prompt}
                else:
                    return {
                        "error": "Failed to parse structured output",
                        "raw_response": response_text
                    }
            except Exception as e:
                return {
                    "error": f"Failed to parse structured output: {str(e)}",
                    "raw_response": response_text
                }
    
    def _create_condensing_prompt(self, job_description):
        """Create a prompt for extracting structured information from job descriptions"""
        prompt = f"""
        You are an expert resume tailoring assistant. Your task is to analyze a job description
        and extract ONLY the most relevant information in a structured format that would help
        someone tailor their resume for this position.
        
        Extract and categorize information into these specific categories:
        [skills, experience, knowledge, responsibilities, qualifications]
        but dont force include any of these categories if the job description doesnt have relevant information
        
        IGNORE:
        - Generic company information
        - vague statements about soft skills like "strong communication skills" or "leadership experience"
        - Cultural fit statements that don't mention specific skills
        - Benefits, perks, and compensation details
        - Application process details
        
        JOB DESCRIPTION:
        {job_description}
        
        Return the condensed information as a JSON object with the categories above as keys.
        Each key should contain an array of concise, consistent bullet points. For example:
        
        {{
          "skills": ["Python", "SQL", "Pytorch", "Numpy", "Pandas", "Git", "Docker", "AWS", "CI/CD"],
          "experience": ["3+ years software development", "Experience with CI/CD pipelines"],
          "knowledge": ["Machine learning fundamentals", "Cloud architecture patterns"],
          "responsibilities": ["Design and develop web applications", "Optimize database queries"],
          "qualifications": ["Bachelor's in Computer Science or related field", "AWS certification"]
        }}
        
        IMPORTANT: Return ONLY the JSON with no additional text, markdown, or code blocks.
        """
        return prompt

if __name__ == "__main__":
    api_key = "AIzaSyD3fnGbKojcbSYiD2eKJQvum0oF4N5iWlA"
    job_condenser = JobCondenser(api_key=api_key)

    with open("llm+rag.txt", "r") as file:
        job_description = file.read()
    print(job_condenser.condense(job_description))
