// Login View
function renderLogin(app) {
    if (app.state.user) {
        window.location.hash = '#/dashboard';
        return;
    }

    const html = `
        <div style="max-width: 420px; margin: 3rem auto;">
            <header style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">🏊</div>
                <h1 style="margin: 0;">Welcome back</h1>
                <p style="color: var(--muted-color); margin: 0.5rem 0 0;">Log in to continue training</p>
            </header>
            <form id="login-form" class="card" style="padding: 1.5rem;">
                <div style="margin-bottom: 1rem;">
                    <label for="login-email">Email</label>
                    <input type="email" id="login-email" name="email" required autocomplete="email" placeholder="you@example.com">
                </div>
                <div style="margin-bottom: 1.5rem;">
                    <label for="login-password">Password</label>
                    <input type="password" id="login-password" name="password" required autocomplete="current-password" placeholder="••••••••">
                </div>
                <button type="submit" class="primary" id="login-submit" style="width: 100%;">Log in</button>
                <p style="text-align: center; margin: 1rem 0 0; font-size: 0.875rem; color: var(--muted-color);">
                    No account? <a href="#/register">Create one</a>
                </p>
            </form>
        </div>
    `;

    document.getElementById('app').innerHTML = html;

    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('login-submit');
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        if (!email || !password) {
            app.showError('Please enter email and password.');
            return;
        }
        btn.disabled = true;
        btn.textContent = 'Logging in…';
        try {
            await api.login(email, password);
            await app.checkAuth();
            window.location.hash = '#/dashboard';
        } catch (err) {
            app.showError(err.message || 'Login failed');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Log in';
        }
    });
}

window.renderLogin = renderLogin;
