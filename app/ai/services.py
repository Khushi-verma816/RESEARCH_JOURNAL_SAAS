import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("AIzaSyAyvv5CjKsNNmXqZ_dAIWRUxlbHtN1liRE"))

model = genai.GenerativeModel("gemini-pro")

def ask_ai(prompt):
    response = model.generate_content(prompt)
    return response.text
