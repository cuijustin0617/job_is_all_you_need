import json
from google import genai

class BlockRanker:
    """
    Module for ranking resume blocks based on relevance to a job description.
    Determines which blocks must be included and ranks the rest by priority.
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def rank_resume_blocks(self, parsed_resume, job_requirements):
        """
        Main function to filter and rank resume blocks.
        
        Args:
            parsed_resume (dict): The parsed resume from ResumeParser
            job_requirements (dict): Job requirements from JobCondenser
            
        Returns:
            dict: Dictionary with "must_include" and "ranked_list" keys
        """
        # Step 1: Filter blocks to be ranked
        filtered_blocks = self.filter_blocks(parsed_resume)
        
        # Step 2: Rank the filtered blocks
        ranking_result = self.rank_blocks(filtered_blocks, job_requirements)
        
        return ranking_result
    
    def filter_blocks(self, parsed_resume):
        """
        Filter resume blocks to exclude education, professional summary, and skills, contact information.
        
        Args:
            parsed_resume (dict): The parsed resume from ResumeParser
            
        Returns:
            dict: Dictionary containing only the blocks to be ranked
        """
        excluded_types = ["education", "professional summary", "skills", "contact information"]
        filtered_blocks = {}
        
        for block_id, block_data in parsed_resume.items():
            # Skip the "total_blocks" key and excluded block types
            if block_id == "total_blocks":
                continue
                
            if "block_type" in block_data and block_data["block_type"].lower() not in excluded_types:
                filtered_blocks[block_id] = block_data
                
        return filtered_blocks
    
    def rank_blocks(self, filtered_blocks, job_requirements):
        """
        Rank blocks based on relevance to job requirements.
        
        Args:
            filtered_blocks (dict): Resume blocks to be ranked
            job_requirements (dict): Job requirements from JobCondenser
            
        Returns:
            dict: Dictionary with "must_include" and "ranked_list" keys and prompt used
        """
        prompt = self._create_ranking_prompt(filtered_blocks, job_requirements)
        
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        # Extract the structured output
        result = self._parse_ranking_response(response.text)
        # Add the prompt to the result
        result["prompt"] = prompt
        return result
    
    def _create_ranking_prompt(self, filtered_blocks, job_requirements):
        """Create a prompt for ranking resume blocks"""
        prompt = f"""
        You are an expert resume tailoring assistant. Your task is to evaluate resume blocks
        against a job description and determine:
        
        1. Which blocks MUST be included in the resume (these are non-negotiable)
        2. Rank the remaining blocks in priority order (most important first)
        
        RESUME BLOCKS:
        {json.dumps(filtered_blocks, indent=2)}
        
        JOB REQUIREMENTS:
        {json.dumps(job_requirements, indent=2)}
        
        RANKING CRITERIA:
        - Work experience directly relevant to the job requirements should be prioritized highly and usually be in MUST INCLUDE
        - For research/R&D positions, relevant or prestigious publications should be in MUST INCLUDE
        - Projects are generally less important than work experience, but directly relevant projects can be prioritized
        - Don't consider bullet length at this stage - focus on relevance only
        
        Return your analysis in this JSON format:
        
        {{
          "must_include": [
            "block_1",
            "block_7"
          ],
          "ranked_list": [
            {{
              "block_id": "block_4",
              "rank": 1
            }},
            {{
              "block_id": "block_2",
              "rank": 2
            }}
          ]
        }}
        
        IMPORTANT NOTES:
        - The "must_include" list should contain block_ids that are essential, e.g. a resume cannot not have any work experience
        - The "ranked_list" should contain all remaining blocks ranked from most important (rank 1) to least important (rank n)
        - Ensure every block from the provided resume blocks appears exactly once (either in must_include or ranked_list)
        - Provide the output as valid JSON with no additional text or explanation
        """
        return prompt
    
    def _parse_ranking_response(self, response_text):
        """Parse the structured response from the model"""
        # Try to extract JSON from the response
        try:
            # First attempt direct JSON parsing
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(1).strip()
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    pass
            
            # If all parsing attempts fail, return error
            return {
                "error": "Failed to parse ranking response",
                "raw_response": response_text
            }

    def determine_inclusion_threshold(self, ranking_result, parsed_resume):
        """
        Determine a threshold cutoff for blocks to include in a one-page resume.
        
        Args:
            ranking_result (dict): Dict with "must_include" and "ranked_list" from rank_resume_blocks
            parsed_resume (dict): The parsed resume from ResumeParser
            
        Returns:
            dict: Enhanced ranking with threshold information and prompt used
        """
        # Enhance ranked list with descriptive information
        enhanced_ranked_list = []
        for item in ranking_result["ranked_list"]:
            block_id = item["block_id"]
            block_data = parsed_resume[block_id]
            
            # Extract description based on block type
            description = ""
            if block_data["block_type"].lower() == "work experience":
                description = f"Experience: {block_data.get('company', '')} - {block_data.get('title', '')}"
            elif block_data["block_type"].lower() == "project":
                description = f"Project: {block_data.get('title', '')}"
            elif block_data["block_type"].lower() == "publication":
                description = f"Publication: {block_data.get('title', '')}"
            else:
                description = f"{block_data['block_type']}: {block_data.get('name', '')}"
            
            enhanced_ranked_list.append({
                "block_id": block_id,
                "rank": item["rank"],
                "description": description,
                "type": block_data["block_type"].lower()
            })
        
        # Get must-include blocks with descriptions
        must_include_blocks = []
        for block_id in ranking_result["must_include"]:
            block_data = parsed_resume[block_id]
            
            # Extract description based on block type
            description = ""
            if block_data["block_type"].lower() == "experience":
                description = f"Experience: {block_data.get('company', '')} - {block_data.get('title', '')}"
            elif block_data["block_type"].lower() == "project":
                description = f"Project: {block_data.get('title', '')}"
            elif block_data["block_type"].lower() == "publication":
                description = f"Publication: {block_data.get('title', '')}"
            else:
                description = f"{block_data['block_type']}: {block_data.get('name', '')}"
            
            must_include_blocks.append({
                "block_id": block_id,
                "description": description,
                "type": block_data["block_type"].lower()
            })
        
        # Create prompt for threshold determination
        prompt = f"""
        You are a resume optimization expert. Your task is to determine which blocks to include in a one-page resume.
        
        MUST INCLUDE BLOCKS (non-negotiable):
        {json.dumps(must_include_blocks, indent=2)}
        
        RANKED BLOCKS (in order of importance):
        {json.dumps(enhanced_ranked_list, indent=2)}
        
        GUIDELINES:
        - A one-page resume typically has limited space
        - Experience sections usually take 6-8 lines each
        - Project sections usually take 3-4 lines each
        - Publication sections usually take 2-3 lines each
        - Education and skills sections (not in the ranked list) will also occupy space
        - The goal is to include as many relevant blocks as possible while keeping to one page
        
        Determine a rank threshold (1-{len(enhanced_ranked_list)}) from the ranked list. All blocks with rank less than or equal to this threshold should be included.
        
        Return ONLY the rank as a number, nothing else.
        """
        
        # Get the response
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        
        # Extract the threshold value
        try:
            threshold = int(response.text.strip())
        except ValueError:
            # If response isn't a clean integer, try to extract it
            import re
            match = re.search(r'\b(\d+)\b', response.text)
            if match:
                threshold = int(match.group(1))
            else:
                # Default threshold if extraction fails
                threshold = 2
        
        # Add threshold to the result
        enhanced_result = ranking_result.copy()
        enhanced_result["threshold"] = threshold
        enhanced_result["enhanced_ranked_list"] = enhanced_ranked_list
        enhanced_result["threshold_prompt"] = prompt
        
        return enhanced_result

