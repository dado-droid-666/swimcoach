// Public pages: landing, privacy, terms (no login required, AdSense-friendly)
function renderLanding(app) {
    if (app.state.user) {
        window.location.hash = '#/dashboard';
        return;
    }
    const html = `
        <div style="max-width: 860px; margin: 0 auto; padding: 1rem 0 3rem;">
            <header style="text-align: center; margin: 2.5rem 0;">
                <div style="font-size: 3.5rem;">🏊</div>
                <h1 style="margin: 0.5rem 0;">SwimCoach — Competition-focused swim periodization</h1>
                <p style="color: var(--muted-color); font-size: 1.05rem; max-width: 640px; margin: 0.75rem auto;">
                    Personalized swim training plans built around your goal race: CSS-based zones,
                    strength with KB / TRX / bodyweight, and guided sessions with timer and RPE.
                </p>
                <div style="display: flex; gap: 0.75rem; justify-content: center; margin-top: 1.25rem; flex-wrap: wrap;">
                    <a href="#/register" role="button" class="primary" style="text-decoration: none; padding: 0.75rem 1.5rem;">Start free — 1 month trial</a>
                    <a href="#/login" role="button" class="secondary" style="text-decoration: none; padding: 0.75rem 1.5rem;">Log in</a>
                </div>
                <p style="font-size: 0.85rem; color: var(--muted-color);">Free trial included. Upgrade to Pro for $100 MXN/month.</p>
            </header>

            <section class="card" style="padding: 1.5rem; margin-bottom: 1rem;">
                <h2>How it works</h2>
                <ol style="margin: 0; padding-left: 1.25rem; line-height: 1.7;">
                    <li><strong>Tell us your level:</strong> 400m time or CSS test, swim days per week, available equipment, strength days.</li>
                    <li><strong>Get your 6-week macrocycle:</strong> Base → Build → Peak → Taper → Race, with weekly volume matched to your level (up to 12k / 16k / 25k m).</li>
                    <li><strong>Train guided:</strong> each swim session has warm-up with drills, main set by CSS zones Z1–Z5 with target paces and SPM, and cool-down. Strength sessions rotate A/B/C (Pull+Core TRX, Legs+Hips KB, Stamina BW).</li>
                    <li><strong>Log and adapt:</strong> RPE and per-exercise effort feed progression. Retest CSS every 6 weeks.</li>
                </ol>
            </section>

            <section class="grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                <article class="card" style="padding: 1.25rem;">
                    <h3 style="margin-top: 0;">📐 CSS zones</h3>
                    <p style="color: var(--muted-color); font-size: 0.95rem;">Z1 recovery through Z5 sprint, with paces derived from your critical swim speed. Every length is a multiple of 25m.</p>
                </article>
                <article class="card" style="padding: 1.25rem;">
                    <h3 style="margin-top: 0;">🏋️ Strength that fits swimming</h3>
                    <p style="color: var(--muted-color); font-size: 0.95rem;">Kettlebell, TRX and bodyweight templates, max 4 sessions/week, respecting your availability and AM/PM overlap.</p>
                </article>
                <article class="card" style="padding: 1.25rem;">
                    <h3 style="margin-top: 0;">⏱️ Guided player</h3>
                    <p style="color: var(--muted-color); font-size: 0.95rem;">Interval timer, metronome for stroke rate, drill library in warm-ups, and weekly Lun–Dom view with drag &amp; drop for Pro.</p>
                </article>
            </section>

            <section class="card" style="padding: 1.5rem; margin-bottom: 1rem;">
                <h2>Who is it for?</h2>
                <p style="line-height: 1.7;">SwimCoach is for triathletes, open-water swimmers and pool competitors who want a structured plan without hiring a full-time coach. Beginners use technique-biased sets and conservative volume; advanced swimmers get threshold and VO2max work plus race-pace rehearsals. All plans respect rest days — recovery is part of the program.</p>
                <h2>Frequently asked questions</h2>
                <p><strong>Do I need equipment?</strong> No. Swim with any 25m/50m pool; strength adapts to what you have (KB, TRX, or bodyweight only).</p>
                <p><strong>Is there a free plan?</strong> Yes. The free tier includes full training generation with ads. Pro ($100 MXN/month) removes ads, unlocks drag &amp; drop rescheduling and week regeneration.</p>
                <p><strong>How is my data used?</strong> Training data improves your plan only. Anonymous data is used for research solely with your explicit consent. See <a href="#/privacy">Privacy Policy</a> and <a href="#/terms">Terms</a>.</p>
            </section>

            <section style="text-align: center; margin-top: 1.5rem;">
                <div style="font-size: 10px; color: var(--muted-color); text-transform: uppercase; letter-spacing: .08em;">Advertisement</div>
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-4540036176937342"
                     data-ad-slot="7276396302"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
            </section>

            <footer style="text-align: center; margin-top: 2rem; color: var(--muted-color); font-size: 0.875rem;">
                Contact: <a href="mailto:swimcoach.app@gmail.com">swimcoach.app@gmail.com</a> ·
                <a href="#/privacy">Privacy</a> · <a href="#/terms">Terms</a>
            </footer>
        </div>
    `;
    document.getElementById('app').innerHTML = html;
    if (window.refreshAds) setTimeout(window.refreshAds, 100);
}

function renderPrivacy(app) {
    document.getElementById('app').innerHTML = `
        <div style="max-width: 760px; margin: 0 auto; padding: 1rem 0 3rem; line-height: 1.7;">
            <h1>Privacy Policy</h1>
            <p style="color: var(--muted-color);">Last updated: September 30, 2026. Contact: <a href="mailto:swimcoach.app@gmail.com">swimcoach.app@gmail.com</a></p>
            <h2>1. What we collect</h2>
            <p>Account data (email, password hash), training profile (level, CSS test results, availability, equipment), generated plans, session feedback (RPE, completed distances) and optional per-exercise logs (weight, reps, effort). We do not collect payment card data directly — payments are processed by MercadoPago.</p>
            <h2>2. How we use it</h2>
            <p>To generate and adapt your training plan, show your dashboard and week views, and improve pacing zones. Anonymous training data is used for research <strong>only with your explicit consent</strong> (opt-in).</p>
            <h2>3. Advertising and cookies — Google AdSense</h2>
            <p>SwimCoach shows ads on the free tier via Google AdSense. Google and its partners use cookies and similar technologies to serve personalized or non-personalized ads, measure performance and prevent fraud. Data collected may include cookie identifiers, IP address, device info and pages visited.</p>
            <ul>
                <li>Learn how Google uses data: <a href="https://policies.google.com/technologies/ads" target="_blank" rel="noopener">policies.google.com/technologies/ads</a> and <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Privacy Policy</a>.</li>
                <li>Manage or opt out of personalized ads: <a href="https://adssettings.google.com" target="_blank" rel="noopener">adssettings.google.com</a> and <a href="https://www.aboutads.info/choices" target="_blank" rel="noopener">aboutads.info/choices</a>.</li>
                <li>Pro subscribers ($100 MXN/month) see no ads.</li>
            </ul>
            <h2>4. Third parties</h2>
            <p>Hosting and database (Render, Supabase), payments (MercadoPago). Each processes data under its own policy and only as needed to operate the service.</p>
            <h2>5. Your rights</h2>
            <p>You may request access, correction or deletion of your data at <a href="mailto:swimcoach.app@gmail.com">swimcoach.app@gmail.com</a>. Deleting your account removes profile, plans and logs within 30 days, except anonymized research data previously consented.</p>
            <h2>6. Children</h2>
            <p>SwimCoach is not directed at children under 13. Accounts for minors require a parent or guardian.</p>
            <p><a href="#/">← Back to home</a></p>
        </div>
    `;
}

function renderTerms(app) {
    document.getElementById('app').innerHTML = `
        <div style="max-width: 760px; margin: 0 auto; padding: 1rem 0 3rem; line-height: 1.7;">
            <h1>Terms of Service</h1>
            <p style="color: var(--muted-color);">Last updated: September 30, 2026.</p>
            <h2>1. Service</h2>
            <p>SwimCoach provides automated swim training plans for informational purposes. It is not medical advice. Consult a physician before starting intense exercise; stop and seek care if you feel pain, dizziness or unusual fatigue. Never swim alone in open water.</p>
            <h2>2. Plans and billing</h2>
            <p>Free tier includes training generation with ads and a 1-month free trial of Pro features where offered. Pro ($100 MXN/month, via MercadoPago) removes ads and unlocks session rescheduling and week regeneration. You may cancel anytime; Pro stays active until the end of the billing period. Prices in Mexican pesos, taxes where applicable.</p>
            <h2>3. Acceptable use</h2>
            <p>One account per person; do not share credentials, scrape, or misuse the service. We may suspend accounts for abuse or payment failure.</p>
            <h2>4. Intellectual property</h2>
            <p>Training methodology text, drill library and software are owned by SwimCoach. You may use generated plans for personal training.</p>
            <h2>5. Warranty and liability</h2>
            <p>Service provided "as is" without warranties. To the maximum extent permitted by law, SwimCoach is not liable for injuries or indirect damages from following generated plans. You train at your own risk.</p>
            <h2>6. Contact and governing</h2>
            <p>Contact <a href="mailto:swimcoach.app@gmail.com">swimcoach.app@gmail.com</a>. These terms are governed by the laws of Mexico; disputes resolved in competent courts of Mexico City unless mandatory consumer rules provide otherwise.</p>
            <p><a href="#/">← Back to home</a> · <a href="#/privacy">Privacy Policy</a></p>
        </div>
    `;
}

window.renderLanding = renderLanding;
window.renderPrivacy = renderPrivacy;
window.renderTerms = renderTerms;
