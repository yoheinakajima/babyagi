#this is an example of how to use the babyagi framework in a custom flask app

from flask import Flask
import babyagi
from babyagi import register_function, load_functions

app = Flask(__name__)

# Use the babyagi blueprints
babyagi.use_blueprints(app, dashboard_route='/dashboard')

@register_function()
def integrated_function():
    return "Hello from integrated function!"

load_functions('plugins/firecrawl')

@app.route('/')
def home():
    return "Welcome to the main app. Visit /dashboard for BabyAGI dashboard."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
