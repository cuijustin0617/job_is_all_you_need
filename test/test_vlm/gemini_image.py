from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import PIL.Image
load_dotenv()

image = PIL.Image.open('test/test_vlm/test_resume.png')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=["what are the top 3 things you would adjust in this resume?", image])

print(response.text)