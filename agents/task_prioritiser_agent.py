
from agents.IAgent import AgentData

class ObjectiveCompletionAgent:
    def __init__(self):
        pass
        
    def conclude(self,  agent: AgentData):
        description_string = ",AND ".join(task.description for task in agent.active_tasks)

        agent.logger.log(f"""List of tasks remaining: {description_string}""")

        prompt = f"""You are a Result Compiler Agent.
        Based on the following completed tasks: {agent.completed_tasks}, 
        Your job is to compile and write a comprehensive answer to that objective: {agent.objective}
        
        Note: Assess your work at the very end, and include ideas on how to improve output (what would our team of agents need to achieve the goal)"""
        
        agent.logger.log(f"""Conclusion Prompt: {prompt}""")
        response = agent.open_ai.generate_text(prompt)
        agent.logger.log(f"""Conclusion: {response}""")