// SwimCoach API Client
const API_BASE = '/api';

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE;
        this.csrfToken = null;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'include', // Include cookies
            ...options
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            
            // Handle 401 - unauthorized
            if (response.status === 401) {
                // Try to refresh or redirect to login
                if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
                    window.location.hash = '#/login';
                    throw new Error('Unauthorized');
                }
            }
            
            // Handle 403 - forbidden (pro feature)
            if (response.status === 403) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || 'Pro feature - upgrade required');
            }
            
            // Handle other errors (422 validation included)
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                let msg = data.detail || `HTTP ${response.status}`;
                if (Array.isArray(msg)) {
                    msg = msg.map(e => {
                        const field = (e.loc || []).filter(x => x !== 'body').join('.');
                        return field ? `${field}: ${e.msg}` : e.msg;
                    }).join('; ');
                }
                throw new Error(msg);
            }
            
            // Parse JSON if present
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error - are you offline?');
            }
            throw error;
        }
    }

    // Auth
    async register(email, password, fullName) {
        return this.request('/auth/register', {
            method: 'POST',
            body: { email, password, full_name: fullName }
        });
    }

    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: { email, password }
        });
    }

    async logout() {
        return this.request('/auth/logout', { method: 'POST' });
    }

    async deleteAccount() {
        return this.request('/auth/account', { method: 'DELETE' });
    }

    async getMe() {
        return this.request('/auth/me');
    }

    // Profile
    async getProfile() {
        return this.request('/profile');
    }

    async updateProfile(data) {
        return this.request('/profile', {
            method: 'PUT',
            body: data
        });
    }

    async createProfile(data) {
        return this.request('/profile', {
            method: 'POST',
            body: data
        });
    }

    // Competition
    async getCompetition() {
        return this.request('/competition');
    }

    async createCompetition(data) {
        return this.request('/competition', {
            method: 'POST',
            body: data
        });
    }

    async updateCompetition(data) {
        return this.request('/competition', {
            method: 'PUT',
            body: data
        });
    }

    async deleteCompetition() {
        return this.request('/competition', { method: 'DELETE' });
    }

    async generateMacrocycle() {
        return this.request('/competition/generate', { method: 'POST' });
    }

    async resetTraining() {
        return this.request('/competition/reset', { method: 'POST' });
    }

    // Plan
    async getMacrocycle() {
        return this.request('/plan/macrocycle');
    }

    async getWeekPlan(startDate) {
        return this.request(`/plan/week?start=${startDate}`);
    }

    async getTodayPlan() {
        return this.request('/plan/today');
    }

    async moveSession(type, id, date) {
        return this.request(`/plan/session/move?session_type=${type}&session_id=${id}&date=${date}`, {
            method: 'PUT'
        });
    }

    async regenerateWeek(startDate) {
        return this.request(`/plan/week/regenerate?start=${startDate}`, { method: 'POST' });
    }

    // Feedback
    async submitFeedback(data) {
        return this.request('/feedback', {
            method: 'POST',
            body: data
        });
    }

    async getFeedbackHistory(page = 1, pageSize = 20) {
        return this.request(`/feedback/history?page=${page}&page_size=${pageSize}`);
    }

    async getFeedback(date) {
        return this.request(`/feedback/${date}`);
    }

    async submitExerciseLogs(logs) {
        return this.request('/feedback/logs', {
            method: 'POST',
            body: { logs }
        });
    }

    async getExerciseLogs(limit = 200) {
        return this.request(`/feedback/logs/history?limit=${limit}`);
    }

    async saveSwimTest(data) {
        return this.request('/tests', {
            method: 'POST',
            body: data
        });
    }

    async getLatestTest() {
        return this.request('/tests/latest');
    }

    // Stats
    async getStatsSummary() {
        return this.request('/stats/summary');
    }

    async getReadiness() {
        return this.request('/stats/readiness');
    }

    async getProgress() {
        return this.request('/stats/progress');
    }

    // Subscription
    async createCheckout() {
        return this.request('/subscription/checkout', { method: 'POST' });
    }

    async getBillingPortal() {
        return this.request('/subscription/portal');
    }

    async cancelSubscription() {
        return this.request('/subscription/cancel', { method: 'POST' });
    }

    async getTierStatus() {
        return this.request('/subscription/status');
    }
}

// Export singleton
window.api = new ApiClient();