import ray

@ray.remote
class CooperativeTaskListStorage:
    def __init__(self):
        self.task_list = []

    def add_task(self, task):
        self.task_list.append(task)

    def get_task(self, index):
        return self.task_list[index]

    def remove_task(self, index):
        del self.task_list[index]

    def get_all_tasks(self):
        return self.task_list

    def get_task_count(self):
        return len(self.task_list)