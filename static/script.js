// --- Personal Finance Advisor Bot - Frontend JavaScript --- //

document.addEventListener('DOMContentLoaded', () => {
  // --- State ---
  let currentMonth = new Date().toISOString().slice(0, 7);
  let availableMonths = [];
  let summaryData = null;
  let allExpenses = [];
  let categoryChartInstance = null;

  // Visual Category Palette
  const CATEGORY_COLORS = {
    "Food": "#10b981",          // Emerald Green
    "Rent": "#3b82f6",          // Royal Blue
    "Transport": "#f59e0b",     // Amber
    "Entertainment": "#ec4899", // Pink
    "Shopping": "#8b5cf6",      // Violet
    "Education": "#06b6d4",     // Cyan
    "Healthcare": "#ef4444",    // Red
    "Utilities": "#14b8a6",     // Teal
    "Other": "#64748b"          // Slate
  };

  const CATEGORY_ICONS = {
    "Food": "fa-utensils",
    "Rent": "fa-house",
    "Transport": "fa-bus",
    "Entertainment": "fa-gamepad",
    "Shopping": "fa-bag-shopping",
    "Education": "fa-graduation-cap",
    "Healthcare": "fa-heart-pulse",
    "Utilities": "fa-bolt",
    "Other": "fa-tags"
  };

  // --- DOM Elements ---
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const navItems = document.querySelectorAll('.nav-item');
  const contentSections = document.querySelectorAll('.content-section');
  const viewTitle = document.getElementById('viewTitle');
  const viewSubtitle = document.getElementById('viewSubtitle');
  const monthSelector = document.getElementById('monthSelector');
  const toastContainer = document.getElementById('toastContainer');

  // Income Modal Elements
  const incomeModal = document.getElementById('incomeModal');
  const openIncomeModalBtn = document.getElementById('openIncomeModalBtn');
  const closeIncomeModalBtn = document.getElementById('closeIncomeModalBtn');
  const cancelIncomeModalBtn = document.getElementById('cancelIncomeModalBtn');
  const incomeForm = document.getElementById('incomeForm');
  const incomeAmountInput = document.getElementById('incomeAmount');
  const incomeMonthInput = document.getElementById('incomeMonth');
  const incomeSourceInput = document.getElementById('incomeSource');

  // Expense Form & Filter Elements
  const quickAddExpenseBtn = document.getElementById('quickAddExpenseBtn');
  const addExpenseForm = document.getElementById('addExpenseForm');
  const expenseAmountInput = document.getElementById('expenseAmount');
  const expenseCategorySelect = document.getElementById('expenseCategory');
  const expenseDateInput = document.getElementById('expenseDate');
  const expenseDescInput = document.getElementById('expenseDescription');
  const searchExpenseInput = document.getElementById('searchExpenseInput');
  const filterCategorySelect = document.getElementById('filterCategorySelect');
  const clearExpenseFiltersBtn = document.getElementById('clearExpenseFiltersBtn');
  const filteredCountLabel = document.getElementById('filteredCountLabel');
  const filteredTotalLabel = document.getElementById('filteredTotalLabel');

  // Demo Controls
  const seedDataBtn = document.getElementById('seedDataBtn');
  const resetDataBtn = document.getElementById('resetDataBtn');
  const engineStatusLabel = document.getElementById('engineStatusLabel');

  // AI Advisor Elements
  const askAiBtn = document.getElementById('askAiBtn');
  const aiCustomPrompt = document.getElementById('aiCustomPrompt');
  const aiSpinner = document.getElementById('aiSpinner');
  const aiModeTag = document.getElementById('aiModeTag');
  const aiModeLabel = document.getElementById('aiModeLabel');
  const adviceSummaryTitle = document.getElementById('adviceSummaryTitle');
  const adviceSourceBadge = document.getElementById('adviceSourceBadge');
  const adviceRecommendationsList = document.getElementById('adviceRecommendationsList');
  const adviceActionItemsList = document.getElementById('adviceActionItemsList');
  const aiWarningCallout = document.getElementById('aiWarningCallout');
  const chipButtons = document.querySelectorAll('.chip-btn');

  // Summary View Elements
  const printSummaryBtn = document.getElementById('printSummaryBtn');

  // Set default expense date to today
  if (expenseDateInput) {
    expenseDateInput.value = new Date().toISOString().slice(0, 10);
  }

  // --- Helper: Format Indian Rupee Currency ---
  function formatINR(amount) {
    const num = Number(amount) || 0;
    return '₹' + num.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  // --- Toast Notification ---
  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-info');
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  // --- Navigation & Section Switching ---
  const sectionMeta = {
    dashboard: {
      title: "Dashboard",
      subtitle: "Overview of your monthly cash flow, savings, and expense breakdown"
    },
    expenses: {
      title: "Expense Tracking",
      subtitle: "Add, review, and filter all outgoing transactions for the selected month"
    },
    budget: {
      title: "Budget Advisor",
      subtitle: "Sensible 50/30/20 category benchmarks vs. actual monthly expenditure"
    },
    "ai-advisor": {
      title: "AI Financial Advisor",
      subtitle: "Actionable, intelligent spending evaluations and customized wealth-building recommendations"
    },
    summary: {
      title: "Monthly Financial Summary",
      subtitle: "Comprehensive monthly balance sheet, health scoring, and audit breakdown"
    }
  };

  function switchSection(sectionId) {
    navItems.forEach(item => {
      item.classList.toggle('active', item.dataset.section === sectionId);
    });

    contentSections.forEach(section => {
      section.classList.toggle('active', section.id === `section-${sectionId}`);
    });

    if (sectionMeta[sectionId]) {
      viewTitle.textContent = sectionMeta[sectionId].title;
      viewSubtitle.textContent = sectionMeta[sectionId].subtitle;
    }

    // Close mobile sidebar if open
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('active');

    // Section specific refresh
    if (sectionId === 'budget') {
      renderBudgetView();
    } else if (sectionId === 'summary') {
      renderSummaryView();
    } else if (sectionId === 'ai-advisor' && adviceRecommendationsList.children.length <= 1) {
      loadAiAdvice();
    }
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      switchSection(item.dataset.section);
    });
  });

  // Mobile navigation drawer toggle
  if (hamburgerBtn) {
    hamburgerBtn.addEventListener('click', () => {
      sidebar.classList.add('open');
      sidebarOverlay.classList.add('active');
    });
  }

  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener('click', () => {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('active');
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('active');
    });
  }

  // Quick Action Buttons
  document.getElementById('viewBudgetBtn')?.addEventListener('click', () => switchSection('budget'));
  document.getElementById('viewAllExpensesBtn')?.addEventListener('click', () => switchSection('expenses'));
  quickAddExpenseBtn?.addEventListener('click', () => {
    switchSection('expenses');
    expenseAmountInput.focus();
  });

  // --- Month Selector Management ---
  async function loadMonthsList() {
    try {
      const res = await fetch('/api/months');
      const data = await res.json();
      availableMonths = data.months || [currentMonth];

      if (!availableMonths.includes(currentMonth)) {
        availableMonths.unshift(currentMonth);
      }

      monthSelector.innerHTML = '';
      availableMonths.forEach(m => {
        const option = document.createElement('option');
        option.value = m;
        // Format month name: e.g. "September 2026"
        const [year, month] = m.split('-');
        const dateObj = new Date(year, parseInt(month) - 1, 1);
        const monthName = dateObj.toLocaleString('en-US', { month: 'long', year: 'numeric' });
        option.textContent = monthName;
        if (m === currentMonth) option.selected = true;
        monthSelector.appendChild(option);
      });
    } catch (err) {
      console.error('Failed to load months:', err);
    }
  }

  monthSelector.addEventListener('change', (e) => {
    currentMonth = e.target.value;
    refreshAllData();
  });

  // --- Fetch Summary & Dashboard Data ---
  async function fetchSummary() {
    try {
      const res = await fetch(`/api/summary?month=${currentMonth}`);
      if (!res.ok) throw new Error('Failed to fetch summary');
      summaryData = await res.json();
      renderDashboard();
    } catch (err) {
      console.error('Error fetching summary:', err);
      showToast('Could not load financial summary', 'error');
    }
  }

  // --- Render Dashboard ---
  function renderDashboard() {
    if (!summaryData) return;

    // 1. KPI Cards
    const kpiIncome = document.getElementById('kpiIncome');
    const kpiExpenses = document.getElementById('kpiExpenses');
    const kpiSavings = document.getElementById('kpiSavings');
    const kpiSavingsRate = document.getElementById('kpiSavingsRate');
    const kpiIncomeBadge = document.getElementById('kpiIncomeBadge');
    const kpiExpenseBadge = document.getElementById('kpiExpenseBadge');
    const kpiSavingsBadge = document.getElementById('kpiSavingsBadge');
    const kpiRateBadge = document.getElementById('kpiRateBadge');

    kpiIncome.textContent = formatINR(summaryData.income);
    kpiExpenses.textContent = formatINR(summaryData.total_expenses);
    kpiSavings.textContent = formatINR(summaryData.savings);
    kpiSavingsRate.textContent = `${summaryData.savings_percentage}%`;

    // Badges & Colorings
    if (summaryData.income > 0) {
      kpiIncomeBadge.textContent = "Active";
      kpiIncomeBadge.className = "kpi-badge badge-success";
      const expPercent = Math.round((summaryData.total_expenses / summaryData.income) * 100);
      kpiExpenseBadge.textContent = `${expPercent}% of Income`;
    } else {
      kpiIncomeBadge.textContent = "Not Set";
      kpiIncomeBadge.className = "kpi-badge badge-warning";
      kpiExpenseBadge.textContent = "No Income Set";
    }

    if (summaryData.savings >= 0) {
      kpiSavings.style.color = "var(--text-main)";
      kpiSavingsBadge.textContent = "Surplus / Savings";
      kpiSavingsBadge.className = "kpi-badge badge-success";
    } else {
      kpiSavings.style.color = "var(--danger)";
      kpiSavingsBadge.textContent = "Deficit!";
      kpiSavingsBadge.className = "kpi-badge badge-danger";
    }

    if (summaryData.savings_percentage >= 20) {
      kpiRateBadge.className = "kpi-badge badge-success";
      kpiRateBadge.textContent = "Healthy (≥20%)";
    } else if (summaryData.savings_percentage > 0) {
      kpiRateBadge.className = "kpi-badge badge-warning";
      kpiRateBadge.textContent = "Below 20% Goal";
    } else {
      kpiRateBadge.className = "kpi-badge badge-danger";
      kpiRateBadge.textContent = "Deficit (0%)";
    }

    // 2. Overspending Alert Banner
    const overspendingBanner = document.getElementById('overspendingAlertBanner');
    const overspendingText = document.getElementById('overspendingAlertText');
    if (summaryData.overspending_areas && summaryData.overspending_areas.length > 0) {
      const overList = summaryData.overspending_areas.map(o => `${o.category} (+₹${o.overspent_amount.toLocaleString('en-IN')})`).join(', ');
      overspendingText.textContent = `You have exceeded recommended budget limits in: ${overList}.`;
      overspendingBanner.classList.remove('hidden');
    } else {
      overspendingBanner.classList.add('hidden');
    }

    // 3. Category Breakdown Chart & Legend
    renderCategoryChart(summaryData.category_spending, summaryData.total_expenses);

    // 4. Financial Health Card
    document.getElementById('dashHealthGrade').textContent = `Grade: ${summaryData.health_grade}`;
    document.getElementById('dashHealthStatus').textContent = summaryData.health_status;
    document.getElementById('dashHealthScore').textContent = `Score: ${summaryData.health_score}/100`;
    document.getElementById('dashHealthBar').style.width = `${Math.min(summaryData.health_score, 100)}%`;

    document.getElementById('dashTxCount').textContent = summaryData.transaction_count;
    document.getElementById('dashTopCat').textContent = summaryData.highest_spending_category || 'None';
    document.getElementById('dashTopCatAmt').textContent = formatINR(summaryData.highest_spending_amount);
    document.getElementById('dashTargetSavings').textContent = formatINR(summaryData.target_savings_recommended);

    // 5. Advisor Snippet
    const snippetEl = document.getElementById('dashSnippetText');
    if (summaryData.overspending_areas && summaryData.overspending_areas.length > 0) {
      const firstOver = summaryData.overspending_areas[0];
      snippetEl.textContent = `You spent ₹${firstOver.spent.toLocaleString('en-IN')} on ${firstOver.category} this month, which is above your suggested limit of ₹${firstOver.recommended.toLocaleString('en-IN')}.`;
    } else if (summaryData.savings > 0) {
      snippetEl.textContent = `You currently save ₹${summaryData.savings.toLocaleString('en-IN')} per month (${summaryData.savings_percentage}%). Keep managing your discretionary spending to maintain this momentum!`;
    } else {
      snippetEl.textContent = "Start by setting your income and logging your daily expenses to unlock automated financial recommendations.";
    }

    // 6. Recent Expenses Table
    renderRecentExpenses();
  }

  // --- Render Chart.js Category Breakdown ---
  function renderCategoryChart(categorySpending, totalExpenses) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;

    document.getElementById('chartTotalBadge').textContent = `${formatINR(totalExpenses)} Total`;

    // Filter categories that have > 0 spending
    const activeCats = Object.keys(categorySpending).filter(c => categorySpending[c] > 0);
    const legendContainer = document.getElementById('categoryLegend');
    legendContainer.innerHTML = '';

    if (activeCats.length === 0) {
      if (categoryChartInstance) categoryChartInstance.destroy();
      ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
      legendContainer.innerHTML = '<p class="text-muted" style="grid-column: span 2; text-align: center; font-size: 0.85rem;">No expenses recorded for this month yet.</p>';
      return;
    }

    const labels = activeCats;
    const dataValues = activeCats.map(c => categorySpending[c]);
    const bgColors = activeCats.map(c => CATEGORY_COLORS[c] || '#64748b');

    // Build legend
    activeCats.forEach(cat => {
      const amt = categorySpending[cat];
      const pct = Math.round((amt / totalExpenses) * 100);
      const item = document.createElement('div');
      item.className = 'legend-item';
      item.innerHTML = `
        <div class="legend-left">
          <span class="legend-color" style="background-color: ${CATEGORY_COLORS[cat] || '#64748b'}"></span>
          <span class="legend-name">${cat}</span>
        </div>
        <span class="legend-val">${formatINR(amt)} (${pct}%)</span>
      `;
      legendContainer.appendChild(item);
    });

    if (categoryChartInstance) {
      categoryChartInstance.destroy();
    }

    categoryChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: dataValues,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                const val = context.raw || 0;
                const pct = Math.round((val / totalExpenses) * 100);
                return ` ${context.label}: ₹${val.toLocaleString('en-IN')} (${pct}%)`;
              }
            }
          }
        },
        cutout: '68%'
      }
    });
  }

  // --- Fetch & Render Expenses ---
  async function fetchExpenses() {
    try {
      const res = await fetch(`/api/expenses?month=${currentMonth}`);
      if (!res.ok) throw new Error('Failed to fetch expenses');
      const data = await res.json();
      allExpenses = data.expenses || [];
      renderExpensesTable();
      renderRecentExpenses();
    } catch (err) {
      console.error('Error fetching expenses:', err);
    }
  }

  function renderRecentExpenses() {
    const tbody = document.getElementById('recentExpensesTableBody');
    if (!tbody) return;

    const recent = allExpenses.slice(0, 5);
    if (recent.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-table-state">No recent expenses found for this month.</td></tr>';
      return;
    }

    tbody.innerHTML = recent.map(exp => `
      <tr>
        <td><strong>${exp.date}</strong></td>
        <td>
          <span class="category-tag">
            <i class="fa-solid ${CATEGORY_ICONS[exp.category] || 'fa-tag'}" style="color: ${CATEGORY_COLORS[exp.category] || '#64748b'}"></i>
            ${exp.category}
          </span>
        </td>
        <td>${escapeHtml(exp.description)}</td>
        <td class="text-right" style="font-weight: 700; color: var(--danger);">${formatINR(exp.amount)}</td>
        <td class="text-center">
          <button class="btn-delete-expense" data-id="${exp.id}" title="Delete expense">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      </tr>
    `).join('');

    attachDeleteHandlers(tbody);
  }

  function renderExpensesTable() {
    const tbody = document.getElementById('allExpensesTableBody');
    if (!tbody) return;

    const searchTerm = (searchExpenseInput?.value || '').toLowerCase().trim();
    const filterCat = filterCategorySelect?.value || '';

    const filtered = allExpenses.filter(exp => {
      const matchCat = filterCat === '' || exp.category === filterCat;
      const matchSearch = searchTerm === '' || exp.description.toLowerCase().includes(searchTerm);
      return matchCat && matchSearch;
    });

    const totalFilteredAmt = filtered.reduce((acc, curr) => acc + curr.amount, 0);
    if (filteredCountLabel) filteredCountLabel.textContent = `Showing ${filtered.length} of ${allExpenses.length} expenses`;
    if (filteredTotalLabel) filteredTotalLabel.textContent = `Total: ${formatINR(totalFilteredAmt)}`;

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-table-state">No expenses match your search or filter.</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map(exp => `
      <tr>
        <td><strong>${exp.date}</strong></td>
        <td>
          <span class="category-tag">
            <i class="fa-solid ${CATEGORY_ICONS[exp.category] || 'fa-tag'}" style="color: ${CATEGORY_COLORS[exp.category] || '#64748b'}"></i>
            ${exp.category}
          </span>
        </td>
        <td>${escapeHtml(exp.description)}</td>
        <td class="text-right" style="font-weight: 700; color: var(--danger);">${formatINR(exp.amount)}</td>
        <td class="text-center">
          <button class="btn-delete-expense" data-id="${exp.id}" title="Delete expense">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      </tr>
    `).join('');

    attachDeleteHandlers(tbody);
  }

  function attachDeleteHandlers(container) {
    container.querySelectorAll('.btn-delete-expense').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = btn.dataset.id;
        if (!confirm('Are you sure you want to delete this expense?')) return;

        try {
          const res = await fetch(`/api/expenses/${id}`, { method: 'DELETE' });
          const data = await res.json();
          if (res.ok) {
            showToast(data.message || 'Expense deleted successfully');
            refreshAllData();
          } else {
            showToast(data.error || 'Failed to delete expense', 'error');
          }
        } catch (err) {
          showToast('Network error while deleting expense', 'error');
        }
      });
    });
  }

  // Filter Event Listeners
  searchExpenseInput?.addEventListener('input', renderExpensesTable);
  filterCategorySelect?.addEventListener('change', renderExpensesTable);
  clearExpenseFiltersBtn?.addEventListener('click', () => {
    if (searchExpenseInput) searchExpenseInput.value = '';
    if (filterCategorySelect) filterCategorySelect.value = '';
    renderExpensesTable();
  });

  // --- Add Expense Form Submission ---
  addExpenseForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = parseFloat(expenseAmountInput.value);
    const category = expenseCategorySelect.value;
    const description = expenseDescInput.value.trim();
    const date = expenseDateInput.value;

    if (!amount || amount <= 0) {
      showToast('Please enter a valid expense amount greater than 0', 'error');
      return;
    }
    if (!category) {
      showToast('Please select an expense category', 'error');
      return;
    }
    if (!description) {
      showToast('Please enter a description for the expense', 'error');
      return;
    }

    try {
      const res = await fetch('/api/expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount, category, description, date })
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || 'Expense added successfully!');
        expenseAmountInput.value = '';
        expenseDescInput.value = '';
        refreshAllData();
      } else {
        showToast(data.error || 'Failed to add expense', 'error');
      }
    } catch (err) {
      showToast('Network error while adding expense', 'error');
    }
  });

  // --- Render Budget Advisor View ---
  async function renderBudgetView() {
    try {
      const res = await fetch(`/api/budget-advisor?month=${currentMonth}`);
      if (!res.ok) throw new Error('Failed to fetch budget advice');
      const data = await res.json();

      document.getElementById('budgetIncomeRef').textContent = formatINR(data.income);
      document.getElementById('budgetTargetSavingsRef').textContent = formatINR(data.income * 0.20);
      document.getElementById('budgetTotalExpenseCapRef').textContent = formatINR(data.income * 0.80);

      const grid = document.getElementById('budgetComparisonGrid');
      grid.innerHTML = '';

      data.budget_comparison.forEach(item => {
        const card = document.createElement('div');
        const isExceeded = item.status === 'exceeded';
        const isWarning = item.status === 'warning';
        card.className = `budget-card ${isExceeded ? 'status-exceeded' : ''}`;

        let barClass = 'fill-green';
        if (isExceeded) barClass = 'fill-red';
        else if (isWarning) barClass = 'fill-amber';

        let diffHtml = '';
        if (item.difference >= 0) {
          diffHtml = `<span class="diff-positive"><i class="fa-solid fa-check"></i> ₹${item.difference.toLocaleString('en-IN')} remaining</span>`;
        } else {
          diffHtml = `<span class="diff-negative"><i class="fa-solid fa-triangle-exclamation"></i> ₹${Math.abs(item.difference).toLocaleString('en-IN')} over limit!</span>`;
        }

        const badgeHtml = isExceeded
          ? '<span class="badge badge-danger">Over Budget</span>'
          : (isWarning ? '<span class="badge badge-warning">Near Limit</span>' : '<span class="badge badge-success">On Track</span>');

        card.innerHTML = `
          <div class="b-header">
            <div class="b-title-group">
              <i class="fa-solid ${CATEGORY_ICONS[item.category] || 'fa-tag'}" style="color: ${CATEGORY_COLORS[item.category] || '#64748b'}; font-size: 1.15rem;"></i>
              <span class="b-cat-name">${item.category}</span>
            </div>
            ${badgeHtml}
          </div>

          <div class="b-figures">
            <div>
              <span class="b-spent-val">${formatINR(item.spent)}</span>
              <span class="b-cap-val"> / ${formatINR(item.recommended)} (${item.recommended_percent}%)</span>
            </div>
            <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-muted);">${item.percent_used}%</span>
          </div>

          <div class="b-progress-bar-bg">
            <div class="b-progress-bar-fill ${barClass}" style="width: ${Math.min(item.percent_used, 100)}%;"></div>
          </div>

          <div class="b-diff-footer">
            ${diffHtml}
            <span style="color: var(--text-muted); font-size: 0.75rem;">Cap: ${item.recommended_percent}%</span>
          </div>
        `;
        grid.appendChild(card);
      });

      // Overspending Warnings Detail Section
      const alertsContainer = document.getElementById('overspendingAlertsContainer');
      const countBadge = document.getElementById('overspendingCountBadge');
      if (data.overspending_areas && data.overspending_areas.length > 0) {
        countBadge.textContent = `${data.overspending_areas.length} Categories Exceeded`;
        countBadge.className = 'card-badge badge-danger';
        alertsContainer.innerHTML = data.overspending_areas.map(o => `
          <div class="alert-item-box">
            <div>
              <strong style="color: var(--danger);"><i class="fa-solid fa-circle-exclamation"></i> ${o.category}:</strong>
              <span>Spent ₹${o.spent.toLocaleString('en-IN')} vs. recommended limit of ₹${o.recommended.toLocaleString('en-IN')}.</span>
            </div>
            <span class="badge badge-danger">+₹${o.overspent_amount.toLocaleString('en-IN')} over limit</span>
          </div>
        `).join('');
      } else {
        countBadge.textContent = '0 Warnings';
        countBadge.className = 'card-badge badge-success';
        alertsContainer.innerHTML = '<p class="text-success" style="font-weight: 600;"><i class="fa-solid fa-circle-check"></i> Superb control! All category expenses are within the recommended 50/30/20 guidelines.</p>';
      }

    } catch (err) {
      console.error('Error rendering budget view:', err);
    }
  }

  // --- Render AI Advisor View ---
  async function loadAiAdvice(customQuery = '') {
    if (aiSpinner) aiSpinner.classList.remove('hidden');
    if (askAiBtn) askAiBtn.disabled = true;

    try {
      const res = await fetch('/api/ai-advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          month: currentMonth,
          prompt: customQuery
        })
      });
      const data = await res.json();

      // Update Engine & Mode Labels
      if (data.is_ai) {
        aiModeLabel.textContent = data.source;
        adviceSourceBadge.textContent = data.source;
        adviceSourceBadge.className = 'card-badge badge-success';
        aiModeTag.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      } else {
        aiModeLabel.textContent = data.source;
        adviceSourceBadge.textContent = "Deterministic Financial Rules";
        adviceSourceBadge.className = 'card-badge badge-primary';
      }

      if (data.warning) {
        aiWarningCallout.textContent = data.warning;
        aiWarningCallout.classList.remove('hidden');
      } else {
        aiWarningCallout.classList.add('hidden');
      }

      adviceSummaryTitle.textContent = data.summary || "Personalized Financial Diagnosis";

      // Populate Recommendations
      adviceRecommendationsList.innerHTML = '';
      if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach(rec => {
          const li = document.createElement('li');
          li.innerHTML = escapeHtml(rec);
          adviceRecommendationsList.appendChild(li);
        });
      } else {
        adviceRecommendationsList.innerHTML = '<li>All spending metrics look standard. Continue recording expenses.</li>';
      }

      // Populate Action Items
      adviceActionItemsList.innerHTML = '';
      if (data.action_items && data.action_items.length > 0) {
        data.action_items.forEach(act => {
          const li = document.createElement('li');
          li.innerHTML = `<i class="fa-solid fa-circle-check" style="margin-right: 8px;"></i> ${escapeHtml(act)}`;
          adviceActionItemsList.appendChild(li);
        });
      }

    } catch (err) {
      console.error('Error loading AI advice:', err);
      showToast('Could not generate financial advice', 'error');
    } finally {
      if (aiSpinner) aiSpinner.classList.add('hidden');
      if (askAiBtn) askAiBtn.disabled = false;
    }
  }

  askAiBtn?.addEventListener('click', () => {
    const query = aiCustomPrompt.value.trim();
    loadAiAdvice(query);
  });

  aiCustomPrompt?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const query = aiCustomPrompt.value.trim();
      loadAiAdvice(query);
    }
  });

  chipButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const query = btn.dataset.query;
      aiCustomPrompt.value = query;
      loadAiAdvice(query);
    });
  });

  // --- Render Monthly Summary View ---
  async function renderSummaryView() {
    try {
      const res = await fetch(`/api/monthly-summary?month=${currentMonth}`);
      if (!res.ok) throw new Error('Failed to fetch monthly summary');
      const data = await res.json();

      const [y, m] = data.month.split('-');
      const dObj = new Date(y, parseInt(m) - 1, 1);
      const mName = dObj.toLocaleString('en-US', { month: 'long', year: 'numeric' });
      document.getElementById('summaryMonthTitle').textContent = `Financial Statement: ${mName}`;

      document.getElementById('sumIncome').textContent = formatINR(data.income);
      document.getElementById('sumExpenses').textContent = formatINR(data.total_expenses);
      document.getElementById('sumSavings').textContent = formatINR(data.savings);
      document.getElementById('sumSavingsRate').textContent = `${data.savings_percentage}%`;
      document.getElementById('sumHealthScore').textContent = `${data.health_score}/100 (${data.health_grade})`;

      // Highlights
      if (data.highest_spending_category) {
        document.getElementById('sumHighestCategory').textContent = `${data.highest_spending_category} (${formatINR(data.highest_spending_amount)})`;
      } else {
        document.getElementById('sumHighestCategory').textContent = "None recorded";
      }

      if (data.overspending_areas && data.overspending_areas.length > 0) {
        const areaStr = data.overspending_areas.map(o => `${o.category} (+₹${o.overspent_amount.toLocaleString('en-IN')})`).join(', ');
        document.getElementById('sumOverspendingSummary').textContent = areaStr;
      } else {
        document.getElementById('sumOverspendingSummary').textContent = "None! All categories strictly within budget limits.";
      }

      document.getElementById('sumHealthAssessment').textContent = `${data.health_status} (Grade ${data.health_grade})`;

      // Recommendations list
      const recUl = document.getElementById('sumRecommendationsList');
      recUl.innerHTML = '';
      if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach(r => {
          const li = document.createElement('li');
          li.textContent = r;
          recUl.appendChild(li);
        });
      }

      // Breakdown Table
      const bTbody = document.getElementById('summaryBreakdownTableBody');
      bTbody.innerHTML = '';

      // Get budget comparisons for complete table
      const bRes = await fetch(`/api/budget-advisor?month=${currentMonth}`);
      const bData = await bRes.json();

      bData.budget_comparison.forEach(item => {
        const tr = document.createElement('tr');
        const isOver = item.overspent;
        const diffStyle = item.difference >= 0 ? 'color: var(--accent);' : 'color: var(--danger); font-weight: 700;';
        const diffText = item.difference >= 0 ? `+${formatINR(item.difference)}` : `-${formatINR(Math.abs(item.difference))}`;

        tr.innerHTML = `
          <td>
            <span class="category-tag">
              <i class="fa-solid ${CATEGORY_ICONS[item.category] || 'fa-tag'}" style="color: ${CATEGORY_COLORS[item.category] || '#64748b'}"></i>
              ${item.category}
            </span>
          </td>
          <td class="text-right">${formatINR(item.recommended)}</td>
          <td class="text-right" style="font-weight: 700;">${formatINR(item.spent)}</td>
          <td class="text-right" style="${diffStyle}">${diffText}</td>
          <td class="text-right">${item.percent_used}%</td>
          <td class="text-center">
            ${isOver ? '<span class="badge badge-danger">Over Budget</span>' : '<span class="badge badge-success">OK</span>'}
          </td>
        `;
        bTbody.appendChild(tr);
      });

    } catch (err) {
      console.error('Error rendering summary view:', err);
    }
  }

  printSummaryBtn?.addEventListener('click', () => {
    window.print();
  });

  // --- Income Modal Handlers ---
  function openIncomeModal() {
    incomeMonthInput.value = currentMonth;
    if (summaryData && summaryData.income > 0) {
      incomeAmountInput.value = summaryData.income;
    } else {
      incomeAmountInput.value = '';
    }
    incomeModal.classList.remove('hidden');
    incomeAmountInput.focus();
  }

  function closeIncomeModal() {
    incomeModal.classList.add('hidden');
  }

  openIncomeModalBtn?.addEventListener('click', openIncomeModal);
  closeIncomeModalBtn?.addEventListener('click', closeIncomeModal);
  cancelIncomeModalBtn?.addEventListener('click', closeIncomeModal);

  incomeForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = parseFloat(incomeAmountInput.value);
    const month = incomeMonthInput.value;
    const source = incomeSourceInput.value.trim() || 'Primary Salary';

    if (isNaN(amount) || amount < 0) {
      showToast('Please enter a valid non-negative income amount', 'error');
      return;
    }

    try {
      const res = await fetch('/api/income', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount, month, source })
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || 'Income updated successfully!');
        closeIncomeModal();
        currentMonth = month;
        refreshAllData();
      } else {
        showToast(data.error || 'Failed to update income', 'error');
      }
    } catch (err) {
      showToast('Network error while updating income', 'error');
    }
  });

  // --- Course Demo Seeding & Reset ---
  seedDataBtn?.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/seed', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || 'Demo data loaded successfully!');
        await loadMonthsList();
        refreshAllData();
      } else {
        showToast(data.error || 'Failed to load demo data', 'error');
      }
    } catch (err) {
      showToast('Network error while seeding demo data', 'error');
    }
  });

  resetDataBtn?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear all income and expense records?')) return;

    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showToast('All financial records cleared');
        refreshAllData();
      } else {
        showToast(data.error || 'Failed to reset data', 'error');
      }
    } catch (err) {
      showToast('Network error while resetting data', 'error');
    }
  });

  // --- Utility: HTML Escape ---
  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // --- Full Refresh ---
  async function refreshAllData() {
    await fetchSummary();
    await fetchExpenses();

    // Check active section and refresh if needed
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection) {
      if (activeSection.id === 'section-budget') renderBudgetView();
      if (activeSection.id === 'section-summary') renderSummaryView();
      if (activeSection.id === 'section-ai-advisor') loadAiAdvice();
    }
  }

  // --- Initialize App ---
  async function init() {
    await loadMonthsList();
    await refreshAllData();
  }

  init();
});
