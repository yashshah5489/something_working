/**
 * Chart.js implementations for Smart Financial Analyzer
 */

// Color palette for India-themed charts
const CHART_COLORS = {
    primary: '#3498db',
    secondary: '#2ecc71',
    success: '#27ae60',
    danger: '#e74c3c',
    warning: '#f39c12',
    info: '#00bcd4',
    light: '#f1f1f1',
    dark: '#1a1a2e',
    saffron: '#FF9933',
    white: '#FFFFFF',
    navy: '#000080',
    green: '#138808'
};

// Default chart options for dark theme
const darkThemeOptions = {
    plugins: {
        legend: {
            labels: {
                color: '#f1f1f1'
            }
        }
    },
    scales: {
        x: {
            grid: {
                color: 'rgba(255, 255, 255, 0.1)'
            },
            ticks: {
                color: '#a3a3a3'
            }
        },
        y: {
            grid: {
                color: 'rgba(255, 255, 255, 0.1)'
            },
            ticks: {
                color: '#a3a3a3'
            }
        }
    }
};

/**
 * Create Market Overview Chart
 * @param {CanvasRenderingContext2D} ctx - The canvas context
 * @returns {Chart} Chart.js chart instance
 */
function createMarketOverviewChart(ctx) {
    // Mock data - will be replaced with actual API data in production
    const labels = [];
    const niftyData = [];
    const sensexData = [];
    
    // Generate last 7 days
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(today.getDate() - i);
        labels.push(date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }));
    }
    
    // Create a sample pattern based on realistic market movements
    // This will be replaced with actual data from APIs in production
    niftyData.push(19200);
    niftyData.push(19250);
    niftyData.push(19310);
    niftyData.push(19280);
    niftyData.push(19350);
    niftyData.push(19400);
    niftyData.push(19420);
    
    // Create approximate Sensex values (roughly 3.3x Nifty)
    for (let i = 0; i < niftyData.length; i++) {
        sensexData.push(niftyData[i] * 3.3);
    }
    
    const marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'NIFTY 50',
                    data: niftyData,
                    borderColor: CHART_COLORS.saffron,
                    backgroundColor: 'rgba(255, 153, 51, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    yAxisID: 'y'
                },
                {
                    label: 'SENSEX',
                    data: sensexData,
                    borderColor: CHART_COLORS.green,
                    backgroundColor: 'rgba(19, 136, 8, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#f1f1f1'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a3a3a3'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'NIFTY 50',
                        color: CHART_COLORS.saffron
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a3a3a3'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'SENSEX',
                        color: CHART_COLORS.green
                    },
                    grid: {
                        drawOnChartArea: false,
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a3a3a3'
                    }
                }
            }
        }
    });
    
    return marketChart;
}

/**
 * Create Sector Performance Chart
 * @param {CanvasRenderingContext2D} ctx - The canvas context
 * @param {Array} sectorData - Array of sector performance data
 * @returns {Chart} Chart.js chart instance
 */
function createSectorPerformanceChart(ctx, sectorData) {
    // Process data
    let sectors = [];
    let performances = [];
    let backgroundColors = [];
    
    // If we have sector data, use it
    if (sectorData && sectorData.length > 0) {
        // Sort by performance
        sectorData.sort((a, b) => b.change - a.change);
        
        // Limit to top 5 sectors
        const topSectors = sectorData.slice(0, 5);
        
        for (const item of topSectors) {
            sectors.push(item.sector);
            performances.push(item.change);
            
            // Choose color based on performance
            if (item.change > 1) {
                backgroundColors.push(CHART_COLORS.success);
            } else if (item.change > 0) {
                backgroundColors.push(CHART_COLORS.secondary);
            } else if (item.change > -1) {
                backgroundColors.push(CHART_COLORS.warning);
            } else {
                backgroundColors.push(CHART_COLORS.danger);
            }
        }
    } else {
        // Use placeholder data if no sector data is available
        sectors = ['IT', 'Banking', 'Pharma', 'Auto', 'FMCG'];
        performances = [2.3, 1.2, 0.7, -0.5, -1.2];
        backgroundColors = [
            CHART_COLORS.success,
            CHART_COLORS.secondary,
            CHART_COLORS.secondary,
            CHART_COLORS.warning,
            CHART_COLORS.danger
        ];
    }
    
    const sectorChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sectors,
            datasets: [{
                label: 'Performance (%)',
                data: performances,
                backgroundColor: backgroundColors,
                borderWidth: 1,
                borderColor: 'rgba(255, 255, 255, 0.3)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let value = context.raw;
                            return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a3a3a3',
                        callback: function(value) {
                            return `${value >= 0 ? '+' : ''}${value}%`;
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#f1f1f1'
                    }
                }
            }
        }
    });
    
    return sectorChart;
}

/**
 * Create Stock Price Chart for individual stock pages
 * @param {CanvasRenderingContext2D} ctx - The canvas context
 * @param {Array} dates - Array of date strings
 * @param {Array} prices - Array of price values
 * @param {String} symbol - Stock symbol
 * @param {Boolean} isPositive - Whether the stock is showing positive or negative change
 * @returns {Chart} Chart.js chart instance
 */
function createStockPriceChart(ctx, dates, prices, symbol, isPositive = true) {
    const borderColor = isPositive ? CHART_COLORS.secondary : CHART_COLORS.danger;
    const backgroundColor = isPositive ? 'rgba(46, 204, 113, 0.1)' : 'rgba(231, 76, 60, 0.1)';
    
    const stockChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: `${symbol} Price (₹)`,
                data: prices,
                borderColor: borderColor,
                backgroundColor: backgroundColor,
                borderWidth: 2,
                fill: true,
                tension: 0.2,
                pointRadius: 1,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `₹${context.raw.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        maxRotation: 0,
                        color: '#a3a3a3',
                        maxTicksLimit: 8
                    }
                },
                y: {
                    position: 'right',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a3a3a3',
                        callback: function(value) {
                            return `₹${value}`;
                        }
                    }
                }
            }
        }
    });
    
    return stockChart;
}

/**
 * Create Volume Chart for stock analysis
 * @param {CanvasRenderingContext2D} ctx - The canvas context
 * @param {Array} dates - Array of date strings
 * @param {Array} volumes - Array of volume values
 * @returns {Chart} Chart.js chart instance
 */
function createVolumeChart(ctx, dates, volumes) {
    const volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Trading Volume',
                data: volumes,
                backgroundColor: CHART_COLORS.info,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 0,
                        color: '#a3a3a3',
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a3a3a3',
                        callback: function(value) {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M';
                            } else if (value >= 1000) {
                                return (value / 1000).toFixed(1) + 'K';
                            }
                            return value;
                        }
                    }
                }
            }
        }
    });
    
    return volumeChart;
}

/**
 * Create Comparative Analysis Chart (comparing multiple stocks)
 * @param {CanvasRenderingContext2D} ctx - The canvas context
 * @param {Array} stocksData - Array of stock data objects
 * @returns {Chart} Chart.js chart instance
 */
function createComparativeChart(ctx, stocksData) {
    const datasets = [];
    const colors = [
        CHART_COLORS.primary,
        CHART_COLORS.secondary,
        CHART_COLORS.warning,
        CHART_COLORS.danger,
        CHART_COLORS.info
    ];
    
    // Process each stock's data
    stocksData.forEach((stock, index) => {
        datasets.push({
            label: stock.symbol,
            data: stock.prices,
            borderColor: colors[index % colors.length],
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 1,
            pointHoverRadius: 5
        });
    });
    
    const compareChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: stocksData[0].dates, // Assuming all stocks have the same date range
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#f1f1f1'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a3a3a3'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a3a3a3',
                        callback: function(value) {
                            return `₹${value}`;
                        }
                    }
                }
            }
        }
    });
    
    return compareChart;
}

/**
 * Create Asset Allocation Chart (pie/doughnut chart)
 * @param {CanvasRenderingContext2D} ctx - The canvas context
 * @param {Array} labels - Asset class labels
 * @param {Array} data - Asset allocation percentages
 * @returns {Chart} Chart.js chart instance
 */
function createAssetAllocationChart(ctx, labels, data) {
    const backgroundColors = [
        CHART_COLORS.primary,
        CHART_COLORS.secondary,
        CHART_COLORS.warning,
        CHART_COLORS.danger,
        CHART_COLORS.info,
        CHART_COLORS.saffron
    ];
    
    const allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: 'rgba(255, 255, 255, 0.3)',
                borderWidth: 1,
                hoverOffset: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#f1f1f1',
                        padding: 10,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${value}%`;
                        }
                    }
                }
            }
        }
    });
    
    return allocationChart;
}
