// Authentication related JavaScript functions

async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    try {
        const response = await fetch('/login', {
            method: 'POST',
            body: formData,
            credentials: 'include' // Include cookies in the request
        });

        if (response.ok) {
            // Successful login, redirect to home page
            window.location.href = '/';
        } else {
            // Handle login error
            const errorDiv = document.getElementById('login-error');
            errorDiv.textContent = 'Email ou senha inválidos';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Error during login:', error);
    }
}

async function logout() {
    try {
        // Clear the auth cookie by setting it to expire
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
        // Redirect to home page
        window.location.href = '/';
    } catch (error) {
        console.error('Error during logout:', error);
    }
}

// Add event listener to handle 401 errors globally
document.addEventListener('DOMContentLoaded', () => {
    window.addEventListener('unhandledrejection', event => {
        if (event.reason?.response?.status === 401) {
            window.location.href = '/login';
        }
    });
});
