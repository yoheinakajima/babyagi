document.addEventListener('DOMContentLoaded', () => {
    loadLogs();
});

async function loadLogs() {
    try {
        const response = await fetch(apiLogsUrl);
        if (!response.ok) {
            throw new Error('Failed to fetch logs');
        }
        const logs = await response.json();
        renderGraph(logs);
    } catch (error) {
        console.error('Error loading logs:', error);
        alert('Failed to load logs. Please try again later.');
    }
}

function renderGraph(logs) {
    // Process logs and build graph data
    const elements = logs.map(log => ({
        data: { id: log.id, label: log.function_name }
    }));

    // Add edges for relationships
    logs.forEach(log => {
        if (log.parent_log_id) {
            elements.push({
                data: {
                    id: `parent-${log.id}`,
                    source: log.parent_log_id,
                    target: log.id,
                    label: 'Parent'
                }
            });
        }
        if (log.triggered_by_log_id) {
            elements.push({
                data: {
                    id: `trigger-${log.id}`,
                    source: log.triggered_by_log_id,
                    target: log.id,
                    label: 'Triggered By'
                }
            });
        }
    });

    // Initialize Cytoscape graph
    var cy = cytoscape({
        container: document.getElementById('graph'),
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'background-color': '#666',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'color': '#fff',
                    'text-outline-width': 2,
                    'text-outline-color': '#666'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier'
                }
            }
        ],
        layout: {
            name: 'breadthfirst',
            directed: true,
            padding: 10
        }
    });

    // Add event listeners if needed
}
