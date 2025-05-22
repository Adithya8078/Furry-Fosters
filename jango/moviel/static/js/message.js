const currentUserId = '{{ request.user.id }}';
let currentPetId = null;
let currentRecipientId = null;

function toggleExpand() {
    const container = document.getElementById('messages-container');
    const button = document.getElementById('expand-button');
    const isExpanded = container.style.display !== 'none';
    
    container.style.display = isExpanded ? 'none' : 'block';
    button.innerHTML = isExpanded ? 
        '<i class="fas fa-chevron-up"></i>' : 
        '<i class="fas fa-chevron-down"></i>';
}

function openChat(username, avatar, petId, recipientId) {
    if (!petId) {
        console.error('Pet ID is missing');
        return;
    }

    document.getElementById('messages-list').style.display = 'none';
    document.getElementById('chat-view').style.display = 'flex';
    document.getElementById('chat-username').textContent = username;
    document.getElementById('chat-avatar').textContent = avatar;

    currentPetId = petId;
    currentRecipientId = recipientId;

    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = ''; // Clear existing messages

    // Ensure the URL is correctly formed
    fetch(`/fetch-chat/${petId}/${recipientId}/`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.messages) {
            const chatMessages = document.getElementById('chat-messages');
              // Clear existing messages

            data.messages.forEach(message => {
                const messageDiv = document.createElement('div');
                messageDiv.className = message.sender === currentUserId ? 
                    'message-outgoing' : 'message-incoming';
                messageDiv.innerHTML = `<div class="message-bubble">${message.content}</div>`;
                chatMessages.appendChild(messageDiv);
            });

            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    })
    .catch(error => {
        console.error('Error fetching chat:', error);
    });

}


function sendChatMessage() {
    if (!currentPetId || !currentRecipientId) {
        alert("Pet or recipient information is missing.");
        return;
    }

    const input = document.getElementById('message-input');
    const content = input.value.trim();
    if (!content) return;

    const chatMessages = document.getElementById('chat-messages');
    const newMessage = document.createElement('div');
    newMessage.className = 'message-outgoing';
    newMessage.innerHTML = `<div class="message-bubble">${content}</div>`;
    chatMessages.appendChild(newMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    input.value = '';

    fetch(`/send-message/${currentPetId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `content=${encodeURIComponent(content)}&recipient_id=${currentRecipientId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // After successfully sending, re-fetch the chat messages
            fetch(`/fetch-chat/${currentPetId}/${currentRecipientId}/`)
    .then(response => {
        console.log(response); // Log the response to verify its structure
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log(data); // Log the data for further debugging
        if (data.success && data.messages) {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = '';  // Clear existing messages
            data.messages.forEach(message => {
                const messageDiv = document.createElement('div');
                messageDiv.className = message.sender === currentUserId ? 
                    'message-outgoing' : 'message-incoming';
                messageDiv.innerHTML = `<div class="message-bubble">${message.content}</div>`;
                chatMessages.appendChild(messageDiv);
            });

            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    })
    .catch(error => {
        console.error('Error fetching chat:', error);
    });
        } else {
            chatMessages.removeChild(newMessage);
            alert('Failed to send message');
        }
    })
    .catch(error => {
        chatMessages.removeChild(newMessage);
        console.error('Error:', error);
    });
}

function closeChat() {
    document.getElementById('chat-view').style.display = 'none';
    document.getElementById('messages-list').style.display = 'block';
}

// Add event listener for Enter key
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendChatMessage();
    }
});