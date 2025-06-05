document.addEventListener("DOMContentLoaded", () => {
    // Helper to bind reply and toggle logic to a comment element
    function bindCommentLogic(commentElement) {
      let toggleBtn = commentElement.querySelector(".toggle-replies");
      const replyBtn = commentElement.querySelector(".reply-btn");
      let replies = commentElement.querySelector(".replies");
  
      // Hide toggle if replies are empty or missing
      if (toggleBtn && (!replies || replies.children.length === 0)) {
        toggleBtn.style.display = "none";
      }
  
      if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
          replies.classList.toggle("expanded");
          toggleBtn.textContent = replies.classList.contains("expanded")
            ? "Hide Replies"
            : "Show Replies";
        });
      }
  
      if (replyBtn) {
        replyBtn.addEventListener("click", () => {
          // Prevent multiple forms
          if (commentElement.querySelector(".reply-form")) return;
  
          const form = document.createElement("form");
          form.className = "reply-form";
  
          const input = document.createElement("input");
          input.type = "text";
          input.placeholder = "Write a reply...";
          input.required = true;
  
          const submit = document.createElement("button");
          submit.type = "submit";
          submit.textContent = "Post";
  
          form.appendChild(input);
          form.appendChild(submit);
          commentElement.appendChild(form);
  
          form.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;
  
            // Create new comment
            const newComment = document.createElement("div");
            newComment.className = "comment";
            newComment.innerHTML = `
              <p>${text}</p>
              <button class="toggle-replies" style="display:none">Show Replies</button>
              <button class="reply-btn">Reply</button>
              <div class="replies"></div>
            `;
  
            // Get or create replies container
            let replies = commentElement.querySelector(".replies");
            if (!replies) {
              replies = document.createElement("div");
              replies.className = "replies expanded";
              commentElement.appendChild(replies);
  
              // Also add a toggle button if it doesn't exist
              toggleBtn = document.createElement("button");
              toggleBtn.className = "toggle-replies";
              toggleBtn.textContent = "Hide Replies";
              commentElement.insertBefore(toggleBtn, replyBtn);
  
              // Bind the toggle
              toggleBtn.addEventListener("click", () => {
                replies.classList.toggle("expanded");
                toggleBtn.textContent = replies.classList.contains("expanded")
                  ? "Hide Replies"
                  : "Show Replies";
              });
            } else {
              replies.classList.add("expanded");
  
              // Make sure existing toggle is visible
              if (toggleBtn) {
                toggleBtn.style.display = "inline";
              }
            }
  
            // Add new reply
            replies.appendChild(newComment);
            form.remove();
  
            // Bind logic to new reply
            bindCommentLogic(newComment);
          });
        });
      }
    }
  
    // Bind logic to all existing comments
    document.querySelectorAll(".comment").forEach(bindCommentLogic);
  });
  