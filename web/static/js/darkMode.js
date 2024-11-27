// Function to toggle dark mode and save preference
function toggleDarkMode() {
    const body = document.body;

    // Toggle the dark-mode class
    body.classList.toggle('dark-mode');

    // Save the preference to localStorage
    if (body.classList.contains('dark-mode')) {
        localStorage.setItem('darkMode', 'enabled');
    } else {
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Apply dark mode on page load based on saved preference
document.addEventListener('DOMContentLoaded', () => {
    const darkModePreference = localStorage.getItem('darkMode');
    if (darkModePreference === 'enabled') {
        document.body.classList.add('dark-mode');
    }
});