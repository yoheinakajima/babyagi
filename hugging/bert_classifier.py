from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification, pipeline
import torch

class BERTClassifier:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

        self.model2 = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased")
        self.classifier = pipeline("text-classification", model=self.model2, tokenizer=self.tokenizer)

    def classify(self, query, links, titles, snippets):
        inputs = self.tokenizer(query + ' ' + ' '.join(titles) + ' ' + ' '.join(snippets), return_tensors="pt", padding=True, truncation=True)
        outputs = self.model(**inputs).last_hidden_state
        cls_token = outputs[:, 0, :]
        scores = torch.nn.functional.softmax(cls_token, dim=1).tolist()[0]
        results = []
        for i, link in enumerate(links):
            results.append({'link': link, 'title': titles[i], 'snippet': snippets[i], 'score': scores[i + 1]})
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        return [{'link': r['link'], 'title': r['title'], 'snippet': r['snippet']} for r in results[:2]]
    
    def classify2(self, objective, task_description):
        task_text = f"{objective} {task_description}"
        result = self.classifier(task_text)[0]
        score = int(result['score'] * 100)
        return score