import os
from dotenv import load_dotenv
import time
from datetime import datetime
from skills.skill_registry import SkillRegistry
from tasks.task_registry import TaskRegistry
from ongoing_tasks import ongoing_tasks

load_dotenv()  # Load environment variables from .env file

api_keys = {
    'openai': os.getenv('OPENAI_API_KEY'),
    'serpapi': os.getenv('SERPAPI_API_KEY')
    #'airtable': os.getenv('AIRTABLE_API_KEY')
}

OBJECTIVE = "Research Yohei Nakajima and write a poem about him."
LOAD_SKILLS = ['web_search', 'text_completion', 'code_reader','google_jobs_api_search','image_generation','startup_analysis','play_music','game_generation']
#add web_search and documentation_search after you add SERPAPI_API_KEY in your secrets. airtable_search once you've added your AIRTABLE_API_KEY, and add base/table/column data to airtable_search.py, etc...
REFLECTION = False #Experimental reflection step between each task run (when running tasklist)

def run_single_task(task_id, task, skill_registry, task_outputs, OBJECTIVE, task_registry):
    """Execute a single task and update its status"""
    task_output = task_registry.execute_task(task_id, task, skill_registry, task_outputs, OBJECTIVE)
    
    task_outputs[task_id]["output"] = task_output
    task_outputs[task_id]["completed"] = True
    task_outputs[task_id]["description"] = task.get('description', 'No description available')
    task_outputs[task_id]["skill"] = task.get('skill', 'No skill information available')
    
    if task_output:
        task_registry.update_tasks({"id": task_id, "status": "completed", "result": task_output})

        completed_task = task_registry.get_task(task_id)
        print(f"Task #{task_id}: {completed_task.get('task')} [COMPLETED][{completed_task.get('skill')}]")
        
        if REFLECTION:
            new_tasks, insert_after_ids, tasks_to_update = task_registry.reflect_on_output(task_output, skill_descriptions)
            for new_task, after_id in zip(new_tasks, insert_after_ids):
                task_registry.add_task(new_task, after_id)

            if isinstance(tasks_to_update, dict) and tasks_to_update:
                tasks_to_update = [tasks_to_update]
            
            for task_to_update in tasks_to_update:
                task_registry.update_tasks(task_to_update)




def run_main_loop(OBJECTIVE, LOAD_SKILLS, api_keys, REFLECTION=False):
    """Main execution loop"""
    try:
        skill_descriptions = ",".join(f"[{skill.name}: {skill.description}]" for skill in global_skill_registry.skills.values())
        task_registry = TaskRegistry()
        task_registry.create_tasklist(OBJECTIVE, skill_descriptions)

        skill_names = [skill.name for skill in global_skill_registry.skills.values()]
        session_summary = f"OBJECTIVE:{OBJECTIVE}.#SKILLS:{','.join(skill_names)}.#"

        task_outputs = {task["id"]: {"completed": False, "output": None} for task in task_registry.get_tasks()}

        task_output = None  # Initialize task_output to None

        while not all(task["completed"] for task in task_outputs.values()):
            tasks = task_registry.get_tasks()
            task_registry.print_tasklist(tasks)

            for task in tasks:
                if task["id"] not in task_outputs:
                    task_outputs[task["id"]] = {"completed": False, "output": None}

                ready_tasks = [(task["id"], task) for task in tasks if all((dep in task_outputs and task_outputs[dep]["completed"]) for dep in task.get('dependent_task_ids', [])) and not task_outputs[task["id"]]["completed"]]

                for task_id, task in ready_tasks:
                    run_single_task(task_id, task, global_skill_registry, task_outputs, OBJECTIVE, task_registry)

                time.sleep(0.1)

            # Assuming the last task in tasks has the latest output. Adjust if your use case is different.
            last_task_id = tasks[-1]["id"] if tasks else None
            task_output = task_outputs[last_task_id]["output"] if last_task_id else None

            task_registry.reflect_on_final(OBJECTIVE, task_registry.get_tasks(), task_output, skill_descriptions)
            global_skill_registry.reflect_skills(OBJECTIVE, task_registry.get_tasks(), task_output, skill_descriptions)

            with open(f'output/output_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.txt', 'w') as file:
                file.write(session_summary)
            print("...file saved.")
            print("END")

        return task_output  # Return the last task output

    except Exception as e:
        return f"An error occurred: {e}"



# Removed repeated logic for initiating skill registry
global_skill_registry = SkillRegistry(api_keys=api_keys, main_loop_function=run_main_loop, skill_names=LOAD_SKILLS)


def execute_skill(skill_name, objective, task_id):
    """Execute a single skill"""
    skill = global_skill_registry.get_skill(skill_name)
    if skill:
        try:
            result = skill.execute(objective, "", objective)
            ongoing_tasks[task_id].update({"status": "completed", "output": result})
        except Exception as e:
            ongoing_tasks[task_id].update({"status": "error", "error": str(e)})
        return task_id
    return "Skill not found :("

def execute_task_list(objective, api_keys, task_id):
    """Execute a list of tasks"""
    try:
        task_registry = TaskRegistry()
        result = run_main_loop(objective, get_skills(), api_keys)
        ongoing_tasks[task_id].update({"status": "completed", "output": result})
        return task_registry.get_tasks(), task_id
    except Exception as e:
        ongoing_tasks[task_id].update({"status": "error", "error": str(e)})
        print(f"Error in execute_task_list: {e}")
    return task_id



def get_skills():
    """Return the global skill registry"""
    # Removed repeated logic for initiating skill registry
    global global_skill_registry
    print("Returning GLOBAL SKILL REGISTRY")
    return global_skill_registry

# Removed repeated logic for initiating skill registry
global_skill_registry = SkillRegistry(api_keys=api_keys, main_loop_function=run_main_loop, skill_names=LOAD_SKILLS)

if __name__ == "__main__":
    run_main_loop(OBJECTIVE, LOAD_SKILLS, api_keys, REFLECTION)