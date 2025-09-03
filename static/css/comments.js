function toggleComments() {
    const section = document.getElementById('comment-section');
    const btn = document.getElementById('toggle-comments-btn');
    if (section.style.display === "none") {
        section.style.display = "block";
        btn.innerText = "Hide Comments";
    } else {
        section.style.display = "none";
        btn.innerText = "Show Comments";
    }
}

function toggleReplyForm(commentId) {
    const form = document.getElementById('reply-form-' + commentId);
    form.style.display = (form.style.display === "none") ? "block" : "none";
}
