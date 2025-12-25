// Load and visualize the emotion data
let storyData = null;
let config = null;

// Chart.js defaults for dark theme
Chart.defaults.font.family = "'Space Mono', monospace";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#d4af37';
Chart.defaults.borderColor = 'rgba(212, 175, 55, 0.2)';

// Load data
Promise.all([
    fetch('data/story.json').then(r => r.json()),
    fetch('data/config.json').then(r => r.json())
]).then(([story, cfg]) => {
    storyData = story;
    config = cfg;
    initCharts();
    initScrollAnimations();
}).catch(err => {
    console.error('Error loading data:', err);
});

function initCharts() {
    createSelectionsDistribution();
    createEmotionBiasChart();
    createConsensusScatter();
    createGenreHeatmap();
    createFeatureImportanceChart();
    createEmotionFeaturesChart();
    createModelComparisonChart();
}

// Scroll-triggered fade-in animations
function initScrollAnimations() {
    const fadeElements = document.querySelectorAll('.fade-in');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    fadeElements.forEach(el => observer.observe(el));
}

// 1. Selections Distribution
function createSelectionsDistribution() {
    const tracks = storyData.tracks;

    // Calculate distribution of selections_per_rater
    const bins = {};
    tracks.forEach(t => {
        const rounded = Math.round(t.selections_per_rater * 2) / 2; // Round to 0.5
        bins[rounded] = (bins[rounded] || 0) + 1;
    });

    const labels = Object.keys(bins).sort((a, b) => parseFloat(a) - parseFloat(b));
    const data = labels.map(l => bins[l]);

    const ctx = document.getElementById('selectionsDistribution').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of tracks',
                data: data,
                backgroundColor: 'rgba(0, 255, 255, 0.7)',
                borderColor: '#00ffff',
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 26, 0.9)',
                    titleColor: '#ffb347',
                    bodyColor: '#f4e8d0',
                    borderColor: '#d4af37',
                    borderWidth: 1,
                    callbacks: {
                        label: (context) => `${context.parsed.y} tracks`
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Emotions selected per rater',
                        font: { size: 13, weight: 600 },
                        color: '#d4af37'
                    },
                    grid: { display: false },
                    ticks: { color: '#d4af37' }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Number of tracks',
                        font: { size: 13, weight: 600 },
                        color: '#d4af37'
                    },
                    beginAtZero: true,
                    grid: { color: 'rgba(212, 175, 55, 0.1)' },
                    ticks: { color: '#d4af37' }
                }
            }
        }
    });
}

// 2. Emotion Bias Chart
function createEmotionBiasChart() {
    const emotionBias = storyData.emotion_bias;

    const ctx = document.getElementById('emotionBiasChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: emotionBias.map(e => e.emotion.charAt(0).toUpperCase() + e.emotion.slice(1)),
            datasets: [{
                label: 'Share of selections',
                data: emotionBias.map(e => e.share * 100),
                backgroundColor: emotionBias.map(e => {
                    const color = config.emotion_colors[e.emotion];
                    return color + 'cc';
                }),
                borderColor: emotionBias.map(e => config.emotion_colors[e.emotion]),
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 26, 0.9)',
                    titleColor: '#ffb347',
                    bodyColor: '#f4e8d0',
                    borderColor: '#d4af37',
                    borderWidth: 1,
                    callbacks: {
                        label: (context) => `${context.parsed.x.toFixed(1)}% of all selections`
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Percentage of total selections',
                        font: { size: 13, weight: 600 },
                        color: '#d4af37'
                    },
                    grid: { color: 'rgba(212, 175, 55, 0.1)' },
                    ticks: { color: '#d4af37' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#d4af37' }
                }
            }
        }
    });
}

// 3. Consensus Scatter
function createConsensusScatter() {
    const tracks = storyData.tracks;

    // Prepare scatter data with genre colors
    const dataByGenre = {};
    tracks.forEach(t => {
        if (!dataByGenre[t.genre]) {
            dataByGenre[t.genre] = [];
        }
        dataByGenre[t.genre].push({
            x: t.entropy,
            y: t.max_p,
            track_id: t.track_id,
            genre: t.genre
        });
    });

    const datasets = Object.keys(dataByGenre).map(genre => ({
        label: genre.charAt(0).toUpperCase() + genre.slice(1),
        data: dataByGenre[genre],
        backgroundColor: config.genre_colors[genre] + 'cc',
        borderColor: config.genre_colors[genre],
        borderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 8,
        pointHoverBorderWidth: 3
    }));

    const ctx = document.getElementById('consensusScatter').getContext('2d');
    new Chart(ctx, {
        type: 'scatter',
        data: { datasets },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#d4af37',
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 26, 0.9)',
                    titleColor: '#ffb347',
                    bodyColor: '#f4e8d0',
                    borderColor: '#d4af37',
                    borderWidth: 1,
                    callbacks: {
                        label: (context) => {
                            const point = context.raw;
                            return [
                                `${point.genre} Track ${point.track_id}`,
                                `Entropy: ${point.x.toFixed(2)}`,
                                `Max consensus: ${(point.y * 100).toFixed(0)}%`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Entropy (higher = more ambiguous) →',
                        font: { size: 13, weight: 600 },
                        color: '#d4af37'
                    },
                    grid: { color: 'rgba(212, 175, 55, 0.1)' },
                    ticks: { color: '#d4af37' }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Max emotion % (higher = more consensus) →',
                        font: { size: 13, weight: 600 },
                        color: '#d4af37'
                    },
                    ticks: {
                        callback: (value) => (value * 100).toFixed(0) + '%',
                        color: '#d4af37'
                    },
                    grid: { color: 'rgba(212, 175, 55, 0.1)' }
                }
            }
        }
    });
}

// 4. Genre Heatmap
function createGenreHeatmap() {
    const genreMeans = storyData.genre_means;
    const emotions = storyData.emotions;

    // Prepare data for grouped bar chart
    const datasets = emotions.map(emotion => ({
        label: emotion.charAt(0).toUpperCase() + emotion.slice(1),
        data: genreMeans.map(g => (g[`mean_${emotion}`] * 100)),
        backgroundColor: config.emotion_colors[emotion] + 'aa',
        borderColor: config.emotion_colors[emotion],
        borderWidth: 1,
        borderRadius: 3
    }));

    const ctx = document.getElementById('genreHeatmap').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: genreMeans.map(g => g.genre.charAt(0).toUpperCase() + g.genre.slice(1)),
            datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: { size: 11 },
                        color: '#d4af37'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 26, 0.9)',
                    titleColor: '#ffb347',
                    bodyColor: '#f4e8d0',
                    borderColor: '#d4af37',
                    borderWidth: 1,
                    callbacks: {
                        label: (context) => {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: false,
                    grid: { display: false },
                    ticks: { color: '#d4af37' }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Average % of raters selecting emotion',
                        font: { size: 13, weight: 600 },
                        color: '#d4af37'
                    },
                    stacked: false,
                    grid: { color: 'rgba(212, 175, 55, 0.1)' },
                    ticks: { color: '#d4af37' }
                }
            }
        }
    });
}

// 5. Feature Importance Chart
function createFeatureImportanceChart() {
    const features = storyData.feature_importance_overall.slice(0, 15);

    const ctx = document.getElementById('featureImportanceChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: features.map(f => f.feature),
            datasets: [{
                label: 'Importance',
                data: features.map(f => f.importance),
                backgroundColor: 'rgba(255, 0, 255, 0.7)',
                borderColor: '#ff00ff',
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 26, 0.9)',
                    titleColor: '#ffb347',
                    bodyColor: '#f4e8d0',
                    borderColor: '#d4af37',
                    borderWidth: 1,
                    callbacks: {
                        label: (context) => `Importance: ${context.parsed.x.toFixed(5)}`
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Permutation importance',
                        font: { size: 13, weight: 600 },
                        color: '#d4af37'
                    },
                    grid: { color: 'rgba(212, 175, 55, 0.1)' },
                    ticks: { color: '#d4af37' }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 11 },
                        color: '#d4af37'
                    }
                }
            }
        }
    });
}

// 6. Emotion-Specific Features Chart
function createEmotionFeaturesChart() {
    const emotionFeatures = storyData.feature_importance_by_emotion;

    // emotionFeatures is a dict: {emotion: [{feature, importance}, ...]}
    const emotionsToShow = ['joy', 'calmness', 'tension', 'amazement'];
    const featuresByEmotion = {};

    emotionsToShow.forEach(emotion => {
        if (emotionFeatures[emotion]) {
            featuresByEmotion[emotion] = emotionFeatures[emotion].slice(0, 5);
        }
    });

    // Create grouped bar chart
    const allFeatures = new Set();
    Object.values(featuresByEmotion).forEach(features => {
        features.forEach(f => allFeatures.add(f.feature));
    });

    const featureList = Array.from(allFeatures).slice(0, 12); // Limit to 12 features

    const datasets = emotionsToShow.map(emotion => ({
        label: emotion.charAt(0).toUpperCase() + emotion.slice(1),
        data: featureList.map(feature => {
            const found = featuresByEmotion[emotion] ? featuresByEmotion[emotion].find(f => f.feature === feature) : null;
            return found ? found.importance : 0;
        }),
        backgroundColor: config.emotion_colors[emotion] + 'aa',
        borderColor: config.emotion_colors[emotion],
        borderWidth: 1,
        borderRadius: 3
    }));

    const ctx = document.getElementById('emotionFeaturesChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: featureList,
            datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#d4af37',
                        padding: 10
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 26, 0.9)',
                    titleColor: '#ffb347',
                    bodyColor: '#f4e8d0',
                    borderColor: '#d4af37',
                    borderWidth: 1,
                    callbacks: {
                        label: (context) => {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(5)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 10 },
                        maxRotation: 45,
                        minRotation: 45,
                        color: '#d4af37'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Permutation importance',
                        font: { size: 13, weight: 600 },
                        color: '#d4af37'
                    },
                    grid: { color: 'rgba(212, 175, 55, 0.1)' },
                    ticks: { color: '#d4af37' }
                }
            }
        }
    });
}

// 7. Model Comparison Chart
function createModelComparisonChart() {
    // Load metrics from CSV
    fetch('artifacts/metrics.csv')
        .then(r => r.text())
        .then(csvText => {
            console.log('Loaded metrics CSV, length:', csvText.length);
            const rows = csvText.split('\n').slice(1).filter(r => r.trim());

            // Parse CSV
            const metrics = rows.map(row => {
                const [metric, emotion, value, split, model, genre] = row.split(',');
                return { metric, emotion, value: parseFloat(value), split, model, genre };
            });

            // Calculate macro averages
            const models = ['RandomForest', 'XGBoost', 'Ridge', 'MLP'];
            const splits = ['stratified', 'logo_classical', 'logo_electronic', 'logo_pop', 'logo_rock'];

            const results = {};

            models.forEach(model => {
                results[model] = {};

                // Stratified
                const stratMetrics = metrics.filter(m => m.model === model && m.split === 'stratified' && m.metric === 'pearson' && m.value && !isNaN(m.value));
                if (stratMetrics.length > 0) {
                    results[model].stratified = stratMetrics.reduce((sum, m) => sum + m.value, 0) / stratMetrics.length;
                }

                // LOGO average
                const logoSplits = splits.filter(s => s.startsWith('logo_'));
                const logoMetrics = metrics.filter(m =>
                    m.model === model &&
                    logoSplits.includes(m.split) &&
                    m.metric === 'pearson' &&
                    m.value &&
                    !isNaN(m.value)
                );

                if (logoMetrics.length > 0) {
                    results[model].logo = logoMetrics.reduce((sum, m) => sum + m.value, 0) / logoMetrics.length;
                }
            });

            // Create chart
            const ctx = document.getElementById('modelComparisonChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: models,
                    datasets: [
                        {
                            label: 'Stratified (80/20)',
                            data: models.map(m => results[m].stratified || 0),
                            backgroundColor: 'rgba(0, 255, 255, 0.7)',
                            borderColor: '#00ffff',
                            borderWidth: 1,
                            borderRadius: 6
                        },
                        {
                            label: 'LOGO (cross-genre)',
                            data: models.map(m => results[m].logo || 0),
                            backgroundColor: 'rgba(255, 0, 255, 0.7)',
                            borderColor: '#ff00ff',
                            borderWidth: 1,
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                color: '#d4af37',
                                padding: 15
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(26, 26, 26, 0.9)',
                            titleColor: '#ffb347',
                            bodyColor: '#f4e8d0',
                            borderColor: '#d4af37',
                            borderWidth: 1,
                            callbacks: {
                                label: (context) => {
                                    return `${context.dataset.label}: ${context.parsed.y.toFixed(3)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#d4af37' }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Pearson Correlation',
                                font: { size: 13, weight: 600 },
                                color: '#d4af37'
                            },
                            beginAtZero: true,
                            max: 0.6,
                            grid: { color: 'rgba(212, 175, 55, 0.1)' },
                            ticks: { color: '#d4af37' }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error('Error loading metrics CSV:', err);
        });
}
