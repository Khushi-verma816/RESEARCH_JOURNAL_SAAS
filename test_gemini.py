from google import genai

client = genai.Client(api_key="AIzaSyCU-QzpyVi47gsIKdxjv4AmAmRR8B9zv3s")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say hello"
)

print("✅ SUCCESS!")
print(response.text)
