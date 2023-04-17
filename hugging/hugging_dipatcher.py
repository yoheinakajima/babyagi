from hugging.bert_classifier import BERTClassifier
from hugging.chart_generator import ChartGenerator
from hugging.xl_transformer import TransformerXL


class HuggingDispatcher:
    def __init__(self, model_name):
        self.model_name = model_name
        self.models = {
            "transformerxl": TransformerXL(),
            "chart": ChartGenerator(),
            "bert": BERTClassifier(),
        }
        
        if model_name not in self.models:
            raise ValueError("Invalid model name.")
        
        self.model = self.models[model_name]
    
    def generate(self, prompt):
        return self.model.generate(prompt)