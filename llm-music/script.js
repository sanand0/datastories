// Global data storage
let meansData = [];
let emotionStats = [];
let currentSong = null;

const emotions = [
    'amazement', 'solemnity', 'tenderness', 'nostalgia',
    'calmness', 'power', 'joyful_activation', 'tension', 'sadness'
];

const emotionLabels = {
    'amazement': 'Amazement',
    'solemnity': 'Solemnity',
    'tenderness': 'Tenderness',
    'nostalgia': 'Nostalgia',
    'calmness': 'Calmness',
    'power': 'Power',
    'joyful_activation': 'Joyful Activation',
    'tension': 'Tension',
    'sadness': 'Sadness'
};

// Color schemes - matching dark theme
const colors = {
    human: '#00d9ff',      // accent-cool (cyan)
    ai: '#ff6b35',         // accent-warm (orange)
    positive: '#06ffa5',   // success (green)
    negative: '#ff006e',   // danger (pink/red)
    neutral: '#f7931e',    // accent-hot (amber)
    bg: '#12141d',         // bg-panel
    text: '#f4f1de',       // text-primary
    textSecondary: '#b8b5a0',  // text-secondary
    border: '#1a1f3a'      // border-color
};

// Initialize the page
async function init() {
    try {
        // Load CSV data
        const meansCSV = await d3.csv('means_comparison.csv');
        meansData = processCSVData(meansCSV);

        // Calculate emotion-level statistics
        emotionStats = calculateEmotionStats(meansData);

        // Create visualizations
        createSongSelector();
        createEmotionGrid();
        createEmotionPerformanceChart();
        createBestWorstChart();
        createCorrelationMatrices();

    } catch (error) {
        console.error('Error initializing:', error);
    }
}

// Process CSV data into structured format
function processCSVData(csv) {
    const songs = {};

    csv.forEach(row => {
        const song = row.song;
        if (!songs[song]) {
            songs[song] = { gemini: {}, emotify: {}, diff: {} };
        }

        const source = row.source;
        emotions.forEach(emotion => {
            songs[song][source][emotion] = parseFloat(row[emotion]);
        });
    });

    return songs;
}

// Calculate per-emotion statistics
function calculateEmotionStats(data) {
    const stats = {};

    emotions.forEach(emotion => {
        const geminiValues = [];
        const emotifyValues = [];
        const diffs = [];

        Object.keys(data).forEach(song => {
            geminiValues.push(data[song].gemini[emotion]);
            emotifyValues.push(data[song].emotify[emotion]);
            diffs.push(data[song].diff[emotion]);
        });

        // Calculate correlation
        const correlation = pearsonCorrelation(geminiValues, emotifyValues);

        // Calculate mean bias
        const bias = d3.mean(diffs);

        // Calculate MAE
        const mae = d3.mean(diffs.map(d => Math.abs(d)));

        stats[emotion] = {
            correlation: correlation,
            bias: bias,
            mae: mae,
            geminiMean: d3.mean(geminiValues),
            emotifyMean: d3.mean(emotifyValues)
        };
    });

    return stats;
}

// Pearson correlation coefficient
function pearsonCorrelation(x, y) {
    const n = x.length;
    const sum_x = d3.sum(x);
    const sum_y = d3.sum(y);
    const sum_xy = d3.sum(x.map((xi, i) => xi * y[i]));
    const sum_x2 = d3.sum(x.map(xi => xi * xi));
    const sum_y2 = d3.sum(y.map(yi => yi * yi));

    const numerator = n * sum_xy - sum_x * sum_y;
    const denominator = Math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y));

    return denominator === 0 ? 0 : numerator / denominator;
}

// Create song selector buttons
function createSongSelector() {
    const selector = d3.select('#songSelector');
    const songs = Object.keys(meansData).sort((a, b) => {
        const numA = parseInt(a.split('_')[1]);
        const numB = parseInt(b.split('_')[1]);
        return numA - numB;
    });

    // Create buttons for first 20 songs (to keep it manageable)
    songs.slice(0, 20).forEach(song => {
        selector.append('div')
            .attr('class', 'song-button')
            .text(song.replace('_', ' ').toUpperCase())
            .on('click', () => selectSong(song));
    });

    // Select first song by default
    selectSong(songs[0]);
}

// Handle song selection
function selectSong(song) {
    currentSong = song;

    // Update button states
    d3.selectAll('.song-button')
        .classed('active', function() {
            return this.textContent === song.replace('_', ' ').toUpperCase();
        });

    // Update audio player
    const audioPlayer = d3.select('#audioPlayer');
    const audioElement = d3.select('#audioElement');
    const songTitle = d3.select('#currentSongTitle');

    audioPlayer.style('display', 'block');
    songTitle.text(song.replace('_', ' ').toUpperCase());
    audioElement.attr('src', `data/${song}.opus`);

    // Update radar chart
    updateRadarChart(song);
}

// Create radar chart
function updateRadarChart(song) {
    const svg = d3.select('#radarChart');
    svg.selectAll('*').remove();

    const width = 600;
    const height = 600;
    const margin = 80;
    const radius = Math.min(width, height) / 2 - margin;

    const g = svg.append('g')
        .attr('transform', `translate(${width/2}, ${height/2})`);

    // Prepare data
    const geminiData = emotions.map(e => meansData[song].gemini[e]);
    const emotifyData = emotions.map(e => meansData[song].emotify[e]);

    // Scales
    const angleScale = d3.scaleLinear()
        .domain([0, emotions.length])
        .range([0, 2 * Math.PI]);

    const radiusScale = d3.scaleLinear()
        .domain([0, 1])
        .range([0, radius]);

    // Draw circular grid
    const levels = 5;
    for (let i = 1; i <= levels; i++) {
        const r = radius * (i / levels);
        g.append('circle')
            .attr('r', r)
            .attr('fill', 'none')
            .attr('stroke', colors.border)
            .attr('stroke-width', 1)
            .attr('opacity', 0.5);

        // Add level labels
        g.append('text')
            .attr('x', 5)
            .attr('y', -r)
            .attr('font-size', '10px')
            .attr('fill', colors.textSecondary)
            .text((i / levels).toFixed(1));
    }

    // Draw axes
    emotions.forEach((emotion, i) => {
        const angle = angleScale(i) - Math.PI / 2;
        const x = radius * Math.cos(angle);
        const y = radius * Math.sin(angle);

        g.append('line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', x)
            .attr('y2', y)
            .attr('stroke', colors.border)
            .attr('stroke-width', 1)
            .attr('opacity', 0.5);

        // Add labels
        const labelRadius = radius + 30;
        const labelX = labelRadius * Math.cos(angle);
        const labelY = labelRadius * Math.sin(angle);

        g.append('text')
            .attr('x', labelX)
            .attr('y', labelY)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('font-size', '12px')
            .attr('font-weight', '600')
            .attr('fill', colors.text)
            .text(emotionLabels[emotion])
            .call(wrap, 100);
    });

    // Draw data polygons
    const lineGenerator = d3.lineRadial()
        .angle((d, i) => angleScale(i) - Math.PI / 2)
        .radius(d => radiusScale(d))
        .curve(d3.curveLinearClosed);

    // Emotify (human) data
    g.append('path')
        .datum(emotifyData)
        .attr('d', lineGenerator)
        .attr('fill', colors.human)
        .attr('fill-opacity', 0.2)
        .attr('stroke', colors.human)
        .attr('stroke-width', 3);

    // Gemini (AI) data
    g.append('path')
        .datum(geminiData)
        .attr('d', lineGenerator)
        .attr('fill', colors.ai)
        .attr('fill-opacity', 0.2)
        .attr('stroke', colors.ai)
        .attr('stroke-width', 3);

    // Add data points with tooltips
    emotions.forEach((emotion, i) => {
        const angle = angleScale(i) - Math.PI / 2;

        // Human points
        const humanR = radiusScale(emotifyData[i]);
        const humanX = humanR * Math.cos(angle);
        const humanY = humanR * Math.sin(angle);

        g.append('circle')
            .attr('cx', humanX)
            .attr('cy', humanY)
            .attr('r', 5)
            .attr('fill', colors.human)
            .style('cursor', 'pointer')
            .append('title')
            .text(`Human: ${emotionLabels[emotion]} = ${(emotifyData[i] * 100).toFixed(1)}%`);

        // AI points
        const aiR = radiusScale(geminiData[i]);
        const aiX = aiR * Math.cos(angle);
        const aiY = aiR * Math.sin(angle);

        g.append('circle')
            .attr('cx', aiX)
            .attr('cy', aiY)
            .attr('r', 5)
            .attr('fill', colors.ai)
            .style('cursor', 'pointer')
            .append('title')
            .text(`AI: ${emotionLabels[emotion]} = ${(geminiData[i] * 100).toFixed(1)}%`);
    });
}

// Wrap text for labels
function wrap(text, width) {
    text.each(function() {
        const text = d3.select(this);
        const words = text.text().split(/\s+/).reverse();
        let word;
        let line = [];
        let lineNumber = 0;
        const lineHeight = 1.1;
        const y = text.attr('y');
        const dy = 0;
        let tspan = text.text(null).append('tspan').attr('x', text.attr('x')).attr('y', y).attr('dy', dy + 'em');

        while (word = words.pop()) {
            line.push(word);
            tspan.text(line.join(' '));
            if (tspan.node().getComputedTextLength() > width && line.length > 1) {
                line.pop();
                tspan.text(line.join(' '));
                line = [word];
                tspan = text.append('tspan').attr('x', text.attr('x')).attr('y', y).attr('dy', ++lineNumber * lineHeight + dy + 'em').text(word);
            }
        }
    });
}

// Create emotion grid with statistics
function createEmotionGrid() {
    const grid = d3.select('#emotionGrid');

    // Sort emotions by correlation (worst to best)
    const sortedEmotions = emotions.slice().sort((a, b) =>
        emotionStats[a].correlation - emotionStats[b].correlation
    );

    sortedEmotions.forEach(emotion => {
        const stats = emotionStats[emotion];
        const card = grid.append('div')
            .attr('class', 'emotion-card');

        card.append('div')
            .attr('class', 'emotion-name')
            .text(emotionLabels[emotion]);

        const corrClass = stats.correlation < 0 ? 'correlation-negative' :
                         stats.correlation < 0.2 ? 'correlation-neutral' :
                         'correlation-positive';

        card.append('div')
            .attr('class', `correlation ${corrClass}`)
            .text(`r = ${stats.correlation.toFixed(3)}`);

        card.append('div')
            .attr('class', 'bias')
            .html(`Bias: ${stats.bias >= 0 ? '+' : ''}${(stats.bias * 100).toFixed(1)}%<br>MAE: ${(stats.mae * 100).toFixed(1)}%`);
    });
}

// Create emotion performance chart
function createEmotionPerformanceChart() {
    const svg = d3.select('#emotionPerformanceChart');
    svg.selectAll('*').remove();

    const width = 1100;
    const height = 500;
    const margin = { top: 40, right: 100, bottom: 120, left: 80 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);

    // Prepare data
    const data = emotions.map(emotion => ({
        emotion: emotionLabels[emotion],
        correlation: emotionStats[emotion].correlation,
        mae: emotionStats[emotion].mae,
        bias: emotionStats[emotion].bias
    })).sort((a, b) => b.correlation - a.correlation);

    // Scales
    const xScale = d3.scaleBand()
        .domain(data.map(d => d.emotion))
        .range([0, chartWidth])
        .padding(0.2);

    const yScale = d3.scaleLinear()
        .domain([-0.4, 0.4])
        .range([chartHeight, 0]);

    // Axes
    g.append('g')
        .attr('transform', `translate(0, ${yScale(0)})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .attr('transform', 'rotate(-45)')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em');

    g.append('g')
        .call(d3.axisLeft(yScale).tickFormat(d => d.toFixed(1)));

    // Zero line
    g.append('line')
        .attr('x1', 0)
        .attr('x2', chartWidth)
        .attr('y1', yScale(0))
        .attr('y2', yScale(0))
        .attr('stroke', colors.textSecondary)
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '4')
        .attr('opacity', 0.5);

    // Bars for correlation
    g.selectAll('.correlation-bar')
        .data(data)
        .enter()
        .append('rect')
        .attr('class', 'correlation-bar')
        .attr('x', d => xScale(d.emotion))
        .attr('y', d => d.correlation >= 0 ? yScale(d.correlation) : yScale(0))
        .attr('width', xScale.bandwidth() * 0.4)
        .attr('height', d => Math.abs(yScale(d.correlation) - yScale(0)))
        .attr('fill', d => d.correlation < 0 ? colors.negative : colors.positive)
        .attr('opacity', 0.7);

    // Bars for bias
    g.selectAll('.bias-bar')
        .data(data)
        .enter()
        .append('rect')
        .attr('class', 'bias-bar')
        .attr('x', d => xScale(d.emotion) + xScale.bandwidth() * 0.5)
        .attr('y', d => d.bias >= 0 ? yScale(d.bias) : yScale(0))
        .attr('width', xScale.bandwidth() * 0.4)
        .attr('height', d => Math.abs(yScale(d.bias) - yScale(0)))
        .attr('fill', colors.ai)
        .attr('opacity', 0.7);

    // Axis labels
    g.append('text')
        .attr('x', chartWidth / 2)
        .attr('y', -20)
        .attr('text-anchor', 'middle')
        .attr('font-size', '14px')
        .attr('font-weight', '600')
        .attr('fill', colors.text)
        .text('Correlation (bars) and Bias (orange bars)');

    // Legend
    const legend = svg.append('g')
        .attr('transform', `translate(${width - margin.right + 10}, ${margin.top})`);

    legend.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', 15)
        .attr('height', 15)
        .attr('fill', colors.positive);

    legend.append('text')
        .attr('x', 20)
        .attr('y', 12)
        .attr('font-size', '12px')
        .attr('fill', colors.text)
        .text('Correlation');

    legend.append('rect')
        .attr('x', 0)
        .attr('y', 25)
        .attr('width', 15)
        .attr('height', 15)
        .attr('fill', colors.ai);

    legend.append('text')
        .attr('x', 20)
        .attr('y', 37)
        .attr('font-size', '12px')
        .attr('fill', colors.text)
        .text('Bias');
}

// Create best vs worst chart
function createBestWorstChart() {
    const svg = d3.select('#bestWorstChart');
    svg.selectAll('*').remove();

    const width = 1100;
    const height = 400;
    const margin = { top: 40, right: 40, bottom: 60, left: 80 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);

    // Calculate MAE for each song
    const songMAEs = Object.keys(meansData).map(song => {
        const maes = emotions.map(emotion => Math.abs(meansData[song].diff[emotion]));
        return {
            song: song,
            mae: d3.mean(maes)
        };
    }).sort((a, b) => a.mae - b.mae);

    // Get best 5 and worst 5
    const best5 = songMAEs.slice(0, 5);
    const worst5 = songMAEs.slice(-5).reverse();
    const data = [...best5, ...worst5];

    // Scales
    const yScale = d3.scaleBand()
        .domain(data.map(d => d.song))
        .range([0, chartHeight])
        .padding(0.2);

    const xScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.mae)])
        .range([0, chartWidth]);

    // Axes
    g.append('g')
        .call(d3.axisLeft(yScale).tickFormat(d => d.replace('_', ' ').toUpperCase()));

    g.append('g')
        .attr('transform', `translate(0, ${chartHeight})`)
        .call(d3.axisBottom(xScale).tickFormat(d => (d * 100).toFixed(0) + '%'));

    // Bars
    g.selectAll('.mae-bar')
        .data(data)
        .enter()
        .append('rect')
        .attr('class', 'mae-bar')
        .attr('x', 0)
        .attr('y', d => yScale(d.song))
        .attr('width', d => xScale(d.mae))
        .attr('height', yScale.bandwidth())
        .attr('fill', (d, i) => i < 5 ? colors.positive : colors.negative)
        .attr('opacity', 0.7);

    // Labels
    g.append('text')
        .attr('x', chartWidth / 2)
        .attr('y', -20)
        .attr('text-anchor', 'middle')
        .attr('font-size', '14px')
        .attr('font-weight', '600')
        .attr('fill', colors.text)
        .text('Mean Absolute Error by Song (Best 5 and Worst 5)');

    g.append('text')
        .attr('x', chartWidth / 2)
        .attr('y', chartHeight + 50)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .attr('fill', colors.textSecondary)
        .text('Mean Absolute Error (%)');
}

// Create correlation matrices
function createCorrelationMatrices() {
    createCorrelationMatrix('#humanCorrelationMatrix', 'emotify');
    createCorrelationMatrix('#aiCorrelationMatrix', 'gemini');
}

function createCorrelationMatrix(selector, source) {
    const svg = d3.select(selector);
    svg.selectAll('*').remove();

    const size = 500;
    const margin = 60;
    const cellSize = (size - 2 * margin) / emotions.length;

    const g = svg.append('g')
        .attr('transform', `translate(${margin}, ${margin})`);

    // Calculate correlation matrix
    const correlations = [];
    for (let i = 0; i < emotions.length; i++) {
        for (let j = 0; j < emotions.length; j++) {
            const values1 = Object.keys(meansData).map(song => meansData[song][source][emotions[i]]);
            const values2 = Object.keys(meansData).map(song => meansData[song][source][emotions[j]]);
            const corr = pearsonCorrelation(values1, values2);

            correlations.push({
                i: i,
                j: j,
                emotion1: emotions[i],
                emotion2: emotions[j],
                correlation: corr
            });
        }
    }

    // Color scale
    const colorScale = d3.scaleSequential()
        .domain([-1, 1])
        .interpolator(d3.interpolateRdBu);

    // Draw cells
    g.selectAll('.cell')
        .data(correlations)
        .enter()
        .append('rect')
        .attr('class', 'cell')
        .attr('x', d => d.j * cellSize)
        .attr('y', d => d.i * cellSize)
        .attr('width', cellSize - 1)
        .attr('height', cellSize - 1)
        .attr('fill', d => colorScale(d.correlation))
        .attr('opacity', 0.8)
        .append('title')
        .text(d => `${emotionLabels[d.emotion1]} vs ${emotionLabels[d.emotion2]}: ${d.correlation.toFixed(3)}`);

    // Add labels
    const shortLabels = {
        'amazement': 'Amaze',
        'solemnity': 'Solem',
        'tenderness': 'Tender',
        'nostalgia': 'Nostal',
        'calmness': 'Calm',
        'power': 'Power',
        'joyful_activation': 'Joy',
        'tension': 'Tension',
        'sadness': 'Sad'
    };

    // Top labels
    emotions.forEach((emotion, i) => {
        g.append('text')
            .attr('x', i * cellSize + cellSize / 2)
            .attr('y', -5)
            .attr('text-anchor', 'end')
            .attr('font-size', '10px')
            .attr('fill', colors.text)
            .attr('transform', `rotate(-45, ${i * cellSize + cellSize / 2}, -5)`)
            .text(shortLabels[emotion]);
    });

    // Left labels
    emotions.forEach((emotion, i) => {
        g.append('text')
            .attr('x', -5)
            .attr('y', i * cellSize + cellSize / 2)
            .attr('text-anchor', 'end')
            .attr('dominant-baseline', 'middle')
            .attr('font-size', '10px')
            .attr('fill', colors.text)
            .text(shortLabels[emotion]);
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
