/**
 * Main JavaScript for Smart Financial Analyzer
 */

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Enable tooltips and popovers if Bootstrap JS is loaded
    if (typeof bootstrap !== 'undefined') {
        // Initialize all tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize all popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // Setup API request error handling
    function handleApiError(error) {
        console.error('API Error:', error);
        return {
            success: false,
            error: 'An unexpected error occurred. Please try again.'
        };
    }
    
    // Format currency for Indian Rupees
    window.formatIndianCurrency = function(amount) {
        if (!amount) return '₹0';
        
        // Format with commas for Indian number system (lakhs, crores)
        const formatter = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        return formatter.format(amount);
    };
    
    // Format percentage values
    window.formatPercentage = function(value) {
        if (value === null || value === undefined) return '-';
        
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}%`;
    };
    
    // Convert date strings to formatted dates
    window.formatDate = function(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };
    
    // Load stock data from API
    window.fetchStockData = function(symbol, exchange = 'NSE', callback) {
        fetch(`/api/stocks/data?symbol=${symbol}&exchange=${exchange}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.stock_data) {
                    if (callback && typeof callback === 'function') {
                        callback(data.stock_data);
                    }
                } else {
                    console.error('Error fetching stock data:', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                handleApiError(error);
            });
    };
    
    // Load historical stock data from API
    window.fetchHistoricalData = function(symbol, exchange = 'NSE', period = '1mo', callback) {
        fetch(`/api/stocks/historical?symbol=${symbol}&exchange=${exchange}&period=${period}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.historical_data) {
                    if (callback && typeof callback === 'function') {
                        callback(data.historical_data);
                    }
                } else {
                    console.error('Error fetching historical data:', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                handleApiError(error);
            });
    };
    
    // Submit financial question to insights API
    window.submitFinancialQuestion = function(query, callback) {
        fetch('/api/insights/question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (callback && typeof callback === 'function') {
                        callback(data);
                    }
                } else {
                    console.error('Error getting insights:', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                handleApiError(error);
            });
    };
    
    // Get book recommendations from API
    window.getBookRecommendations = function(topic, goal, callback) {
        fetch('/api/books/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                topic: topic,
                goal: goal
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (callback && typeof callback === 'function') {
                        callback(data);
                    }
                } else {
                    console.error('Error getting book recommendations:', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                handleApiError(error);
            });
    };
    
    // Apply syntax highlighting to code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    if (codeBlocks.length > 0 && typeof hljs !== 'undefined') {
        codeBlocks.forEach(block => {
            hljs.highlightBlock(block);
        });
    }
    
    // Handle stock search form submission
    const stockSearchForm = document.getElementById('stockSearchForm');
    if (stockSearchForm) {
        stockSearchForm.addEventListener('submit', function(event) {
            const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
            const exchange = document.getElementById('stockExchange').value;
            
            if (!symbol) {
                event.preventDefault();
                alert('Please enter a valid stock symbol');
            }
        });
    }
    
    // Handle insights form
    const insightsForm = document.getElementById('insightsForm');
    if (insightsForm) {
        const insightsQuery = document.getElementById('insightsQuery');
        const insightsButton = document.getElementById('insightsButton');
        
        insightsForm.addEventListener('submit', function(event) {
            if (!insightsQuery.value.trim()) {
                event.preventDefault();
                alert('Please enter a question');
                return;
            }
            
            // Set loading state for button
            insightsButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            insightsButton.disabled = true;
        });
    }
    
    // Handle books recommendation form
    const booksForm = document.getElementById('booksForm');
    if (booksForm) {
        const topicInput = document.getElementById('topic');
        const goalInput = document.getElementById('goal');
        const recommendButton = document.getElementById('recommendButton');
        
        booksForm.addEventListener('submit', function(event) {
            if (!topicInput.value.trim() || !goalInput.value.trim()) {
                event.preventDefault();
                alert('Please enter both a financial topic and goal');
                return;
            }
            
            // Set loading state for button
            recommendButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Finding Books...';
            recommendButton.disabled = true;
        });
    }
    
    // Enable scrollable containers with perfect-scrollbar if available
    const scrollContainers = document.querySelectorAll('.scrollable');
    if (scrollContainers.length > 0 && typeof PerfectScrollbar !== 'undefined') {
        scrollContainers.forEach(container => {
            new PerfectScrollbar(container);
        });
    }
});

// NL2BR - Convert newlines to <br> tags
if (!String.prototype.nl2br) {
    String.prototype.nl2br = function() {
        return this.replace(/\n/g, '<br>');
    };
}
