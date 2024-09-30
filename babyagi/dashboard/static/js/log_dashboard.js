let currentSort = { key: 'timestamp', direction: 'desc' }; // Set default sort to 'timestamp' descending
let allLogs = []; // Holds all fetched logs
let filteredLogs = []; // Holds logs after filtering
let rootLogs = []; // Holds the root logs after building the tree

// Fetch unique values for function names and log types to populate filter dropdowns
async function populateFilters() {
    try {
        const response = await fetch(apiLogsUrl);
        if (!response.ok) {
            throw new Error('Failed to fetch logs for filters');
        }
        let logs = await response.json();

        // **Sort logs by timestamp descending (most recent first)**
        logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        allLogs = logs;
        filteredLogs = logs;

        const functionFilter = document.getElementById('functionFilter');
        const logTypeFilter = document.getElementById('logTypeFilter');

        const uniqueFunctions = [...new Set(logs.map(log => log.function_name))].sort();
        uniqueFunctions.forEach(func => {
            const option = document.createElement('option');
            option.value = func;
            option.textContent = func;
            functionFilter.appendChild(option);
        });

        const uniqueLogTypes = [...new Set(logs.map(log => log.log_type))].sort();
        uniqueLogTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = capitalizeFirstLetter(type);
            logTypeFilter.appendChild(option);
        });

        // Build the tree structure
        rootLogs = buildLogTree(filteredLogs);

        renderLogs();
    } catch (error) {
        console.error('Error populating filters:', error);
        alert('Failed to load logs for filters. Please try again later.');
    }
}

// Build log tree based on parent_log_id
function buildLogTree(logs) {
    const logsById = {};
    const rootLogs = [];

    // Initialize logsById mapping and add children array to each log
    logs.forEach(log => {
        log.children = [];
        logsById[log.id] = log;
    });

    // Build the tree
    logs.forEach(log => {
        if (log.parent_log_id !== null) {
            const parentLog = logsById[log.parent_log_id];
            if (parentLog) {
                parentLog.children.push(log);
            } else {
                // Parent log not found, treat as root
                rootLogs.push(log);
            }
        } else {
            rootLogs.push(log);
        }
    });

    return rootLogs;
}

// Render logs in table and grid formats
function renderLogs() {
    renderTable();
    renderGrid();
}

// Render Logs Table (Desktop View)
function renderTable() {
    const tableBody = document.querySelector('#logTable tbody');
    tableBody.innerHTML = '';

    rootLogs.forEach(log => {
        renderLogRow(tableBody, log, 0);
    });
}

// Recursive function to render each log row and its children
function renderLogRow(tableBody, log, depth, parentRowId) {
    const row = document.createElement('tr');
    const rowId = 'log-' + log.id;
    row.id = rowId;

    // If it's a child row, add a class to indicate it's a child
    if (parentRowId) {
        row.classList.add('child-of-log-' + parentRowId);
        row.style.display = 'none'; // Hide child rows by default
    }

    // Check if log has children
    const hasChildren = log.children && log.children.length > 0;

    // Create expand/collapse icon
    let toggleIcon = '';
    if (hasChildren) {
        toggleIcon = `<span class="toggle-icon" data-log-id="${log.id}" style="cursor:pointer;">[+]</span> `;
    }

    row.innerHTML = `
        <td><a href="${dashboardRoute}/log/${log.id}" class="function-link">${log.id}</a></td>
        <td><a href="${dashboardRoute}/function/${encodeURIComponent(log.function_name)}" class="function-link">${log.function_name}</a></td>
        <td style="padding-left:${depth * 20}px">${toggleIcon}${log.message}</td>
        <td>${new Date(log.timestamp).toLocaleString()}</td>
        <td>${capitalizeFirstLetter(log.log_type)}</td>
        <td>${log.time_spent ? log.time_spent.toFixed(3) : 'N/A'}</td>
        <td>${log.parent_log_id !== null ? log.parent_log_id : 'N/A'}</td>
        <td>${log.triggered_by_log_id !== null ? log.triggered_by_log_id : 'N/A'}</td>
    `;
    tableBody.appendChild(row);

    // Add event listener for toggle
    if (hasChildren) {
        row.querySelector('.toggle-icon').addEventListener('click', function() {
            toggleChildRows(log.id);
            // Update the icon
            const icon = this;
            if (icon.textContent === '[+]') {
                icon.textContent = '[-]';
            } else {
                icon.textContent = '[+]';
            }
        });
    }

    // Recursively render children
    if (hasChildren) {
        log.children.forEach(childLog => {
            renderLogRow(tableBody, childLog, depth + 1, log.id);
        });
    }
}

// Function to toggle child rows
function toggleChildRows(parentLogId) {
    const childRows = document.querySelectorAll('.child-of-log-' + parentLogId);

    childRows.forEach(row => {
        if (row.style.display === 'none') {
            row.style.display = '';
        } else {
            row.style.display = 'none';
            // Recursively hide any child rows
            const childLogId = row.id.replace('log-', '');
            toggleChildRows(childLogId);
            // Reset the toggle icon of child rows to '[+]'
            const toggleIcon = row.querySelector('.toggle-icon');
            if (toggleIcon) {
                toggleIcon.textContent = '[+]';
            }
        }
    });
}

// Render Logs Grid (Mobile View)
function renderGrid() {
    const logGrid = document.getElementById('logGrid');
    logGrid.innerHTML = '';

    rootLogs.forEach(log => {
        renderLogCard(logGrid, log, 0);
    });
}

// Recursive function to render log cards and their children
function renderLogCard(container, log, depth) {
    const card = document.createElement('div');
    card.className = 'log-card';
    card.style.marginLeft = (depth * 20) + 'px';

    card.innerHTML = `
        <h5>ID: <a href="${dashboardRoute}/log/${log.id}" class="function-link">${log.id}</a></h5>
        <div class="log-meta">Function: <a href="${dashboardRoute}/function/${encodeURIComponent(log.function_name)}">${log.function_name}</a> | ${new Date(log.timestamp).toLocaleString()}</div>
        <div class="log-details"><strong>Message:</strong> ${log.message}</div>
        <div class="log-details"><strong>Log Type:</strong> ${capitalizeFirstLetter(log.log_type)}</div>
        <div class="log-details"><strong>Time Spent:</strong> ${log.time_spent ? log.time_spent.toFixed(3) : 'N/A'} seconds</div>
        <div class="log-details"><strong>Parent Log ID:</strong> ${log.parent_log_id !== null ? log.parent_log_id : 'N/A'}</div>
        <div class="log-details"><strong>Triggered By Log ID:</strong> ${log.triggered_by_log_id !== null ? log.triggered_by_log_id : 'N/A'}</div>
    `;
    container.appendChild(card);

    // Recursively render children
    if (log.children && log.children.length > 0) {
        log.children.forEach(childLog => {
            renderLogCard(container, childLog, depth + 1);
        });
    }
}

// Capitalize the first letter of a string
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

// Sort logs based on a key
function sortLogs(key) {
    if (currentSort.key === key) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.key = key;
        currentSort.direction = 'asc';
    }

    // Sort root logs
    rootLogs.sort((a, b) => {
        let valA = a[key];
        let valB = b[key];

        // Handle null or undefined values
        if (valA === null || valA === undefined) valA = '';
        if (valB === null || valB === undefined) valB = '';

        // If sorting by timestamp, convert to Date
        if (key === 'timestamp') {
            valA = new Date(valA);
            valB = new Date(valB);
        }

        // If sorting by time_spent or IDs, ensure numerical comparison
        if (key === 'time_spent' || key === 'id' || key === 'parent_log_id' || key === 'triggered_by_log_id') {
            valA = Number(valA);
            valB = Number(valB);
        }

        if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
        if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
        return 0;
    });

    renderLogs();
}

// Apply Filters
function applyFilters() {
    const functionFilter = document.getElementById('functionFilter').value.toLowerCase();
    const logTypeFilter = document.getElementById('logTypeFilter').value.toLowerCase();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    // First, filter the logs
    filteredLogs = allLogs.filter(log => {
        let matchesFunction = true;
        let matchesLogType = true;
        let matchesStartDate = true;
        let matchesEndDate = true;

        if (functionFilter) {
            matchesFunction = log.function_name.toLowerCase().includes(functionFilter);
        }

        if (logTypeFilter) {
            matchesLogType = log.log_type.toLowerCase() === logTypeFilter;
        }

        if (startDate) {
            matchesStartDate = new Date(log.timestamp) >= new Date(startDate);
        }

        if (endDate) {
            // Add one day to endDate to include the entire end day
            const endDateObj = new Date(endDate);
            endDateObj.setDate(endDateObj.getDate() + 1);
            matchesEndDate = new Date(log.timestamp) < endDateObj;
        }

        return matchesFunction && matchesLogType && matchesStartDate && matchesEndDate;
    });

    // Rebuild the tree
    rootLogs = buildLogTree(filteredLogs);

    renderLogs();
}

// Reset Filters
function resetFilters() {
    document.getElementById('functionFilter').value = '';
    document.getElementById('logTypeFilter').value = '';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    filteredLogs = allLogs;

    // Rebuild the tree
    rootLogs = buildLogTree(filteredLogs);

    renderLogs();
}

// Initialize the logs dashboard
document.addEventListener('DOMContentLoaded', () => {
    populateFilters();
});
