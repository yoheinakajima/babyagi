import os
from dotenv import load_dotenv
import importlib.util
import json
import openai
import concurrent.futures
import time
from datetime import datetime
from skills.skill import Skill
from skills.skill_registry import SkillRegistry
from tasks.task_registry import TaskRegistry


load_dotenv()  # Load environment variables from .env file

# Retrieve all API keys
api_keys = {
    'openai': os.environ['OPENAI_API_KEY'],
    'serpapi': os.environ['SERPAPI_API_KEY']
    # Add more keys here as needed
}

# Set OBJECTIVE
OBJECTIVE = "Create an example objective and tasklist for 'write a poem', which only uses text_completion in the tasks. Do this by usign code_reader to read example1.json, then writing the JSON objective tasklist pair using text_completion, and saving it using objective_saver."
LOAD_SKILLS = ['text_completion','code_reader','objective_saver']
REFLECTION = False

##### START MAIN LOOP########

# Print OBJECTIVE
print("\033[96m\033[1m"+"\n*****OBJECTIVE*****\n"+"\033[0m\033[0m")
print(OBJECTIVE)

if __name__ == "__main__":
    session_summary = ""
  
    # Initialize the SkillRegistry and TaskRegistry
    skill_registry = SkillRegistry(api_keys=api_keys, skill_names=LOAD_SKILLS)
    skill_descriptions = ",".join(f"[{skill.name}: {skill.description}]" for skill in skill_registry.skills.values())
    task_registry = TaskRegistry()

    # Create the initial task list based on an objective
    task_registry.create_tasklist(OBJECTIVE, skill_descriptions)
  
    # Initialize task outputs
    task_outputs = {i: {"completed": False, "output": None} for i, _ in enumerate(task_registry.get_tasks())}

    # Create a thread pool for parallel execution
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Loop until all tasks are completed
        while not all(task["completed"] for task in task_outputs.values()):
        
            # Get the tasks that are ready to be executed (i.e., all their dependencies have been completed)
            tasks = task_registry.get_tasks()
            # Print the updated task list
            task_registry.print_tasklist(tasks) 
            
            # Update task_outputs to include new tasks
            for task in tasks:
                if task["id"] not in task_outputs:
                    task_outputs[task["id"]] = {"completed": False, "output": None}

          
            ready_tasks = [(task["id"], task) for task in tasks
               if all((dep in task_outputs and task_outputs[dep]["completed"]) 
               for dep in task.get('dependent_task_ids', [])) 
               and not task_outputs[task["id"]]["completed"]]

            session_summary += str(task)+"\n"
            futures = [executor.submit(task_registry.execute_task, task_id, task, skill_registry, task_outputs, OBJECTIVE) 
                       for task_id, task in ready_tasks if not task_outputs[task_id]["completed"]]
            
            # Wait for the tasks to complete
            for future in futures:
                i, output = future.result()
                task_outputs[i]["output"] = output
                task_outputs[i]["completed"] = True
                
                # Update the task in the TaskRegistry
                task_registry.update_tasks({"id": i, "status": "completed", "result": output})
                
                completed_task = task_registry.get_task(i)
                print(f"\033[92mTask #{i}: {completed_task.get('task')} \033[0m\033[92m[COMPLETED]\033[0m\033[92m[{completed_task.get('skill')}]\033[0m")

                # Reflect on the output
                if output:
                    session_summary += str(output)+"\n"

                  
                    if REFLECTION == True:
                      new_tasks, insert_after_ids, tasks_to_update = task_registry.reflect_on_output(output, skill_descriptions)
                      # Insert new tasks
                      for new_task, after_id in zip(new_tasks, insert_after_ids):
                          task_registry.add_task(new_task, after_id)
      
                      # Update existing tasks
                      for task_to_update in tasks_to_update:
                        task_registry.update_tasks(task_to_update)
                    


            #print(task_outputs.values())
            if all(task["status"] == "completed" for task in task_registry.tasks):
              print("All tasks completed!")
              break
                  
            # Short delay to prevent busy looping
            time.sleep(0.1)


        # Print session summary
        print("\033[96m\033[1m"+"\n*****SAVING FILE...*****\n"+"\033[0m\033[0m")
        file = open(f'output/output_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.txt', 'w')
        file.write(session_summary)
        file.close()
        print("...file saved.")
        print("END")
        executor.shutdown()