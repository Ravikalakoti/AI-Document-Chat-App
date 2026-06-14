document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("uploadForm");

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(form);
      const statusBox = document.getElementById("uploadStatus");

      statusBox.innerHTML =
        '<div class="alert alert-info">Uploading...</div>';

      try {
        const res = await fetch("/api/upload/", {
          method: "POST",

          credentials: "same-origin", // 🔥 VERY IMPORTANT

          headers: {
            "X-CSRFToken": getCookie("csrftoken")
          },

          body: formData
        });

        const data = await res.json();

        if (res.ok) {
          statusBox.innerHTML =
            '<div class="alert alert-success">Uploaded successfully. Redirecting...</div>';

          setTimeout(() => {
            window.location.href = `/doc/${data.id}/`;
          }, 1000);

        } else {
          statusBox.innerHTML =
            `<div class="alert alert-danger">${data.error || "Upload failed"}</div>`;
        }

      } catch (err) {
        console.error(err);
        statusBox.innerHTML =
          '<div class="alert alert-danger">Server error</div>';
      }
    });
  }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// async function sendChat(docId) {
//   const input = document.getElementById("chatInput");
//   const chatBox = document.getElementById("chatBox");
//   const message = input.value.trim();
//   if (!message) return;

//   chatBox.innerHTML += `
//     <div class="chat-msg user">
//       <div class="chat-bubble">${message}</div>
//     </div>
//   `;

//   input.value = "";

//   const res = await fetch(`/api/chat/${docId}/`, {
//     method: "POST",
//     credentials: "include",   // 🔥 IMPORTANT

//     headers: {
//       "Content-Type": "application/json",
//       "X-CSRFToken": getCookie("csrftoken")   // 🔥 THIS FIXES ERROR
//     },

//     body: JSON.stringify({ message })
//   });

//   const data = await res.json();
//   chatBox.innerHTML += `
//     <div class="chat-msg bot">
//       <div class="chat-bubble">${data.reply || "No response"}</div>
//     </div>
//   `;

//   chatBox.scrollTop = chatBox.scrollHeight;
// }