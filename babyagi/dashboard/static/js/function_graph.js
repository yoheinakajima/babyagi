// function_graph.js
let cy;

document.addEventListener('DOMContentLoaded', () => {
    cy = cytoscape({
        container: document.getElementById('graph'),
        style: [
            {
                selector: 'node',
                style: {
                    'shape': 'rectangle',
                    'background-color': '#E6F2FF',
                    'label': 'data(id)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'text-wrap': 'wrap',
                    'text-max-width': '150px',
                    'width': 'label',
                    'height': 'label',
                    'padding': '12px',
                    'font-weight': 'bold',
                    'font-size': '16px',
                    'color': '#333333',
                    'text-outline-color': '#FFFFFF',
                    'text-outline-width': 1,
                    'cursor': 'pointer'
                }
            },
            {
                selector: 'node[type="import"]',
                style: {
                    'background-color': '#E6FFF2'
                }
            },
            {
                selector: 'node[type="trigger"]',
                style: {
                    'background-color': '#FFE6E6'
                }
            },
            {
                selector: 'node:hover',
                style: {
                    'background-opacity': 0.8
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': '#999999',
                    'target-arrow-color': '#999999',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.5
                }
            },
            {
                selector: 'edge[type="dependency"]',
                style: {
                    'width': 2
                }
            },
            {
                selector: 'edge[type="trigger"]',
                style: {
                    'line-style': 'dashed',
                    'label': 'trigger',
                    'font-size': '12px',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -10
                }
            }
        ],
        layout: {
            name: 'cose',
            idealEdgeLength: 50,
            nodeOverlap: 20,
            refresh: 20,
            fit: true,
            padding: 30,
            randomize: false,
            componentSpacing: 80,
            nodeRepulsion: 450000,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
        },
        wheelSensitivity: 0.2
    });

    fetch('/api/functions')
        .then(response => response.json())
        .then(data => {
            const elements = [];
            const imports = new Set();

            data.forEach(func => {
                elements.push({ data: { id: func.name, type: 'function' } });

                func.dependencies.forEach(dep => {
                    elements.push({ data: { id: dep, type: 'function' } });
                    elements.push({ data: { source: func.name, target: dep, type: 'dependency' } });
                });

                func.triggers.forEach(trigger => {
                    elements.push({ data: { id: trigger, type: 'trigger' } });
                    elements.push({ data: { source: func.name, target: trigger, type: 'trigger' } });
                });

                func.imports.forEach(imp => imports.add(imp));
            });

            imports.forEach(imp => {
                elements.push({ data: { id: imp, type: 'import' } });
            });

            data.forEach(func => {
                func.imports.forEach(imp => {
                    elements.push({ data: { source: func.name, target: imp, type: 'import' } });
                });
            });

            cy.add(elements);
            cy.layout({ name: 'cose' }).run();

            cy.fit(40);

            cy.zoom({
                level: cy.zoom() * 1.3,
                renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
            });
        });

    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        if (node.data('type') === 'function' || node.data('type') === 'trigger') {
            showFunctionOverlay(node.id());
        }
    });

    cy.on('zoom pan', () => {
        closeOverlay();
    });
});

function showFunctionOverlay(functionName) {
    const overlay = document.getElementById('overlay');
    const content = document.getElementById('overlay-content');

    fetch(`/api/function/${functionName}`)
        .then(response => response.json())
        .then(data => {
            content.innerHTML = `
                <h3>${data.name}</h3>
                <div id="tab-buttons">
                    <button class="tab-button active" onclick="showTab('description', '${data.name}')">Description</button>
                    <button class="tab-button" onclick="showTab('code', '${data.name}')">Code</button>
                    <button class="tab-button" onclick="showTab('logs', '${data.name}')">Logs</button>
                </div>
                <div id="tab-content">
                    <div id="description-tab">
                        <p><strong>Description:</strong> ${data.metadata.description || 'No description available.'}</p>
                        <p><strong>Version:</strong> ${data.version}</p>
                    </div>
                    <div id="code-tab" style="display: none;"></div>
                    <div id="logs-tab" style="display: none;"></div>
                </div>
            `;

            const node = cy.$id(functionName);
            const renderedPosition = node.renderedPosition();

            overlay.style.left = `${renderedPosition.x + 10}px`;
            overlay.style.top = `${renderedPosition.y + 10}px`;
            overlay.style.display = 'block';
        });
}

function showTab(tabName, functionName) {
    const tabs = ['description', 'code', 'logs'];
    tabs.forEach(tab => {
        const tabElement = document.getElementById(`${tab}-tab`);
        const tabButton = document.querySelector(`button.tab-button:nth-child(${tabs.indexOf(tab) + 1})`);
        if (tab === tabName) {
            tabElement.style.display = 'block';
            tabButton.classList.add('active');
        } else {
            tabElement.style.display = 'none';
            tabButton.classList.remove('active');
        }
    });

    if (tabName === 'code' && document.getElementById('code-tab').innerHTML === '') {
        showCode(functionName);
    } else if (tabName === 'logs' && document.getElementById('logs-tab').innerHTML === '') {
        showLogs(functionName);
    }
}

function showCode(functionName) {
    fetch(`/api/function/${functionName}`)
        .then(response => response.json())
        .then(data => {
            const codeTab = document.getElementById('code-tab');
            codeTab.innerHTML = `
                <h4>Code:</h4>
                <pre><code>${data.code}</code></pre>
            `;
        });
}

function showLogs(functionName) {
    fetch(`/api/logs/${functionName}`)
        .then(response => response.json())
        .then(data => {
            const logsTab = document.getElementById('logs-tab');
            logsTab.innerHTML = `
                <h4>Logs:</h4>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            `;
        });
}

function closeOverlay() {
    document.getElementById('overlay').style.display = 'none';
}