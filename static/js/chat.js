document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("uploadForm");
  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const formData = new FormData(form);
      const statusBox = document.getElementById("uploadStatus");
      statusBox.innerHTML = '<div class="alert alert-info">Uploading...</div>';

      const res = await fetch("/api/upload/", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (res.ok) {
        statusBox.innerHTML = `<div class="alert alert-success">Uploaded successfully. Redirecting...</div>`;
        setTimeout(() => {
          window.location.href = `/doc/${data.id}/`;
        }, 1000);
      } else {
        statusBox.innerHTML = `<div class="alert alert-danger">${data.error || "Upload failed"}</div>`;
      }
    });
  }
});

async function sendChat(docId) {
  const input = document.getElementById("chatInput");
  const chatBox = document.getElementById("chatBox");
  const message = input.value.trim();
  if (!message) return;

  chatBox.innerHTML += `
    <div class="chat-msg user">
      <div class="chat-bubble">${message}</div>
    </div>
  `;

  input.value = "";

  const res = await fetch(`/api/chat/${docId}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message })
  });

  const data = await res.json();

  chatBox.innerHTML += `
    <div class="chat-msg bot">
      <div class="chat-bubble">${data.reply || "No response"}</div>
    </div>
  `;

  chatBox.scrollTop = chatBox.scrollHeight;
}