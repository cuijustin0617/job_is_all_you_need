import json
from google import genai

class BulletAdapter:
    """
    Module 2: Interactive Bullet Adaptation for tailoring resume to job descriptions
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def adapt_experience(self, experience_data, job_description):
        """
        Adapt a single work experience section based on the job description
        
        Args:
            experience_data (dict): Single work experience entry with title, company, and bullets
            job_description (str): The target job description
            
        Returns:
            dict: Adaptation suggestions organized by category (keep, adjust, add)
        """
        prompt = self._create_adaptation_prompt(experience_data, job_description)
        
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        return self._extract_adaptation_from_response(response.text)
    
    def adapt_all_experiences(self, resume_data, job_description):
        """
        Process all work experiences in the resume
        
        Args:
            resume_data (dict): Parsed resume data
            job_description (str): The target job description
            
        Returns:
            dict: All adaptation suggestions for each experience
        """
        adaptations = {}
        
        # Get the number of work experiences
        num_experiences = int(resume_data.get("number_of_work_experiences", 0))
        
        # Process each work experience
        for i in range(1, num_experiences + 1):
            exp_key = f"Work_Experience_{i}"
            if exp_key in resume_data:
                exp_data = resume_data[exp_key]  # Get the first (and only) item in the list
                adaptations[exp_key] = self.adapt_experience(exp_data, job_description)
        
        return adaptations
    
    def _create_adaptation_prompt(self, experience_data, job_description):
        """Create a detailed prompt for bullet point adaptation"""
        bullets = "\n".join([f"- {bullet}" for bullet in experience_data.get("bullets", [])])
        
        prompt = f"""
        You are an expert tech industry resume tailoring assistant. Your task is to analyze a work experience section 
        from a resume and provide suggestions for tailoring it to match a specific job description
        
        WORK EXPERIENCE:
        Title: {experience_data.get('title', '')}
        Company: {experience_data.get('company', '')}
        Duration: {experience_data.get('duration', '')}
        
        Current Bullet Points:
        {bullets}
        
        Condensed Job Description:
        {job_description}
        
        Based on this job description, analyze the bullet points and provide THREE categories of suggestions:
        
        1. TO KEEP: List bullet points that are already well-aligned with the job description and should be kept exactly as-is; or if the bullet point is not super relevant but nothing to change, keep it.
        2. TO ADJUST: For bullet points that could be improved, show both the original version and a tailored version that better highlights relevant skills/experience.
        3. TO ADD: Suggest 3-4 new bullet points that would greatly strengthen the resume for this specific job. These should be based on the role and mainly new job description.
        4. TITLE SUGGESTIONS: Suggest 2 job titles (either alternatives or original) that best align with the target job description. These should be reasonable based on the actual responsibilities in the experience, not fabricated roles.
        
        Return your analysis in the following JSON format ONLY:
        {{
            "to_keep": [
                "Bullet point 1 to keep unchanged",
                "Bullet point 2 to keep unchanged"
            ],
            "to_adjust": [
                {{
                    "original": "Original bullet point text 1",
                    "tailored": "Improved bullet point text 1"
                }},
                {{
                    "original": "Original bullet point text 2",
                    "tailored": "Improved bullet point text 2"
                }}
            ],
            "to_add": [
                "New suggested bullet point 1",
                "New suggested bullet point 2"
            ],
            "title_suggestions": [
                {{
                    "current": "{experience_data.get('title', '')}",
                    "suggested1": "Suggested title 1",
                    "suggested2": "Suggested title 2"
                }}
            ]
        }}

        Important:
        - ideally, structure each bullet as: [Strong Action Verb] + [Specific Technical Solution with Named Tools/Frameworks] + [Problem Solved] + [Quantifiable Impact with %]. Include precise technologies, demonstrate end-to-end ownership, and always quantify your impact through metrics (improved accuracy, reduced latency, cost savings).
        - Do not include any additional text or explanation in the JSON
        - the adjusted bullet points should be roughly same length
        - dont add vague phrases that sounds too generic 
        - dont add bullet points that are not relevant to the job description
        - dont blur out specific details in the original bullet points
        - bullets to add should follow ideal structure unless another point without the structure is more relevant to the job description
        
        Ensure each section has appropriate suggestions, but any section can be empty if not applicable.
        Focus on making the experience relevant without exaggerating skills or responsibilities too much.
        """
        return prompt
    
    def _extract_adaptation_from_response(self, response_text):
        """Extract JSON adaptation data from model response text"""
        import re
        import json
        
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
                    # Last attempt with more aggressive cleaning
                    try:
                        # Replace single quotes with double quotes for JSON compatibility
                        fixed_json = cleaned_json.replace("'", "\"")
                        return json.loads(fixed_json)
                    except:
                        # If JSON parsing fails, create a simplified response structure
                        print("Failed to parse JSON from response, creating simplified structure")
                        return {
                            "to_keep": [],
                            "to_adjust": [],
                            "to_add": [
                                "Please edit the model response format in BulletAdapter.py",
                                "The current response couldn't be parsed as valid JSON"
                            ],
                            "title_suggestions": []
                        }
        else:
            # If no JSON found, create a simplified error response
            return {
                "to_keep": [],
                "to_adjust": [],
                "to_add": [
                    "No JSON found in model response",
                    "Check API response format in BulletAdapter.py"
                ],
                "title_suggestions": []
            }

    def structure_selected_bullets(self, user_input, original_resume_data):
        """
        Convert free-form bullet point selections into structured resume format
        
        Args:
            user_input (str): Free-form text with bullet points for different positions
            original_resume_data (dict): Original parsed resume with company/position info
            
        Returns:
            dict: Structured resume data with updated bullets
        """
        # Create original experience information to help with matching
        original_experiences = []
        num_experiences = int(original_resume_data.get("number_of_work_experiences", 0))
        for i in range(1, num_experiences + 1):
            exp_key = f"Work Experience_{i}"
            if exp_key in original_resume_data:
                exp = original_resume_data[exp_key] 
                original_experiences.append({
                    "company": exp.get("company", ""),
                    "title": exp.get("title", ""),
                })
        
        # Create the prompt for the LLM
        prompt = f"""
        You are a resume formatting assistant. Your task is to convert a user's free-form bullet point selections
        into a structured JSON format that matches the original resume structure.
        
        ORIGINAL RESUME EXPERIENCE DATA:
        {json.dumps(original_experiences, indent=2)}
        
        USER'S SELECTED TITLE AND BULLET POINTS:
        {user_input}
        
        Based on the user's input, create a structured JSON that includes the company name, position title,
        and bullet points for each experience. Match each bullet point block to the appropriate original experience
        based on the company information.
        
        Return ONLY a valid JSON in the following format:
        {{
            "Work_Experience_1": 
                {{
                    "company": "Company Name",
                    "title": "Position Title",
                    "bullets": [
                        "Bullet point 1",
                        "Bullet point 2",
                        ...
                    ]
                }}
            "Work_Experience_2": 
                {{
                    "company": "Company Name",
                    "title": "Position Title",
                    "bullets": [
                        "Bullet point 1",
                        "Bullet point 2",
                        ...
                    ]
                }}
            ...
        }}
        
        Notes:
        - the bullets ordering should follow the most reasonable order for the work experience section
        - Use the same "Work_Experience_X" keys as in the original data
        - Match experiences based on company and title information
        - if original job title and User's selected title are different, the title should be the user's SELECTED title
        - Remove any bullet point markers (-, *, etc.) from the beginning of each bullet
        - Ensure all bullet points are properly formatted as strings in an array
        - Fix any obvious typos in the bullet points or weird error or special code
        """
        
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        # Extract and parse JSON from response
        return self._extract_json_from_response(response.text)
    
    def _extract_json_from_response(self, response_text):
        """Extract JSON from model response text and handle parsing errors"""
        import re
        import json
        
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
                    # Last attempt with more aggressive cleaning
                    try:
                        # Replace single quotes with double quotes for JSON compatibility
                        fixed_json = cleaned_json.replace("'", "\"")
                        return json.loads(fixed_json)
                    except:
                        print("Failed to parse JSON from response")
                        return {"error": "Failed to parse response into JSON format"}
        else:
            return {"error": "No JSON found in model response"}
