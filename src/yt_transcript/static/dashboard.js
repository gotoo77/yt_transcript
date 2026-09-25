/**
 * Dashboard Analytics JavaScript - Phase 6
 * Gestion des graphiques interactifs et mise à jour temps réel
 */

class DashboardManager {
    constructor() {
        this.currentPeriod = 30;
        this.charts = {};
        this.refreshInterval = null;
        this.isLoading = false;
        this.lastData = null;

        this.initializeEventListeners();
        this.updatePeriodLabels();
        this.loadDashboard();
        this.startAutoRefresh();
    }

    initializeEventListeners() {
        // Period selector buttons
        document.querySelectorAll('[data-period]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.changePeriod(parseInt(e.target.dataset.period));
            });
        });

        document.querySelectorAll('[data-export-format]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.exportReport(btn.dataset.exportFormat, btn);
            });
        });

        window.addEventListener('yt-theme-change', () => {
            if (this.lastData) {
                this.renderCharts(this.lastData);
            }
        });

        window.addEventListener('yt-language-change', () => {
            this.updatePeriodLabels();
            if (this.lastData) {
                this.renderDashboard(this.lastData);
                this.updateRefreshStatus(this.t('dashboard.updated'));
            }
        });

        // Auto-refresh toggle (could be added)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
                this.loadDashboard();
            }
        });
    }

    t(key, params = {}) {
        return window.YTI18n?.t(key, params) ?? key;
    }

    dateLocale() {
        return window.YTI18n?.getDateLocale?.() ?? 'fr-FR';
    }

    updatePeriodLabels() {
        document.querySelectorAll('[data-period]').forEach(btn => {
            const days = Number(btn.dataset.period);
            btn.textContent = days === 365
                ? this.t('dashboard.year')
                : this.t('dashboard.days', {count:days});
        });
    }

    changePeriod(days) {
        this.currentPeriod = days;
        
        // Update UI
        document.querySelectorAll('[data-period]').forEach(btn => {
            const active = Number(btn.dataset.period) === days;
            btn.classList.toggle('active', active);
            btn.setAttribute('aria-pressed', String(active));
        });
        
        // Reload data
        this.loadDashboard();
    }

    async loadDashboard() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(true);
        
        try {
            const response = await fetch(`/api/dashboard/data?days=${this.currentPeriod}`);
            const result = await response.json();
            
            if (result.success && result.data) {
                await this.renderDashboard(result.data);
                this.showLoading(false);
                this.updateRefreshStatus(this.t('dashboard.updated'));
            } else {
                this.showError(result.error || this.t('dashboard.loadError'));
            }
        } catch (error) {
            console.error('Erreur dashboard:', error);
            this.showError(this.t('dashboard.connectionError'));
        } finally {
            this.isLoading = false;
        }
    }

    async renderDashboard(data) {
        console.log('Dashboard data:', data);
        this.lastData = data;
        
        // Render KPIs
        this.renderKPIs(data.kpis);
        
        // Render Charts
        await this.renderCharts(data);
        
        // Render Insights
        this.renderInsights(data.insights);
        
        // Update timestamp
        this.updateLastUpdate(data.generated_at);
    }

    renderKPIs(kpis) {
        if (!kpis) return;
        
        // Total Analyses
        document.getElementById('total-analyses').textContent = 
            this.formatNumber(kpis.totals?.analyses_period || 0);
        
        // Total Words
        document.getElementById('total-words').textContent = 
            this.formatNumber(kpis.totals?.words_analyzed || 0);
        
        // Reading Time
        document.getElementById('total-reading-time').textContent = 
            (kpis.totals?.reading_time_hours || 0) + 'h';
        
        // Average Complexity
        document.getElementById('avg-complexity').textContent = 
            (kpis.averages?.complexity_score || 0).toFixed(2);
    }

    async renderCharts(data) {
        // Destroy existing charts
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};

        // 1. Analyses Evolution Chart
        if (data.trends?.daily_analyses) {
            this.charts.analyses = await this.createAnalysesChart(data.trends.daily_analyses);
        }

        // 2. Analysis Modes Chart
        if (data.kpis?.distributions?.analysis_mode) {
            this.charts.modes = await this.createModesChart(data.kpis.distributions.analysis_mode);
        }

        // 3. Sentiment Chart
        if (data.kpis?.distributions?.sentiment) {
            this.charts.sentiment = await this.createSentimentChart(data.kpis.distributions.sentiment);
        }

        // 4. Complexity Distribution
        if (data.insights?.distributions?.complexity_ranges) {
            this.charts.complexity = await this.createComplexityChart(data.insights.distributions.complexity_ranges);
        }

        // 5. Weekly Activity
        if (data.insights?.content_patterns?.active_weekdays) {
            this.charts.weekday = await this.createWeekdayChart(data.insights.content_patterns.active_weekdays);
        }

        // 6. Word Count Ranges
        if (data.insights?.distributions?.word_count_ranges) {
            this.charts.wordRanges = await this.createWordRangesChart(data.insights.distributions.word_count_ranges);
        }
    }

    getChartPalette() {
        const styles = getComputedStyle(document.documentElement);
        const read = (name) => styles.getPropertyValue(name).trim();
        return {
            ink: read('--ui-ink'),
            muted: read('--ui-muted'),
            surface: read('--ui-surface'),
            grid: read('--ui-chart-grid'),
            accent: read('--ui-accent'),
            accentSoft: read('--ui-accent-soft'),
            success: read('--ui-success'),
            danger: read('--ui-danger'),
            warning: read('--ui-warning'),
            series: [
                read('--ui-chart-1'),
                read('--ui-chart-2'),
                read('--ui-chart-3'),
                read('--ui-chart-4'),
                read('--ui-chart-5')
            ]
        };
    }

    async createAnalysesChart(dailyData) {
        const ctx = document.getElementById('analysesChart').getContext('2d');
        
        const labels = dailyData.map(d => new Date(d.date).toLocaleDateString(this.dateLocale()));
        const counts = dailyData.map(d => d.count);
        const palette = this.getChartPalette();

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: this.t('dashboard.datasetAnalyses'),
                    data: counts,
                    borderColor: palette.accent,
                    backgroundColor: palette.accentSoft,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: palette.accent,
                    pointBorderColor: palette.surface,
                    pointBorderWidth: 2,
                    pointRadius: 6
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
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            color: palette.muted
                        },
                        grid: {
                            color: palette.grid
                        }
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 7,
                            color: palette.muted
                        },
                        grid: {
                            color: palette.grid
                        }
                    }
                },
                elements: {
                    point: {
                        hoverRadius: 8
                    }
                }
            }
        });
    }

    async createModesChart(modeData) {
        const ctx = document.getElementById('modesChart').getContext('2d');
        
        const labels = Object.keys(modeData);
        const data = Object.values(modeData);
        const palette = this.getChartPalette();
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
                datasets: [{
                    data: data,
                    backgroundColor: labels.map((_, index) => palette.series[index % palette.series.length]),
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            color: palette.muted
                        }
                    }
                }
            }
        });
    }

    async createSentimentChart(sentimentData) {
        const ctx = document.getElementById('sentimentChart').getContext('2d');
        
        const labels = Object.keys(sentimentData);
        const data = Object.values(sentimentData);
        const palette = this.getChartPalette();
        const colors = {
            'positif': palette.success,
            'neutre': palette.warning,
            'négatif': palette.danger
        };

        const backgroundColors = labels.map(label => colors[label] || palette.muted);
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            color: palette.muted
                        },
                        grid: {
                            color: palette.grid
                        }
                    }
                }
            }
        });
    }

    async createComplexityChart(complexityData) {
        const ctx = document.getElementById('complexityChart').getContext('2d');
        
        const labels = Object.keys(complexityData);
        const data = Object.values(complexityData);
        const palette = this.getChartPalette();

        return new Chart(ctx, {
            type: 'polarArea',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: palette.series,
                    borderColor: palette.surface,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            fontSize: 10,
                            color: palette.muted
                        }
                    }
                }
            }
        });
    }

    async createWeekdayChart(weekdayData) {
        const ctx = document.getElementById('weekdayChart').getContext('2d');
        
        const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const dayLabels = this.dateLocale() === 'en-GB'
            ? weekdays
            : ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

        const data = weekdays.map(day => weekdayData[day] || 0);
        const palette = this.getChartPalette();

        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: dayLabels,
                datasets: [{
                    label: this.t('dashboard.chartWeekday'),
                    data: data,
                    borderColor: palette.accent,
                    backgroundColor: palette.accentSoft,
                    borderWidth: 2,
                    pointBackgroundColor: palette.accent,
                    pointBorderColor: palette.surface,
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            color: palette.muted,
                            backdropColor: 'transparent'
                        },
                        grid: {
                            color: palette.grid
                        },
                        angleLines: {
                            color: palette.grid
                        },
                        pointLabels: {
                            color: palette.muted
                        }
                    }
                }
            }
        });
    }

    async createWordRangesChart(wordRangesData) {
        const ctx = document.getElementById('wordRangesChart').getContext('2d');
        
        const labels = Object.keys(wordRangesData);
        const data = Object.values(wordRangesData);
        const palette = this.getChartPalette();

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: palette.accentSoft,
                    borderColor: palette.accent,
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            color: palette.muted
                        },
                        grid: {
                            color: palette.grid
                        }
                    },
                    x: {
                        ticks: {
                            fontSize: 10,
                            color: palette.muted
                        },
                        grid: {
                            color: palette.grid
                        }
                    }
                }
            }
        });
    }

    renderInsights(insights) {
        if (!insights) return;
        
        const insightsContainer = document.getElementById('insights-section');
        let insightsHTML = '';
        
        // Content Metrics Card
        if (insights.content_metrics) {
            const metrics = insights.content_metrics;
            insightsHTML += `
                <div class="insight-card">
                    <div class="insight-title">
                        <i class="fas fa-chart-bar text-info"></i>
                        ${this.t('dashboard.contentMetrics')}
                    </div>
                    <div class="metric-row">
                        <span>${this.t('dashboard.avgWords')}</span>
                        <strong>${this.formatNumber(metrics.avg_words_per_analysis || 0)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>${this.t('dashboard.avgUnique')}</span>
                        <strong>${this.formatNumber(metrics.avg_unique_words || 0)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>${this.t('dashboard.avgRichness')}</span>
                        <strong>${(metrics.avg_vocabulary_richness || 0).toFixed(2)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>${this.t('dashboard.avgSentiment')}</span>
                        <strong class="${this.getSentimentClass(metrics.avg_sentiment)}">
                            ${(metrics.avg_sentiment || 0).toFixed(3)}
                        </strong>
                    </div>
                </div>
            `;
        }
        
        // Content Patterns Card
        if (insights.content_patterns) {
            const patterns = insights.content_patterns;
            insightsHTML += `
                <div class="insight-card">
                    <div class="insight-title">
                        <i class="fas fa-clock text-warning"></i>
                        ${this.t('dashboard.patterns')}
                    </div>
                    <div class="metric-row">
                        <span>${this.t('dashboard.patternsTotal')}</span>
                        <strong>${patterns.total_patterns_analyzed || 0}</strong>
                    </div>
                    <div class="metric-row">
                        <span>${this.t('dashboard.preferredMode')}</span>
                        <strong>${this.getPreferredMode(patterns.preferred_modes)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>${this.t('dashboard.activeDay')}</span>
                        <strong>${this.getMostActiveDay(patterns.active_weekdays)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>${this.t('dashboard.peakHour')}</span>
                        <strong>${this.getPeakHour(patterns.peak_hours)}h</strong>
                    </div>
                </div>
            `;
        }
        
        insightsContainer.innerHTML = insightsHTML;
        
        // Render top analyses
        this.renderTopAnalyses(insights.top_analyses);
    }

    renderTopAnalyses(topAnalyses) {
        if (!topAnalyses) return;
        
        const container = document.getElementById('top-analyses');
        let html = '';
        
        if (topAnalyses.most_words && topAnalyses.most_words.length > 0) {
            const top = topAnalyses.most_words[0];
            html += `
                <div class="metric-row">
                    <span>${this.t('dashboard.mostWords')}</span>
                    <strong>${this.formatNumber(top.words)} mots</strong>
                </div>
            `;
        }
        
        if (topAnalyses.most_complex && topAnalyses.most_complex.length > 0) {
            const top = topAnalyses.most_complex[0];
            html += `
                <div class="metric-row">
                    <span>${this.t('dashboard.mostComplex')}</span>
                    <strong>${top.complexity.toFixed(3)}</strong>
                </div>
            `;
        }
        
        if (topAnalyses.richest_vocabulary && topAnalyses.richest_vocabulary.length > 0) {
            const top = topAnalyses.richest_vocabulary[0];
            html += `
                <div class="metric-row">
                    <span>${this.t('dashboard.richest')}</span>
                    <strong>${top.richness.toFixed(3)}</strong>
                </div>
            `;
        }
        
        if (html === '') {
            html = `<p class="text-muted text-center">${this.t('dashboard.noData')}</p>`;
        }
        
        container.innerHTML = html;
    }

    exportReport(format, button) {
        const originalText = button.innerHTML;
        button.innerHTML = `<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> ${this.t('dashboard.exporting')}`;
        button.disabled = true;

        const link = document.createElement('a');
        link.href = `/api/dashboard/export/${format}?days=${this.currentPeriod}`;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        link.remove();

        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 2000);
    }

    // Utility functions
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString(this.dateLocale());
    }

    getSentimentClass(score) {
        if (score > 0.1) return 'sentiment-positive';
        if (score < -0.1) return 'sentiment-negative';
        return 'sentiment-neutral';
    }

    getPreferredMode(modes) {
        if (!modes) return 'N/A';
        const entries = Object.entries(modes);
        if (entries.length === 0) return 'N/A';
        return entries.sort((a, b) => b[1] - a[1])[0][0].charAt(0).toUpperCase() + entries.sort((a, b) => b[1] - a[1])[0][0].slice(1);
    }

    getMostActiveDay(weekdays) {
        if (!weekdays) return 'N/A';
        const entries = Object.entries(weekdays);
        if (entries.length === 0) return 'N/A';
        const dayName = entries.sort((a, b) => b[1] - a[1])[0][0];
        if (this.dateLocale() === 'en-GB') return dayName;
        const dayTranslations = {
            'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
            'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
        };
        return dayTranslations[dayName] || dayName;
    }

    getPeakHour(hours) {
        if (!hours) return 'N/A';
        const entries = Object.entries(hours);
        if (entries.length === 0) return 'N/A';
        return entries.sort((a, b) => b[1] - a[1])[0][0];
    }

    showLoading(show) {
        document.getElementById('loading-state').hidden = !show;
        document.getElementById('dashboard-content').hidden = show;
    }

    showError(message) {
        console.error('Dashboard error:', message);
        const loadingState = document.getElementById('loading-state');
        document.getElementById('dashboard-content').hidden = true;
        loadingState.hidden = false;
        loadingState.innerHTML = `
            <div class="ui-empty-state ui-empty-state-error" role="alert">
                <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                <div>
                    <strong>${this.t('dashboard.errorTitle')}</strong>
                    <p>${message}</p>
                </div>
                <button class="btn btn-outline-danger" type="button" id="dashboard-retry">${this.t('dashboard.retry')}</button>
            </div>
        `;
        document.getElementById('dashboard-retry').addEventListener('click', () => this.loadDashboard());
    }

    updateRefreshStatus(message) {
        document.getElementById('refresh-text').textContent = message;
        
        // Flash green
        const indicator = document.querySelector('.status-indicator');
        indicator.style.background = '#28a745';
        setTimeout(() => {
            indicator.style.background = '#28a745';
        }, 1000);
    }

    updateLastUpdate(timestamp) {
        if (timestamp) {
            const date = new Date(timestamp);
            document.getElementById('last-update').textContent = 
                date.toLocaleString(this.dateLocale());
        }
    }

    startAutoRefresh() {
        this.stopAutoRefresh();
        
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            if (!document.hidden) {
                this.loadDashboard();
            }
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new DashboardManager();
});

// Export the manager reference for diagnostics/integration hooks.
window.dashboard = dashboard;
