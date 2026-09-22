// SwimCoach Main App
class App {
    constructor() {
        this.state = {
            user: null,
            profile: null,
            competition: null,
            macrocycle: null,
            currentWeek: null,
            todaySession: null,
            tier: 'free'
        };
        this.currentRoute = null;
        this.init();
    }

    async init() {
        // Check for existing session
        await this.checkAuth();
        
        // Set up router
        window.addEventListener('hashchange', () => { this.handleRoute(); this.updateNav(); });
        window.addEventListener('load', () => this.handleRoute());

        // Bottom nav wiring
        document.querySelectorAll('#bottomnav .navbtn').forEach(btn => {
            btn.addEventListener('click', () => { window.location.hash = btn.dataset.route; });
        });
        
        // Handle install prompt
        this.setupInstallPrompt();

        // Preload ML models (silent fail -> heuristic/rules fallback)
        if (window.loadModel1) window.loadModel1();
        if (window.loadModel2) window.loadModel2();

        // Initial route
        this.handleRoute();
    }

    async checkAuth() {
        try {
            const user = await api.getMe();
            this.state.user = user;
            this.state.tier = user.subscription_tier || 'free';
            
            // Load profile and competition
            await this.loadProfile();
            await this.loadCompetition();
        } catch (error) {
            // Not authenticated
            this.state.user = null;
            this.state.tier = 'free';
        }
        this.updateNav();
    }

    async loadProfile() {
        try {
            this.state.profile = await api.getProfile();
        } catch (error) {
            this.state.profile = null;
        }
    }

    async loadCompetition() {
        try {
            this.state.competition = await api.getCompetition();
            if (this.state.competition) {
                await this.loadMacrocycle();
            }
        } catch (error) {
            this.state.competition = null;
            this.state.macrocycle = null;
        }
    }

    async loadMacrocycle() {
        try {
            this.state.macrocycle = await api.getMacrocycle();
        } catch (error) {
            this.state.macrocycle = null;
        }
    }

    updateNav() {
        const navLinks = document.getElementById('nav-links');
        if (navLinks) {
            navLinks.style.display = this.state.user ? 'flex' : 'none';
        }
        const bottom = document.getElementById('bottomnav');
        if (bottom) {
            const publicRoutes = ['#/login', '#/register', '#/onboarding'];
            const hash = window.location.hash || '#/dashboard';
            const isPublic = publicRoutes.some(r => hash.startsWith(r));
            bottom.style.display = (this.state.user && !isPublic) ? 'flex' : 'none';
            bottom.querySelectorAll('.navbtn').forEach(btn => {
                const route = btn.dataset.route;
                btn.classList.toggle('active', hash.startsWith(route));
            });
        }
    }

    setupInstallPrompt() {
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            this.showInstallButton(deferredPrompt);
        });
    }

    showInstallButton(deferredPrompt) {
        // Create install banner
        const banner = document.createElement('div');
        banner.id = 'install-banner';
        banner.className = 'container';
        banner.style.cssText = 'margin-top: 1rem; padding: 1rem; background: var(--primary); color: #06333b; border-radius: 14px; display: flex; justify-content: space-between; align-items: center;';
        banner.innerHTML = `
            <span>Install SwimCoach for offline access and notifications</span>
            <div>
                <button class="secondary" id="install-btn">Install</button>
                <button class="secondary" id="dismiss-install" style="margin-left: 0.5rem;">Dismiss</button>
            </div>
        `;
        
        const main = document.getElementById('app');
        main.insertBefore(banner, main.firstChild);
        
        document.getElementById('install-btn').addEventListener('click', async () => {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') {
                banner.remove();
            }
            deferredPrompt = null;
        });
        
        document.getElementById('dismiss-install').addEventListener('click', () => {
            banner.remove();
        });
    }

    // Routing
    handleRoute() {
        const hash = window.location.hash.slice(1) || '/dashboard';
        const [path, queryString] = hash.split('?');
        const query = new URLSearchParams(queryString);
        
        // Parse route with params
        const routes = {
            '/login': () => this.renderLogin(),
            '/register': () => this.renderRegister(),
            '/onboarding': () => this.renderOnboarding(),
            '/dashboard': () => this.renderDashboard(),
            '/macrocycle': () => this.renderMacrocycle(),
            '/week': (params) => this.renderWeek(params.get('start') || null),
            '/session': (params) => this.renderSession(params.get('date') || 'today'),
            '/feedback': () => this.renderFeedback(),
            '/profile': () => this.renderProfile(),
            '/upgrade': () => this.renderUpgrade(),
            '/settings': () => this.renderSettings()
        };
        
        // Match route
        let matched = false;
        for (const [routePath, handler] of Object.entries(routes)) {
            if (path.startsWith(routePath)) {
                // Check auth for protected routes
                const protectedRoutes = ['/dashboard', '/macrocycle', '/week', '/session', '/feedback', '/profile', '/upgrade', '/settings'];
                const isProtected = protectedRoutes.some(r => path.startsWith(r));
                
                if (isProtected && !this.state.user) {
                    window.location.hash = '#/login';
                    return;
                }
                
                // Check if onboarding needed (skip for public auth routes)
                if (path === '/login' || path === '/register') {
                    const params = new URLSearchParams(queryString);
                    handler(params);
                    matched = true;
                    break;
                }

                if (path !== '/onboarding' && this.state.user && !this.state.profile) {
                    window.location.hash = '#/onboarding';
                    return;
                }
                
                // Check if competition needed for dashboard
                if (path === '/dashboard' && this.state.user && this.state.profile && !this.state.competition) {
                    window.location.hash = '#/onboarding?step=4';
                    return;
                }
                
                // Pro-only routes (no dedicated views yet -> send to upgrade with notice)
                const proRoutes = ['/stats/readiness', '/stats/progress'];
                const isProRoute = proRoutes.some(r => path.startsWith(r));
                if (isProRoute) {
                    if (this.state.tier !== 'pro') {
                        window.location.hash = '#/upgrade';
                    } else {
                        window.location.hash = '#/dashboard';
                    }
                    return;
                }
                
                // Execute handler
                const params = new URLSearchParams(queryString);
                handler(params);
                matched = true;
                break;
            }
        }
        
        if (!matched) {
            window.location.hash = '#/dashboard';
        }
    }

    // Render methods - will be implemented in separate files
    renderLogin() { renderLogin(this); }
    renderRegister() { renderRegister(this); }
    renderOnboarding() { renderOnboarding(this); }
    renderDashboard() { renderDashboard(this); }
    renderMacrocycle() { renderMacrocycle(this); }
    renderWeek(start) { renderWeek(this, start); }
    renderSession(date) { renderSession(this, date); }
    renderFeedback() { renderFeedback(this); }
    renderProfile() { renderProfile(this); }
    renderUpgrade() { renderUpgrade(this); }
    renderSettings() { renderSettings(this); }

    // Helper
    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-error';
        alert.style.cssText = 'padding: 1rem; background: var(--error-background); color: var(--error-color); border-radius: 0.5rem; margin-bottom: 1rem;';
        alert.textContent = message;
        
        const main = document.getElementById('app');
        main.insertBefore(alert, main.firstChild);
        
        setTimeout(() => alert.remove(), 5000);
    }

    showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success';
        alert.style.cssText = 'padding: 1rem; background: var(--success-background); color: var(--success-color); border-radius: 0.5rem; margin-bottom: 1rem;';
        alert.textContent = message;
        
        const main = document.getElementById('app');
        main.insertBefore(alert, main.firstChild);
        
        setTimeout(() => alert.remove(), 3000);
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    }

    formatDuration(minutes) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    }

    getPhaseColor(phaseName) {
        const colors = {
            'Base': '#10b981',
            'Build': '#f59e0b',
            'Peak': '#ef4444',
            'Taper': '#8b5cf6',
            'Race': '#ec4899'
        };
        return colors[phaseName] || '#6b7280';
    }
}

// Initialize app when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize AdSense for free tier
    initAdSense();
    window.app = new App();
});

// AdSense initialization
function initAdSense() {
    // Check if user is on free tier (will be updated after auth)
    // AdSense script is loaded in index.html
    // Ads are conditionally rendered in components based on tier
    
    // Auto-refresh ads on route change for free tier
    window.addEventListener('hashchange', () => {
        if (window.adsbygoogle && window.app && window.app.state.tier === 'free') {
            try {
                (window.adsbygoogle = window.adsbygoogle || []).push({});
            } catch (e) {
                // Ignore AdSense errors
            }
        }
    });
}

// Function to refresh AdSense ads (called after route changes for free tier)
window.refreshAds = function() {
    if (window.adsbygoogle && window.app && window.app.state.tier === 'free') {
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch (e) {
            // Ignore AdSense errors
        }
    }
}

// Export for other modules
window.App = App;