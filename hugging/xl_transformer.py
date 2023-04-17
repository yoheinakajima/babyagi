import torch
from transformers import TransfoXLTokenizer, TransfoXLLMHeadModel

class TransformerXL:
    def __init__(self):
        self.tokenizer = TransfoXLTokenizer.from_pretrained('transfo-xl-wt103')
        self.model = TransfoXLLMHeadModel.from_pretrained('transfo-xl-wt103')

    def generate(self, prompt):
        print(prompt)
        input_ids = torch.tensor(self.tokenizer.encode(prompt)).unsqueeze(0)
        print(input_ids)
        outputs = self.model.generate(input_ids, max_length=200, do_sample=True)
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text
