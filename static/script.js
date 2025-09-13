// Espera a que todo el contenido de la página se cargue antes de ejecutar el script
document.addEventListener("DOMContentLoaded", () => {
    // Obtenemos referencias a los elementos del HTML que vamos a usar
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
    const chatMessages = document.getElementById("chat-messages");

    // Función para enviar el mensaje
    const sendMessage = async () => {
        const messageText = messageInput.value.trim();

        // Si el mensaje está vacío, no hacemos nada
        if (messageText === "") {
            return;
        }

        // 1. Muestra el mensaje del usuario en la ventana de chat
        addMessage(messageText, "user");
        messageInput.value = ""; // Limpia el campo de entrada

        try {
            // 2. Envía el mensaje a la API de Flask
            const response = await fetch('https://mi-chatbot-mateo.onrender.com/webhook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }), // Envía el mensaje en formato JSON
            });

            if (!response.ok) {
                throw new Error('La respuesta de la red no fue correcta.');
            }

            const data = await response.json();
            const botReply = data.response;

            // 3. Muestra la respuesta del bot en la ventana de chat
            addMessage(botReply, "bot");

        } catch (error) {
            console.error("Hubo un error al contactar al servidor:", error);
            addMessage("Lo siento, no puedo conectarme con mi cerebro en este momento.", "bot");
        }
    };

    // Función auxiliar para agregar mensajes a la ventana del chat
    const addMessage = (text, sender) => {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender); // Añade las clases 'message' y 'user' o 'bot'
        messageElement.textContent = text;
        chatMessages.appendChild(messageElement);

        // Hace scroll hacia abajo automáticamente para ver el último mensaje
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Asigna el evento 'click' al botón de enviar
    sendButton.addEventListener("click", sendMessage);

    // Permite enviar el mensaje también presionando la tecla "Enter"
    messageInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
});