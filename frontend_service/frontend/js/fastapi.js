const authAPIUrl = 'http://localhost/api/v1/auth';
const moviesAPIUrl = 'http://localhost/api/v1';

document.getElementById('register-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    const response = await fetch(`${authAPIUrl}/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    if (response.ok) {
        alert('User registered');
    } else {
        alert(`Error: ${data.detail}`);
    }
});

document.getElementById('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    const response = await fetch(`${authAPIUrl}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    if (data.access_token) {
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        alert('Login successful');
        loadFilms();
    } else {
        alert('Login failed');
    }
});

document.getElementById('logout-btn').addEventListener('click', async () => {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        alert('You are already logged out');
        return;
    }

    try {
        const response = await fetch(`${authAPIUrl}/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            }
        });

        if (response.ok) {
            localStorage.removeItem('accessToken');
            alert('Logged out successfully');
            loadFilms();
        } else {
            const errorData = await response.json();
            alert(`Logout failed: ${errorData.detail}`);
        }
    } catch (error) {
        console.error('Logout error:', error);
        alert('Logout request failed');
    }
});

document.getElementById('refresh-btn').addEventListener('click', async () => {
    const refresh_token = localStorage.getItem('refreshToken');
    const response = await fetch(`${authAPIUrl}/refresh`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${refresh_token}`
        }
    });

    const data = await response.json();
    if (data.access_token) {
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        alert('Token refreshed');
    } else {
        alert('Token refresh failed');
    }
});

document.getElementById('change-credentials-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const access_token = localStorage.getItem('accessToken');
    const newEmail = document.getElementById('new-email').value;
    const newPassword = document.getElementById('new-password').value;
    const oldPassword = document.getElementById('old-password').value;

    const requestBody = {};
    if (newEmail) requestBody.email = newEmail;
    if (newPassword) requestBody.password = newPassword;
    if (Object.keys(requestBody).length === 0) {
        alert('Please fill at least one field to update credentials.');
        return;
    }
    if (oldPassword) requestBody.old_password = oldPassword;

    try {
        const response = await fetch(`${authAPIUrl}/change-credentials`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (response.ok) {
            if (data.access_token) {
                localStorage.setItem('accessToken', data.access_token);
            }
            alert('Credentials updated successfully');
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Request failed');
    }
});

document.getElementById('login-history-btn').addEventListener('click', async () => {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        alert('You need to log in first');
        return;
    }

    try {
        const response = await fetch(`${authAPIUrl}/login-history`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            renderHistory(data);
        } else {
            const errorData = await response.json();
            alert(`Failed to fetch history: ${errorData.detail}`);
        }
    } catch (error) {
        console.error('History fetch error:', error);
        alert('Failed to retrieve login history');
    }
});

function renderHistory(history) {
    const output = document.getElementById('history-output');

    if (!history.length) {
        output.innerHTML = '<p>No login history available.</p>';
        return;
    }

    const table = document.createElement('table');
    table.classList.add('history-table');

    table.innerHTML = `
        <tr>
            <th>Login Time</th>
            <th>IP Address</th>
            <th>Action</th>
        </tr>
    `;

    history.forEach(entry => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${new Date(entry.login_time).toLocaleString()}</td>
            <td>${entry.ip_address || 'Unknown'}</td>
            <td>${entry.action}</td>
        `;
        table.appendChild(row);
    });

    output.innerHTML = '';
    output.appendChild(table);
}

let currentPage = 0;
let pageSize = 10;

async function fetchData(endpoint, page = 0, size = 10) {
    const accessToken = localStorage.getItem('accessToken');
    const url = new URL(`${moviesAPIUrl}/${endpoint}`);

    url.searchParams.set('page_number', page * size);
    url.searchParams.set('page_size', size);

    const response = await fetch(url, {
        headers: accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}
    });

    if (!response.ok) {
        throw new Error('Failed to fetch data');
    }

    return response.json();
}

async function loadFilms(page=0, size=10) {
    const films = await fetchData('films', page, size);
    renderList(films, 'films-output');

    document.getElementById('current-page').textContent = `Page ${page + 1}`;
    document.getElementById('prev-page').disabled = page === 0;
    document.getElementById('next-page').disabled = films.length < size;
}

function renderList(items, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = items.length ?
        `<ul>${items.map(item => `
            <li>
                <strong>${item.title || item.name}</strong>
                ${item.labels && item.labels.length > 0 ? `<p>Tags: ${item.labels.join(', ')}</p>` : ''}
            </li>
        `).join('')}</ul>` :
        '<p>No data available</p>';
}

document.getElementById('prev-page').addEventListener('click', () => {
    if (currentPage > 0) {
        currentPage--;
        loadFilms(currentPage, pageSize);
    }
});

document.getElementById('next-page').addEventListener('click', () => {
    currentPage++;
    loadFilms(currentPage, pageSize);
});

document.addEventListener('DOMContentLoaded', () => {
    loadFilms(currentPage, pageSize);
});
