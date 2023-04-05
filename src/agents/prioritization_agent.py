class PrioritizationAgent(BaseAgent):
    def prioritize_tasks(self, this_task_id: int, objective: str, task_manager: TaskManager) -> None:
        """
        Prioritize tasks using the prioritization agent.

        :param this_task_id: The current task ID.
        :param objective: The objective for the prioritization agent.
        :param task_manager: An instance of the TaskManager class.
        :return: None
        """
        task_names = self._get_task_names(task_manager)
        next_task_id = this_task_id + 1
        response_text = super().__call__(task_names=task_names, objective=objective, next_task_id=next_task_id)
        
        new_tasks = self._parse_response(response_text)
        self._update_task_manager(task_manager, new_tasks)

    @staticmethod
    def _get_task_names(task_manager: TaskManager) -> List[str]:
        """
        Get task names from the task manager.

        :param task_manager: An instance of the TaskManager class.
        :return: List of task names.
        """
        return [t["task_name"] for t in task_manager.task_list]

    @staticmethod
    def _parse_response(response_text: str) -> List[Dict[str, str]]:
        """
        Parse the response text from the prioritization agent.

        :param response_text: The response text returned by the prioritization agent.
        :return: List of dictionaries containing task_id and task_name.
        """
        task_strings = response_text.split('\n')
        tasks = []
        for task_string in task_strings:
            task_parts = task_string.strip().split(".", 1)
            if len(task_parts) == 2:
                task_id = task_parts[0].strip()
                task_name = task_parts[1].strip()
                tasks.append({"task_id": task_id, "task_name": task_name})
        return tasks
