// Global state
let currentStep = null;
let currentChart = null;

// Data for visualizations
const publicationData = {
    years: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    articles: [30000, 42000, 58000, 72000, 85000, 85000, 125104, 95000, 80000],
    journalCount: [54, 78, 110, 155, 190, 210, 230, 230, 230]
};

const qualityMetrics = {
    categories: ['Article<br>Quality', 'Peer Review<br>Quality', 'Editorial<br>Boards', 'Author<br>Experience', 'Reviewer<br>Experience', 'Editor<br>Experience'],
    scores2024: [94, 92, 93, 91, 87, 80],
    scores2020: [78, 75, 80, 82, 79, 72] // Estimated pre-pivot
};

const airaData = {
    years: [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    checks: [15, 20, 25, 30, 35, 50, 60],
    rejectionRate: [10, 12, 15, 18, 25, 42, 52]
};

const impactData = {
    metric: 'Frontiers in Science (2024)',
    articles: 65,
    views: 850000,
    downloads: 120000,
    citations: 280,
    viewsPerArticle: 13077,
    citationsPerArticle: 4.3
};

const institutionalData = [
    { name: 'University of California', country: 'USA', type: 'Flat Fee', year: 2024, institutions: 10 },
    { name: 'German National Consortium', country: 'Germany', type: 'Flat Fee', year: 2024, institutions: 200 },
    { name: 'Swedish Bibsam', country: 'Sweden', type: 'Flat Fee', year: 2024, institutions: 85 },
    { name: 'Other Partners', country: 'Various', type: 'Flat Fee', year: 2024, institutions: 76 }
];

// Chart configurations by step
const chartConfigs = {
    intro: {
        type: 'line',
        title: 'Frontiers Publication Growth (2016-2024)',
        subtitle: 'The rise, the peak, and the deliberate decline',
        render: renderPublicationTrend
    },
    crisis: {
        type: 'annotation',
        title: 'The Shadow Industry',
        subtitle: 'Paper mills exploit fast-growing publishers',
        render: renderCrisisContext
    },
    choice: {
        type: 'line-annotated',
        title: 'The Strategic Pivot',
        subtitle: '36% decline from peak—by design, not by accident',
        render: renderStrategicPivot
    },
    weapon: {
        type: 'dual-axis',
        title: 'AIRA: The AI Fighting AI',
        subtitle: 'Quality checks vs. rejection rates over time',
        render: renderAIRAGrowth
    },
    resistance: {
        type: 'funnel',
        title: 'The New Editorial Funnel',
        subtitle: 'How submissions flow through integrity screening',
        render: renderEditorialFunnel
    },
    results: {
        type: 'bar-comparison',
        title: 'Quality Metrics: Before vs. After',
        subtitle: 'Researcher satisfaction scores (2020 vs. 2024)',
        render: renderQualityComparison
    },
    impact: {
        type: 'metrics-showcase',
        title: 'Impact Per Article: Frontiers in Science',
        subtitle: 'When you publish 65 articles instead of 65,000',
        render: renderImpactShowcase
    },
    institutional: {
        type: 'partnerships',
        title: 'Institutional Partnerships (2024)',
        subtitle: 'Universities voting with their budgets',
        render: renderPartnerships
    },
    broader: {
        type: 'network',
        title: 'Frontiers Planet Prize Reach',
        subtitle: 'Global engagement on critical challenges',
        render: renderPlanetPrize
    },
    industry: {
        type: 'comparison',
        title: 'The $1 Billion Question',
        subtitle: 'Quality vs. Quantity in academic publishing',
        render: renderIndustryComparison
    },
    future: {
        type: 'projection',
        title: 'The Ripple Effect',
        subtitle: 'What Frontiers\' choice could mean for science',
        render: renderFutureImplications
    },
    caveats: {
        type: 'uncertainty',
        title: 'What We Know vs. What We Don\'t',
        subtitle: 'Acknowledging limitations and unknowns',
        render: renderCaveats
    },
    conclusion: {
        type: 'summary',
        title: 'The Counterintuitive Victory',
        subtitle: 'Measuring success differently',
        render: renderConclusion
    }
};

// Initialize scroll observation
function initScrollObserver() {
    const steps = document.querySelectorAll('.step');

    const observerOptions = {
        root: null,
        rootMargin: '-40% 0px -40% 0px',
        threshold: 0.3
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Update step visibility
                steps.forEach(s => s.classList.remove('active'));
                entry.target.classList.add('active');

                // Update chart
                const stepName = entry.target.dataset.step;
                updateChart(stepName);
            }
        });
    }, observerOptions);

    steps.forEach(step => observer.observe(step));
}

// Update chart based on current step
function updateChart(stepName) {
    if (currentStep === stepName) return;
    currentStep = stepName;

    const config = chartConfigs[stepName];
    if (!config) return;

    const container = document.getElementById('chart-container');
    const caption = document.getElementById('chart-caption');

    // Clear previous chart
    container.innerHTML = '';

    // Update caption
    caption.innerHTML = `<strong>${config.title}</strong><br>${config.subtitle}`;

    // Render new chart
    config.render(container);
}

// Chart rendering functions

function renderPublicationTrend(container) {
    const trace1 = {
        x: publicationData.years,
        y: publicationData.articles,
        name: 'Articles Published',
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: '#e74c3c',
            width: 4
        },
        marker: {
            size: 10,
            color: '#e74c3c',
            line: {
                color: 'white',
                width: 2
            }
        },
        hovertemplate: '<b>%{y:,} articles</b><br>in %{x}<extra></extra>'
    };

    const layout = {
        title: '',
        xaxis: {
            title: 'Year',
            gridcolor: '#e0e0e0',
            dtick: 1
        },
        yaxis: {
            title: 'Articles Published',
            gridcolor: '#e0e0e0',
            rangemode: 'tozero'
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { t: 20, r: 20, b: 60, l: 80 },
        hovermode: 'closest',
        annotations: [{
            x: 2022,
            y: 125104,
            text: 'Peak: 125,104',
            showarrow: true,
            arrowhead: 2,
            ax: -40,
            ay: -40,
            font: { size: 13, color: '#e74c3c', family: 'Georgia' },
            arrowcolor: '#e74c3c'
        }]
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot(container, [trace1], layout, config);
}

function renderCrisisContext(container) {
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 40px; background: white; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 4em; color: #e74c3c; margin-bottom: 10px;">⚠️</div>
                <h3 style="font-size: 1.8em; color: #c0392b; margin-bottom: 20px;">The Paper Mill Epidemic</h3>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                <div style="background: #ffebee; padding: 25px; border-radius: 8px; border-left: 4px solid #e74c3c;">
                    <div style="font-size: 2.5em; font-weight: bold; color: #c0392b; margin-bottom: 8px;">11,000+</div>
                    <div style="font-size: 1em; color: #666;">Papers retracted by Wiley (2023)</div>
                </div>
                <div style="background: #fff3e0; padding: 25px; border-radius: 8px; border-left: 4px solid #f39c12;">
                    <div style="font-size: 2.5em; font-weight: bold; color: #d68910; margin-bottom: 8px;">Thousands</div>
                    <div style="font-size: 1em; color: #666;">Estimated fraudulent papers annually</div>
                </div>
            </div>

            <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; border-left: 4px solid #95a5a6;">
                <h4 style="color: #2c3e50; margin-bottom: 15px; font-size: 1.2em;">Paper Mill Techniques:</h4>
                <ul style="color: #555; line-height: 2; font-size: 1em; margin-left: 20px;">
                    <li>AI-generated abstracts with "tortured phrases"</li>
                    <li>Fabricated data and manipulated images</li>
                    <li>Fake author identities and credentials</li>
                    <li>Organized peer review manipulation networks</li>
                    <li>Sophisticated plagiarism evasion techniques</li>
                </ul>
            </div>

            <div style="margin-top: 25px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white; text-align: center; font-style: italic; font-size: 1.1em; line-height: 1.6;">
                "Fast-growing open-access publishers became prime targets for industrial-scale fraud."
            </div>
        </div>
    `;
}

function renderStrategicPivot(container) {
    const trace1 = {
        x: publicationData.years,
        y: publicationData.articles,
        name: 'Articles Published',
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: '#e74c3c',
            width: 4,
            shape: 'spline'
        },
        marker: {
            size: 12,
            color: publicationData.years.map(y => y >= 2023 ? '#27ae60' : '#e74c3c'),
            line: {
                color: 'white',
                width: 2
            }
        },
        hovertemplate: '<b>%{y:,} articles</b><br>%{x}<extra></extra>'
    };

    // Add shaded region for "strategic decline"
    const shapes = [{
        type: 'rect',
        xref: 'x',
        yref: 'paper',
        x0: 2022.5,
        x1: 2024.5,
        y0: 0,
        y1: 1,
        fillcolor: '#d5f4e6',
        opacity: 0.3,
        line: { width: 0 }
    }];

    const layout = {
        title: '',
        xaxis: {
            title: 'Year',
            gridcolor: '#e0e0e0',
            dtick: 1
        },
        yaxis: {
            title: 'Articles Published',
            gridcolor: '#e0e0e0',
            rangemode: 'tozero'
        },
        shapes: shapes,
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { t: 20, r: 20, b: 60, l: 80 },
        hovermode: 'closest',
        annotations: [
            {
                x: 2022,
                y: 125104,
                text: 'Peak: 125,104<br>(2022)',
                showarrow: true,
                arrowhead: 2,
                ax: 0,
                ay: -60,
                font: { size: 12, color: '#e74c3c', family: 'Georgia' },
                arrowcolor: '#e74c3c'
            },
            {
                x: 2024,
                y: 80000,
                text: '~80,000<br>(2024)<br>-36%',
                showarrow: true,
                arrowhead: 2,
                ax: 40,
                ay: -40,
                font: { size: 12, color: '#27ae60', family: 'Georgia' },
                arrowcolor: '#27ae60'
            },
            {
                x: 2023.5,
                y: 140000,
                text: 'Quality Pivot Zone',
                showarrow: false,
                font: { size: 14, color: '#27ae60', family: 'Georgia' }
            }
        ]
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot(container, [trace1], layout, config);
}

function renderAIRAGrowth(container) {
    const trace1 = {
        x: airaData.years,
        y: airaData.checks,
        name: 'Quality Checks',
        type: 'bar',
        marker: {
            color: '#3498db',
            line: {
                color: '#2980b9',
                width: 2
            }
        },
        hovertemplate: '<b>%{y} checks</b><br>in %{x}<extra></extra>',
        yaxis: 'y1'
    };

    const trace2 = {
        x: airaData.years,
        y: airaData.rejectionRate,
        name: 'Rejection Rate',
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: '#e74c3c',
            width: 4
        },
        marker: {
            size: 10,
            color: '#e74c3c',
            line: {
                color: 'white',
                width: 2
            }
        },
        hovertemplate: '<b>%{y}%</b> rejected<br>in %{x}<extra></extra>',
        yaxis: 'y2'
    };

    const layout = {
        title: '',
        xaxis: {
            title: 'Year',
            gridcolor: '#e0e0e0',
            dtick: 1
        },
        yaxis: {
            title: 'Number of AIRA Checks',
            titlefont: { color: '#3498db' },
            tickfont: { color: '#3498db' },
            gridcolor: '#e0e0e0',
            rangemode: 'tozero'
        },
        yaxis2: {
            title: 'Integrity Rejection Rate (%)',
            titlefont: { color: '#e74c3c' },
            tickfont: { color: '#e74c3c' },
            overlaying: 'y',
            side: 'right',
            rangemode: 'tozero'
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { t: 20, r: 80, b: 60, l: 80 },
        hovermode: 'x unified',
        legend: {
            x: 0.05,
            y: 0.95,
            bgcolor: 'rgba(255,255,255,0.9)',
            bordercolor: '#ccc',
            borderwidth: 1
        }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot(container, [trace1, trace2], layout, config);
}

function renderEditorialFunnel(container) {
    const funnelData = [
        { stage: 'Submissions Received', count: 100, color: '#95a5a6' },
        { stage: 'Pass Initial Screening', count: 70, color: '#3498db' },
        { stage: 'Pass AIRA Checks (60+)', count: 48, color: '#2980b9' },
        { stage: 'Enter Peer Review', count: 48, color: '#27ae60' },
        { stage: 'Pass Peer Review', count: 35, color: '#229954' },
        { stage: 'Published', count: 32, color: '#1e8449' }
    ];

    const trace = {
        type: 'funnel',
        y: funnelData.map(d => d.stage),
        x: funnelData.map(d => d.count),
        textposition: 'inside',
        textinfo: 'value+percent initial',
        marker: {
            color: funnelData.map(d => d.color)
        },
        connector: {
            line: {
                color: '#34495e',
                width: 3
            }
        },
        hovertemplate: '<b>%{y}</b><br>%{x} of 100<br>%{percentInitial}<extra></extra>'
    };

    const layout = {
        title: '',
        margin: { t: 20, r: 20, b: 40, l: 200 },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white',
        funnelmode: 'stack',
        annotations: [{
            x: 0.5,
            y: -0.15,
            xref: 'paper',
            yref: 'paper',
            text: 'Note: 52% rejected by integrity team before peer review (2024)',
            showarrow: false,
            font: { size: 11, color: '#666', style: 'italic' }
        }]
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot(container, [trace], layout, config);
}

function renderQualityComparison(container) {
    const trace1 = {
        x: qualityMetrics.categories,
        y: qualityMetrics.scores2020,
        name: '2020 (Pre-Pivot)',
        type: 'bar',
        marker: {
            color: 'rgba(149, 165, 166, 0.7)',
            line: {
                color: '#7f8c8d',
                width: 2
            }
        },
        hovertemplate: '<b>%{x}</b><br>2020: %{y}%<extra></extra>'
    };

    const trace2 = {
        x: qualityMetrics.categories,
        y: qualityMetrics.scores2024,
        name: '2024 (Post-Pivot)',
        type: 'bar',
        marker: {
            color: 'rgba(39, 174, 96, 0.8)',
            line: {
                color: '#27ae60',
                width: 2
            }
        },
        hovertemplate: '<b>%{x}</b><br>2024: %{y}%<extra></extra>'
    };

    const layout = {
        title: '',
        xaxis: {
            title: '',
            tickangle: 0
        },
        yaxis: {
            title: 'Satisfaction Score (%)',
            gridcolor: '#e0e0e0',
            range: [0, 100],
            dtick: 20
        },
        barmode: 'group',
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { t: 20, r: 20, b: 80, l: 70 },
        legend: {
            x: 0.5,
            y: 1.15,
            xanchor: 'center',
            orientation: 'h',
            bgcolor: 'rgba(255,255,255,0.9)',
            bordercolor: '#ccc',
            borderwidth: 1
        },
        hovermode: 'x'
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot(container, [trace1, trace2], layout, config);
}

function renderImpactShowcase(container) {
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 40px; background: white; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 35px;">
                <h3 style="font-size: 1.5em; color: #2c3e50; margin-bottom: 10px;">Frontiers in Science (2024)</h3>
                <p style="color: #7f8c8d; font-size: 1em;">Selective flagship journal: Quality over quantity</p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 30px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 3.5em; font-weight: bold; margin-bottom: 8px;">65</div>
                    <div style="font-size: 1.1em; opacity: 0.95;">Articles Published</div>
                </div>
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 3.5em; font-weight: bold; margin-bottom: 8px;">850K+</div>
                    <div style="font-size: 1.1em; opacity: 0.95;">Total Views</div>
                </div>
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 30px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 3.5em; font-weight: bold; margin-bottom: 8px;">120K+</div>
                    <div style="font-size: 1.1em; opacity: 0.95;">Downloads</div>
                </div>
                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 30px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 3.5em; font-weight: bold; margin-bottom: 8px;">280</div>
                    <div style="font-size: 1.1em; opacity: 0.95;">Citations</div>
                </div>
            </div>

            <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; border-left: 4px solid #3498db;">
                <h4 style="color: #2c3e50; margin-bottom: 15px; font-size: 1.2em;">Impact Per Article:</h4>
                <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 2.2em; font-weight: bold; color: #e74c3c;">13,077</div>
                        <div style="color: #666; font-size: 0.95em;">views/article</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.2em; font-weight: bold; color: #27ae60;">4.3</div>
                        <div style="color: #666; font-size: 0.95em;">citations/article</div>
                    </div>
                </div>
            </div>

            <div style="margin-top: 25px; text-align: center; color: #7f8c8d; font-style: italic; font-size: 0.95em;">
                Plus media coverage in The Guardian, CNN, and major international outlets
            </div>
        </div>
    `;
}

function renderPartnerships(container) {
    const trace = {
        type: 'treemap',
        labels: ['All Partners', 'Germany', 'UC System', 'Sweden', 'Others'],
        parents: ['', 'All Partners', 'All Partners', 'All Partners', 'All Partners'],
        values: [371, 200, 10, 85, 76],
        text: ['76 Total Partners', 'German Consortium<br>200 institutions', 'UC System<br>10 campuses', 'Swedish Bibsam<br>85 institutions', 'Other Partners<br>76 institutions'],
        textposition: 'middle center',
        marker: {
            colors: ['#ecf0f1', '#3498db', '#e74c3c', '#f39c12', '#9b59b6'],
            line: {
                color: 'white',
                width: 3
            }
        },
        hovertemplate: '<b>%{label}</b><br>%{text}<extra></extra>'
    };

    const layout = {
        title: '',
        margin: { t: 20, r: 20, b: 20, l: 20 },
        paper_bgcolor: 'white'
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot(container, [trace], layout, config);
}

function renderPlanetPrize(container) {
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 40px; background: white; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 3em; margin-bottom: 10px;">🌍</div>
                <h3 style="font-size: 1.6em; color: #27ae60; margin-bottom: 10px;">Frontiers Planet Prize 2024</h3>
                <p style="color: #7f8c8d;">Translating research into action on global challenges</p>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 25px;">
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 25px; border-radius: 10px; color: white; text-align: center;">
                    <div style="font-size: 2.8em; font-weight: bold; margin-bottom: 5px;">610</div>
                    <div style="font-size: 1em; opacity: 0.95;">Institutions Registered</div>
                </div>
                <div style="background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%); padding: 25px; border-radius: 10px; color: white; text-align: center;">
                    <div style="font-size: 2.8em; font-weight: bold; margin-bottom: 5px;">4,000+</div>
                    <div style="font-size: 1em; opacity: 0.95;">Researchers Enrolled</div>
                </div>
                <div style="background: linear-gradient(135deg, #4776e6 0%, #8e54e9 100%); padding: 25px; border-radius: 10px; color: white; text-align: center;">
                    <div style="font-size: 2.8em; font-weight: bold; margin-bottom: 5px;">23</div>
                    <div style="font-size: 1em; opacity: 0.95;">National Champions</div>
                </div>
                <div style="background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%); padding: 25px; border-radius: 10px; color: white; text-align: center;">
                    <div style="font-size: 2.8em; font-weight: bold; margin-bottom: 5px;">3,200+</div>
                    <div style="font-size: 1em; opacity: 0.95;">Event Attendees</div>
                </div>
            </div>

            <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-top: 20px;">
                <h4 style="color: #2c3e50; margin-bottom: 15px; font-size: 1.1em;">Focus Areas:</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <span style="background: #d5f4e6; color: #1e8449; padding: 8px 16px; border-radius: 20px; font-size: 0.9em;">Climate Change</span>
                    <span style="background: #fdebd0; color: #d68910; padding: 8px 16px; border-radius: 20px; font-size: 0.9em;">Infectious Diseases</span>
                    <span style="background: #d6eaf8; color: #1f618d; padding: 8px 16px; border-radius: 20px; font-size: 0.9em;">Green Hydrogen</span>
                    <span style="background: #f5eef8; color: #6c3483; padding: 8px 16px; border-radius: 20px; font-size: 0.9em;">Environmental Solutions</span>
                </div>
            </div>

            <div style="margin-top: 20px; text-align: center; color: #7f8c8d; font-style: italic; font-size: 0.95em; line-height: 1.6;">
                Convening scientists and policymakers to address<br>the world's most urgent challenges
            </div>
        </div>
    `;
}

function renderIndustryComparison(container) {
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 40px; background: white; border-radius: 8px;">
            <h3 style="text-align: center; font-size: 1.6em; color: #2c3e50; margin-bottom: 30px;">The Publishing Dilemma</h3>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                <div style="border: 3px solid #e74c3c; border-radius: 12px; padding: 30px; background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 2.5em; margin-bottom: 10px;">📈</div>
                        <h4 style="color: #c0392b; font-size: 1.3em; margin-bottom: 15px;">The Old Model</h4>
                    </div>
                    <ul style="color: #555; line-height: 2; font-size: 0.95em; list-style-position: inside;">
                        <li>Revenue = Articles × APC</li>
                        <li>Growth incentivized</li>
                        <li>Fast review cycles</li>
                        <li>Volume over quality</li>
                        <li>Vulnerable to fraud</li>
                    </ul>
                    <div style="margin-top: 20px; padding: 15px; background: rgba(231, 76, 60, 0.2); border-radius: 6px; text-align: center; font-size: 0.9em; color: #c0392b;">
                        <strong>Peak Frontiers:</strong><br>125,000 articles/year
                    </div>
                </div>

                <div style="border: 3px solid #27ae60; border-radius: 12px; padding: 30px; background: linear-gradient(135deg, #f0fff4 0%, #d5f4e6 100%);">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 2.5em; margin-bottom: 10px;">🎯</div>
                        <h4 style="color: #1e8449; font-size: 1.3em; margin-bottom: 15px;">The New Model</h4>
                    </div>
                    <ul style="color: #555; line-height: 2; font-size: 0.95em; list-style-position: inside;">
                        <li>Flat fee partnerships</li>
                        <li>Quality incentivized</li>
                        <li>Rigorous screening</li>
                        <li>Impact over volume</li>
                        <li>Fraud resistant</li>
                    </ul>
                    <div style="margin-top: 20px; padding: 15px; background: rgba(39, 174, 96, 0.2); border-radius: 6px; text-align: center; font-size: 0.9em; color: #1e8449;">
                        <strong>2024 Frontiers:</strong><br>~80,000 articles/year
                    </div>
                </div>
            </div>

            <div style="margin-top: 30px; padding: 25px; background: #ecf0f1; border-radius: 8px; border-left: 5px solid #34495e;">
                <p style="color: #2c3e50; font-size: 1.05em; line-height: 1.7; margin: 0; font-style: italic; text-align: center;">
                    "The $1 billion question: Can publishers maintain quality while scaling to thousands of articles monthly?"<br>
                    <span style="font-size: 0.85em; font-style: normal; opacity: 0.8;">— Academic Publishing Analysis, 2023</span>
                </p>
            </div>

            <div style="margin-top: 20px; text-align: center; font-size: 1.1em; color: #27ae60; font-weight: 600;">
                Frontiers' answer: We won't try. We'll choose differently.
            </div>
        </div>
    `;
}

function renderFutureImplications(container) {
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 40px; background: white; border-radius: 8px;">
            <h3 style="text-align: center; font-size: 1.7em; color: #2c3e50; margin-bottom: 35px;">If This Works...</h3>

            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div style="background: linear-gradient(to right, #667eea 0%, #764ba2 100%); padding: 25px 30px; border-radius: 10px; color: white;">
                    <div style="font-size: 1.2em; font-weight: 600; margin-bottom: 8px;">👨‍🔬 For Researchers</div>
                    <div style="font-size: 0.95em; opacity: 0.95; line-height: 1.6;">
                        Pressure shifts from "publish constantly" to "publish impactfully"<br>
                        → Fewer, better papers become the norm
                    </div>
                </div>

                <div style="background: linear-gradient(to right, #f093fb 0%, #f5576c 100%); padding: 25px 30px; border-radius: 10px; color: white;">
                    <div style="font-size: 1.2em; font-weight: 600; margin-bottom: 8px;">🏛️ For Universities</div>
                    <div style="font-size: 0.95em; opacity: 0.95; line-height: 1.6;">
                        Tenure criteria evolve beyond publication counts<br>
                        → Quality, citations, and real-world impact matter more
                    </div>
                </div>

                <div style="background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%); padding: 25px 30px; border-radius: 10px; color: white;">
                    <div style="font-size: 1.2em; font-weight: 600; margin-bottom: 8px;">💰 For Funders</div>
                    <div style="font-size: 0.95em; opacity: 0.95; line-height: 1.6;">
                        Confidence in published research increases<br>
                        → Investment in rigorous science grows
                    </div>
                </div>

                <div style="background: linear-gradient(to right, #43e97b 0%, #38f9d7 100%); padding: 25px 30px; border-radius: 10px; color: white;">
                    <div style="font-size: 1.2em; font-weight: 600; margin-bottom: 8px;">🌐 For Science</div>
                    <div style="font-size: 0.95em; opacity: 0.95; line-height: 1.6;">
                        Trust in the scientific enterprise is restored<br>
                        → Research becomes more credible, more influential
                    </div>
                </div>
            </div>

            <div style="margin-top: 30px; padding: 25px; background: #fff3cd; border-radius: 8px; border-left: 5px solid #ffc107;">
                <p style="color: #856404; font-size: 1em; line-height: 1.7; margin: 0; text-align: center; font-style: italic;">
                    "The ripple effects of one publisher's choice could reshape<br>how we measure scientific success."
                </p>
            </div>
        </div>
    `;
}

function renderCaveats(container) {
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 40px; background: white; border-radius: 8px;">
            <h3 style="text-align: center; font-size: 1.6em; color: #e74c3c; margin-bottom: 30px;">⚠️ What We Don't Know Yet</h3>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                <div style="background: #ffebee; padding: 20px; border-radius: 8px; border-left: 4px solid #e74c3c;">
                    <h4 style="color: #c0392b; margin-bottom: 10px; font-size: 1.1em;">⏰ Long-term Impact</h4>
                    <p style="color: #666; font-size: 0.9em; line-height: 1.6; margin: 0;">
                        True scientific impact takes years or decades to measure. 2024 satisfaction scores are encouraging but incomplete.
                    </p>
                </div>

                <div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #f39c12;">
                    <h4 style="color: #d68910; margin-bottom: 10px; font-size: 1.1em;">💰 Financial Sustainability</h4>
                    <p style="color: #666; font-size: 0.9em; line-height: 1.6; margin: 0;">
                        Can declining revenue from fewer articles be offset by institutional partnerships? Still uncertain.
                    </p>
                </div>

                <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 4px solid #4caf50;">
                    <h4 style="color: #2e7d32; margin-bottom: 10px; font-size: 1.1em;">🤖 Arms Race Continues</h4>
                    <p style="color: #666; font-size: 0.9em; line-height: 1.6; margin: 0;">
                        Paper mills are adapting. As AIRA gets smarter, fraud techniques evolve. This is an ongoing battle.
                    </p>
                </div>

                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3;">
                    <h4 style="color: #1565c0; margin-bottom: 10px; font-size: 1.1em;">🌍 Cultural Adoption</h4>
                    <p style="color: #666; font-size: 0.9em; line-height: 1.6; margin: 0;">
                        Will universities change tenure criteria? Will researchers embrace publishing less? Cultural change is slow.
                    </p>
                </div>
            </div>

            <div style="background: #f5f7fa; padding: 25px; border-radius: 8px; margin-top: 15px;">
                <h4 style="color: #2c3e50; margin-bottom: 15px; font-size: 1.15em; text-align: center;">Data Limitations</h4>
                <ul style="color: #555; line-height: 2; font-size: 0.95em; margin-left: 25px;">
                    <li>2024 represents a snapshot; longitudinal data needed</li>
                    <li>Quality surveys measure perceptions, not objective scientific validity</li>
                    <li>Financial data not fully disclosed; assessment is partial</li>
                    <li>Comparison to competitors limited by proprietary data</li>
                    <li>Paper mill prevalence estimates vary widely</li>
                </ul>
            </div>

            <div style="margin-top: 25px; text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white; font-size: 1.05em; line-height: 1.7;">
                <strong>The honest assessment:</strong><br>
                Early results are promising, but the full story will take years to write.
            </div>
        </div>
    `;
}

function renderConclusion(container) {
    const data = [
        {
            type: 'indicator',
            mode: 'number+delta',
            value: 80000,
            delta: { reference: 125104, relative: true, valueformat: '.1%', decreasing: { color: '#27ae60' } },
            title: { text: 'Articles Published (2024 vs. 2022 Peak)', font: { size: 16 } },
            domain: { x: [0, 0.5], y: [0.6, 1] },
            number: { suffix: '', font: { size: 42 } }
        },
        {
            type: 'indicator',
            mode: 'number+delta',
            value: 94,
            delta: { reference: 78, relative: false, valueformat: '.0f', increasing: { color: '#27ae60' } },
            title: { text: 'Quality Rating % (2024 vs. 2020)', font: { size: 16 } },
            domain: { x: [0.5, 1], y: [0.6, 1] },
            number: { suffix: '%', font: { size: 42 } }
        },
        {
            type: 'indicator',
            mode: 'number',
            value: 52,
            title: { text: 'Integrity Rejection Rate %', font: { size: 16 } },
            domain: { x: [0, 0.33], y: [0, 0.4] },
            number: { suffix: '%', font: { size: 38, color: '#e74c3c' } }
        },
        {
            type: 'indicator',
            mode: 'number',
            value: 76,
            title: { text: 'Institutional Partners', font: { size: 16 } },
            domain: { x: [0.33, 0.66], y: [0, 0.4] },
            number: { font: { size: 38, color: '#3498db' } }
        },
        {
            type: 'indicator',
            mode: 'number',
            value: 60,
            title: { text: 'AIRA Quality Checks', font: { size: 16 } },
            domain: { x: [0.66, 1], y: [0, 0.4] },
            number: { suffix: '+', font: { size: 38, color: '#9b59b6' } }
        }
    ];

    const layout = {
        title: '',
        grid: { rows: 2, columns: 3, pattern: 'independent' },
        margin: { t: 40, r: 40, b: 40, l: 40 },
        paper_bgcolor: 'white',
        font: { family: 'Georgia, serif' }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot(container, data, layout, config);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initScrollObserver();
    // Initialize with first chart
    updateChart('intro');
});
