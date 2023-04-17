import pickle
from transformers import pipeline

class ChartGenerator:
    def __init__(self):
        self.model = pipeline('text2text-generation', model='google/chart-transformer')
    
    def generate(self, prompt):
        chart_tensor = self.model(prompt, max_length=512, return_tensors='pt')[0]
        chart_array = chart_tensor.numpy()
        chart_string = pickle.dumps(chart_array).decode('latin1')
        return chart_string
