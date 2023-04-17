import re
from agents.IAgent import AgentData
from agents.ITask import Task
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest


class ResultSummarizerAgent:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        pass

    def summarize_text(self, text, num_sentences=10, chunk_size=1000000):
        summaries = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            doc = self.nlp(chunk)
            stopwords = list(STOP_WORDS)
            word_frequencies = {}
            for word in doc:
                if word.text.lower() not in stopwords:
                    if word.text.lower() not in punctuation:
                        if word.text not in word_frequencies.keys():
                            word_frequencies[word.text] = 1
                        else:
                            word_frequencies[word.text] += 1

            max_frequency = max(word_frequencies.values())
            for word in word_frequencies.keys():
                word_frequencies[word] = (word_frequencies[word]/max_frequency)

            sentence_tokens = [sent for sent in doc.sents]
            sentence_scores = {}
            for sent in sentence_tokens:
                for word in sent:
                    if word.text.lower() in word_frequencies.keys():
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word.text.lower()]
                        else:
                            sentence_scores[sent] += word_frequencies[word.text.lower()]

            summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
            final_sentences = [w.text for w in summary_sentences]
            summary = ' '.join(final_sentences)
            
            # Limit summary to a maximum of 4000 characters
            if len(summary) > 6000:
                summary = summary[:6000] + '...'
                
            summaries.append(summary)
        
        return ' '.join(summaries)
    
    def summarize(self, task: Task, agent: AgentData):
        result = self.summarize_text(task.result, 10)

        prompt = f"""Please rewrite this base text: {result} so that it is cleaner and easier to understand.
            Include relevant information, interesting URL (https:... etc) and examples that support the following task at hand: {task.description}.
            Provide extensive information, and feel free to include as many particulars as possible.

            Note: judge the relevance of the BASE TEXT (return "Grade: ?/10", 0 would be an error in the data), please be strict while assessing the quality of the base text in relation to the task.
            """

        response = agent.open_ai.generate_text(prompt, 0.1)

        agent.logger.log(f"Task Summary: {response}")
        return response