import networkx as nx
import matplotlib.pyplot as plt

def visualize_interactions():
    # Create a new directed graph
    G = nx.DiGraph()

    # Add nodes for each agent
    agents = [
        "ContextAgent",
        "ExecutionAgent",
        "PrioritizationAgent",
        "TaskCreationAgent",
    ]

    for agent in agents:
        G.add_node(agent)

    # Add nodes for helper and task manager
    G.add_node("PineconeHelper")
    G.add_node("TaskManager")

    # Add edges to represent interactions between nodes
    G.add_edges_from(
        [
            ("ContextAgent", "TaskManager"),
            ("ExecutionAgent", "TaskManager"),
            ("PrioritizationAgent", "TaskManager"),
            ("TaskCreationAgent", "TaskManager"),
            ("TaskManager", "PineconeHelper"),
            ("TaskManager", "ExecutionAgent"),
            ("TaskManager", "PrioritizationAgent"),
            ("TaskManager", "TaskCreationAgent"),
            ("TaskManager", "ContextAgent"),
            ("TaskCreationAgent", "ContextAgent"),
        ]
    )

    # Draw the graph and save the diagram as a PNG file
    pos = nx.spring_layout(G, seed=42)
    
    # Customize node and edge appearance
    agent_node_color = "skyblue"
    other_node_color = "lightgreen"
    edge_color = "gray"
    edge_width = 1.5
    node_size = 2000
    font_size = 5
    font_weight = "bold"
    arrowsize = 20

    # Draw nodes
    agent_nodes = [n for n in G.nodes() if n in agents]
    other_nodes = [n for n in G.nodes() if n not in agents]
    nx.draw_networkx_nodes(G, pos, nodelist=agent_nodes, node_color=agent_node_color, node_size=node_size)
    nx.draw_networkx_nodes(G, pos, nodelist=other_nodes, node_color=other_node_color, node_size=node_size)

    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color=edge_color, width=edge_width, arrowsize=arrowsize)

    # Draw node labels
    nx.draw_networkx_labels(G, pos, font_size=font_size, font_weight=font_weight)

    # Save and show the graph
    plt.axis("off")
    plt.savefig("interactions.png", dpi=900, bbox_inches="tight")
    plt.show()

if __name__ == "__main__":
    visualize_interactions()
