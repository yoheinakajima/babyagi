from agent_protocol import (
    Agent,
    StepResult,
    StepHandler,
)
from babyagi import (
    execution_agent,
    YOUR_FIRST_TASK,
    task_creation_agent,
    prioritization_agent,
)


def babyagi(task_input):
    task_input = str(task_input)
    task_list = [{"task_name": YOUR_FIRST_TASK, "task_id": 1}]
    while task := task_list.pop():
        result = execution_agent(task_input, task["task_name"])
        yield result

        result = {"data": result}
        new_tasks = task_creation_agent(
            task_input, result, task["task_name"], [t["task_name"] for t in task_list]
        )

        for new_task in new_tasks:
            task_list.append(new_task)

        task_list = prioritization_agent(task_list, task_input, task["task_id"])


async def task_handler(task_input) -> StepHandler:
    loop = babyagi(task_input)

    async def step_handler(step_input) -> StepResult:
        result = next(loop, None)
        if result is None:
            return StepResult(
                is_last=True,
            )
        return StepResult(
            output=result,
        )

    return step_handler


Agent.handle_task(task_handler).start()
