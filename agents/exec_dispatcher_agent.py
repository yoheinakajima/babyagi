import json
import re
from agents.IAgent import AgentData
from agents.ITask import Task
from agents.dispatcher_agent import DispatcherAgent
from agents.result_summarizer_agent import ResultSummarizerAgent


class ExecutionDispatcherAgent:
    def __init__(self):
        pass

    def extract_grade(self, text):
        pattern = r"\bGrade:\s*(\d)/10\b"
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
        else:
            return 10
        
    def dispatch(self, task: Task, agent: AgentData, retry: dict = None) -> str:
        prompt = f"""You are an Assistant Agent and your job is to search for information.
            Our global objective is to {agent.objective}.
            We need to concentrate on the following task: {task.description}.

            Please return either:
            browse(prompt) The prompt should be a carefully crafted set of KEYWORDS for the google search engine, please avoid special characters.
            browse_ddg(prompt) same but for the duckduckgo search engine.
            scrape(url) to search for a specific url, only if explicitly in the task description.
            openai(prompt) to ask GPT3 for information (costly).
            
            Kindly ensure that you are specific enough to facilitate the completion of the task !
            Return ONLY ONE request containing ONLY the request without ANY comments, explanations or additional information, this is important."""
        
        response_str = agent.open_ai.generate_text(prompt, temperature=0.7)

        result = []
        if response_str is not None:
            agent.logger.log(f"API CALL: {response_str}")
            match = re.match(r"(\w+)\((?:\"|')(.+?)(?:\"|')\)", response_str)

            if match:
                function_name = match.group(1)
                argument = match.group(2)
                print(f"Function Name: {function_name}\nArgument: {argument}")
                dispatcher = DispatcherAgent(function_name, agent)
                r = dispatcher.dispatch(argument)
                result.append(r) 
            else:
                agent.logger.log(f"error with {response_str}")
 
                if retry["retry_count"] < 3:
                    # Update retry data if there's an error with response_str
                    retry["info"] += f"Error with response syntax: {response_str}\n"
                    retry["retry_count"] += 1
                    return self.dispatch(task, agent, retry)
                else:
                    return "Failed to complete task. Max retries exceeded."
                
        result_dump = [json.dumps(r) for r in result]

        task_with_results = Task(id=task.id, description=task.description, result=', '.join(result_dump))
        
        full_result = ResultSummarizerAgent().summarize(task_with_results, agent)

        grade = self.extract_grade(full_result)

        if grade < 6:
            if retry["retry_count"] < 3:
                retry["info"] += f"Result was too poor as the grade was {grade}\n"
                retry["retry_count"] += 1
                return self.dispatch(task, agent, retry)
            else:
                full_task_with_results = Task(id=task.id, description=task.description, result=full_result)
                return full_task_with_results
        else:
            full_task_with_results = Task(id=task.id, description=task.description, result=full_result)
            return full_task_with_results