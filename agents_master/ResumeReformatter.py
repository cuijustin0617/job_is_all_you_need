import os
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from pdf2image import convert_from_path
from google import genai
import PIL.Image

class ResumeReformatter:
    """
    Module for analyzing and reformatting a resume to ensure it fits on one page
    and has proper formatting using VLM (Vision Language Model) feedback.
    """
    def __init__(self, model_name="gemini-2.0-flash", api_key=None):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def reformat_resume(self, pdf_path, latex_content, blocks_within_threshold, blocks_below_threshold):
        """
        Analyze a resume PDF and provide formatting recommendations.
        
        Args:
            pdf_path (str): Path to the resume PDF file
            latex_content (str): Original LaTeX content of the resume
            blocks_within_threshold (list): Resume blocks ranked within the inclusion threshold
            blocks_below_threshold (list): Resume blocks ranked below the inclusion threshold
            
        Returns:
            dict: Formatting recommendations with prompt used
        """
        # Convert PDF to images
        image_paths = self.pdf_to_images(pdf_path)
        
        # Analyze the images with the VLM
        recommendations = self.analyze_with_vlm(image_paths, blocks_within_threshold, blocks_below_threshold)
        
        # Return the combined result
        return recommendations
    
    def regenerate_resume(self, latex_content, parsed_resume, recommendations):
        """
        Regenerate the LaTeX resume based on the formatting recommendations.
        
        Args:
            latex_content (str): The original LaTeX content of the resume
            parsed_resume (dict): The parsed resume structure
            recommendations (dict): The raw recommendations from the VLM
            
        Returns:
            dict: Updated LaTeX content with formatting changes applied and prompt used
        """
        # Create a prompt for the LLM to apply the changes to the LaTeX
        prompt = self._create_regeneration_prompt(latex_content, parsed_resume, recommendations)
        
        # Call Gemini to regenerate the LaTeX
        response = self.client.models.generate_content(
            model=self.model_name, 
            contents=prompt
        )
        
        # Extract the updated LaTeX code from the response
        regenerated_latex = self._extract_latex_from_response(response.text)
        return {
            "latex": regenerated_latex,
            "regeneration_prompt": prompt
        }
    
    def pdf_to_images(self, pdf_path):
        """
        Convert a PDF file to one or more images.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            list: Paths to the generated image files
        """
        # Create a temporary directory for the images
        tmp_dir = tempfile.mkdtemp()
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            # Save images to the temporary directory
            image_paths = []
            for i, image in enumerate(images):
                image_path = os.path.join(tmp_dir, f"resume_page_{i+1}.png")
                image.save(image_path, "PNG")
                image_paths.append(image_path)
            
            return image_paths
        
        except Exception as e:
            # Clean up the temporary directory on error
            shutil.rmtree(tmp_dir)
            raise RuntimeError(f"Failed to convert PDF to images: {str(e)}")
    
    def analyze_with_vlm(self, image_paths, blocks_within_threshold, blocks_below_threshold):
        """
        Analyze the resume images using Gemini vision model and provide formatting recommendations.
        
        Args:
            image_paths (list): Paths to the resume images
            blocks_within_threshold (list): Resume blocks ranked within the inclusion threshold
            blocks_below_threshold (list): Resume blocks ranked below the inclusion threshold
            
        Returns:
            dict: Raw formatting recommendations response with prompt used
        """
        # Load the images using PIL
        pil_images = [PIL.Image.open(path) for path in image_paths]
        
        # Prepare the prompt with context about the resume blocks
        prompt = self._create_formatting_prompt(len(image_paths), blocks_within_threshold, blocks_below_threshold)
        
        # Call Gemini with the prompt and images
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt] + pil_images
        )
        
        # Return the raw response with prompt
        return {
            "original_response": response.text,
            "vision_prompt": prompt,
            "num_images": len(image_paths)
        }
    
    def _create_formatting_prompt(self, num_pages, blocks_within_threshold, blocks_below_threshold):
        """
        Create a prompt for the VLM to analyze the resume formatting.
        
        Args:
            num_pages (int): Number of pages in the resume
            blocks_within_threshold (list): Resume blocks ranked within the inclusion threshold
            blocks_below_threshold (list): Resume blocks ranked below the inclusion threshold
            
        Returns:
            str: Prompt for the VLM
        """
        within_ids = [block["id"] for block in blocks_within_threshold[-2:]] if blocks_within_threshold else []
        below_ids = [block["id"] for block in blocks_below_threshold[:2]] if blocks_below_threshold else []
        
        prompt = f"""
        You are an expert resume formatting assistant. Analyze this {num_pages}-page resume and suggest minimal changes
        to make it fit exactly on one page while maintaining a professional appearance.

        CONTEXT:
        - This resume needs to be exactly one page.
        - The least important blocks that are still included in the resume have IDs: {within_ids}
        - The most important blocks that were excluded from the resume have IDs: {below_ids}
        
        PLEASE RECOMMEND:
        1. If the resume is too long:
           - Suggest removing the least important block(s) that are still included
           - Identify specific bullet points that could be removed
           - Suggest spacing adjustments between sections
           - Recommend slight font size reductions if appropriate (e.g., from 11pt to 10.5pt)
           - Suggest margin adjustments if needed
        
        2. If the resume is too short (significantly under one page):
           - Suggest adding the most important block(s) that were excluded
           - Suggest adding more spacing between sections
           - Recommend slightly larger font sizes if appropriate
           - Suggest increasing margins if needed
        
        3. If the resume has formatting issues:
           - Identify and suggest fixes for typos, misalignments, or formatting inconsistencies
           - Suggest minor font size or font style adjustments if needed
        
        Return a clear, structured list of at most 3-5 specific changes to make the resume perfect.
        IMPORTANT: Do NOT change the actual content information in the bullet points.
        """
        
        return prompt
        
    def _create_regeneration_prompt(self, latex_content, parsed_resume, recommendations):
        """
        Create a prompt for regenerating the LaTeX resume based on recommendations.
        
        Args:
            latex_content (str): The original LaTeX content
            parsed_resume (dict): The parsed resume structure
            recommendations (dict): The formatting recommendations
            
        Returns:
            str: Prompt for regenerating the LaTeX
        """
        # Get the original recommendations
        original_recommendations = recommendations.get("original_response", "")
        
        prompt = f"""
        You are an expert LaTeX resume editor. Your task is to modify the LaTeX code of a resume
        based on formatting recommendations to make it fit perfectly on one page.
        
        # Parsed Resume(in case you need to reference original content, but you shouldnt be adding information from this unless the recommendations say so):
        {parsed_resume}
        
        # FORMATTING RECOMMENDATIONS:
        {original_recommendations}
        
        # ORIGINAL LATEX CODE:
        ```
        {latex_content}
        ```
        
        # INSTRUCTIONS:
        1. Apply all the formatting recommendations to the LaTeX code.
        2. Focus on making the resume fit exactly on one page.
        3. DO NOT add any new content or information unless explicitly mentioned in the recommendations.
        4. DO NOT change the actual content information in the bullet points unless explicitly mentioned in the recommendations.
        5. Preserve the overall structure and style of the original LaTeX code unless the recommendations say otherwise.
        
        Return ONLY the modified LaTeX code without any explanations or markers.
        """
        
        return prompt
    
    def _extract_latex_from_response(self, response_text):
        """
        Extract LaTeX code from the LLM response.
        
        Args:
            response_text (str): The raw text response from the LLM
            
        Returns:
            str: Extracted LaTeX code
        """
        # Check if the response is enclosed in code blocks
        if "```" in response_text:
            # Extract content between code blocks
            parts = response_text.split("```")
            if len(parts) >= 3:
                # Return the content of the first code block
                return parts[1].strip()
        
        # If no code blocks, assume the entire response is LaTeX
        return response_text.strip()
    


