import os
import pathlib
import requests
from google import genai
from google.genai import types
import PIL.Image
from dotenv import load_dotenv

load_dotenv()

# Set your API key from environment variable or replace with your actual key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # Set this in your environment

# Paths to resume images
image_path_1 = "test/test_vlm/resume1_page1.png"
image_path_2 = "test/test_vlm/resume1_page2.png"

# Load both images using PIL
pil_image_1 = PIL.Image.open(image_path_1)
pil_image_2 = PIL.Image.open(image_path_2)

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Create the prompt
prompt = "This is supposed to be a one-page resume. Please list the necessary safest way with minimal changesto make it exactly one page. Things you can do include 1.change the font slightly, 2.specify which bullet point to remove. 3. specify which section to remove. 4.  adjust spacing (add/remove) between sections   PLEASE just return a concise list of at most 3 things to change together that guarantees it will be one page.  "

# Generate content with both resume images
response = client.models.generate_content(
    model="gemini-2.0-flash",  # Using vision model to analyze images
    contents=[prompt, pil_image_1, pil_image_2]
)

# Print the response
print("\n=============== RESUME FORMATTING SUGGESTIONS ===============\n")
print(response.text)
print("\n============================================================\n")
