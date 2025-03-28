import json
import re
from google import genai

class LLMResumeParser:
    """
    Module 1: Parse LaTeX resume into structured data
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def parse_latex(self, latex_content):
        """Parse LaTeX resume content into structured JSON"""
        prompt = self._create_parsing_prompt(latex_content)

        print("generating response...")
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        print("response generated")
        # Extract JSON from response
        return self._extract_json_from_response(response.text)
    
    def _create_parsing_prompt(self, latex_content):
        """Create a detailed prompt to extract resume information"""
        prompt = f"""
        Extract structured information from this LaTeX resume. 
        
        Parse it into the following sections:
        1. Work Experience: Extract company name, job title, location, time period, and bullet points for each role; a section for each work experience 
        2. Skills: Extract skill categories and lists of skills under each category, if there are no categories, just return a list of skills under category "Skills"
        
        Return ONLY a valid JSON object with this structure:
        {{"number_of_work_experiences": "number of work experiences in the resume",
            "Work_Experience_1": 
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "location": "Location",
                    "duration": "Start – End (in the same format as the input resume)",
                    "bullets": [
                        "Bullet point 1 (in plain text, NO bolding or formatting)",
                        "Bullet point 2 (in plain text, NO bolding or formatting)"
                    ]
                }},
            "Work_Experience_2": 
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "location": "Location",
                    "duration": "Start – End (in the same format as the input resume)",
                    "bullets": [
                        "Bullet point 1 (in plain text, NO bolding or formatting)",
                        "Bullet point 2 (in plain text, NO bolding or formatting)"
                    ]
                }},
            "Skills": {{
                "Category1": ["Skill1", "Skill2"],
                "Category2": ["Skill3", "Skill4"]
            }}
        }}
        Important:
        - Do not include any additional text or explanation in the JSON
        - return all the bullets in plain text, no bolding(should not include any "\\textbf" in latex) or formatting
        
        Here's the LaTeX resume:
        ```
        {latex_content}
        ```
        
        Return ONLY valid JSON with no additional text or explanation.
        """
        return prompt
    
    def _extract_json_from_response(self, response_text):
        """Extract JSON from model response text"""
        # Find JSON block in response
        match = re.search(r'({[\s\S]*})', response_text)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Clean up JSON string and try again
                cleaned_json = re.sub(r'```json|```', '', json_str).strip()
                try:
                    return json.loads(cleaned_json)
                except:
                    raise ValueError("Failed to parse JSON from response")
        else:
            raise ValueError("No JSON found in response")