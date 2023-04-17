import json
import re
from agents.IAgent import AgentData
from agents.ITask import Task
from agents.agent_constant import AVAILABLE_AGENTS
from agents.dispatcher_agent import DispatcherAgent
from agents.result_summarizer_agent import ResultSummarizerAgent


class ExecutionDispatcherAgent:
    def __init__(self):
        self.available_agents = AVAILABLE_AGENTS

    def extract_grade(self, text):
        pattern = r"\bGrade:\s*(\d)/10\b"
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
        else:
            return 10
        
    def dispatch(self, task: Task, agent: AgentData, warning: str) -> str:
        description_string = " AND ".join(task.description for task in agent.completed_tasks)

        prompt = f"""You are an Assistant Agent and your job is to search for information.
            Our global objective is to {agent.objective}.
            The previous completed tasks related to the objective are: {description_string}.

            We need to concentrate on the following task: {task.description}.
            Please return either:
            'browse(prompt)' The prompt should be a carefully crafted set of KEYWORDS for the google search engine, please avoid special characters.
            'openai(prompt)' to ask GPT3 for information.
            'scrape(url)' to search for a specific url, only if explicitly in the task description.

            Kindly ensure that you are specific enough to facilitate the completion of the task, this is the most important step in our process !
            Return ONLY ONE request containing ONLY the request without ANY comments, explanations or additional information, this is important."""

        #agent.logger.log(f"Executing: {prompt}")
        response = agent.open_ai.generate_text(prompt, temperature=0.7)

        #agent.logger.log(f"Dispatching: {response}")
        
        result = []
        response_str = response
        
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
                print("No match found")
                
        #result_id = f"result_{task.id}"
        result_dump = [json.dumps(r) for r in result]
        
        #data = { "task": task.description, "result": ', '.join(result_dump) }
        #context = ContextData(result_id, data)

        #agent.vectordb.upsert(context, agent.objective)
        
        task_with_results = Task(id=task.id, description=task.description, result=', '.join(result_dump))
        
        full_result = ResultSummarizerAgent().summarize(task_with_results, agent)

        grade = self.extract_grade(full_result)

        if grade < 6:
            return self.dispatch(task, agent, warning)
        else:
            full_task_with_results = Task(id=task.id, description=task.description, result=full_result)
            return full_task_with_results