/**
 * GreenBot - Chatbot Widget for Greenfield University
 * Features: Typing effect, session management, streaming responses
 */

const API_BASE = window.location.origin + "/api";
let sessionId = localStorage.getItem("gu_chat_session") || null;

// DOM Elements
const chatWindow = document.getElementById("chat-window");
const chatToggle = document.getElementById("chat-toggle");
const chatClose = document.getElementById("chat-close");
const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const chatNotif = document.querySelector(".chat-notif");

// Toggle chat window
chatToggle.addEventListener("click", () => {
  chatWindow.classList.toggle("chat-hidden");
  if (chatNotif) chatNotif.style.display = "none";
});
chatClose.addEventListener("click", () => chatWindow.classList.add("chat-hidden"));

// Send message on Enter
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
chatSend.addEventListener("click", sendMessage);

function addMessage(role, content, sources = []) {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("msg", role === "user" ? "user-msg" : "bot-msg");

  const bubble = document.createElement("div");
  bubble.classList.add("msg-bubble");

  if (role === "assistant") {
    // Render markdown-like formatting
    bubble.innerHTML = formatMessage(content);
    if (sources && sources.length > 0) {
      const srcDiv = document.createElement("div");
      srcDiv.classList.add("msg-sources");
      srcDiv.textContent = `📄 Sources: ${sources.join(", ")}`;
      msgDiv.appendChild(bubble);
      msgDiv.appendChild(srcDiv);
      chatMessages.appendChild(msgDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      return;
    }
  } else {
    bubble.textContent = content;
  }

  msgDiv.appendChild(bubble);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(text) {
  // Basic markdown-like formatting
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n\n/g, "<br/><br/>")
    .replace(/\n/g, "<br/>")
    .replace(/•/g, "•");
}

function addTypingIndicator() {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("msg", "bot-msg");
  msgDiv.id = "typing-indicator";

  const bubble = document.createElement("div");
  bubble.classList.add("msg-bubble");
  bubble.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;

  msgDiv.appendChild(bubble);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.getElementById("typing-indicator");
  if (indicator) indicator.remove();
}

async function typeText(element, text, speed = 15) {
  /** Typing effect for bot responses */
  element.innerHTML = "";
  const formatted = formatMessage(text);
  // Use a temporary div to strip tags for character-by-character typing
  const temp = document.createElement("div");
  temp.innerHTML = formatted;
  const plainText = temp.textContent || text;

  let i = 0;
  return new Promise((resolve) => {
    const interval = setInterval(() => {
      if (i < plainText.length) {
        // Type raw text
        element.textContent += plainText[i];
        i++;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      } else {
        // Replace with formatted version once done
        element.innerHTML = formatted;
        clearInterval(interval);
        resolve();
      }
    }, speed);
  });
}

async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message) return;

  chatInput.value = "";
  chatInput.disabled = true;
  chatSend.disabled = true;

  // Add user message
  addMessage("user", message);

  // Add typing indicator
  addTypingIndicator();

  try {
    const response = await fetch(`${API_BASE}/chat/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const data = await response.json();

    // Save session ID
    if (data.session_id) {
      sessionId = data.session_id;
      localStorage.setItem("gu_chat_session", sessionId);
    }

    removeTypingIndicator();

    // Add bot message with typing effect
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("msg", "bot-msg");
    const bubble = document.createElement("div");
    bubble.classList.add("msg-bubble");
    msgDiv.appendChild(bubble);

    if (data.sources && data.sources.length > 0) {
      const srcDiv = document.createElement("div");
      srcDiv.classList.add("msg-sources");
      srcDiv.textContent = `📄 Sources: ${data.sources.join(", ")}`;
      chatMessages.appendChild(msgDiv);
      chatMessages.appendChild(srcDiv);
    } else {
      chatMessages.appendChild(msgDiv);
    }

    // Typing effect
    await typeText(bubble, data.response);
    chatMessages.scrollTop = chatMessages.scrollHeight;

  } catch (error) {
    removeTypingIndicator();
    addMessage(
      "assistant",
      "I'm having trouble connecting right now. Please try again in a moment, or contact us directly at info@greenfield.edu"
    );
    console.error("Chat error:", error);
  } finally {
    chatInput.disabled = false;
    chatSend.disabled = false;
    chatInput.focus();
  }
}

// Quick suggestion chips
const SUGGESTIONS = [
  "What are the admission requirements?",
  "What programs do you offer?",
  "How much is tuition?",
  "Check my application APP-2024-001",
  "Do you offer scholarships?",
  "What is the application deadline?",
];

// Add suggestion chips to chat
function addSuggestions() {
  const container = document.createElement("div");
  container.style.cssText = "display:flex;flex-wrap:wrap;gap:0.4rem;padding:0.5rem 0;";

  SUGGESTIONS.slice(0, 3).forEach((suggestion) => {
    const chip = document.createElement("button");
    chip.textContent = suggestion;
    chip.style.cssText = `
      padding: 0.35rem 0.75rem;
      border-radius: 100px;
      border: 1.5px solid #2d6a9f;
      background: transparent;
      color: #2d6a9f;
      font-size: 0.78rem;
      cursor: pointer;
      transition: all 0.15s;
      font-family: 'DM Sans', sans-serif;
    `;
    chip.addEventListener("mouseenter", () => {
      chip.style.background = "#2d6a9f";
      chip.style.color = "white";
    });
    chip.addEventListener("mouseleave", () => {
      chip.style.background = "transparent";
      chip.style.color = "#2d6a9f";
    });
    chip.addEventListener("click", () => {
      chatInput.value = suggestion;
      container.remove();
      sendMessage();
    });
    container.appendChild(chip);
  });

  chatMessages.appendChild(container);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initialize suggestions
setTimeout(addSuggestions, 500);
