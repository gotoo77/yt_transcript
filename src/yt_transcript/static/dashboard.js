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
        
        this.initializeEventListeners();
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
                this.updateRefreshStatus('Données mises à jour');
            } else {
                this.showError(result.error || 'Erreur lors du chargement');
            }
        } catch (error) {
            console.error('Erreur dashboard:', error);
            this.showError('Erreur de connexion');
        } finally {
            this.isLoading = false;
        }
    }

    async renderDashboard(data) {
        console.log('Dashboard data:', data);
        
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

    async createAnalysesChart(dailyData) {
        const ctx = document.getElementById('analysesChart').getContext('2d');
        
        const labels = dailyData.map(d => new Date(d.date).toLocaleDateString('fr-FR'));
        const counts = dailyData.map(d => d.count);
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Analyses par jour',
                    data: counts,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
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
                            stepSize: 1
                        }
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 7
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
        const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'];
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
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
                            usePointStyle: true
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
        const colors = {
            'positif': '#28a745',
            'neutre': '#ffc107', 
            'négatif': '#dc3545'
        };
        
        const backgroundColors = labels.map(label => colors[label] || '#6c757d');
        
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
                            stepSize: 1
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
        
        return new Chart(ctx, {
            type: 'polarArea',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.6)',
                        'rgba(46, 204, 113, 0.6)', 
                        'rgba(241, 196, 15, 0.6)',
                        'rgba(230, 126, 34, 0.6)',
                        'rgba(231, 76, 60, 0.6)'
                    ],
                    borderColor: [
                        'rgba(52, 152, 219, 1)',
                        'rgba(46, 204, 113, 1)',
                        'rgba(241, 196, 15, 1)', 
                        'rgba(230, 126, 34, 1)',
                        'rgba(231, 76, 60, 1)'
                    ],
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
                            fontSize: 10
                        }
                    }
                }
            }
        });
    }

    async createWeekdayChart(weekdayData) {
        const ctx = document.getElementById('weekdayChart').getContext('2d');
        
        const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const weekdaysFr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
        
        const data = weekdays.map(day => weekdayData[day] || 0);
        
        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: weekdaysFr,
                datasets: [{
                    label: 'Activité',
                    data: data,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderWidth: 2,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
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
                            stepSize: 1
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
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: '#667eea',
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
                            stepSize: 1
                        }
                    },
                    x: {
                        ticks: {
                            fontSize: 10
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
                        Métriques de Contenu
                    </div>
                    <div class="metric-row">
                        <span>Mots moyens par analyse</span>
                        <strong>${this.formatNumber(metrics.avg_words_per_analysis || 0)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>Vocabulaire unique moyen</span>
                        <strong>${this.formatNumber(metrics.avg_unique_words || 0)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>Richesse vocabulaire</span>
                        <strong>${(metrics.avg_vocabulary_richness || 0).toFixed(2)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>Sentiment moyen</span>
                        <strong style="color: ${this.getSentimentColor(metrics.avg_sentiment)}">
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
                        Patterns d'Utilisation
                    </div>
                    <div class="metric-row">
                        <span>Analyses totales étudiées</span>
                        <strong>${patterns.total_patterns_analyzed || 0}</strong>
                    </div>
                    <div class="metric-row">
                        <span>Mode préféré</span>
                        <strong>${this.getPreferredMode(patterns.preferred_modes)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>Jour le plus actif</span>
                        <strong>${this.getMostActiveDay(patterns.active_weekdays)}</strong>
                    </div>
                    <div class="metric-row">
                        <span>Heure de pic</span>
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
                    <span>Plus de mots</span>
                    <strong>${this.formatNumber(top.words)} mots</strong>
                </div>
            `;
        }
        
        if (topAnalyses.most_complex && topAnalyses.most_complex.length > 0) {
            const top = topAnalyses.most_complex[0];
            html += `
                <div class="metric-row">
                    <span>Plus complexe</span>
                    <strong>${top.complexity.toFixed(3)}</strong>
                </div>
            `;
        }
        
        if (topAnalyses.richest_vocabulary && topAnalyses.richest_vocabulary.length > 0) {
            const top = topAnalyses.richest_vocabulary[0];
            html += `
                <div class="metric-row">
                    <span>Vocabulaire le plus riche</span>
                    <strong>${top.richness.toFixed(3)}</strong>
                </div>
            `;
        }
        
        if (html === '') {
            html = '<p class="text-muted text-center">Aucune donnée disponible</p>';
        }
        
        container.innerHTML = html;
    }

    exportReport(format, button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Export…';
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
        return num.toLocaleString('fr-FR');
    }

    getSentimentColor(score) {
        if (score > 0.1) return '#28a745';
        if (score < -0.1) return '#dc3545';
        return '#ffc107';
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
                    <strong>Impossible de charger le tableau de bord</strong>
                    <p>${message}</p>
                </div>
                <button class="btn btn-outline-danger" type="button" id="dashboard-retry">Réessayer</button>
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
                date.toLocaleString('fr-FR');
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
