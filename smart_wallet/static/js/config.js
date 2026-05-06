const CONFIG = {
    API_BASE_URL: 'http://127.0.0.1:8000',
    API_ENDPOINTS: {

        REGISTER: '/auth/users/',
        ACTIVATION: '/auth/users/activation/',
        LOGIN: '/auth/jwt/create/',
        REFRESH: '/auth/jwt/refresh/',
        VERIFY: '/auth/jwt/verify/',
        USER_DETAILS: '/auth/users/me/',
        USER_UPDATE: '/auth/users/me/',
        
        ADVISOR_ASK: '/advisor/ask/',
        ADVISOR_HISTORY: '/advisor/history/',
        
        BUDGETS: '/api/budgets/',
        BUDGET_DETAIL: (id) => `/api/budgets/${id}/`,
        
        SAVING_GOALS: '/api/saving-goals/',
        SAVING_GOAL_DETAIL: (id) => `/api/saving-goals/${id}/`,
        
        CATEGORIES: '/api/categories/',
        CATEGORY_DETAIL: (id) => `/api/categories/${id}/`,
        
        TRANSACTIONS: '/api/transactions/',
        TRANSACTION_DETAIL: (id) => `/api/transactions/${id}/`,
        RECENT_TRANSACTIONS: '/api/transactions/recent/',
        
        WALLET_BALANCE: '/api/wallet/balance/',
        ACTIVE_GOALS: '/api/goals/active/',
        
        NOTIFICATIONS: '/api/notifications/',
        NOTIFICATION_DETAIL: (id) => `/api/notifications/${id}/`
    },
    STORAGE_KEYS: {
        ACCESS_TOKEN: 'access_token',
        REFRESH_TOKEN: 'refresh_token',
        USER_DATA: 'user_data'
    }
};

function getAccessToken() {
    return localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
}

function setTokens(access, refresh) {
    localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, access);
    localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, refresh);
}

function clearTokens() {
    localStorage.removeItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_DATA);
}

function isAuthenticated() {
    return getAccessToken() !== null;
}