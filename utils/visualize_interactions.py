import os
from graphviz import Digraph


def visualize_interactions():
    # Create a new directed graph
    dot = Digraph("Interactions")

    # Add nodes for each agent
    agents = [
        "ContextAgent",
        "ExecutionAgent",
        "PrioritizationAgent",
        "TaskCreationAgent",
        "BaseAgent",
    ]

    for agent in agents:
        dot.node(agent, agent)

    # Add nodes for helper and task manager
    dot.node("PineconeHelper", "PineconeHelper")
    dot.node("TaskManager", "TaskManager")

    # Add edges to represent interactions between nodes
    dot.edges(
        [
            ("ContextAgent", "BaseAgent"),
            ("ExecutionAgent", "BaseAgent"),
            ("PrioritizationAgent", "BaseAgent"),
            ("TaskCreationAgent", "BaseAgent"),
            ("BaseAgent", "TaskManager"),
            ("TaskManager", "PineconeHelper"),
            ("TaskManager", "ExecutionAgent"),
            ("TaskManager", "PrioritizationAgent"),
            ("TaskManager", "TaskCreationAgent"),
            ("TaskManager", "ContextAgent"),
            ("TaskCreationAgent", "ContextAgent"),
        ]
    )

    # Save the diagram as a PNG file
    dot.format = "png"
    dot.render("interactions", view=True)


if __name__ == "__main__":
    visualize_interactions()

