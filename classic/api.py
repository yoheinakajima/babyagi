from agent_protocol import (
    Agent,
    Step,
    Task,
)
from agent_protocol.models import Status

from babyagi import (
    execution_agent,
    YOUR_FIRST_TASK,
    task_creation_agent,
    prioritization_agent,
)


def _get_future_step_names(task: Task, step: Step) -> list[str]:
    return [s.name for s in task.steps if s.status == Status.created and s != step]


async def task_handler(task: Task) -> None:
    await Agent.db.create_step(task.task_id, YOUR_FIRST_TASK)


async def step_handler(step: Step) -> Step:
    task = await Agent.db.get_task(step.task_id)
    result = execution_agent(task.input, step.name)
    step.output = result

    # Plan new tasks
    new_tasks = task_creation_agent(
        task.input,
        {"data": result},
        step.name,
        _get_future_step_names(task, step),
    )

    step_names = _get_future_step_names(task, step) + new_tasks
    step_id = task.steps.index(step) + 1

    # Prioritize
    result = prioritization_agent(
        [{"task_name": s} for s in step_names],
        task.input,
        step_id,
    )

    # Set up new steps
    task.steps = list(
        filter(lambda s: s.status == Status.completed or s == step, task.steps)
    )
    for i, new_step in enumerate(result):
        await Agent.db.create_step(
            task.task_id,
            new_step["task_name"],
        )

    # End if everything's done
    if len(result) == 0:
        step.is_last = True

    return step


Agent.setup_agent(task_handler, step_handler).start()
