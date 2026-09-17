// Register View
function renderRegister(app) {
    if (app.state.user) {
        window.location.hash = '#/dashboard';
        return;
    }

    const html = `
        <div style="max-width: 420px; margin: 3rem auto;">
            <header style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">🌊</div>
                <h1 style="margin: 0;">Create account</h1>
                <p style="color: var(--muted-color); margin: 0.5rem 0 0;">Start your periodized swim plan</p>
            </header>
            <form id="register-form" class="card" style="padding: 1.5rem;">
                <div style="margin-bottom: 1rem;">
                    <label for="reg-name">Full name</label>
                    <input type="text" id="reg-name" name="full_name" required autocomplete="name" placeholder="Alex Rivera">
                </div>
                <div style="margin-bottom: 1rem;">
                    <label for="reg-email">Email</label>
                    <input type="email" id="reg-email" name="email" required autocomplete="email" placeholder="you@example.com">
                </div>
                <div style="margin-bottom: 1.5rem;">
                    <label for="reg-password">Password (min 8 characters)</label>
                    <input type="password" id="reg-password" name="password" required minlength="8" autocomplete="new-password" placeholder="••••••••">
                </div>
                <button type="submit" class="primary" id="register-submit" style="width: 100%;">Create account</button>
                <p style="text-align: center; margin: 1rem 0 0; font-size: 0.875rem; color: var(--muted-color);">
                    Already have an account? <a href="#/login">Log in</a>
                </p>
            </form>
        </div>
    `;

    document.getElementById('app').innerHTML = html;

    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('register-submit');
        const fullName = document.getElementById('reg-name').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;
        if (!fullName || !email || !password) {
            app.showError('Please complete all fields.');
            return;
        }
        if (password.length < 8) {
            app.showError('Password must be at least 8 characters.');
            return;
        }
        btn.disabled = true;
        btn.textContent = 'Creating…';
        try {
            await api.register(email, password, fullName);
            await app.checkAuth();
            window.location.hash = '#/onboarding';
        } catch (err) {
            app.showError(err.message || 'Registration failed');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Create account';
        }
    });
}

window.renderRegister = renderRegister;
