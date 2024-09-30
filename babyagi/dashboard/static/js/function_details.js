// At the top of function_details.js


// Ensure apiRoutes is defined
window.apiRoutes = window.apiRoutes || {};

// Helper function to get the API route
function getApiRoute(routeName, ...args) {
    if (typeof apiRoutes[routeName] === 'function') {
        return apiRoutes[routeName](...args);
    } else {
        return apiRoutes[routeName];
    }
}

window.getApiRoute = getApiRoute;

let functionData;
let codeEditor;

// Expose necessary functions to the global scope
window.loadFunctionDetails = loadFunctionDetails;
window.loadFunctionLogs = loadFunctionLogs;
window.initCodeEditor = initCodeEditor;
window.displayFunctionDetails = displayFunctionDetails;
window.createExecutionForm = createExecutionForm;
window.updateFunction = updateFunction;
window.executeFunction = executeFunction;
window.toggleVersionHistory = toggleVersionHistory;
window.loadFunctionVersions = loadFunctionVersions;
window.activateVersion = activateVersion;

function loadFunctionDetails() {
    fetch(getApiRoute('getFunction'))
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            functionData = data;
            console.log("functionData",functionData)
            displayFunctionDetails();
            createExecutionForm();
            initCodeEditor();
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('functionDetails').innerHTML = `<p>Error loading function details: ${error.message}</p>`;
        });
}

function loadFunctionLogs() {
    fetch(getApiRoute('getLogs'))
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(logs => {
            let logsHtml = logs.map(log => `
                <div class="log-entry">
                    <strong>Timestamp:</strong> ${new Date(log.timestamp).toLocaleString()}<br>
                    <strong>Message:</strong> ${log.message}<br>
                    <strong>Params:</strong> ${JSON.stringify(log.params)}<br>
                    <strong>Output:</strong> ${JSON.stringify(log.output)}<br>
                    <strong>Time spent:</strong> ${log.time_spent} seconds
                </div>
            `).join('');
            document.getElementById('functionLogs').innerHTML = logsHtml;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('functionLogs').innerHTML = `<p>Error loading logs: ${error.message}</p>`;
        });
}

function initCodeEditor() {
    const editorElement = document.getElementById('codeEditor'); // Example: Get the editor element

    // Check if the editor element exists
    if (!editorElement) {
        console.error("Code editor textarea not found!");
        return;
    }

    // Destroy the previous CodeMirror instance if it exists
    if (codeEditor) {
        codeEditor.toTextArea(); // Converts the editor back into a textarea
        codeEditor = null; // Clear the reference
    }

    // Initialize the new CodeMirror instance
    codeEditor = CodeMirror.fromTextArea(editorElement, {
        mode: "python",
        theme: "monokai",
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        autofocus: true
    });
    console.log("initCodeEditor executing");
    console.log("window.functionData.code", functionData.code);
    console.log("window.functionData", functionData);

    // Set the current function code (if available)
    if (functionData && functionData.code) {
        codeEditor.setValue(functionData.code);
    } else {
        codeEditor.setValue(""); // Clear editor if no code
    }

    // Refresh CodeMirror to fix display issues
    setTimeout(() => {
        codeEditor.refresh();
    }, 200); // Short delay to ensure the editor is fully visible before refreshing
}



function displayFunctionDetails() {
    document.getElementById('functionName').textContent = functionData.name;

    let detailsHtml = `
        <div class="detail-item">
            <span class="detail-label">Version:</span>
            <span class="detail-value">${functionData.version}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Created Date:</span>
            <span class="detail-value">${new Date(functionData.created_date).toLocaleString()}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Description:</span>
            <span class="detail-value">${functionData.metadata.description || 'No description available'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Dependencies:</span>
            <span class="detail-value">$
                <span class="detail-value">
                  ${functionData.dependencies.length ? functionData.dependencies.map(dep => `
                    <a href="${dashboardRoute}/function/${encodeURIComponent(dep)}" class="function-name">${dep}</a>
                  `).join(', ') : 'None'}
                </span>

            </span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Imports:</span>
            <span class="detail-value">${functionData.imports ? functionData.imports.join(', ') : 'None'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Triggers:</span>
            <span class="detail-value">${functionData.triggers.join(', ') || 'None'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Input Parameters:</span>
            <ul class="detail-list">
                ${functionData.input_parameters.map(param => `<li>${param.name} (${param.type})</li>`).join('')}
            </ul>
        </div>
        <div class="detail-item">
            <span class="detail-label">Output Parameters:</span>
            <ul class="detail-list">
                ${functionData.output_parameters.map(param => `<li>${param.name} (${param.type})</li>`).join('')}
            </ul>
        </div>
    `;

    document.getElementById('functionDetails').innerHTML = detailsHtml;
}

function createExecutionForm() {
    let formHtml = '';
    if (functionData.name === 'execute_function_wrapper') {
        formHtml += `
            <div class="param-input">
                <label for="function_name">function_name (str):</label>
                <input type="text" id="function_name" name="function_name">
            </div>
            <div class="param-input">
                <label for="args">args (comma-separated values):</label>
                <input type="text" id="args" name="args">
            </div>
            <div class="param-input">
                <label for="kwargs">kwargs (JSON format):</label>
                <textarea id="kwargs" name="kwargs" rows="5" cols="50"></textarea>
            </div>
        `;
    } else {
        functionData.input_parameters.forEach(param => {
            if (param.type === 'json') {
                formHtml += `
                    <div class="param-input">
                        <label for="${param.name}">${param.name} (${param.type}):</label>
                        <textarea id="${param.name}" name="${param.name}" rows="5" cols="50"></textarea>
                    </div>
                `;
            } else {
                formHtml += `
                    <div class="param-input">
                        <label for="${param.name}">${param.name} (${param.type}):</label>
                        <input type="text" id="${param.name}" name="${param.name}">
                    </div>
                `;
            }
        });
    }
    document.getElementById('executionForm').innerHTML = formHtml;
}

function updateFunction() {
    const updatedCode = codeEditor.getValue();
    fetch(getApiRoute('updateFunction'), {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            code: updatedCode,
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert('Function updated successfully');
        functionData.code = updatedCode;
        if (data.version) {
            functionData.version = data.version;
        }
        displayFunctionDetails();
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('Error updating function');
    });
}

function executeFunction() {
    let params = {};
    if (functionData.name === 'execute_function_wrapper') {
        const functionNameInput = document.getElementById('function_name').value.trim();
        if (!functionNameInput) {
            alert('Function name is required.');
            return;
        }
        const args = document.getElementById('args').value ? 
            document.getElementById('args').value.split(',').map(arg => arg.trim()) : [];
        let kwargs = {};
        const kwargsValue = document.getElementById('kwargs').value.trim();
        if (kwargsValue) {
            try {
                kwargs = JSON.parse(kwargsValue);
            } catch (e) {
                alert('Invalid JSON input for kwargs. Please check your input.');
                return;
            }
        }
        params = {
            function_name: functionNameInput,
            args: args,
            kwargs: kwargs
        };
    } else {
        for (const param of functionData.input_parameters) {
            let value = document.getElementById(param.name).value.trim();

            // Skip empty inputs
            if (value === '') continue;

            try {
                switch (param.type) {
                    case 'int':
                        value = parseInt(value, 10);
                        if (isNaN(value)) throw new Error(`Invalid integer for ${param.name}`);
                        break;
                    case 'float':
                        value = parseFloat(value);
                        if (isNaN(value)) throw new Error(`Invalid float for ${param.name}`);
                        break;
                    case 'bool':
                        value = value.toLowerCase();
                        if (value !== 'true' && value !== 'false') throw new Error(`Invalid boolean for ${param.name}. Use 'true' or 'false'.`);
                        value = value === 'true';
                        break;
                    case 'date':
                        value = new Date(value);
                        if (isNaN(value.getTime())) throw new Error(`Invalid date for ${param.name}`);
                        break;
                    case 'list':
                        value = value.split(',').map(item => item.trim());
                        break;
                    case 'json':
                        value = JSON.parse(value);
                        break;
                }
                params[param.name] = value;
            } catch (error) {
                alert(`Error with parameter ${param.name}: ${error.message}`);
                return;
            }
        }
    }

    fetch(getApiRoute('executeFunction'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(text || response.statusText);
            });
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('executionResult').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    })
    .catch((error) => {
        console.error('Error:', error);
        document.getElementById('executionResult').innerHTML = `<pre class="error">Error executing function: ${error.message}</pre>`;
    });
}

let isVersionHistoryVisible = false;

function toggleVersionHistory() {
    const versionHistory = document.getElementById('versionHistory');
    if (isVersionHistoryVisible) {
        versionHistory.style.display = 'none';
        document.getElementById('toggleVersionHistory').textContent = 'Show Versions';
    } else {
        loadFunctionVersions();
        versionHistory.style.display = 'block';
        document.getElementById('toggleVersionHistory').textContent = 'Hide Versions';
    }
    isVersionHistoryVisible = !isVersionHistoryVisible;
}

function loadFunctionVersions() {
    fetch(getApiRoute('getFunctionVersions'))
        .then(response => response.json())
        .then(versions => {
            const versionHistoryDiv = document.getElementById('versionHistory');
            let versionHtml = versions.map(version => `
                <div class="version-item ${version.is_active ? 'active' : ''}">
                    <strong>Version ${version.version}</strong> - Created: ${new Date(version.created_date).toLocaleString()}
                    <pre>${version.code}</pre>
                    <button class="button" onclick="activateVersion(${version.version})">Activate Version</button>
                </div>
            `).join('');
            versionHistoryDiv.innerHTML = versionHtml;
        })
        .catch(error => console.error('Error loading versions:', error));
}

function activateVersion(version) {
    const url = getApiRoute('activateVersion', version);
    fetch(url, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        alert('Version activated successfully');
        loadFunctionDetails();
        loadFunctionVersions();
    })
    .catch(error => console.error('Error activating version:', error));
}

window.addEventListener('load', function() {
    loadFunctionDetails();
    loadFunctionLogs();
});
