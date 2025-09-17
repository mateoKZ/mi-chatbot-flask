// static/script.js
document.addEventListener("DOMContentLoaded", () => {
    // Referencias a los elementos de Pre-Chat
    const preChatContainer = document.getElementById("pre-chat-container");
    const phoneInput = document.getElementById("phone-input");
    const startChatButton = document.getElementById("start-chat-button");

    // Referencias a los elementos del Chat
    const chatContainer = document.getElementById("chat-container");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
    const chatMessages = document.getElementById("chat-messages");

    let currentUserPhone = null; // Variable para guardar el teléfono del usuario en sesión

    startChatButton.addEventListener("click", () => {
        const phoneNumber = phoneInput.value.trim();
        
        // --- ¡NUEVA VALIDACIÓN CON REGEX! ---
        // Este Regex busca una cadena que contenga solo dígitos y tenga entre 11 y 15 caracteres.
        const phoneRegex = /^\d{11,15}$/;
        
        if (!phoneRegex.test(phoneNumber)) {
            alert("Por favor, ingresa un número de teléfono válido.\nDebe contener solo números, incluyendo el código de país (ej: 5491122334455).");
            return;
        }
        // --- FIN DE LA VALIDACIÓN ---
    
        currentUserPhone = phoneNumber;
        preChatContainer.style.display = "none";
        chatContainer.style.display = "flex";
    });

    // Lógica para enviar un mensaje
    const sendMessage = async () => {
        const messageText = messageInput.value.trim();
        if (messageText === "" || currentUserPhone === null) {
            return;
        }

        addMessage(messageText, "user");
        messageInput.value = "";

        try {
            // ¡MODIFICADO! Ahora enviamos el mensaje, el teléfono y el origen
            const response = await fetch('https://mi-chatbot-mateo.onrender.com/webhook', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: messageText,
                    user_phone: currentUserPhone,
                    origin: 'web'
                }),
            });

            if (!response.ok) throw new Error('La respuesta de la red no fue correcta.');

            const data = await response.json();
            const botReply = data.response;
            addMessage(botReply, "bot");

        } catch (error) {
            console.error("Hubo un error al contactar al servidor:", error);
            addMessage("Lo siento, no puedo conectarme con mi cerebro en este momento.", "bot");
        }
    };
    
    // (La función addMessage no cambia)
    const addMessage = (text, sender) => {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender);
        messageElement.textContent = text;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    sendButton.addEventListener("click", sendMessage);
    messageInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") sendMessage();
    });
});