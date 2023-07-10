import os
import importlib.util
import inspect
from .skill import Skill

class SkillRegistry:
    def __init__(self, api_keys, skill_names=None):
        self.skills = {}
        skill_files = [f for f in os.listdir('skills') if f.endswith('.py') and f != 'skill.py']
        for skill_file in skill_files:
            module_name = skill_file[:-3]
            if skill_names and module_name not in skill_names:
                continue
            module = importlib.import_module(f'skills.{module_name}')
            for attr_name in dir(module):
                attr_value = getattr(module, attr_name)
                if inspect.isclass(attr_value) and issubclass(attr_value, Skill) and attr_value is not Skill:
                    skill = attr_value(api_keys)
                    if skill.valid:
                        self.skills[skill.name] = skill
        # Print the names and descriptions of all loaded skills
        skill_info = "\n".join([f"{skill_name}: {skill.description}" for skill_name, skill in self.skills.items()])
        # print(skill_info)

    def load_all_skills(self):
        skills_dir = os.path.dirname(__file__)
        for filename in os.listdir(skills_dir):
            if filename.endswith(".py") and filename not in ["__init__.py", "skill.py", "skill_registry.py"]:
                skill_name = filename[:-3]  # Remove .py extension
                self.load_skill(skill_name)

    def load_specific_skills(self, skill_names):
        for skill_name in skill_names:
            self.load_skill(skill_name)

    def load_skill(self, skill_name):
        skills_dir = os.path.dirname(__file__)
        filename = f"{skill_name}.py"
        if os.path.isfile(os.path.join(skills_dir, filename)):
            spec = importlib.util.spec_from_file_location(skill_name, os.path.join(skills_dir, filename))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for item_name in dir(module):
                item = getattr(module, item_name)
                if isinstance(item, type) and issubclass(item, Skill) and item is not Skill:
                    skill_instance = item(self.api_keys)
                    self.skills[skill_instance.name] = skill_instance

    def get_skill(self, skill_name):
        skill = self.skills.get(skill_name)
        if skill is None:
            raise Exception(
                f"Skill '{skill_name}' not found. Please make sure the skill is loaded and all required API keys are set.")
        return skill

    def get_all_skills(self):
        return self.skills