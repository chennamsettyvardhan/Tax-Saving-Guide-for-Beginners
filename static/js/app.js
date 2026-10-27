/**
 * TaxWise AI - Frontend Application Controller
 * Handles real-time recalculation, regime switching, Chart.js donut chart,
 * table breakdowns, and interactive AI chat with Google Gemini / Knowledge Base.
 */

// Application State
let currentRegime = 'new';
let donutChart = null;
let recalculateTimer = null;

// Currency Formatter (Indian Rupee: ₹ 12,00,000)
const inrFormatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
});

function formatINR(amount) {
    if (isNaN(amount) || amount === null || amount === undefined) return '₹0';
    return inrFormatter.format(amount);
}

function formatLakhs(amount) {
    const num = parseFloat(amount) || 0;
    if (num >= 10000000) {
        return `₹${(num / 10000000).toFixed(2)} Cr`;
    } else if (num >= 100000) {
        const inLakhs = (num / 100000);
        return `₹${inLakhs % 1 === 0 ? inLakhs.toFixed(0) : inLakhs.toFixed(2)} Lakhs`;
    }
    return formatINR(num);
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    attachInputListeners();
    recalculate();
});

// Setup Chart.js Donut Chart
function initChart() {
    const ctx = document.getElementById('taxDonutChart');
    if (!ctx) return;

    if (typeof Chart === 'undefined') {
        console.warn('Chart.js CDN not yet loaded.');
        return;
    }

    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Take Home', 'Income Tax', 'Deductions'],
            datasets: [{
                data: [1128500, 71500, 75000],
                backgroundColor: [
                    '#10b981', // Emerald Take-home
                    '#ef4444', // Red Tax
                    '#3b82f6'  // Blue Deductions
                ],
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return ` ${label}: ${formatINR(value)}`;
                        }
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true,
                duration: 600
            }
        }
    });
}

function updateChart(takeHome, tax, deductions) {
    if (!donutChart) {
        initChart();
    }
    if (donutChart) {
        donutChart.data.datasets[0].data = [
            Math.max(0, takeHome),
            Math.max(0, tax),
            Math.max(0, deductions)
        ];
        donutChart.update();
    }
}

// Attach Live Input Listeners
function attachInputListeners() {
    const grossInput = document.getElementById('gross_income');
    if (grossInput) {
        grossInput.addEventListener('input', () => {
            const val = parseFloat(grossInput.value) || 0;
            document.getElementById('income-in-words').textContent = formatLakhs(val);
            updatePresetChipActive(val);
            debounceRecalculate();
        });
    }

    const deductionFields = ['sec_80c', 'sec_80d', 'hra_exemption', 'sec_80ccd_1b', 'home_loan_24b'];
    deductionFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', debounceRecalculate);
    });
}

function debounceRecalculate() {
    clearTimeout(recalculateTimer);
    recalculateTimer = setTimeout(recalculate, 250);
}

// Preset Quick Income Chips
function setIncome(val) {
    const input = document.getElementById('gross_income');
    if (input) {
        input.value = val;
        document.getElementById('income-in-words').textContent = formatLakhs(val);
        updatePresetChipActive(val);
        recalculate();
    }
}

function updatePresetChipActive(currentVal) {
    const chips = document.querySelectorAll('.preset-chips .chip');
    chips.forEach(chip => {
        const chipVal = parseInt(chip.textContent.replace(/[^\d]/g, '')) * 100000;
        if (chipVal === currentVal) {
            chip.classList.add('active');
        } else {
            chip.classList.remove('active');
        }
    });
}

// Set Active Regime (Old vs New)
function setRegime(regime) {
    currentRegime = regime;

    const cardOld = document.getElementById('card-old');
    const cardNew = document.getElementById('card-new');
    const radioOld = document.getElementById('radio-old');
    const radioNew = document.getElementById('radio-new');
    const chartLabel = document.getElementById('chart-regime-label');

    if (regime === 'old') {
        cardOld.classList.add('active');
        cardNew.classList.remove('active');
        radioOld.checked = true;
        radioNew.checked = false;
        chartLabel.textContent = 'Old Regime';
    } else {
        cardNew.classList.add('active');
        cardOld.classList.remove('active');
        radioNew.checked = true;
        radioOld.checked = false;
        chartLabel.textContent = 'New Regime';
    }

    recalculate();
}

// Reset Form to Initial Defaults
function resetForm() {
    document.getElementById('gross_income').value = 1200000;
    document.getElementById('income-in-words').textContent = '₹12 Lakhs';
    document.getElementById('is_salaried').checked = true;
    document.getElementById('sec_80c').value = 150000;
    document.getElementById('sec_80d').value = 25000;
    document.getElementById('hra_exemption').value = 100000;
    document.getElementById('sec_80ccd_1b').value = 50000;
    document.getElementById('home_loan_24b').value = 0;
    setRegime('new');
    updatePresetChipActive(1200000);
}

// Table Tab Switching
function showTableTab(tab) {
    const activeBtn = document.getElementById('tab-active-btn');
    const compareBtn = document.getElementById('tab-compare-btn');
    const activeContent = document.getElementById('tab-active-content');
    const compareContent = document.getElementById('tab-compare-content');

    if (tab === 'active') {
        activeBtn.classList.add('active');
        compareBtn.classList.remove('active');
        activeContent.classList.remove('hidden');
        compareContent.classList.add('hidden');
    } else {
        compareBtn.classList.add('active');
        activeBtn.classList.remove('active');
        compareContent.classList.remove('hidden');
        activeContent.classList.add('hidden');
    }
}

// Primary Recalculation Engine
async function recalculate() {
    const grossIncome = parseFloat(document.getElementById('gross_income').value) || 0;
    const isSalaried = document.getElementById('is_salaried').checked;
    const sec80c = parseFloat(document.getElementById('sec_80c').value) || 0;
    const sec80d = parseFloat(document.getElementById('sec_80d').value) || 0;
    const hra = parseFloat(document.getElementById('hra_exemption').value) || 0;
    const nps = parseFloat(document.getElementById('sec_80ccd_1b').value) || 0;
    const homeLoan = parseFloat(document.getElementById('home_loan_24b').value) || 0;

    const payload = {
        gross_income: grossIncome,
        regime: currentRegime,
        is_salaried: isSalaried,
        sec_80c: sec80c,
        sec_80d: sec80d,
        hra_exemption: hra,
        sec_80ccd_1b: nps,
        home_loan_24b: homeLoan,
        other_deductions: 0
    };

    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Calculation failed');
        }

        const data = await response.json();
        renderDashboard(data);

    } catch (err) {
        console.error('Recalculation error:', err);
    }
}

// Render Dashboard Data & Visuals
function renderDashboard(data) {
    const active = data.active_result;
    const comparison = data.comparison;
    const newReg = comparison.new_regime;
    const oldReg = comparison.old_regime;

    // 1. Update Top Metric KPI Cards
    document.getElementById('kpi-total-tax').textContent = formatINR(active.total_tax);
    document.getElementById('kpi-effective-rate').textContent = `${active.effective_rate}% effective rate`;

    // Savings vs alternative
    const altRegimeName = currentRegime === 'new' ? 'Old Tax Regime' : 'New Tax Regime';
    const altTotalTax = currentRegime === 'new' ? oldReg.total_tax : newReg.total_tax;
    const savings = Math.max(0, altTotalTax - active.total_tax);

    document.getElementById('kpi-tax-saved').textContent = formatINR(savings);
    document.getElementById('kpi-saved-tag').textContent = `vs ${altRegimeName}`;

    document.getElementById('kpi-take-home').textContent = formatINR(active.take_home);

    // 2. Update Recommendation Banner
    const banner = document.getElementById('recommendation-banner');
    const headline = document.getElementById('banner-headline');
    const bannerText = document.getElementById('banner-text');
    const bannerIcon = document.getElementById('banner-icon');

    headline.textContent = comparison.headline;
    bannerText.textContent = comparison.advice;

    if (comparison.recommended_regime === currentRegime) {
        banner.style.background = 'linear-gradient(135deg, #eff6ff, #f0fdf4)';
        banner.style.borderColor = '#bbf7d0';
        headline.style.color = '#065f46';
        bannerIcon.textContent = '🎉';
    } else {
        banner.style.background = 'linear-gradient(135deg, #fffbeb, #fef2f2)';
        banner.style.borderColor = '#fed7aa';
        headline.style.color = '#9a3412';
        bannerIcon.textContent = '💡';
    }

    // 3. Update Chart & Legend
    updateChart(active.take_home, active.total_tax, active.total_deductions);
    document.getElementById('legend-take-home').textContent = formatINR(active.take_home);
    document.getElementById('legend-tax').textContent = formatINR(active.total_tax);
    document.getElementById('legend-deductions').textContent = formatINR(active.total_deductions);

    // 4. Update Detailed Calculation Key-Values
    document.getElementById('dt-gross').textContent = formatINR(active.gross_income);
    document.getElementById('dt-std-ded').textContent = `- ${formatINR(active.standard_deduction)}`;

    const otherDedAmount = Math.max(0, active.total_deductions - active.standard_deduction);
    document.getElementById('dt-other-ded').textContent = `- ${formatINR(otherDedAmount)}`;
    document.getElementById('dt-taxable').textContent = formatINR(active.taxable_income);

    // 5. Update Slab Breakdown Table
    const slabTbody = document.getElementById('slab-table-body');
    slabTbody.innerHTML = '';

    active.slab_breakdown.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.slab}</td>
            <td><span class="badge badge-primary">${item.rate}</span></td>
            <td>${formatINR(item.taxable_amount)}</td>
            <td class="text-right">${formatINR(item.tax)}</td>
        `;
        slabTbody.appendChild(tr);
    });

    document.getElementById('foot-base-tax').textContent = formatINR(active.base_tax);

    const rebateRow = document.getElementById('foot-rebate-row');
    const totalRebate = (active.rebate_87a || 0) + (active.marginal_relief || 0);
    if (totalRebate > 0) {
        rebateRow.style.display = 'table-row';
        document.getElementById('foot-rebate').textContent = `- ${formatINR(totalRebate)}`;
    } else {
        rebateRow.style.display = 'none';
    }

    document.getElementById('foot-cess').textContent = formatINR(active.cess);
    document.getElementById('foot-total-tax').textContent = formatINR(active.total_tax);

    // 6. Update Side-by-Side Comparison Table
    document.getElementById('comp-old-gross').textContent = formatINR(oldReg.gross_income);
    document.getElementById('comp-new-gross').textContent = formatINR(newReg.gross_income);

    document.getElementById('comp-old-std').textContent = formatINR(oldReg.standard_deduction);
    document.getElementById('comp-new-std').textContent = formatINR(newReg.standard_deduction);

    document.getElementById('comp-old-ded').textContent = formatINR(oldReg.total_deductions);
    document.getElementById('comp-new-ded').textContent = formatINR(newReg.total_deductions);

    document.getElementById('comp-old-taxable').textContent = formatINR(oldReg.taxable_income);
    document.getElementById('comp-new-taxable').textContent = formatINR(newReg.taxable_income);

    document.getElementById('comp-old-base').textContent = formatINR(oldReg.base_tax);
    document.getElementById('comp-new-base').textContent = formatINR(newReg.base_tax);

    document.getElementById('comp-old-rebate').textContent = formatINR(oldReg.rebate_87a);
    document.getElementById('comp-new-rebate').textContent = formatINR(newReg.rebate_87a + (newReg.marginal_relief || 0));

    document.getElementById('comp-old-cess').textContent = formatINR(oldReg.cess);
    document.getElementById('comp-new-cess').textContent = formatINR(newReg.cess);

    document.getElementById('comp-old-total').textContent = formatINR(oldReg.total_tax);
    document.getElementById('comp-new-total').textContent = formatINR(newReg.total_tax);

    document.getElementById('comp-old-takehome').textContent = formatINR(oldReg.take_home);
    document.getElementById('comp-new-takehome').textContent = formatINR(newReg.take_home);

    // 7. Update Smart Recommendations Grid
    renderRecommendations(data.recommendations);

    // 8. Update AI Co-Pilot Context Badges
    const contextBadge = document.getElementById('ai-context-badge');
    const fabBadge = document.getElementById('fab-active-badge');
    const incomeLabel = formatLakhs(active.gross_income);
    const regimeLabel = currentRegime === 'new' ? 'New Regime' : 'Old Regime';
    if (contextBadge) {
        contextBadge.textContent = `Active Context: ${incomeLabel} · ${regimeLabel}`;
    }
    if (fabBadge) {
        fabBadge.textContent = `${incomeLabel} (${currentRegime === 'new' ? 'New' : 'Old'})`;
    }
}

// Render Smart Recommendations
function renderRecommendations(tips) {
    const container = document.getElementById('tips-container');
    if (!container) return;

    container.innerHTML = '';
    if (!tips || tips.length === 0) {
        container.innerHTML = '<p class="muted">No immediate optimization gaps found. Your deductions are fully claimed!</p>';
        return;
    }

    tips.forEach(tip => {
        const card = document.createElement('div');
        card.className = 'tip-card';

        let savingHTML = '';
        if (tip.potential_saving > 0) {
            savingHTML = `
                <div class="tip-saving-badge">
                    <span>Potential Tax Saving:</span>
                    <strong>${formatINR(tip.potential_saving)}</strong>
                </div>
            `;
        }

        const optionsList = (tip.options || []).map(opt => `<li>${opt}</li>`).join('');

        card.innerHTML = `
            <div>
                <span class="tip-tag">${tip.section} · ${tip.applicability}</span>
                <h4>${tip.title}</h4>
                <p class="tip-desc">${tip.description}</p>
                <ul class="tip-options">${optionsList}</ul>
            </div>
            ${savingHTML}
        `;
        container.appendChild(card);
    });
}

// ==========================================================================
// AI Assistant Chat Logic
// ==========================================================================

function askQuickPrompt(questionText) {
    const input = document.getElementById('chat-input');
    input.value = questionText;
    submitChat();
    // Smooth scroll to chat box
    document.getElementById('ai-assistant').scrollIntoView({ behavior: 'smooth' });
}

function clearChat() {
    const stream = document.getElementById('chat-stream');
    stream.innerHTML = `
        <div class="chat-msg bot-msg">
            <div class="msg-bubble">
                <strong>👋 Namaste! I am your TaxWise AI Financial Co-pilot.</strong>
                <p>Conversation reset. I am synchronized with your active numbers on the calculator above. Ask me to <strong>audit your current salary</strong>, explain deductions, or find out how to maximize your take-home pay under Indian Income Tax rules for <strong>FY 2025-26</strong>!</p>
            </div>
        </div>
    `;
}

function scrollToAI() {
    const el = document.getElementById('ai-assistant');
    if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
        setTimeout(() => {
            const input = document.getElementById('chat-input');
            if (input) input.focus();
        }, 400);
    }
}

function copyAnswer(btn) {
    const bubble = btn.closest('.msg-bubble');
    const content = bubble ? bubble.querySelector('.msg-content') : null;
    const textToCopy = content ? content.innerText : '';

    if (navigator.clipboard && textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            const span = btn.querySelector('span');
            if (span) span.textContent = 'Copied! ✓';
            setTimeout(() => {
                if (span) span.textContent = 'Copy';
            }, 2000);
        });
    }
}

async function submitChat() {
    const input = document.getElementById('chat-input');
    const stream = document.getElementById('chat-stream');
    const sendBtn = document.getElementById('chat-send-btn');
    const question = input.value.trim();

    if (!question) return;

    // Capture User Financial Context from live inputs
    const userContext = {
        gross_income: parseFloat(document.getElementById('gross_income').value) || 0,
        is_salaried: document.getElementById('is_salaried').checked,
        regime: currentRegime,
        sec_80c: parseFloat(document.getElementById('sec_80c').value) || 0,
        sec_80d: parseFloat(document.getElementById('sec_80d').value) || 0,
        hra_exemption: parseFloat(document.getElementById('hra_exemption').value) || 0,
        sec_80ccd_1b: parseFloat(document.getElementById('sec_80ccd_1b').value) || 0,
        home_loan_24b: parseFloat(document.getElementById('home_loan_24b').value) || 0
    };

    // 1. Append User Message
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-msg user-msg';
    userMsg.innerHTML = `<div class="msg-bubble">${escapeHTML(question)}</div>`;
    stream.appendChild(userMsg);

    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;

    // 2. Append Loading Placeholder
    const botMsg = document.createElement('div');
    botMsg.className = 'chat-msg bot-msg';
    botMsg.innerHTML = `
        <div class="msg-bubble">
            <span class="muted"><em>⚡ TaxWise AI is analyzing Indian tax rules...</em></span>
        </div>
    `;
    stream.appendChild(botMsg);
    stream.scrollTop = stream.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                user_context: userContext
            })
        });

        const data = await response.json();
        const bubble = botMsg.querySelector('.msg-bubble');

        if (!response.ok) {
            bubble.innerHTML = `<span class="text-red">Error: ${escapeHTML(data.error || 'Could not fetch response')}</span>`;
        } else {
            const formattedHTML = formatMarkdownToHTML(data.answer);
            bubble.innerHTML = `
                <div class="msg-content">${formattedHTML}</div>
                <div class="msg-footer">
                    <span class="msg-source-tag">Source: ${escapeHTML(data.source || 'TaxWise AI Knowledge Base')}</span>
                    <button type="button" class="btn-copy" onclick="copyAnswer(this)" title="Copy advice">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
                            <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
                        </svg>
                        <span>Copy</span>
                    </button>
                </div>
            `;
        }

    } catch (err) {
        const bubble = botMsg.querySelector('.msg-bubble');
        bubble.innerHTML = `<span class="text-red">Unable to connect to TaxWise AI service.</span>`;
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
        stream.scrollTop = stream.scrollHeight;
    }
}

// Lightweight Markdown to HTML Formatter for Assistant Responses
function formatMarkdownToHTML(md) {
    if (!md) return '';

    let text = md;

    // Convert markdown tables
    const tableRegex = /((?:\|.+?\|\r?\n)+)/g;
    text = text.replace(tableRegex, (match) => {
        const rows = match.trim().split(/\r?\n/);
        if (rows.length < 2) return match;

        let htmlTable = '<div class="table-responsive"><table class="data-table">';
        rows.forEach((row, idx) => {
            if (row.includes('---')) return; // delimiter line
            const cells = row.split('|').map(c => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length - 1);
            if (cells.length === 0) return;

            htmlTable += '<tr>';
            cells.forEach(cell => {
                const tag = idx === 0 ? 'th' : 'td';
                htmlTable += `<${tag}>${cell}</${tag}>`;
            });
            htmlTable += '</tr>';
        });
        htmlTable += '</table></div>';
        return htmlTable;
    });

    let html = text
        // Headers (from h5 down to h1)
        .replace(/^##### (.*$)/gim, '<h6 class="chat-h">$1</h6>')
        .replace(/^#### (.*$)/gim, '<h5 class="chat-h">$1</h5>')
        .replace(/^### (.*$)/gim, '<h4 class="chat-h">$1</h4>')
        .replace(/^## (.*$)/gim, '<h3 class="chat-h">$1</h3>')
        .replace(/^# (.*$)/gim, '<h2 class="chat-h">$1</h2>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>')
        // Bold & Italic
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Blockquotes
        .replace(/^\> (.*$)/gim, '<blockquote class="chat-quote">$1</blockquote>')
        // Bullet lists
        .replace(/^\s*[-*]\s+(.*$)/gim, '<li>$1</li>')
        .replace(/^\s*\d+\.\s+(.*$)/gim, '<li>$1</li>')
        // Linebreaks
        .replace(/\n\n/g, '<br><br>');

    // Wrap consecutive <li> tags in <ul>
    if (html.includes('<li>')) {
        html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul class="chat-list">$&</ul>');
    }

    return html;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    }[tag] || tag));
}
