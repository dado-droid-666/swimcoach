// Upgrade View
async function renderUpgrade(app) {
    const tier = app.state.tier;
    const user = app.state.user;
    
    const html = `
        <div class="upgrade-view" style="max-width: 700px; margin: 0 auto;">
            <header style="margin-bottom: 2rem; text-align: center;">
                <h1>Upgrade to Pro</h1>
                <p style="color: var(--muted-color);">Unlock the full SwimCoach experience</p>
            </header>
            
            ${tier === 'pro' ? renderProActive(app) : renderUpgradeCards(app)}
        </div>
    `;
    
    document.getElementById('app').innerHTML = html;
    
    if (tier === 'pro') {
        // Load billing portal link
        try {
            const portal = await api.getBillingPortal();
            document.getElementById('billing-portal-btn').href = portal.portal_url;
        } catch (error) {
            console.log('Could not load billing portal');
        }
    }
}

function renderProActive(app) {
    const user = app.state.user;
    return `
        <div class="card" style="text-align: center; padding: 2rem; background: var(--success-background); border-color: var(--success-color);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🌟</div>
            <h2 style="margin: 0 0 0.5rem; color: var(--success-color);">Pro Active!</h2>
            <p style="color: var(--muted-color); margin: 0 0 1rem;">Thanks for supporting SwimCoach</p>
            
            <div style="background: white; border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; text-align: left;">
                <h3 style="margin: 0 0 0.5rem;">Your Pro Features</h3>
                <ul style="margin: 0; padding-left: 1.5rem; color: var(--muted-color);">
                    <li>Unlimited feedback history</li>
                    <li>Readiness score & advanced charts</li>
                    <li>Regenerate any week</li>
                    <li>Export CSV/PDF</li>
                    <li>No ads</li>
                    <li>Priority support</li>
                </ul>
            </div>
            
            <div style="margin-top: 1.5rem;">
                <a href="#" class="primary" id="billing-portal-btn" target="_blank" rel="noopener" style="text-decoration: none;">Manage Subscription</a>
                <button class="secondary" style="margin-left: 0.5rem;" onclick="cancelSubscription()">Cancel Subscription</button>
            </div>
            
            <p style="margin: 1rem 0 0; font-size: 0.875rem; color: var(--muted-color);">
                Current period ends: ${new Date(app.state.user.current_period_end).toLocaleDateString()}
            </p>
        </div>
    `;
}

function renderUpgradeCards(app) {
    return `
        <div class="grid" style="margin-bottom: 2rem;">
            <article class="card" style="position: relative; border: 2px solid var(--border-color); padding: 2rem;">
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <h3 style="margin: 0 0 0.5rem;">Free</h3>
                    <div style="font-size: 3rem; font-weight: bold; color: var(--muted-color);">$0</div>
                    <div style="color: var(--muted-color);">/month</div>
                </div>
                
                <ul style="margin: 0; padding-left: 1.5rem; color: var(--muted-color);">
                    <li>Generate macrocycle plan</li>
                    <li>Swim + Strength sessions</li>
                    <li>Daily feedback logging</li>
                    <li>30-day feedback history</li>
                    <li>Basic weekly stats</li>
                    <li>1 competition goal</li>
                    <li><strong>With ads</strong></li>
                </ul>
                
                <button class="secondary" style="width: 100%; margin-top: 1.5rem;" disabled>Current Plan</button>
            </article>
            
            <article class="card" style="position: relative; border: 2px solid var(--primary); padding: 2rem; background: var(--primary-background);">
                <div style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--primary); color: white; padding: 0.25rem 1rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold;">MOST POPULAR</div>
                
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <h3 style="margin: 0 0 0.5rem;">Pro</h3>
                    <div style="font-size: 3rem; font-weight: bold; color: var(--primary);">$100 MXN</div>
                    <div style="color: var(--muted-color);">/month</div>
                </div>
                
                <ul style="margin: 0; padding-left: 1.5rem; color: var(--muted-color);">
                    <li>Everything in Free</li>
                    <li><strong>Unlimited</strong> feedback history</li>
                    <li><strong>Readiness score</strong> & advanced charts</li>
                    <li>Regenerate any week</li>
                    <li>Drag-to-reschedule sessions</li>
                    <li>Export CSV/PDF reports</li>
                    <li><strong>No ads</strong></li>
                    <li>Multiple competition goals (coming soon)</li>
                    <li>Priority email support</li>
                </ul>
                
                <button class="primary" style="width: 100%; margin-top: 1.5rem; padding: 1rem; font-size: 1.125rem;" onclick="startCheckout()">Upgrade to Pro - $100 MXN/month</button>
            </article>
        </div>
        
        <section style="margin-top: 2rem; padding: 1.5rem; background: var(--muted-background); border-radius: 0.5rem;">
            <h3 style="margin: 0 0 1rem;">Why Upgrade?</h3>
            <div class="grid" style="gap: 1rem;">
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                    <strong>Readiness Score</strong>
                    <p style="margin: 0.5rem 0 0; font-size: 0.875rem; color: var(--muted-color);">Know exactly how prepared you are for race day</p>
                </div>
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔄</div>
                    <strong>Flexible Planning</strong>
                    <p style="margin: 0.5rem 0 0; font-size: 0.875rem; color: var(--muted-color);">Regenerate weeks, drag sessions, adapt to life</p>
                </div>
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
                    <strong>Progress Tracking</strong>
                    <p style="margin: 0.5rem 0 0; font-size: 0.875rem; color: var(--muted-color);">Advanced charts, volume trends, pace analysis</p>
                </div>
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🚫</div>
                    <strong>No Ads</strong>
                    <p style="margin: 0.5rem 0 0; font-size: 0.875rem; color: var(--muted-color);">Clean, focused training experience</p>
                </div>
            </div>
        </section>
        
        <section style="margin-top: 2rem; padding: 1.5rem; background: var(--muted-background); border-radius: 0.5rem; text-align: center;">
            <h3 style="margin: 0 0 1rem;">FAQ</h3>
            <div style="text-align: left; max-width: 500px; margin: 0 auto;">
                <details style="margin-bottom: 0.5rem;">
                    <summary style="cursor: pointer; font-weight: bold;">Can I cancel anytime?</summary>
                    <p style="margin: 0.5rem 0 0; color: var(--muted-color);">Yes, cancel anytime from the billing portal. Access continues until period ends.</p>
                </details>
                <details style="margin-bottom: 0.5rem;">
                    <summary style="cursor: pointer; font-weight: bold;">What payment methods?</summary>
                    <p style="margin: 0.5rem 0 0; color: var(--muted-color);">MercadoPago (credit/debit cards, bank transfer, cash payments in LatAm)</p>
                </details>
                <details style="margin-bottom: 0.5rem;">
                    <summary style="cursor: pointer; font-weight: bold;">Will my data be lost if I cancel?</summary>
                    <p style="margin: 0.5rem 0 0; color: var(--muted-color);">No, your data stays. Pro features just become locked until you resubscribe.</p>
                </details>
            </div>
        </section>
    `;
}

async function startCheckout() {
    const btn = document.querySelector('[onclick="startCheckout()"]');
    if (btn) { btn.disabled = true; btn.textContent = 'Redirecting…'; }
    try {
        const data = await api.createCheckout();
        // Redirect to MercadoPago checkout (or mock checkout in dev)
        window.location.href = data.init_point;
    } catch (error) {
        window.app.showError(error.message || 'Failed to start checkout');
        if (btn) { btn.disabled = false; btn.textContent = 'Upgrade to Pro - $100 MXN/month'; }
    }
}

async function cancelSubscription() {
    if (!confirm('Cancel your Pro subscription? Access continues until the period ends.')) return;
    try {
        await api.cancelSubscription();
        window.app.showSuccess('Subscription cancelled. Pro features remain until period ends.');
        await window.app.checkAuth();
        renderUpgrade(window.app);
    } catch (error) {
        window.app.showError(error.message || 'Failed to cancel subscription');
    }
}

window.renderUpgrade = renderUpgrade;
window.startCheckout = startCheckout;
window.cancelSubscription = cancelSubscription;
window.handleMockCheckoutReturn = handleMockCheckoutReturn;

// Handle mock checkout return (development only)
function handleMockCheckoutReturn() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('mock_checkout') === '1' && urlParams.get('preapproval_id')) {
        // Simulate successful upgrade
        const preapprovalId = urlParams.get('preapproval_id');
        app.showSuccess('Upgrade successful! Welcome to Pro!');
        
        // Update user tier in state
        app.state.tier = 'pro';
        app.state.user.subscription_tier = 'pro';
        app.state.user.subscription_status = 'active';
        app.state.user.current_period_end = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
        
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
        
        // Re-render upgrade page
        setTimeout(() => window.location.reload(), 1500);
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', handleMockCheckoutReturn);