        // Display message function
        function displayMessage(content, role = "user") {
            let messageHTML = createMessageHTML(content, role);
            $("#chat-messages").append(messageHTML);
            if (role === "ongoing") {
                $(".bg-green-100:last").parent().addClass("ai-processing");
            }
        }

        function createMessageHTML(content, role) {
            if (role === "user") {
                return `<div class="flex justify-end mb-2">
                            <div class="bg-blue-200 text-black rounded-lg p-3 max-w-lg lg:max-w-xl text-right relative before:absolute before:inset-r-0 before:w-3 before:h-3 before:bg-blue-500 before:transform before:-rotate-45 before:-translate-y-1/2">
                                ${content}
                            </div>
                        </div>`;
            } else {
                return `<div class="flex justify-start mb-2">
                            <div class="bg-green-100 text-black rounded-lg p-3 max-w-lg lg:max-w-xl relative before:absolute before:inset-l-0 before:w-3 before:h-3 before:bg-gray-300 before:transform before:-rotate-45 before:-translate-y-1/2">
                                ${content}
                            </div>
                        </div>`;
            }
        }

        // Send message function
        function sendMessage() {
            const userMessage = $("#user-input").val().trim();

            if (!userMessage) {
                alert("Message cannot be empty!");
                return;
            }

            // Display the user's message
            displayMessage(userMessage, "user");
            scrollToBottom();
            // Display processing message
            displayMessage('...', 'ongoing');
            scrollToBottom();

            // Clear the input and disable the button
            $("#user-input").val("");
            toggleSendButton();

            // Send the message to the backend for processing
            $.ajax({
                type: 'POST',
                url: '/determine-response',
                data: JSON.stringify({ user_message: userMessage }),
                contentType: 'application/json',
                dataType: 'json',
                success: handleResponseSuccess,
                error: handleResponseError
            });
        }

        function handleResponseSuccess(data) {
            $(".ai-processing").remove();
            displayMessage(data.message, "assistant");
            scrollToBottom();

            if (data.objective) {
                displayTaskWithStatus(`Task: ${data.objective}`, "ongoing", data.skill_used, data.task_id);
            }
          
            if (data.path !== "ChatCompletion") {
                checkTaskCompletion(data.task_id);
            } else {
                
            }
            
        }

        function handleResponseError(error) {
            $(".ai-processing").remove();
            const errorMessage = error.responseJSON && error.responseJSON.error ? error.responseJSON.error : "Unknown error";
            displayMessage(`Error: ${errorMessage}`, "error");
            scrollToBottom();
        }

        // Other utility functions
        function toggleSendButton() {
            if ($("#user-input").val().trim()) {
                $("button").prop("disabled", false);
            } else {
                $("button").prop("disabled", true);
            }
        }

function scrollToBottom() {
    setTimeout(() => {
        const chatBox = document.getElementById("chat-messages");
        chatBox.scrollTop = chatBox.scrollHeight;
    }, 100);  // small delay to ensure content is rendered
}



        function checkTaskCompletion(taskId) {
            $.ajax({
                type: 'GET',
                url: `/check-task-status/${taskId}`,
                dataType: 'json',
                success(data) {
                    if (data.status === "completed") {                            updateTaskStatus(taskId, "completed");
                      fetchTaskOutput(taskId);
                      displayMessage("Hey, I just finished a task!", "assistant");
                    } else {
                      fetchTaskOutput(taskId);
                        setTimeout(() => {
                            checkTaskCompletion(taskId);
                        }, 5000); // Check every 5 seconds
                    }
                },
                error(error) {
                    console.error(`Error checking task status for ${taskId}:`, error);
                }
            });
        }

function fetchTaskOutput(taskId) {
    $.ajax({
        type: 'GET',
        url: `/fetch-task-output/${taskId}`,
        dataType: 'json',
        success(data) {
            if (data.output) {
                const $taskItem = $(`.task-item[data-task-id="${taskId}"]`);  // Find the task item with the given task ID
                console.log('taskItem:'+$taskItem)
                const $outputContainer = $taskItem.find('.task-output');
                console.log('outputContainer:'+$outputContainer)
                console.log('data.output:'+data.output)
                
                // Update the task's output content
                $outputContainer.html(`<p>${data.output}</p>`);
            }
        },
        error(error) {
            console.error(`Error fetching task output for ${taskId}:`, error);
        }
    });
}




$(document).ready(function() {
  toggleSendButton();
  loadPreviousMessages();
  loadAllTasks(); 
  $("#send-btn").on('click', function() {
    sendMessage();
  });
  $("#user-input").on('keyup', toggleSendButton);
  $("#user-input").on('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
          e.preventDefault();
          sendMessage();
      }
  });
  $("#task-search").on("keyup", function() {
    let value = $(this).val().toLowerCase();
    $(".task-item").filter(function() {
      $(this).toggle($(this).find(".task-title").text().toLowerCase().indexOf(value) > -1);
    });
  });


});

        function loadPreviousMessages() {
            $.ajax({
                type: 'GET',
                url: '/get-all-messages',
                dataType: 'json',
                success(data) {
                    data.forEach(message => displayMessage(message.content, message.role));
                    scrollToBottom();
                },
                error(error) {
                    console.error("Error fetching previous messages:", error);
                }
            });
        }

function getStatusBadgeHTML(status) {
    switch (status) {
        case 'ongoing':
            return `<span class="status-badge inline-block bg-yellow-300 rounded-full px-2 py-1 text-xs font-semibold text-gray-700 mr-2 ml-2">Ongoing</span>`;
        case 'completed':
            return `<span class="status-badge inline-block bg-green-300 rounded-full px-2 py-1 text-xs font-semibold text-gray-700 mr-2 ml-2">Completed</span>`;
        case 'error':
            return `<span class="status-badge inline-block bg-red-400 rounded-full px-2 py-1 text-xs font-semibold text-white mr-2 ml-2">Error</span>`;
        default:
            return `<span class="status-badge inline-block bg-gray-400 rounded-full px-2 py-1 text-xs font-semibold text-white mr-2 ml-2">Unknown</span>`;
    }
}

function displayTaskWithStatus(taskDescription, status, skillType = "Unknown Skill", taskId, output = null) {
    let statusBadgeHTML = getStatusBadgeHTML(status);

    let skillBadgeHTML = '';
    if (skillType) {
        skillBadgeHTML = `<span class="inline-block bg-purple-300 rounded-full px-2 py-1 text-xs font-semibold text-gray-700 ml-2">${skillType}</span>`;
    }

    let outputHTML = output ? `<p>${output}</p>` : '<p><small>No output yet...</small></p>';

    const taskHTML = `
         <div class="task-item" data-task-id="${taskId}">
             <span class="task-title">${taskDescription}</span></br>
             <span class="toggle-output-icon" style="cursor: pointer;">▶</span> 
             ${statusBadgeHTML}${skillBadgeHTML}
             <div class="task-output hidden">
                 ${outputHTML}
             </div>
         </div>`;
    $("#task-list").prepend(taskHTML);
}


function updateTaskStatus(taskId, status, output) {
    const $taskToUpdate = $(`#task-list > .task-item[data-task-id="${taskId}"]`);
    
    // Remove the existing status badge
    $taskToUpdate.find(".status-badge").remove();
    
    // Insert the new status badge right before the skill badge
    $taskToUpdate.find(".toggle-output-icon").after(getStatusBadgeHTML(status));
    
    // Update output, if available
    const $outputContainer = $taskToUpdate.find(".task-output");
    if (output) {
        $outputContainer.html(`<p>${output}</p>`);
    } else {
        $outputContainer.find("p").text("No output yet...");
    }
}

function loadAllTasks() {
    $.ajax({
        type: 'GET',
        url: '/get-all-tasks',
        dataType: 'json',
        success(data) {
            console.log("Debug: Received tasks:", data);  // Debug print
            data.forEach(task => {
                const description = task.description || '';
                const status = task.status || '';
                const skill_used = task.skill_used || '';
                const task_id = task.task_id || '';
                const output = task.output || null;  // Get the output, if it exists, otherwise set to null
                displayTaskWithStatus(description, status, skill_used, task_id, output);
            });
        },
        error(error) {
            console.error("Error fetching all tasks:", error);
        }
    });
}






$(document).on('click', '.toggle-output-icon', function() {
    const $task = $(this).closest(".task-item");
    const $output = $task.find(".task-output");
    $output.toggleClass('hidden');
    // Change the icon when the output is toggled
    const icon = $(this);
    if ($output.hasClass('hidden')) {
        icon.text('▶'); // Icon indicating the output is hidden
    } else {
        icon.text('▼'); // Icon indicating the output is shown
    }
});
