function showUiMessage(message, tone = 'info') {
    const status = document.getElementById('ui-status');
    status.className = `ui-status ui-status-${tone}`;
    status.textContent = message;
    status.hidden = false;
    window.clearTimeout(showUiMessage.timeoutId);
    showUiMessage.timeoutId = window.setTimeout(() => {
        status.hidden = true;
    }, 5000);
}

document.getElementById('transcribe-btn').addEventListener('click', async () => {
    const videoId = document.getElementById('video-id').value.trim();
    const selectedLanguage = document.getElementById('language-select').value;
    console.log("[Transcription] ID ou URL saisi :", videoId);
    console.log("[Transcription] Langue sélectionnée :", selectedLanguage);

    if (!videoId) {
        document.getElementById('status-msg').textContent = '⚠️ Veuillez saisir un ID ou URL de vidéo.';
        return;
    }

    // Désactivation du bouton pendant le traitement
    const transcribeBtn = document.getElementById('transcribe-btn');
    const originalText = transcribeBtn.textContent;
    transcribeBtn.disabled = true;
    transcribeBtn.textContent = 'Traitement...';
    
    const languageText = selectedLanguage === 'auto' ? 'auto-détection' : selectedLanguage;
    document.getElementById('status-msg').textContent = `⏳ Transcription en cours (${languageText})...`;
    document.getElementById('analyze-btn').disabled = true;

    try {
        const res = await fetch('/transcribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                video_id: videoId,
                language: selectedLanguage 
            })
        });

        const data = await res.json();
        console.log("[Transcription] Réponse du serveur :", data);

        if (data.success) {
            document.getElementById('transcript-textarea').value = data.transcript;
            document.getElementById('analyze-btn').disabled = false;
            document.getElementById('summary-btn').disabled = false;
            
            // Activer aussi les autres boutons
            document.getElementById('format-btn').disabled = false;
            document.getElementById('download-btn').disabled = false;
            
            const charCount = data.transcript.length;
            const message = data.message || 'Transcription réussie';
            
            // Afficher des informations détaillées sur la langue détectée
            let statusMessage = `✅ ${message} (${charCount} caractères)`;
            
            if (data.detected_language && data.detected_language_name) {
                console.log('🌍 Langue détectée:', data.detected_language_name);
                if (data.requested_language !== 'auto' && data.detected_language !== data.requested_language) {
                    statusMessage += ` 🔄 Fallback appliqué`;
                }
            }
            
            document.getElementById('status-msg').textContent = statusMessage;
            
            console.log('✅ Transcription réussie, boutons activés');
            
        } else {
            document.getElementById('status-msg').textContent = `❌ ${data.error}`;
        }
    } catch (err) {
        console.error("[Transcription] Erreur réseau :", err);
        document.getElementById('status-msg').textContent = '❌ Erreur de connexion au serveur';
    } finally {
        // Réactivation du bouton
        transcribeBtn.disabled = false;
        transcribeBtn.textContent = originalText;
    }
});

document.getElementById('format-btn').addEventListener('click', () => {
    const textarea = document.getElementById('transcript-textarea');
    console.log("[Format] Texte avant mise en forme :", textarea.value.slice(0, 200));
    textarea.value = textarea.value.replace(/\.\s+/g, '.\n');
    console.log("[Format] Texte après mise en forme :", textarea.value.slice(0, 200));
});

document.getElementById('download-btn').addEventListener('click', () => {
    const text = document.getElementById('transcript-textarea').value;
    const id = document.getElementById('video-id').value.trim().slice(-11) || 'video';
    console.log("[Download] Enregistrement avec nom : transcript_" + id + ".txt");

    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `transcript_${id}.txt`;
    a.click();
});

document.getElementById('analyze-btn').addEventListener('click', async () => {
    console.log('📈 Bouton Analyser cliqué!');
    const text = document.getElementById('transcript-textarea').value.trim();
    const mode = document.getElementById('mode-select').value;
    
    // Récupération du nombre de mots (seulement pour le mode style)
    const maxWords = mode === 'style' ? 
        parseInt(document.getElementById('max-words-input').value) || 30 : 30;
    
    console.log('Texte:', text.length, 'caractères, Mode:', mode, 'Max mots:', maxWords);

    if (!text) {
        showUiMessage('Veuillez d’abord transcrire une vidéo ou saisir du texte.', 'warning');
        return;
    }

    // Désactivation du bouton pendant l'analyse
    const analyzeBtn = document.getElementById('analyze-btn');
    const originalText = analyzeBtn.textContent;
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyse en cours...';

    console.log(`[Analyse] Début analyse (mode: ${mode}, max_words: ${maxWords})`);
    try {
        const requestBody = { text, mode };
        
        // Ajouter max_words seulement pour le mode style
        if (mode === 'style') {
            requestBody.max_words = maxWords;
        }
        
        const res = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await res.json();
        console.log("[Analyse] Résultat reçu :", data);

        const resultDiv = document.getElementById('analysis-results');
        
        if (data.success) {
            if (mode === 'style') {
                // Affichage pour l'analyse de style
                const maxWordsDisplay = mode === 'style' ? maxWords : data.result.length;
                resultDiv.innerHTML = `
                    <h5><i class="fas fa-chart-bar"></i> Analyse stylistique</h5>
                    <p><strong>Top ${maxWordsDisplay} des mots les plus fréquents</strong> (${data.result.length} résultats sur ${data.word_count} mots analysés)</p>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-group list-group-flush">
                                ${data.result.slice(0, Math.ceil(data.result.length/2)).map(([word, count]) => 
                                    `<li class="list-group-item d-flex justify-content-between align-items-center">
                                        <span><mark>${word}</mark></span>
                                        <span class="badge bg-primary rounded-pill">${count}</span>
                                    </li>`
                                ).join('')}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="list-group list-group-flush">
                                ${data.result.slice(Math.ceil(data.result.length/2)).map(([word, count]) => 
                                    `<li class="list-group-item d-flex justify-content-between align-items-center">
                                        <span><mark>${word}</mark></span>
                                        <span class="badge bg-primary rounded-pill">${count}</span>
                                    </li>`
                                ).join('')}
                            </ul>
                        </div>
                    </div>
                `;
                
                // Créer le graphique de fréquence
                createFrequencyChart(data.result.slice(0, 15)); // Top 15 pour la lisibilité
                
            } else if (mode === 'concepts') {
                // Affichage pour l'analyse conceptuelle
                if (data.result.length > 0) {
                        resultDiv.innerHTML = `
                            <h5><i class="fas fa-brain"></i> Analyse conceptuelle</h5>
                            <p><strong>${data.result.length} thèmes détectés</strong> dans le texte (${data.word_count} mots analysés)</p>
                            <div class="concept-grid">
                                ${data.result.map(([category, info]) => `
                                    <article class="concept-category">
                                        <div class="concept-heading">
                                            <h6 class="text-capitalize mb-0">
                                                <i class="fas fa-tag text-primary" aria-hidden="true"></i> ${category}
                                            </h6>
                                            <span class="badge bg-success">${info.percentage}%</span>
                                        </div>
                                        <p class="concept-score"><strong>${info.score}</strong> mentions</p>
                                        <div class="concept-keywords" aria-label="Mots-clés">
                                            ${[...new Set(info.words)].map(word => `<span class="badge bg-secondary">${word}</span>`).join('')}
                                        </div>
                                    </article>
                                `).join('')}
                            </div>
                        `;
                        
                        // Créer le graphique des concepts
                        createConceptsChart(data.result);
                    } else {
                        resultDiv.innerHTML = `
                            <h5><i class="fas fa-brain"></i> Analyse conceptuelle</h5>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i> Aucun thème spécifique détecté dans ce texte.
                                Les concepts recherchés: technologie, économie, social, santé, environnement.
                            </div>
                        `;
                    }
            }
            
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> ${data.error}
                </div>
            `;
        }
        
        resultDiv.hidden = false;
        resultDiv.scrollIntoView({ behavior: 'smooth' });
        
        // Charger les statistiques et le nuage de mots après l'analyse
        loadStatistics(text);
        loadWordCloud(text);
        
        // Afficher l'analyse de sentiment si disponible
        if (data.advanced_analysis) {
            displayAdvancedAnalysis(data.advanced_analysis);
        }
        
    } catch (err) {
        console.error("[Analyse] Erreur réseau :", err);
        const resultDiv = document.getElementById('analysis-results');
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> Erreur de connexion au serveur
            </div>
        `;
        resultDiv.hidden = false;
    } finally {
        // Réactivation du bouton
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = originalText;
    }
});

// === NOUVELLES FONCTIONNALITÉS PHASE 2 ===

// Fonction de recherche dans la transcription
document.getElementById('search-btn').addEventListener('click', () => {
    const searchBox = document.getElementById('search-box');
    const searchInput = document.getElementById('search-input');
    
    searchBox.hidden = !searchBox.hidden;
    if (!searchBox.hidden) {
        searchInput.focus();
    } else {
        clearHighlights();
    }
});

// Recherche en temps réel
document.getElementById('search-input').addEventListener('input', function() {
    const query = this.value.trim();
    const textarea = document.getElementById('transcript-textarea');
    const resultsDiv = document.getElementById('search-results');
    
    if (!query) {
        clearHighlights();
        resultsDiv.textContent = '';
        return;
    }
    
    if (query.length < 2) {
        resultsDiv.textContent = 'Tapez au moins 2 caractères...';
        return;
    }
    
    searchInText(query, textarea.value);
});

// Effacer la recherche
document.getElementById('clear-search').addEventListener('click', () => {
    document.getElementById('search-input').value = '';
    clearHighlights();
    document.getElementById('search-results').textContent = '';
});

function searchInText(query, text) {
    const resultsDiv = document.getElementById('search-results');
    const textarea = document.getElementById('transcript-textarea');
    
    if (!text || !query) {
        resultsDiv.textContent = '';
        return;
    }
    
    const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
    const matches = text.match(regex);
    
    if (matches) {
        resultsDiv.innerHTML = `<i class="fas fa-search"></i> ${matches.length} occurrence(s) trouvée(s)`;
        
        // Surlignage dans le textarea (simulation avec styles)
        const highlightedText = text.replace(regex, '<span class="highlight">$&</span>');
        // Note: Le textarea ne supporte pas le HTML, donc on utilise une approche alternative
        
    } else {
        resultsDiv.innerHTML = `<i class="fas fa-search"></i> Aucun résultat pour "${query}"`;
    }
}

function clearHighlights() {
    // Clear highlights - dans une vraie implémentation, on utiliserait un div overlay
    document.getElementById('search-results').textContent = '';
}

// Génération de résumé
document.getElementById('summary-btn').addEventListener('click', async () => {
    console.log('📄 Bouton Résumé cliqué!');
    const text = document.getElementById('transcript-textarea').value.trim();
    
    if (!text) {
        showUiMessage('Veuillez d’abord transcrire une vidéo ou saisir du texte.', 'warning');
        return;
    }
    
    const summaryBtn = document.getElementById('summary-btn');
    const originalText = summaryBtn.textContent;
    summaryBtn.disabled = true;
    summaryBtn.textContent = 'Génération...';
    
    try {
        const res = await fetch('/summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, num_sentences: 3 })
        });
        
        const data = await res.json();
        
        if (data.success) {
            const summarySection = document.getElementById('summary-section');
            const summaryContent = document.getElementById('summary-content');
            
            summaryContent.innerHTML = `
                <div class="mb-3">
                    <p class="mb-2"><strong>Résumé :</strong></p>
                    <p class="lead">${data.summary}</p>
                </div>
                <div class="row text-center">
                    <div class="col-4">
                        <small class="text-muted">Texte original</small><br>
                        <strong>${data.original_length}</strong> caractères
                    </div>
                    <div class="col-4">
                        <small class="text-muted">Résumé</small><br>
                        <strong>${data.summary_length}</strong> caractères
                    </div>
                    <div class="col-4">
                        <small class="text-muted">Compression</small><br>
                        <strong class="text-success">${data.compression_ratio}%</strong>
                    </div>
                </div>
            `;
            
            summarySection.hidden = false;
            summarySection.classList.add('fade-in');
            summarySection.scrollIntoView({ behavior: 'smooth' });
            
        } else {
            showUiMessage('Erreur : ' + data.error, 'danger');
        }
        
    } catch (err) {
        console.error('Erreur résumé:', err);
        showUiMessage('Erreur de connexion au serveur.', 'danger');
    } finally {
        summaryBtn.disabled = false;
        summaryBtn.textContent = originalText;
    }
});

// Variables globales pour les graphiques
let frequencyChart = null;
let conceptsChart = null;

// Activer les boutons quand du texte est saisi manuellement
document.getElementById('transcript-textarea').addEventListener('input', function() {
    const text = this.value.trim();
    const hasText = text.length > 10;
    
    document.getElementById('analyze-btn').disabled = !hasText;
    document.getElementById('summary-btn').disabled = !hasText;
    document.getElementById('format-btn').disabled = !hasText;
    document.getElementById('download-btn').disabled = !hasText;
    
    console.log('Texte détecté:', hasText ? 'Boutons activés' : 'Boutons désactivés');
});

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier s'il y a déjà du texte dans la zone
    const textarea = document.getElementById('transcript-textarea');
    const text = textarea.value.trim();
    const hasText = text.length > 10;
    
    // Activer/désactiver les boutons en conséquence
    document.getElementById('analyze-btn').disabled = !hasText;
    document.getElementById('summary-btn').disabled = !hasText;
    document.getElementById('format-btn').disabled = !hasText;
    document.getElementById('download-btn').disabled = !hasText;
    
    console.log('🚀 Application initialisée - Boutons:', hasText ? 'activés' : 'désactivés');
});

// Fonction pour créer le graphique de fréquence
function createFrequencyChart(data) {
    const ctx = document.getElementById('frequency-chart').getContext('2d');
    
    // Détruire le graphique existant
    if (frequencyChart) {
        frequencyChart.destroy();
    }
    
    const labels = data.map(([word, count]) => word);
    const counts = data.map(([word, count]) => count);
    
    frequencyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Fréquence',
                data: counts,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Mots les plus fréquents'
                },
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
                        maxRotation: 45
                    }
                }
            }
        }
    });
    
    document.getElementById('frequency-chart-panel').hidden = false;
    document.getElementById('concepts-chart-panel').hidden = true;
    const chartsSection = document.getElementById('charts-section');
    chartsSection.hidden = false;
    chartsSection.classList.add('fade-in');
}

// Fonction pour créer le graphique des concepts
function createConceptsChart(data) {
    const ctx = document.getElementById('concepts-chart').getContext('2d');
    
    // Détruire le graphique existant
    if (conceptsChart) {
        conceptsChart.destroy();
    }
    
    const labels = data.map(([category, info]) => category);
    const percentages = data.map(([category, info]) => info.percentage);
    
    const colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'
    ];
    
    conceptsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: percentages,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Répartition des concepts'
                },
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
    
    document.getElementById('frequency-chart-panel').hidden = true;
    document.getElementById('concepts-chart-panel').hidden = false;
    const chartsSection = document.getElementById('charts-section');
    if (chartsSection.hidden) {
        chartsSection.hidden = false;
        chartsSection.classList.add('fade-in');
    }
}

// Fonction pour charger les statistiques
async function loadStatistics(text) {
    try {
        const res = await fetch('/statistics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        const data = await res.json();
        
        if (data.success) {
            const statsContent = document.getElementById('stats-content');
            const stats = data.statistics;
            
            statsContent.innerHTML = `
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-tile">
                        <h4 class="text-primary mb-1">${stats.total_words}</h4>
                        <small class="text-muted">Mots total</small>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-tile">
                        <h4 class="text-success mb-1">${stats.unique_words}</h4>
                        <small class="text-muted">Mots uniques</small>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-tile">
                        <h4 class="text-info mb-1">${stats.reading_time_minutes}min</h4>
                        <small class="text-muted">Temps lecture</small>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-tile">
                        <h4 class="text-warning mb-1">${stats.complexity_score}</h4>
                        <small class="text-muted">Complexité</small>
                    </div>
                </div>
                <div class="col-12 mt-3">
                    <div class="row text-center">
                        <div class="col-md-4">
                            <strong>Richesse vocabulaire:</strong> ${stats.vocabulary_richness}%
                        </div>
                        <div class="col-md-4">
                            <strong>Longueur moyenne mot:</strong> ${stats.average_word_length} caract.
                        </div>
                        <div class="col-md-4">
                            <strong>Phrases:</strong> ${stats.sentences}
                        </div>
                    </div>
                </div>
            `;
            
            const statsSection = document.getElementById('stats-section');
            statsSection.hidden = false;
            statsSection.classList.add('fade-in');
        }
        
    } catch (err) {
        console.error('Erreur chargement statistiques:', err);
    }
}

// Fonction pour charger le nuage de mots
async function loadWordCloud(text) {
    try {
        const res = await fetch('/wordcloud', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, max_words: 40 })
        });
        
        const data = await res.json();
        
        if (data.success) {
            const wordCloudDiv = document.getElementById('word-cloud');
            
            wordCloudDiv.innerHTML = data.wordcloud_data.map(wordInfo => `
                <span class="word" style="
                    font-size: ${wordInfo.size * 0.8 + 0.8}rem;
                    background-color: ${wordInfo.color};
                    color: white;
                    opacity: ${0.7 + wordInfo.size * 0.1};
                " title="${wordInfo.word}: ${wordInfo.count} occurrences">
                    ${wordInfo.word}
                </span>
            `).join('');
            
            const wordcloudSection = document.getElementById('wordcloud-section');
            wordcloudSection.hidden = false;
            wordcloudSection.classList.add('fade-in');
        }
        
    } catch (err) {
        console.error('Erreur chargement nuage de mots:', err);
    }
}

// === NOUVELLES FONCTIONNALITÉS PHASE 3 ===

// Bouton historique
document.getElementById('history-btn').addEventListener('click', () => {
    console.log('📜 Bouton Historique cliqué!');
    toggleHistorySection();
    loadHistory();
});

// Bouton actualiser historique
document.getElementById('refresh-history').addEventListener('click', () => {
    console.log('🔄 Actualisation historique');
    loadHistory();
});

// Recherche dans l'historique
document.getElementById('search-history-btn').addEventListener('click', () => {
    const query = document.getElementById('history-search').value.trim();
    if (query) {
        searchHistory(query);
    } else {
        loadHistory();
    }
});

// Recherche en tapant Entrée
document.getElementById('history-search').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const query = e.target.value.trim();
        if (query) {
            searchHistory(query);
        } else {
            loadHistory();
        }
    }
});

function toggleHistorySection() {
    const historySection = document.getElementById('history-section');
    const historyButton = document.getElementById('history-btn');
    historySection.hidden = !historySection.hidden;
    historyButton.setAttribute('aria-expanded', String(!historySection.hidden));
    if (!historySection.hidden) {
        historySection.classList.add('fade-in');
        historySection.scrollIntoView({ behavior: 'smooth' });
    }
}

async function loadHistory() {
    try {
        const res = await fetch('/history?limit=20');
        const data = await res.json();
        
        if (data.success) {
            displayHistory(data.history, data.stats);
        } else {
            console.error('Erreur chargement historique:', data.error);
        }
    } catch (err) {
        console.error('Erreur réseau historique:', err);
    }
}

async function searchHistory(query) {
    try {
        const res = await fetch(`/history/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        
        if (data.success) {
            displayHistory(data.results, null, `Résultats pour "${query}"`);
        } else {
            console.error('Erreur recherche:', data.error);
        }
    } catch (err) {
        console.error('Erreur réseau recherche:', err);
    }
}

function displayHistory(analyses, stats, title = 'Historique récent') {
    const historyContent = document.getElementById('history-content');
    const historyStats = document.getElementById('history-stats');
    
    // Statistiques
    if (stats) {
        historyStats.innerHTML = `
            <div><strong>${stats.total_analyses}</strong> analyses</div>
            <div><strong>${stats.total_words_analyzed}</strong> mots analysés</div>
        `;
    }
    
    // Contenu
    if (analyses.length === 0) {
        historyContent.innerHTML = `
            <div class="alert alert-info text-center">
                <i class="fas fa-info-circle"></i> Aucune analyse trouvée
            </div>
        `;
        return;
    }
    
    const analysesHtml = analyses.map(analysis => {
        const date = new Date(analysis.created_at).toLocaleString('fr-FR');
        const sentimentBadge = analysis.sentiment_label ? 
            `<span class="badge bg-${
                analysis.sentiment_label === 'positive' ? 'success' : 
                analysis.sentiment_label === 'negative' ? 'danger' : 'secondary'
            }">${analysis.sentiment_label}</span>` : '';
            
        return `
            <div class="card mb-2 analysis-card" data-id="${analysis.id}">
                <div class="card-body p-3">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h6 class="card-title mb-1">
                                <i class="fas fa-${analysis.analysis_mode === 'style' ? 'chart-bar' : 'brain'}"></i>
                                Analyse ${analysis.analysis_mode} - ${date}
                            </h6>
                            <p class="card-text small text-muted mb-1">${analysis.text_preview}</p>
                            <div>
                                ${analysis.video_id ? `<span class="badge bg-info me-1">YouTube: ${analysis.video_id}</span>` : ''}
                                <span class="badge bg-light text-dark me-1">${analysis.total_words || 0} mots</span>
                                ${sentimentBadge}
                            </div>
                        </div>
                        <div class="col-md-4 text-end">
                            <button class="btn btn-sm btn-outline-primary" onclick="loadAnalysisDetails(${analysis.id})">
                                <i class="fas fa-eye"></i> Voir détails
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    historyContent.innerHTML = `
        <h6>${title}</h6>
        ${analysesHtml}
    `;
}

async function loadAnalysisDetails(analysisId) {
    try {
        console.log(`Chargement détails analyse ${analysisId}`);
        const res = await fetch(`/history/${analysisId}`);
        const data = await res.json();
        
        if (data.success) {
            displayAnalysisModal(data.analysis);
        } else {
            showUiMessage('Erreur : ' + data.error, 'danger');
        }
    } catch (err) {
        console.error('Erreur chargement détails:', err);
        showUiMessage('Erreur de connexion.', 'danger');
    }
}

function displayAnalysisModal(analysis) {
    const previousFocus = document.activeElement;
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.tabIndex = -1;

    const content = document.createElement('div');
    content.className = 'modal-content analysis-modal';
    
    const date = new Date(analysis.created_at).toLocaleString('fr-FR');
    
    content.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h4 id="analysis-modal-title"><i class="fas fa-chart-line" aria-hidden="true"></i> Analyse du ${date}</h4>
            <button class="btn btn-outline-secondary modal-close" type="button" aria-label="Fermer la fenêtre">
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <h6>Informations générales</h6>
                <ul class="list-unstyled">
                    <li><strong>Mode:</strong> ${analysis.analysis_mode}</li>
                    <li><strong>Mots:</strong> ${analysis.total_words || 'N/A'}</li>
                    <li><strong>Phrases:</strong> ${analysis.sentences || 'N/A'}</li>
                    <li><strong>Richesse:</strong> ${analysis.vocabulary_richness || 'N/A'}%</li>
                    <li><strong>Temps lecture:</strong> ${analysis.reading_time_minutes || 'N/A'} min</li>
                </ul>
            </div>
            
            <div class="col-md-6">
                <h6>Sentiment & Lisibilité</h6>
                <ul class="list-unstyled">
                    <li><strong>Sentiment:</strong> ${analysis.sentiment_label || 'N/A'}</li>
                    <li><strong>Polarité:</strong> ${analysis.sentiment_polarity || 'N/A'}</li>
                    <li><strong>Flesch Score:</strong> ${analysis.flesch_reading_ease || 'N/A'}</li>
                    <li><strong>Grade Level:</strong> ${analysis.flesch_kincaid_grade || 'N/A'}</li>
                </ul>
            </div>
        </div>
        
        <div class="mt-3">
            <h6>Extrait du texte</h6>
            <div class="analysis-modal-excerpt border p-3 bg-light">
                ${analysis.original_text.substring(0, 500)}${analysis.original_text.length > 500 ? '...' : ''}
            </div>
        </div>
        
        <div class="mt-3 text-end">
            <button class="btn btn-secondary modal-close" type="button">Fermer</button>
        </div>
    `;
    
    modal.setAttribute('aria-labelledby', 'analysis-modal-title');

    const closeModal = () => {
        modal.remove();
        if (previousFocus instanceof HTMLElement) {
            previousFocus.focus();
        }
    };

    modal.appendChild(content);
    document.body.appendChild(modal);

    const focusable = () => [...modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )].filter(element => !element.disabled && !element.hidden);

    modal.querySelectorAll('.modal-close').forEach(button => {
        button.addEventListener('click', closeModal);
    });

    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            e.preventDefault();
            closeModal();
            return;
        }
        if (e.key === 'Tab') {
            const elements = focusable();
            if (elements.length === 0) {
                e.preventDefault();
                return;
            }
            const first = elements[0];
            const last = elements[elements.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    const initialFocus = focusable()[0];
    (initialFocus || modal).focus();
}

function displayAdvancedAnalysis(analysis) {
    // Affichage du sentiment
    if (analysis.sentiment) {
        displaySentimentAnalysis(analysis.sentiment);
    }
    
    // Affichage des émotions
    if (analysis.emotions) {
        displayEmotionsAnalysis(analysis.emotions);
    }
    
    // Affichage de la lisibilité
    if (analysis.readability) {
        displayReadabilityAnalysis(analysis.readability);
    }
}

function displaySentimentAnalysis(sentiment) {
    const sentimentSection = document.getElementById('sentiment-section');
    const sentimentContent = document.getElementById('sentiment-content');
    
    const sentimentColor = 
        sentiment.label === 'positive' ? 'success' :
        sentiment.label === 'negative' ? 'danger' : 'secondary';
    
    const sentimentIcon = 
        sentiment.label === 'positive' ? 'smile' :
        sentiment.label === 'negative' ? 'frown' : 'meh';
    
    sentimentContent.innerHTML = `
        <div class="row">
            <div class="col-md-4 text-center">
                <div class="p-3 border rounded">
                    <i class="fas fa-${sentimentIcon} fa-3x text-${sentimentColor} mb-2"></i>
                    <h5 class="text-${sentimentColor}">${sentiment.label.toUpperCase()}</h5>
                    <small>Confiance: ${Math.round(sentiment.confidence * 100)}%</small>
                </div>
            </div>
            <div class="col-md-8">
                <div class="mb-3">
                    <label>Polarité: <strong>${sentiment.polarity}</strong></label>
                    <div class="progress">
                        <div class="progress-bar bg-${sentimentColor}" style="width: ${Math.abs(sentiment.polarity) * 50 + 50}%"></div>
                    </div>
                    <small class="text-muted">-1 (très négatif) à +1 (très positif)</small>
                </div>
                <div class="mb-3">
                    <label>Subjectivité: <strong>${sentiment.subjectivity}</strong></label>
                    <div class="progress">
                        <div class="progress-bar bg-info" style="width: ${sentiment.subjectivity * 100}%"></div>
                    </div>
                    <small class="text-muted">0 (objectif) à 1 (subjectif)</small>
                </div>
            </div>
        </div>
    `;
    
    sentimentSection.hidden = false;
    sentimentSection.classList.add('fade-in');
}

function displayReadabilityAnalysis(readability) {
    const readabilitySection = document.getElementById('readability-section');
    const readabilityContent = document.getElementById('readability-content');
    
    const easeColor = 
        readability.flesch_ease >= 70 ? 'success' :
        readability.flesch_ease >= 50 ? 'warning' : 'danger';
    
    readabilityContent.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Niveau de Lisibilité</h5>
                        <h3 class="text-${easeColor}">${readability.ease_level}</h3>
                        <p class="card-text">Score Flesch: <strong>${readability.flesch_ease}</strong></p>
                        <div class="progress">
                            <div class="progress-bar bg-${easeColor}" style="width: ${Math.max(0, readability.flesch_ease)}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <h6>Métriques détaillées</h6>
                <ul class="list-group list-group-flush">
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Niveau scolaire Flesch-Kincaid</span>
                        <strong>${readability.flesch_kincaid}</strong>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Mots par phrase (moyenne)</span>
                        <strong>${readability.avg_sentence_length}</strong>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Syllabes par mot (moyenne)</span>
                        <strong>${readability.avg_syllables_per_word}</strong>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Complexité lexicale</span>
                        <strong>${readability.lexical_complexity}%</strong>
                    </li>
                </ul>
            </div>
        </div>
    `;
    
    readabilitySection.hidden = false;
    readabilitySection.classList.add('fade-in');
}

function displayEmotionsAnalysis(data) {
    const emotionsSection = document.getElementById('emotions-section');
    const emotionsContent = document.getElementById('emotions-content');

    const distribution = data?.emotions || {};
    const emotionList = Object.entries(distribution)
        .filter(([, score]) => Number.isFinite(Number(score)))
        .map(([emotion, score]) => ({ emotion, score: Number(score) }))
        .sort((a, b) => b.score - a.score);

    if (emotionList.length === 0) {
        emotionsContent.innerHTML = `
            <div class="emotion-summary">
                <div><span class="text-muted">Émotion dominante</span><strong>Aucune</strong></div>
                <div><span class="text-muted">Mots émotionnels</span><strong>${data?.total_emotion_words ?? 0}</strong></div>
                <div><span class="text-muted">Intensité émotionnelle</span><strong>${Number(data?.emotional_intensity || 0).toFixed(1)}%</strong></div>
            </div>
        `;
        emotionsSection.hidden = false;
        return;
    }

    emotionsContent.innerHTML = `
        <div class="emotion-summary">
            <div><span class="text-muted">Émotion dominante</span><strong class="text-capitalize">${data.dominant_emotion || 'Aucune'}</strong></div>
            <div><span class="text-muted">Mots émotionnels</span><strong>${data.total_emotion_words ?? 0}</strong></div>
            <div><span class="text-muted">Intensité émotionnelle</span><strong>${Number(data.emotional_intensity || 0).toFixed(1)}%</strong></div>
        </div>
        <div class="emotion-bars mt-3">
            ${emotionList.map(item => `
                <div class="emotion-row">
                    <div class="d-flex justify-content-between gap-3">
                        <span class="text-capitalize">${item.emotion}</span>
                        <strong>${item.score.toFixed(1)}%</strong>
                    </div>
                    <div class="progress" role="progressbar" aria-label="${item.emotion}" aria-valuenow="${item.score}" aria-valuemin="0" aria-valuemax="100">
                        <div class="progress-bar" style="width: ${Math.min(100, Math.max(0, item.score))}%"></div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    emotionsSection.hidden = false;
    emotionsSection.classList.add('fade-in');
}

// Faire loadAnalysisDetails globale pour les onclick
window.loadAnalysisDetails = loadAnalysisDetails;

// === GESTION DU CONTRÔLEUR DE NOMBRE DE MOTS ===

// Références aux éléments
const modeSelect = document.getElementById('mode-select');
const maxWordsSection = document.getElementById('max-words-section');
const maxWordsSlider = document.getElementById('max-words-slider');
const maxWordsInput = document.getElementById('max-words-input');

// Gestion de l'affichage du contrôleur selon le mode
modeSelect.addEventListener('change', function() {
    const isStyleMode = this.value === 'style';
    
    if (isStyleMode) {
        maxWordsSection.classList.remove('hidden');
    } else {
        maxWordsSection.classList.add('hidden');
    }
});

// Synchronisation slider <-> input
maxWordsSlider.addEventListener('input', function() {
    maxWordsInput.value = this.value;
});

maxWordsInput.addEventListener('input', function() {
    const value = Math.max(1, Math.min(200, parseInt(this.value) || 30));
    this.value = value;
    maxWordsSlider.value = value;
});

// Validation sur blur (perte de focus)
maxWordsInput.addEventListener('blur', function() {
    const value = Math.max(1, Math.min(200, parseInt(this.value) || 30));
    this.value = value;
    maxWordsSlider.value = value;
});

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', function() {
    // Masquer le contrôleur si pas en mode Style
    const isStyleMode = modeSelect.value === 'style';
    if (!isStyleMode) {
        maxWordsSection.classList.add('hidden');
    }
});
