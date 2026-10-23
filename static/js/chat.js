const chatForm = document.getElementById("chat-form");
const questionInput = document.getElementById("question-input");
const messagesContainer = document.getElementById("messages");
const welcomeSection = document.getElementById("welcome");
const loadingIndicator = document.getElementById("loading");
const sendButton = document.getElementById("send-button");
const errorMessage = document.getElementById("error-message");

let isWaiting = false;

if (window.marked) {
    marked.setOptions({
        gfm: true,
        breaks: true
    });
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
}

function clearError() {
    errorMessage.textContent = "";
    errorMessage.hidden = true;
}

function setLoading(loading) {
    isWaiting = loading;
    loadingIndicator.hidden = !loading;
    sendButton.disabled = loading;
    questionInput.disabled = loading;

    if (loading) {
        sendButton.querySelector("span:first-child").textContent = "Sending";
    } else {
        sendButton.querySelector("span:first-child").textContent = "Send";
    }
}

function addUserMessage(question) {
    const wrapper = document.createElement("article");
    wrapper.className = "message user";

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = "You";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = question;

    wrapper.append(label, bubble);
    messagesContainer.appendChild(wrapper);
}

function cleanMarkdown(text) {
    // Some model responses contain escaped Markdown characters.
    // Normalize these so bullets and bold headings render correctly.
    return String(text || "")
        .replace(/\\([*_`#])/g, "$1");
}

function renderAnswer(text) {
    const normalized = cleanMarkdown(text);

    if (window.marked && window.DOMPurify) {
        const rawHtml = marked.parse(normalized);
        return DOMPurify.sanitize(rawHtml);
    }

    // Safe fallback if the Markdown libraries are unavailable.
    const escaped = normalized
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    return escaped.replace(/\n/g, "<br>");
}

function makeSourceUrl(documentName, pageNumber) {
    const safeFilename = encodeURIComponent(documentName);
    const page = Number.parseInt(pageNumber, 10);

    let url = `/documents/${safeFilename}`;

    if (Number.isInteger(page) && page > 0) {
        url += `#page=${page}`;
    }

    return url;
}

function addSources(parent, sources, grounded) {
    if (!Array.isArray(sources) || sources.length === 0) {
        const note = document.createElement("p");
        note.className = "grounding-note";
        note.textContent = grounded
            ? "No source links were returned for this answer."
            : "The supplied documents did not provide enough evidence for a grounded answer.";
        parent.appendChild(note);
        return;
    }

    const panel = document.createElement("section");
    panel.className = "sources-panel";

    const title = document.createElement("div");
    title.className = "sources-title";
    title.textContent = `📚 Sources (${sources.length})`;
    panel.appendChild(title);

    sources.forEach((source) => {
        const filename = source.document || source.source || "";
        const page = Number.parseInt(source.page, 10);

        if (!filename) return;

        const link = document.createElement("a");
        link.className = "source-link";
        link.href = makeSourceUrl(filename, page);
        link.target = "_blank";
        link.rel = "noopener noreferrer";

        const name = document.createElement("span");
        name.className = "source-name";
        name.textContent = filename;

        const pageLabel = document.createElement("span");
        pageLabel.className = "source-page";
        pageLabel.textContent = Number.isInteger(page) && page > 0
            ? `PDF page ${page} ↗`
            : "Open PDF ↗";

        link.append(name, pageLabel);
        panel.appendChild(link);
    });

    parent.appendChild(panel);
}

function addAssistantMessage(data) {
    const wrapper = document.createElement("article");
    wrapper.className = "message assistant";

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = "Cedarhaven Assistant";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML = renderAnswer(data.answer || "Sorry, no answer was returned.");

    wrapper.append(label, bubble);

    addSources(
        wrapper,
        data.sources,
        data.grounded
    );

    messagesContainer.appendChild(wrapper);
}

async function askQuestion(rawQuestion) {
    const question = String(rawQuestion || "").trim();

    if (!question || isWaiting) return;

    clearError();
    welcomeSection.hidden = true;

    addUserMessage(question);
    questionInput.value = "";
    questionInput.style.height = "auto";

    setLoading(true);
    messagesContainer.scrollIntoView({
        behavior: "smooth",
        block: "end"
    });

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            // Include both common key names for compatibility with
            // Flask handlers that read either "question" or "message".
            body: JSON.stringify({
                question: question,
                message: question
            })
        });

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error("The server returned an invalid response. Check the Flask terminal.");
        }

        if (!response.ok) {
            throw new Error(
                data.error || data.message || `Request failed (${response.status}).`
            );
        }

        if (typeof data.answer !== "string") {
            throw new Error("The server response does not contain an answer field. Check the /chat endpoint.");
        }

        addAssistantMessage(data);

    } catch (error) {
        showError(
            `${error.message || "Something went wrong."} Please check that the Flask app is running and try again.`
        );
    } finally {
        setLoading(false);
        questionInput.disabled = false;
        questionInput.focus();

        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: "smooth"
        });
    }
}

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!isWaiting) {
        askQuestion(questionInput.value);
    }
});

document.querySelectorAll(".suggestion-chip").forEach((button) => {
    button.addEventListener("click", () => {
        askQuestion(button.dataset.question);
    });
});

questionInput.addEventListener("input", () => {
    questionInput.style.height = "auto";
    questionInput.style.height = `${Math.min(questionInput.scrollHeight, 140)}px`;
});

questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});