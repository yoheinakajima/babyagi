from skills.skill import Skill
import openai
import json

class StartupAnalysis(Skill):
  name = 'startup_analysis'
  description = "A tool specialized in providing a detailed analysis of startups using OpenAI's text completion API. Analyzes parameters like customers, ICP, pain points, competitors, etc."
  api_keys_required = ['openai']

  def __init__(self, api_keys, main_loop_function):
    super().__init__(api_keys, main_loop_function)

  def execute(self, params, dependent_task_outputs, objective):
    if not self.valid:
      return

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a great AI analyst specialized in writing VC investment memos. Write one paragraph each in the third person on customers, ICP, pain points, alternate solutions, competitors, potential partners, key incumbents, history of innovation in the industry, key risks, legal considerations, important figures or influencers, and other recent trends in the space. The user will provide the startup description."
            },
            {
                "role": "user",
                "content": params
                # User provides a detailed description of their startup
            }
        ],
        functions=[
            {
                "name": "analyze_startup",
                "description": "Analyze the startup based on various parameters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customers": {
                            "type": "string",
                            "description": "Who are the startup's primary customers. Describe in detail in the third person."
                        },
                        "ICP": {
                            "type": "string",
                            "description": "What is the startup's Ideal Customer Profile. Describe in detail in the third person."
                        },
                        "pain_points": {
                            "type": "string",
                            "description": "What are the pain points the startup is trying to solve. Describe in detail in the third person."
                        },
                        "alternate_solutions": {
                            "type": "string",
                            "description": "What are the alternate solutions available in the market. Describe in detail in the third person."
                        },
                        "competitors": {
                            "type": "string",
                            "description": "Who are the startup's main competitors. Describe in detail in the third person."
                        },
                        "potential_partners": {
                            "type": "string",
                            "description": "Who could be the startup's potential partners. Describe in detail in the third person."
                        },
                        "key_incumbents": {
                            "type": "string",
                            "description": "Key incumbents in the industry. Describe in detail."
                        },
                        "history_of_innovation": {
                            "type": "string",
                            "description": "History of innovation in the startup's industry. Describe in detail in the third person."
                        },
                        "key_risks": {
                            "type": "string",
                            "description": "What are the key risks involved in the startup. Describe in detail in the third person."
                        },
                        "legal_considerations": {
                            "type": "string",
                            "description": "Any legal considerations that the startup should be aware of"
                        },
                        "important_figures": {
                            "type": "string",
                            "description": "Important figures or influencers in the industry. Describe in detail in the third person."
                        },
                        "recent_trends": {
                            "type": "string",
                            "description": "What are the recent trends in the startup's industry. Describe in detail."
                        }
                    },
                    "required": [
                        "customers", "ICP", "pain_points", "alternate_solutions",
                        "competitors", "potential_partners", "key_incumbents",
                        "history_of_innovation", "key_risks", "legal_considerations",
                        "important_figures", "recent_trends"
                    ],
                },
            },
        ],
        function_call={"name": "analyze_startup"}
    )
    
    response_data = completion.choices[0]['message']['function_call']['arguments']
    
    html_content = ""
    for key, value in json.loads(response_data).items():
        html_content += f"<strong>{key.capitalize()}</strong>: {value}</br>\n"
    

    return html_content
