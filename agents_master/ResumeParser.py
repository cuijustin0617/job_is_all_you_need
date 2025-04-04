import json
import re
from google import genai

class LLMResumeParser:
    """
    Module 1: Parse LaTeX resume into structured data with sequential blocks
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def parse_latex(self, latex_content):
        """Parse LaTeX resume content into structured JSON with sequential blocks"""
        prompt = self._create_parsing_prompt(latex_content)

        print("generating response...")
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        print("response generated")
        # Extract JSON from response
        return self._extract_json_from_response(response.text)
    
    def _create_parsing_prompt(self, latex_content):
        """Create a detailed prompt to extract resume information into sequential blocks"""
        prompt = f"""
        Extract structured information from this LaTeX resume. 
        
        Parse it into sequential blocks where EACH INDIVIDUAL ITEM gets its own block:
        - EACH job/role should be a separate block
        - EACH project should be a separate block
        - EACH publication should be a separate block
        - Entire contact information section should be a single block
        - Entire Education section can be a single block
        - Entire Skills section can be a single block

        Each block MUST have a block_type key as one of the following:
        - "contact information" (for name, personal and contact information section)
        - "work experience" (for individual jobs/roles)
        - "skills" (for skills section)
        - "education" (for education section)
        - "publication" (for individual publications)
        - "project" (for individual projects)
        - "professional summary" (for professional summary section)
        - Or provide a custom name for items that don't fit the above categories
        
        Return ONLY a valid JSON object with this structure:
        {{
            "block_1": {{
                "block_type": "contact information",
                ... own structure that matches the original contact information entry
            }},
            "block_2": {{
                "block_type": "education",
                ... own structure that matches the original project entry
                // If multiple degrees, include a nested structure for each degree
            }},
            "block_3": {{
                "block_type": "work experience", 
                "title": "Job Title",
                "company": "Company Name",
                "location": "Location",
                "duration": "Start – End",
                "bullets": [
                    "Bullet point 1 (in plain text, NO bolding or formatting)",
                    "Bullet point 2 (in plain text, NO bolding or formatting)"
                ]
            }},
            "block_4": {{
                "block_type": "work experience",
                "title": "Different Job Title", 
                "company": "Different Company Name",
                "location": "Location",
                "duration": "Start – End",
                "bullets": [
                    "Bullet point 1 (in plain text, NO bolding or formatting)",
                    "Bullet point 2 (in plain text, NO bolding or formatting)"
                ]
            }},
            "block_5": {{
                "block_type": "skills",
                "Category1": ["Skill1", "Skill2"],
                "Category2": ["Skill3", "Skill4"]
                // If no categories, use "Skills" as the only category key
            }},
            "block_6": {{
                "block_type": "project",
                "title": "Project Title",
                ... own structure that matches the original first project entry
            }},
            "block_7": {{
                "block_type": "project",
                "title": "Project Title",
                ... own structure that matches the original second project entry
            }},
            "block_8": {{
                "block_type": "publication",
                "title": "Publication Title",
                ... own structure that matches the original first publication entry
            }},
            "block_9": {{
                "block_type": "publication",
                "title": "Publication Title",
                ... own structure that matches the original second publication entry
            }},
            "block_10": {{
                "block_type": "professional summary",
                ... own structure that matches the original professional summary entry
            }},
            "total_blocks": "number of blocks in the resume"
        }}
        Important:
        - EACH INDIVIDUAL job, INDIVIDUAL project, INDIVIDUAL publication, should have its own numbered block -- even if they are grouped together in one section in the resume
            - for example, any project with its own title, description, etc. should have its own block
            - for example, any publication with its own title, authors, conference, etc. should have its own block
        - Do not include any additional text or explanation in the JSON
        - Return all the bullets in plain text, no bolding (should not include any "\\textbf" in latex) or formatting
        - Do not extract personal contact information as a block
        - For blocks without specific structure, match the structure appropriately based on the content
        
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
        
if __name__ == "__main__":
    api_key = "AIzaSyD3fnGbKojcbSYiD2eKJQvum0oF4N5iWlA"
    parser = LLMResumeParser(api_key=api_key)

    with open("master_resume.txt", "r") as file:
        latex_content = file.read()
    print(parser.parse_latex(latex_content))
