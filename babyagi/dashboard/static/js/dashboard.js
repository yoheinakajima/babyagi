/* static/js/dashboard.js */

// Assume that dashboardRoute, apiFunctionsUrl, and apiLogsUrl are defined in the HTML template

let currentSort = { key: null, direction: 'asc' };
let allFunctions = []; // This will hold the functions data globally

function filterTable() {
    const input = document.getElementById("searchInput").value.toLowerCase();
    const table = document.getElementById("functionTable");
    const rows = table.getElementsByTagName("tr");
    const grid = document.getElementById("functionGrid");
    const cards = grid.getElementsByClassName("function-card");

    for (let i = 1; i < rows.length; i++) { // Start at 1 to skip header row
        let match = false;
        const cells = rows[i].getElementsByTagName("td");
        for (let j = 0; j < cells.length; j++) {
            if (cells[j].innerText.toLowerCase().includes(input)) {
                match = true;
                break;
            }
        }
        rows[i].style.display = match ? "" : "none";
    }

    // Filter cards for mobile view
    for (let i = 0; i < cards.length; i++) {
        if (cards[i].innerText.toLowerCase().includes(input)) {
            cards[i].style.display = "";
        } else {
            cards[i].style.display = "none";
        }
    }
}
function sortTable(key) {
    const direction = currentSort.key === key && currentSort.direction === 'asc' ? 'desc' : 'asc';
    currentSort = { key, direction };

    const sortedFunctions = [...allFunctions].sort((a, b) => {
        let valA, valB;
        if (key === 'name') {
            valA = a.name.toLowerCase();
            valB = b.name.toLowerCase();
        } else if (key === 'created_date') {
            valA = new Date(a.created_date);
            valB = new Date(b.created_date);
        } else if (key === 'total_logs') {
            valA = a.total_logs || 0;
            valB = b.total_logs || 0;
        } else if (key === 'last_log_date') {
            valA = new Date(a.last_log_date || 0);
            valB = new Date(b.last_log_date || 0);
        }

        if (direction === 'asc') return valA > valB ? 1 : -1;
        return valA < valB ? 1 : -1;
    });

    populateDashboard(sortedFunctions);
}

async function fetchLogs(functionName) {
    try {
        const response = await fetch(`${apiLogsUrl}${encodeURIComponent(functionName)}`);
        if (!response.ok) {
            throw new Error('Failed to fetch logs');
        }
        const logs = await response.json();
        return {
            total_logs: logs.length,
            last_log_date: logs.length > 0 ? logs[logs.length - 1].timestamp : null
        };
    } catch (error) {
        console.error(`Error fetching logs for ${functionName}:`, error);
        return { total_logs: 0, last_log_date: null };
    }
}

function updateLogsAsync(tasks) {
    const promises = tasks.map(([functionName, row]) => {
        return fetchLogs(functionName).then(({ total_logs, last_log_date }) => {
            const totalLogsCell = row.querySelector('.total-logs');
            const lastLogDateCell = row.querySelector('.last-log-date');
            totalLogsCell.textContent = total_logs;
            lastLogDateCell.textContent = last_log_date ? new Date(last_log_date).toLocaleDateString() : 'N/A';

            // Update function in allFunctions array
            const func = allFunctions.find(f => f.name === functionName);
            if (func) {
                func.total_logs = total_logs;
                func.last_log_date = last_log_date;
            }
        });
    });
    return Promise.all(promises);
}

async function populateDashboard(functions) {
    allFunctions = functions; // Store functions globally for sorting
    const tableBody = document.querySelector('#functionTable tbody');
    const grid = document.getElementById('functionGrid');
    const logTasks = [];

    tableBody.innerHTML = '';
    grid.innerHTML = '';

    for (const func of functions) {
        const row = document.createElement('tr');
        const description = func.metadata && func.metadata.description ? func.metadata.description : 'No description available';
        const createdDate = new Date(func.created_date).toLocaleDateString();

        row.innerHTML = `
            <td><a href="${dashboardRoute}/function/${encodeURIComponent(func.name)}" class="function-name">${func.name}</a></td>
            <td class="small-text">v${func.version}</td>
            <td>${description}</td>
            <td>${formatParams(func.input_parameters)}</td>
            <td>${formatParams(func.output_parameters)}</td>
            <td>${formatList(func.dependencies, 'dependencies-list', dashboardRoute)}</td>
            <td>${formatList(func.imports, 'imports-list')}</td>
            <td>${formatList(func.triggers, 'triggers-list', dashboardRoute)}</td>
            <td class="small-text">${createdDate}</td>
            <td class="small-text total-logs">Loading...</td>
            <td class="small-text last-log-date">Loading...</td>
        `;
        tableBody.appendChild(row);

        // Populate card view (for mobile)
        const card = document.createElement('div');
        card.className = 'function-card';
        card.innerHTML = `
            <a href="${dashboardRoute}function/${encodeURIComponent(func.name)}" class="function-name">${func.name}</a>
            <div class="function-meta">v${func.version} | Created: ${createdDate}</div>
            <div class="function-description">${description}</div>
            <div class="params-title">Input Parameters:</div>
            ${formatParams(func.input_parameters)}
            <div class="params-title">Output Parameters:</div>
            ${formatParams(func.output_parameters)}
            <div class="params-title">Dependencies:</div>
            ${formatList(func.dependencies, 'dependencies-list', dashboardRoute)}
            <div class="params-title">Imports:</div>
            ${formatList(func.imports, 'imports-list')}
            <div class="params-title">Triggers:</div>
            ${formatList(func.triggers, 'triggers-list', dashboardRoute)}
            <div class="log-info">
                <span>Total Logs: <span class="total-logs">Loading...</span></span>
                <span>Last Log: <span class="last-log-date">Loading...</span></span>
            </div>
        `;
        grid.appendChild(card);

        logTasks.push([func.name, row]);
    }

    updateLogsAsync(logTasks);
}

function formatParams(params) {
    if (!params || params.length === 0) {
        return '<span class="small-text"></span>';
    }
    return '<ul class="params-list">' + 
        params.map(param => `<li>${param.name}: <span class="small-text">${param.type}</span></li>`).join('') + 
        '</ul>';
}

function formatList(items, className, dashboardRoute) {
    if (!items || items.length === 0) {
        return '<span class="small-text">-</span>';
    }
    return '<ul class="' + className + '">' + 
        items.map(item => {
            if (className === 'dependencies-list' || className === 'triggers-list') {
                return `<li><a href="${dashboardRoute}/function/${encodeURIComponent(item)}" class="function-link">${item}</a></li>`;
            }
            return `<li>${item}</li>`;
        }).join('') + 
        '</ul>';
}

// Fetch functions data and populate the dashboard
async function fetchFunctionsAndPopulate() {
    try {
        const response = await fetch(apiFunctionsUrl);
        if (!response.ok) {
            throw new Error('Failed to fetch functions');
        }
        const data = await response.json();
        populateDashboard(data);
    } catch (error) {
        console.error('Error fetching functions:', error);
        document.querySelector('.container').innerHTML += `<p style="color: red;">Error loading functions. Please try refreshing the page.</p>`;
    }
}

// Call the function when the page loads
document.addEventListener('DOMContentLoaded', () => {
    fetchFunctionsAndPopulate();

    // Add event listener for search input
    const searchInput = document.getElementById("searchInput");
    searchInput.addEventListener('input', filterTable);
});