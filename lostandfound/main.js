document.addEventListener('DOMContentLoaded', function() {
    const notificationsLink = document.getElementById('notifications-link');
    const notificationsDropdown = document.getElementById('notifications-dropdown');
    const notificationBadge = document.getElementById('notification-count');

    // Toggle dropdown visibility
    if (notificationsLink) {
        notificationsLink.addEventListener('click', function(event) {
            event.preventDefault();
            notificationsDropdown.classList.toggle('show');
        });
    }

    // Function to fetch and render notifications
    function fetchNotifications() {
        fetch('/api/notifications/') // Use the URL for your notification endpoint
            .then(response => response.json())
            .then(data => {
                const notifications = data.notifications;
                if (notifications.length > 0) {
                    let html = '';
                    notifications.forEach(notif => {
                        html += `<a href="${notif.url}" class="notification-item">${notif.message}</a>`;
                    });
                    notificationsDropdown.innerHTML = html;
                    notificationBadge.textContent = data.count;
                    notificationBadge.style.display = 'block';
                } else {
                    notificationsDropdown.innerHTML = `<div class="no-notifications-text">No new notifications.</div>`;
                    notificationBadge.style.display = 'none';
                }
            })
            .catch(error => console.error('Error fetching notifications:', error));
    }

    // Fetch notifications on page load
    fetchNotifications();
    // Fetch notifications every 60 seconds
    setInterval(fetchNotifications, 60000); 

    // Front-end Form Validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Check required fields, email format, etc.
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = 'red';
                    isValid = false;
                } else {
                    field.style.borderColor = '#D9D9D9';
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                alert('Please fill out all required fields.');
            }
        });
    });
});