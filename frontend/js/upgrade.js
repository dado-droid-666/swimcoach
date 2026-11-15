// Upgrade View
async function renderUpgrade(app) {
    const hash = window.location.hash.slice(1);
    const query = new URLSearchParams(hash.split('?')[1] || '');
    const search = new URLSearchParams(window.location.search);
    const mockedCheckout = query.get('mock_checkout') === '1';
    const returningFromCheckout = !mockedCheckout && (
        query.get('status') === 'success'
        || query.has('preapproval_id')
        || search.has('preapproval_id')
    );

    let notice = '';
    if (returningFromCheckout) {
        // The MercadoPago webhook may arrive a few seconds after the redirect.
        await app.checkAuth();
        // Clean the query so a reload does not re-trigger this block.
        window.history.replaceState({}, document.title, window.location.pathname + '#/upgrade');

        if (app.state.tier === 'pro') {
            notice = '<div class="alert" style="padding: 1rem; background: var(--success-background); color: var(--success-color); border-radius: 0.5rem; margin-bottom: 1rem;">Payment confirmed. Welcome to Pro!</div>';
        } else {
            notice = '<div class="alert" style="padding: 1rem; background: var(--muted-background); border-radius: 0.5rem; margin-bottom: 1rem;">Payment received. We are confirming your subscription with MercadoPago — this can take a few seconds.</div>';
            setTimeout(async () => {
                await app.checkAuth();
                if (app.state.tier === 'pro') renderUpgrade(app);
            }, 4000);
        }
    } else if (mockedCheckout) {
        window.history.replaceState({}, document.title, window.location.pathname + '#/upgrade');
        notice = '<div class="alert" style="padding: 1rem; background: var(--muted-background); border-radius: 0.5rem; margin-bottom: 1rem;">Dev mode: simulated checkout, no payment was made and Pro was not activated.</div>';
    }

    const tier = app.state.tier;
    const html = `
        <div class="upgrade-view" style="max-width: 700px; margin: 0 auto;">
            <header style="margin-bottom: 2rem; text-align: center;">
                <h1>Upgrade to Pro</h1>
                <p style="color: var(--muted-color);">Unlock the full SwimCoach experience</p>
            </header>

            ${notice}
            ${tier === 'pro' ? renderProActive(app) : renderUpgradeCards(app)}
        </div>
    `;

    document.getElementById('app').innerHTML = html;

    if (tier === 'pro') {
        const btn = document.getElementById('billing-portal-btn');
        try {
            const portal = await api.getBillingPortal();
            if (btn && portal.portal_url) btn.href = portal.portal_url;
        } catch (error) {
            // MercadoPago has no per-subscription billing page; cancellation
            // is handled by the button on this screen.
            if (btn) btn.style.display = 'none';
        }
    }
}

function renderProActive(app) {
    const user = app.state.user;
    const status = user.subscription_status;
    const cancelled = status === 'cancelled';
    const paused = status === 'paused';
    const periodEnd = user.current_period_end
        ? new Date(user.current_period_end).toLocaleDateString()
        : null;

    let statusNotice = '';
    if (cancelled) {
        statusNotice = `<p style="margin: 0 0 1rem; padding: 0.75rem; border-radius: 0.5rem; background: var(--muted-background); color: var(--muted-color);">
            Subscription cancelled. Pro stays active${periodEnd ? ` until ${periodEnd}` : ' until the current period ends'}.
        </p>`;
    } else if (paused) {
        statusNotice = `<p style="margin: 0 0 1rem; padding: 0.75rem; border-radius: 0.5rem; background: var(--muted-background); color: var(--muted-color);">
            Subscription paused in MercadoPago. No charges are being made.
        </p>`;
    }

    return `
        <div class="card" style="text-align: center; padding: 2rem; background: var(--success-background); border-color: var(--success-color);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🌟</div>
            <h2 style="margin: 0 0 0.5rem; color: var(--success-color);">Pro Active!</h2>
            <p style="color: var(--muted-color); margin: 0 0 1rem;">Thanks for supporting SwimCoach</p>

            ${statusNotice}

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
                ${cancelled ? '' : '<button class="secondary" style="margin-left: 0.5rem;" onclick="cancelSubscription()">Cancel Subscription</button>'}
            </div>

            ${periodEnd ? `<p style="margin: 1rem 0 0; font-size: 0.875rem; color: var(--muted-color);">Current period ends: ${periodEnd}</p>` : ''}
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
                <p style="margin: 0.5rem 0 0; font-size: 0.75rem; color: var(--muted-color);">Recurring monthly charge in MercadoPago until you cancel.</p>
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
                    <p style="margin: 0.5rem 0 0; color: var(--muted-color);">Yes, cancel anytime from this page. Access continues until the period ends.</p>
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
        if (!data || !data.init_point) throw new Error('MercadoPago did not return a checkout URL');
        // Redirect to MercadoPago (or the dev mock URL).
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
