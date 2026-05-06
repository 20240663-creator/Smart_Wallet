// transactions.js - Clean version (no duplicates, fixed ordering)

let currentTransactions = [];

// ============= Helper Functions (defined first) =============

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function updateWalletBalance() {
    try {
        const response = await fetchWithAuth(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.WALLET_BALANCE}`);
        if (response.ok) {
            const data = await response.json();
            const balanceEls = document.querySelectorAll('.stat-value, #availableBalance, #currentBalance');
            balanceEls.forEach(el => {
                if (el.id === 'availableBalance' || el.id === 'currentBalance' || el.closest('.stat-card')) {
                    el.textContent = `$${(data.total_balance || 0).toFixed(2)}`;
                }
            });
        }
    } catch (error) {
        console.error('Balance update error:', error);
    }
}

function showSuccessModal(data) {
    const modal = document.getElementById('successModal');
    const details = document.getElementById('successDetails');
    
    if (modal && details) {
        details.innerHTML = `
            <p><strong>Amount:</strong> $${data.amount.toFixed(2)}</p>
            <p><strong>Recipient:</strong> ${escapeHtml(data.recipient)}</p>
            <p><strong>Transaction ID:</strong> #${Math.floor(Math.random() * 1000000)}</p>
            <p><strong>Date:</strong> ${new Date().toLocaleString()}</p>
        `;
        modal.classList.add('active');
        setTimeout(() => closeModal('successModal'), 3000);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
}

function resetSendForm() {
    const form = document.getElementById('sendMoneyForm');
    if (form) form.reset();
}

function resetDepositForm() {
    const form = document.getElementById('depositForm');
    if (form) form.reset();
}

// ============= Core Functions =============

async function fetchTransactions() {
    try {
        const response = await fetchWithAuth(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.TRANSACTIONS}`, {
            method: 'GET'
        });
        
        if (response.ok) {
            const transactions = await response.json();
            currentTransactions = Array.isArray(transactions) ? transactions : [];
            displayTransactions(currentTransactions);
            updateTransactionStats(currentTransactions);
            return currentTransactions;
        }
        return [];
    } catch (error) {
        console.error('Error fetching transactions:', error);
        return [];
    }
}

async function createTransaction(transactionData) {
    try {
        const response = await fetchWithAuth(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.TRANSACTIONS}`, {
            method: 'POST',
            body: JSON.stringify(transactionData)
        });
        
        if (response.ok) {
            showToast('Transaction recorded successfully!', 'success');
            await fetchTransactions();
            await updateWalletBalance();
            return await response.json();
        } else {
            showToast('Failed to create transaction', 'error');
            return null;
        }
    } catch (error) {
        console.error('Error creating transaction:', error);
        showToast('Network error', 'error');
        return null;
    }
}

async function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) return;
    
    try {
        const response = await fetchWithAuth(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.TRANSACTION_DETAIL(id)}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Transaction deleted successfully!', 'success');
            await fetchTransactions();
            await updateWalletBalance();
            return true;
        } else {
            showToast('Failed to delete transaction', 'error');
            return false;
        }
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showToast('Network error', 'error');
        return false;
    }
}

// ============= Display Functions =============

function displayTransactions(transactions) {
    const tableBody = document.getElementById('transactionsTableBody');
    if (!tableBody) return;
    
    if (!transactions || transactions.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="empty-state">No transactions found. Start by adding one.</td></tr>';
        return;
    }
    
    const sorted = [...transactions].sort((a, b) => new Date(b.date) - new Date(a.date));
    tableBody.innerHTML = sorted.map(t => createTransactionRow(t)).join('');
}

function createTransactionRow(transaction) {
    const amount = transaction.amount || 0;
    const isExpense = amount < 0;
    const absAmount = Math.abs(amount);
    const date = new Date(transaction.date).toLocaleDateString();
    
    return `
        <tr>
            <td>${date}</td>
            <td><span class="badge badge-success">completed</span></td>
            <td><span class="transaction-category">${transaction.category || 'Uncategorized'}</span></td>
            <td class="${isExpense ? 'amount-negative' : 'amount-positive'}">
                ${isExpense ? '-' : '+'}$${absAmount.toFixed(2)}
            </td>
            <td>${transaction.description || '-'}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteTransaction(${transaction.id})">🗑️</button>
            </td>
        </tr>
    `;
}

function updateTransactionStats(transactions) {
    const totalIncome = transactions.filter(t => t.amount > 0).reduce((sum, t) => sum + t.amount, 0);
    const totalExpenses = transactions.filter(t => t.amount < 0).reduce((sum, t) => sum + Math.abs(t.amount), 0);
    const netBalance = totalIncome - totalExpenses;
    
    const totalIncomeEl = document.getElementById('totalIncome');
    const totalExpensesEl = document.getElementById('totalExpenses');
    const netBalanceEl = document.getElementById('netBalance');
    const transactionCountEl = document.getElementById('transactionCount');
    
    if (totalIncomeEl) totalIncomeEl.textContent = `$${totalIncome.toFixed(2)}`;
    if (totalExpensesEl) totalExpensesEl.textContent = `$${totalExpenses.toFixed(2)}`;
    if (netBalanceEl) netBalanceEl.textContent = `$${netBalance.toFixed(2)}`;
    if (transactionCountEl) transactionCountEl.textContent = transactions.length;
}

// ============= Send/Deposit Functions =============

async function sendMoney(data) {
    const submitBtn = document.querySelector('#sendMoneyForm button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';
    }
    
    const transactionData = {
        amount: -Math.abs(data.amount),
        type: 'expense',
        description: data.description || `Payment to ${data.recipient}`,
        category: 'Transfer',
        status: 'completed',
        recipient: data.recipient,
        recipient_email: data.recipient_email
    };
    
    const result = await createTransaction(transactionData);
    
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Money';
    }
    
    if (result) {
        resetSendForm();
        showSuccessModal(data);
    }
    return result;
}

async function depositMoney(data) {
    const submitBtn = document.querySelector('#depositForm button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
    }
    
    const transactionData = {
        amount: Math.abs(data.amount),
        type: 'income',
        description: data.description || 'Deposit',
        category: 'Deposit',
        status: 'completed',
        payment_method: data.payment_method
    };
    
    const result = await createTransaction(transactionData);
    
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Deposit Money';
    }
    
    if (result) {
        resetDepositForm();
    }
    return result;
}

// ============= Modal Functions =============

function openTransactionModal() {
    const modal = document.getElementById('transactionModal');
    if (modal) modal.classList.add('active');
    const dateInput = document.getElementById('transactionDate');
    if (dateInput) dateInput.valueAsDate = new Date();
}

function closeTransactionModal() {
    const modal = document.getElementById('transactionModal');
    if (modal) modal.classList.remove('active');
    const form = document.getElementById('transactionForm');
    if (form) form.reset();
}

// ============= Filter Functions =============

function setupFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    const searchInput = document.getElementById('searchInput');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyFilters();
        });
    });
    
    if (searchInput) {
        searchInput.addEventListener('input', () => applyFilters());
    }
}

function applyFilters() {
    const activeFilter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    
    let filtered = [...currentTransactions];
    
    if (activeFilter === 'income') {
        filtered = filtered.filter(t => t.amount > 0);
    } else if (activeFilter === 'expense') {
        filtered = filtered.filter(t => t.amount < 0);
    } else if (activeFilter === 'this-month') {
        const now = new Date();
        const thisMonth = now.getMonth();
        const thisYear = now.getFullYear();
        filtered = filtered.filter(t => {
            const date = new Date(t.date);
            return date.getMonth() === thisMonth && date.getFullYear() === thisYear;
        });
    }
    
    if (searchTerm) {
        filtered = filtered.filter(t => 
            (t.description || '').toLowerCase().includes(searchTerm) ||
            (t.category || '').toLowerCase().includes(searchTerm)
        );
    }
    
    displayTransactions(filtered);
    updateTransactionStats(filtered);
}

// ============= Recent Transfers Display =============

async function displayRecentTransfers() {
    const container = document.getElementById('recentTransfersList');
    if (!container) return;
    
    try {
        const transactions = await fetchTransactions();
        const sends = transactions.filter(t => t.amount < 0).slice(0, 5);
        
        if (sends.length === 0) {
            container.innerHTML = '<div class="empty-state">No recent transfers</div>';
            return;
        }
        
        container.innerHTML = sends.map(t => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; border-bottom: 1px solid #e5e7eb;">
                <div>
                    <div style="font-weight: 600;">${escapeHtml(t.recipient || 'Unknown')}</div>
                    <div style="font-size: 0.75rem; color: var(--gray);">${new Date(t.date).toLocaleDateString()}</div>
                </div>
                <div style="color: var(--danger); font-weight: 600;">-$${Math.abs(t.amount).toFixed(2)}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading transfers:', error);
        container.innerHTML = '<div class="empty-state">Failed to load transfers</div>';
    }
}

// ============= Form Event Listeners =============

function initSendMoneyForm() {
    const form = document.getElementById('sendMoneyForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            recipient: document.getElementById('recipientName')?.value,
            recipient_email: document.getElementById('recipientEmail')?.value,
            amount: parseFloat(document.getElementById('amount')?.value || 0),
            purpose: document.getElementById('purpose')?.value,
            description: document.getElementById('description')?.value
        };
        
        if (data.amount > 0 && data.recipient && data.recipient_email) {
            await sendMoney(data);
        } else {
            showToast('Please fill all required fields', 'warning');
        }
    });
}

function initDepositForm() {
    const form = document.getElementById('depositForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            amount: parseFloat(document.getElementById('amount')?.value || 0),
            payment_method: document.getElementById('paymentMethod')?.value,
            account_number: document.getElementById('accountNumber')?.value,
            description: document.getElementById('description')?.value
        };
        
        if (data.amount > 0 && data.payment_method && data.account_number) {
            await depositMoney(data);
        } else {
            showToast('Please fill all required fields', 'warning');
        }
    });
}

function initTransactionForm() {
    const form = document.getElementById('transactionForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let amount = parseFloat(document.getElementById('transactionAmount')?.value || 0);
        const type = document.getElementById('transactionType')?.value;
        
        if (type === 'expense') {
            amount = -Math.abs(amount);
        } else {
            amount = Math.abs(amount);
        }
        
        const transactionData = {
            amount: amount,
            type: type,
            category: document.getElementById('transactionCategory')?.value,
            date: document.getElementById('transactionDate')?.value,
            description: document.getElementById('transactionDescription')?.value,
            status: 'completed'
        };
        
        await createTransaction(transactionData);
        closeTransactionModal();
        applyFilters();
    });
}

// ============= Page Initialization =============

if (window.location.pathname.includes('transaction.html') || window.location.pathname.includes('transactions.html')) {
    document.addEventListener('DOMContentLoaded', async () => {
        if (!isAuthenticated()) {
            window.location.href = 'login.html';
            return;
        }
        await fetchTransactions();
        setupFilters();
        initTransactionForm();
        applyFilters();
    });
}

if (window.location.pathname.includes('send_money.html')) {
    document.addEventListener('DOMContentLoaded', async () => {
        if (!isAuthenticated()) {
            window.location.href = 'login.html';
            return;
        }
        await updateWalletBalance();
        await displayRecentTransfers();
        initSendMoneyForm();
    });
}

if (window.location.pathname.includes('deposit.html')) {
    document.addEventListener('DOMContentLoaded', async () => {
        if (!isAuthenticated()) {
            window.location.href = 'login.html';
            return;
        }
        await updateWalletBalance();
        initDepositForm();
    });
}

// ============= Global Exports =============
window.deleteTransaction = deleteTransaction;
window.openTransactionModal = openTransactionModal;
window.closeTransactionModal = closeTransactionModal;
window.closeModal = closeModal;
window.sendMoney = sendMoney;
window.depositMoney = depositMoney;
window.displayRecentTransfers = displayRecentTransfers;