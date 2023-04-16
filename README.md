# Introduction

Please see the README for BabyAGI for more information on the original idea.
ToddlerAGI is designed to build on BabyAGI by adding self-reflection agents to the task execution and management system.


# Features
1) Added an option to store memory locally, instead of in Pinecone. This is more of a patch for an issue I was having, but may help others as well.
2) Added task-level and project-level overseers to approve or suggest feedback.

# Planned
1) Add a 'Task' class 
    a. task_type ( = <research|create|clarify>)
    b. subtasks and linked tasks
    c. execute_task is eventually a method on this class

2) Let execute_agents search the web or browse websites (similar to AutoGPT)

3) Declare multiple objectives at start and add an additional level of oversight

4) Add command-line args