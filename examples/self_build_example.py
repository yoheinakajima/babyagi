import babyagi
import os

# Add OpenAI key to enable automated descriptions and embedding of functions.
babyagi.add_key_wrapper('openai_api_key',os.environ['OPENAI_API_KEY'])

# Load below function packs to play with experimental self-building functions
babyagi.load_functions("drafts/code_writing_functions")
babyagi.load_functions("drafts/self_build")


babyagi.self_build("A growth marketer at an enterprise SaaS company.")

@app.route('/')
def home():
    return f"Welcome to the main app. Visit <a href=\"/dashboard\">/dashboard</a> for BabyAGI dashboard."

if __name__ == "__main__":
    app = babyagi.create_app('/dashboard')
    app.run(host='0.0.0.0', port=8080)
