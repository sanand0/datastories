// The Jamnagar Chokepoint - Interactive Visualizations
// Data visualizations for India's trade story

// Color palette (matching The Verge aesthetic)
const colors = {
    purple: '#B366FF',
    cyan: '#66D9FF',
    pink: '#FF6BB3',
    yellow: '#FFD666',
    green: '#66FF99',
    red: '#FF6666',
    gray: '#B4B4B4',
    darkGray: '#1F1F1F',
    bgSecondary: '#151515'
};

// Utility functions
function formatBillion(value) {
    return `$${(value / 1e9).toFixed(1)}B`;
}

function formatPercent(value) {
    return `${(value * 100).toFixed(1)}%`;
}

// Tooltip functions
function showTooltip(event, html) {
    const tooltip = document.getElementById('tooltip');
    tooltip.innerHTML = html;
    tooltip.classList.add('visible');

    const x = event.pageX + 15;
    const y = event.pageY - 10;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    tooltip.classList.remove('visible');
}

// Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.2,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

document.querySelectorAll('.chapter').forEach(chapter => {
    observer.observe(chapter);
});

// Data for visualizations
const portConcentrationData = [
    { port: 'SEZ Jamnagar\n(Reliance)', commodity: 'Petroleum', share: 0.482, value: 34.5 },
    { port: 'DPCC Mumbai', commodity: 'Gems & Jewelry', share: 0.899, value: 14.6 },
    { port: 'GMR Hyderabad\nSEZ', commodity: 'Aircraft', share: 0.812, value: 6.0 },
    { port: 'Mundra', commodity: 'Castor Oil', share: 0.737, value: 0.85 },
    { port: 'Chennai Sea', commodity: 'Tobacco', share: 0.661, value: 0.92 },
    { port: 'Mundra', commodity: 'Ceramics', share: 0.656, value: 1.9 },
    { port: 'Paradip Sea', commodity: 'Iron Ore', share: 0.463, value: 1.3 },
    { port: 'Vedanta\nJharsugda', commodity: 'Aluminium', share: 0.461, value: 3.4 },
    { port: 'Chennai Air', commodity: 'Telecom Equip', share: 0.414, value: 9.2 },
    { port: 'Nhava Sheva\nSea', commodity: 'Multiple', share: 0.30, value: 45.2 }
];

const deficitData = {
    total: -273.7,
    energyGold: -208.8,
    energyGoldShare: 0.763,
    top5: -284.7,
    remaining: -64.9
};

const exportGrowthData = {
    total2023: 431.4,
    total2024: 442.8,
    petroleum2023: 85.8,
    petroleum2024: 71.5,
    nonPetro2023: 345.6,
    nonPetro2024: 371.3
};

const exportShiftsData = [
    { commodity: 'Telecom Instruments', value: 6.37, color: colors.purple },
    { commodity: 'Aircraft & Spacecraft', value: 5.51, color: colors.cyan },
    { commodity: 'Pharmaceuticals', value: 2.04, color: colors.pink },
    { commodity: 'Electric Machinery', value: 1.77, color: colors.yellow },
    { commodity: 'Chemicals', value: 1.42, color: colors.green },
    { commodity: 'Paint & Varnish', value: 1.11, color: colors.red },
    { commodity: 'Other', value: 4.19, color: colors.gray },
    { commodity: 'Petroleum Products', value: -14.26, color: '#FF4444' }
];

const concentrationData = {
    imports: { hhi: 0.065, top5Share: 0.443 },
    exports: { hhi: 0.042, top5Share: 0.332 }
};

// Visualization 1: Port Concentration Bar Chart
function createPortConcentration() {
    const container = d3.select('#viz-port-concentration');
    const width = container.node().getBoundingClientRect().width;
    const height = 500;
    const margin = { top: 20, right: 140, bottom: 60, left: 200 };

    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);

    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scaleLinear()
        .domain([0, 1])
        .range([0, chartWidth]);

    const y = d3.scaleBand()
        .domain(portConcentrationData.map(d => d.port))
        .range([0, chartHeight])
        .padding(0.2);

    // Color scale
    const colorScale = d3.scaleSequential()
        .domain([0, 1])
        .interpolator(d3.interpolateRgb(colors.cyan, colors.purple));

    // Bars
    g.selectAll('.bar')
        .data(portConcentrationData)
        .join('rect')
        .attr('class', 'bar')
        .attr('x', 0)
        .attr('y', d => y(d.port))
        .attr('width', 0)
        .attr('height', y.bandwidth())
        .attr('fill', d => colorScale(d.share))
        .attr('rx', 4)
        .on('mouseenter', (event, d) => {
            showTooltip(event, `
                <strong>${d.port}</strong><br>
                <strong>${d.commodity}</strong><br>
                ${formatPercent(d.share)} of commodity exports<br>
                ${formatBillion(d.value * 1e9)} in 2024
            `);
        })
        .on('mouseleave', hideTooltip)
        .transition()
        .duration(1000)
        .delay((d, i) => i * 50)
        .attr('width', d => x(d.share));

    // Labels
    g.selectAll('.label')
        .data(portConcentrationData)
        .join('text')
        .attr('class', 'label')
        .attr('x', -10)
        .attr('y', d => y(d.port) + y.bandwidth() / 2)
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'middle')
        .attr('fill', colors.gray)
        .attr('font-size', '12px')
        .text(d => d.port);

    // Percentage labels
    g.selectAll('.pct-label')
        .data(portConcentrationData)
        .join('text')
        .attr('class', 'pct-label')
        .attr('x', d => x(d.share) + 10)
        .attr('y', d => y(d.port) + y.bandwidth() / 2)
        .attr('dominant-baseline', 'middle')
        .attr('fill', '#FAFAFA')
        .attr('font-size', '14px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(d => formatPercent(d.share))
        .transition()
        .duration(1000)
        .delay((d, i) => i * 50 + 500)
        .attr('opacity', 1);

    // X-axis
    const xAxis = d3.axisBottom(x)
        .ticks(5)
        .tickFormat(d3.format('.0%'));

    g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .attr('class', 'axis')
        .selectAll('text')
        .attr('fill', colors.gray);

    // Highlight line for 50%
    g.append('line')
        .attr('x1', x(0.5))
        .attr('x2', x(0.5))
        .attr('y1', 0)
        .attr('y2', chartHeight)
        .attr('stroke', colors.yellow)
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '4,4')
        .attr('opacity', 0.5);

    g.append('text')
        .attr('x', x(0.5))
        .attr('y', -5)
        .attr('text-anchor', 'middle')
        .attr('fill', colors.yellow)
        .attr('font-size', '11px')
        .text('50% concentration threshold');
}

// Visualization 2: Deficit Sankey/Flow
function createDeficitSankey() {
    const container = d3.select('#viz-deficit-sankey');
    const width = container.node().getBoundingClientRect().width;
    const height = 400;
    const margin = { top: 40, right: 20, bottom: 40, left: 20 };

    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);

    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create flow visualization
    const totalDeficit = Math.abs(deficitData.total);
    const energyGold = Math.abs(deficitData.energyGold);
    const remaining = Math.abs(deficitData.remaining);

    const barHeight = 80;
    const y = chartHeight / 2 - barHeight / 2;

    // Total deficit bar
    g.append('rect')
        .attr('x', 0)
        .attr('y', y)
        .attr('width', chartWidth)
        .attr('height', barHeight)
        .attr('fill', colors.red)
        .attr('opacity', 0.3)
        .attr('rx', 8);

    g.append('text')
        .attr('x', chartWidth / 2)
        .attr('y', y - 10)
        .attr('text-anchor', 'middle')
        .attr('fill', colors.gray)
        .attr('font-size', '12px')
        .text('Total Trade Deficit 2024');

    g.append('text')
        .attr('x', chartWidth / 2)
        .attr('y', y + barHeight / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#FAFAFA')
        .attr('font-size', '28px')
        .attr('font-weight', '900')
        .text(formatBillion(totalDeficit * 1e9));

    // Energy + Gold section
    const energyWidth = (energyGold / totalDeficit) * chartWidth;

    g.append('rect')
        .attr('x', 0)
        .attr('y', y)
        .attr('width', 0)
        .attr('height', barHeight)
        .attr('fill', colors.purple)
        .attr('opacity', 0.8)
        .attr('rx', 8)
        .transition()
        .duration(1500)
        .attr('width', energyWidth);

    g.append('text')
        .attr('x', energyWidth / 2)
        .attr('y', y + barHeight + 30)
        .attr('text-anchor', 'middle')
        .attr('fill', colors.purple)
        .attr('font-size', '14px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(`Energy + Gold: ${formatBillion(energyGold * 1e9)} (${formatPercent(deficitData.energyGoldShare)})`)
        .transition()
        .delay(1500)
        .duration(800)
        .attr('opacity', 1);

    // Remaining section
    g.append('text')
        .attr('x', energyWidth + (chartWidth - energyWidth) / 2)
        .attr('y', y + barHeight + 30)
        .attr('text-anchor', 'middle')
        .attr('fill', colors.cyan)
        .attr('font-size', '14px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(`All Other: ${formatBillion(remaining * 1e9)} (${formatPercent(1 - deficitData.energyGoldShare)})`)
        .transition()
        .delay(1500)
        .duration(800)
        .attr('opacity', 1);

    // Arrow and annotation
    g.append('path')
        .attr('d', `M ${energyWidth} ${y - 30} L ${energyWidth} ${y - 10}`)
        .attr('stroke', colors.yellow)
        .attr('stroke-width', 2)
        .attr('marker-end', 'url(#arrowhead)')
        .attr('opacity', 0)
        .transition()
        .delay(2000)
        .duration(500)
        .attr('opacity', 1);

    // Arrow marker
    svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('markerWidth', 10)
        .attr('markerHeight', 10)
        .attr('refX', 5)
        .attr('refY', 5)
        .attr('orient', 'auto')
        .append('polygon')
        .attr('points', '0 0, 10 5, 0 10')
        .attr('fill', colors.yellow);
}

// Visualization 3: Export Growth Comparison
function createExportGrowth() {
    const container = d3.select('#viz-export-growth');
    const width = container.node().getBoundingClientRect().width;
    const height = 450;
    const margin = { top: 40, right: 20, bottom: 80, left: 80 };

    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);

    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Data structure
    const data = [
        { category: 'Total Exports', year2023: exportGrowthData.total2023, year2024: exportGrowthData.total2024 },
        { category: 'Petroleum', year2023: exportGrowthData.petroleum2023, year2024: exportGrowthData.petroleum2024 },
        { category: 'Non-Petroleum', year2023: exportGrowthData.nonPetro2023, year2024: exportGrowthData.nonPetro2024 }
    ];

    // Scales
    const x0 = d3.scaleBand()
        .domain(data.map(d => d.category))
        .range([0, chartWidth])
        .padding(0.2);

    const x1 = d3.scaleBand()
        .domain(['2023', '2024'])
        .range([0, x0.bandwidth()])
        .padding(0.1);

    const y = d3.scaleLinear()
        .domain([0, 500])
        .range([chartHeight, 0]);

    const colorMap = {
        '2023': colors.gray,
        '2024': colors.purple
    };

    // Bars
    const categories = g.selectAll('.category')
        .data(data)
        .join('g')
        .attr('class', 'category')
        .attr('transform', d => `translate(${x0(d.category)},0)`);

    categories.selectAll('rect')
        .data(d => [
            { year: '2023', value: d.year2023, category: d.category },
            { year: '2024', value: d.year2024, category: d.category }
        ])
        .join('rect')
        .attr('x', d => x1(d.year))
        .attr('y', chartHeight)
        .attr('width', x1.bandwidth())
        .attr('height', 0)
        .attr('fill', d => colorMap[d.year])
        .attr('rx', 3)
        .on('mouseenter', (event, d) => {
            const change = d.category === 'Total Exports'
                ? exportGrowthData.total2024 - exportGrowthData.total2023
                : d.category === 'Petroleum'
                ? exportGrowthData.petroleum2024 - exportGrowthData.petroleum2023
                : exportGrowthData.nonPetro2024 - exportGrowthData.nonPetro2023;

            const pct = ((change / (d.year === '2023' ? d.value : d.value - change)) * 100).toFixed(1);

            showTooltip(event, `
                <strong>${d.category} (${d.year})</strong><br>
                ${formatBillion(d.value * 1e9)}<br>
                ${change > 0 ? '+' : ''}${formatBillion(change * 1e9)} (${pct}%)
            `);
        })
        .on('mouseleave', hideTooltip)
        .transition()
        .duration(1000)
        .delay((d, i) => i * 100)
        .attr('y', d => y(d.value))
        .attr('height', d => chartHeight - y(d.value));

    // Axes
    g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x0))
        .attr('class', 'axis')
        .selectAll('text')
        .attr('fill', colors.gray)
        .attr('font-size', '13px');

    const yAxis = d3.axisLeft(y)
        .ticks(5)
        .tickFormat(d => `$${d}B`);

    g.append('g')
        .call(yAxis)
        .attr('class', 'axis')
        .selectAll('text')
        .attr('fill', colors.gray);

    // Legend
    const legend = svg.append('g')
        .attr('transform', `translate(${margin.left},${height - 40})`);

    const legendData = [
        { label: '2023', color: colors.gray },
        { label: '2024', color: colors.purple }
    ];

    const legendItems = legend.selectAll('.legend-item')
        .data(legendData)
        .join('g')
        .attr('class', 'legend-item')
        .attr('transform', (d, i) => `translate(${i * 100},0)`);

    legendItems.append('rect')
        .attr('width', 16)
        .attr('height', 16)
        .attr('fill', d => d.color)
        .attr('rx', 3);

    legendItems.append('text')
        .attr('x', 24)
        .attr('y', 12)
        .attr('fill', colors.gray)
        .attr('font-size', '13px')
        .text(d => d.label);

    // Highlight annotation for non-petroleum
    g.append('text')
        .attr('x', x0('Non-Petroleum') + x0.bandwidth() / 2)
        .attr('y', y(exportGrowthData.nonPetro2024) - 10)
        .attr('text-anchor', 'middle')
        .attr('fill', colors.green)
        .attr('font-size', '12px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text('+7.4% growth')
        .transition()
        .delay(1200)
        .duration(600)
        .attr('opacity', 1);
}

// Visualization 4: Export Shifts
function createExportShifts() {
    const container = d3.select('#viz-export-shifts');
    const width = container.node().getBoundingClientRect().width;
    const height = 450;
    const margin = { top: 20, right: 20, bottom: 60, left: 200 };

    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);

    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scaleLinear()
        .domain([d3.min(exportShiftsData, d => d.value), d3.max(exportShiftsData, d => d.value)])
        .range([0, chartWidth]);

    const y = d3.scaleBand()
        .domain(exportShiftsData.map(d => d.commodity))
        .range([0, chartHeight])
        .padding(0.2);

    // Zero line
    g.append('line')
        .attr('x1', x(0))
        .attr('x2', x(0))
        .attr('y1', 0)
        .attr('y2', chartHeight)
        .attr('stroke', colors.gray)
        .attr('stroke-width', 2);

    // Bars
    g.selectAll('.bar')
        .data(exportShiftsData)
        .join('rect')
        .attr('class', 'bar')
        .attr('x', d => d.value < 0 ? x(d.value) : x(0))
        .attr('y', d => y(d.commodity))
        .attr('width', 0)
        .attr('height', y.bandwidth())
        .attr('fill', d => d.color)
        .attr('rx', 4)
        .on('mouseenter', (event, d) => {
            showTooltip(event, `
                <strong>${d.commodity}</strong><br>
                ${d.value > 0 ? '+' : ''}${formatBillion(d.value * 1e9)} change (2023-2024)
            `);
        })
        .on('mouseleave', hideTooltip)
        .transition()
        .duration(1000)
        .delay((d, i) => i * 80)
        .attr('width', d => Math.abs(x(d.value) - x(0)));

    // Labels
    g.selectAll('.label')
        .data(exportShiftsData)
        .join('text')
        .attr('class', 'label')
        .attr('x', -10)
        .attr('y', d => y(d.commodity) + y.bandwidth() / 2)
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'middle')
        .attr('fill', colors.gray)
        .attr('font-size', '12px')
        .text(d => d.commodity);

    // Value labels
    g.selectAll('.value-label')
        .data(exportShiftsData)
        .join('text')
        .attr('class', 'value-label')
        .attr('x', d => d.value < 0 ? x(d.value) - 10 : x(d.value) + 10)
        .attr('y', d => y(d.commodity) + y.bandwidth() / 2)
        .attr('text-anchor', d => d.value < 0 ? 'end' : 'start')
        .attr('dominant-baseline', 'middle')
        .attr('fill', '#FAFAFA')
        .attr('font-size', '13px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(d => (d.value > 0 ? '+' : '') + formatBillion(d.value * 1e9))
        .transition()
        .duration(800)
        .delay((d, i) => i * 80 + 600)
        .attr('opacity', 1);

    // X-axis
    const xAxis = d3.axisBottom(x)
        .ticks(6)
        .tickFormat(d => d === 0 ? '0' : formatBillion(d * 1e9));

    g.append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .attr('class', 'axis')
        .selectAll('text')
        .attr('fill', colors.gray)
        .attr('font-size', '11px');
}

// Visualization 5: Concentration Comparison
function createConcentrationComparison() {
    const container = d3.select('#viz-concentration-comparison');
    const width = container.node().getBoundingClientRect().width;
    const height = 400;
    const margin = { top: 60, right: 20, bottom: 60, left: 20 };

    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);

    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Data
    const data = [
        { type: 'Imports', hhi: concentrationData.imports.hhi, top5: concentrationData.imports.top5Share },
        { type: 'Exports', hhi: concentrationData.exports.hhi, top5: concentrationData.exports.top5Share }
    ];

    const centerX = chartWidth / 2;
    const spacing = chartWidth / 3;

    // Create radial viz for each
    data.forEach((d, i) => {
        const x = i === 0 ? centerX - spacing/2 : centerX + spacing/2;
        const y = chartHeight / 2;
        const maxRadius = 100;

        // Outer circle (max)
        g.append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', maxRadius)
            .attr('fill', 'none')
            .attr('stroke', colors.darkGray)
            .attr('stroke-width', 1)
            .attr('stroke-dasharray', '2,2');

        // HHI circle
        const hhiRadius = (d.hhi / 0.1) * maxRadius; // Scale to 0.1 = max

        g.append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', 0)
            .attr('fill', i === 0 ? colors.red : colors.green)
            .attr('opacity', 0.3)
            .transition()
            .duration(1500)
            .attr('r', hhiRadius);

        // Top 5 ring
        const top5Radius = d.top5 * maxRadius;

        g.append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', 0)
            .attr('fill', 'none')
            .attr('stroke', i === 0 ? colors.red : colors.green)
            .attr('stroke-width', 3)
            .transition()
            .duration(1500)
            .delay(500)
            .attr('r', top5Radius);

        // Labels
        g.append('text')
            .attr('x', x)
            .attr('y', y - maxRadius - 20)
            .attr('text-anchor', 'middle')
            .attr('fill', '#FAFAFA')
            .attr('font-size', '18px')
            .attr('font-weight', '700')
            .text(d.type);

        g.append('text')
            .attr('x', x)
            .attr('y', y)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', '#FAFAFA')
            .attr('font-size', '24px')
            .attr('font-weight', '900')
            .attr('opacity', 0)
            .text(`HHI: ${d.hhi.toFixed(3)}`)
            .transition()
            .delay(1500)
            .duration(600)
            .attr('opacity', 1);

        g.append('text')
            .attr('x', x)
            .attr('y', y + 30)
            .attr('text-anchor', 'middle')
            .attr('fill', colors.gray)
            .attr('font-size', '14px')
            .attr('opacity', 0)
            .text(`Top 5: ${formatPercent(d.top5)}`)
            .transition()
            .delay(2000)
            .duration(600)
            .attr('opacity', 1);
    });

    // Comparison annotation
    g.append('text')
        .attr('x', centerX)
        .attr('y', chartHeight - 20)
        .attr('text-anchor', 'middle')
        .attr('fill', colors.yellow)
        .attr('font-size', '13px')
        .attr('font-weight', '600')
        .attr('opacity', 0)
        .text('Imports are 56% more concentrated than exports')
        .transition()
        .delay(2500)
        .duration(800)
        .attr('opacity', 1);
}

// Initialize all visualizations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    createPortConcentration();
    createDeficitSankey();
    createExportGrowth();
    createExportShifts();
    createConcentrationComparison();
});

// Handle window resize
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        // Clear and redraw all visualizations
        d3.select('#viz-port-concentration').selectAll('*').remove();
        d3.select('#viz-deficit-sankey').selectAll('*').remove();
        d3.select('#viz-export-growth').selectAll('*').remove();
        d3.select('#viz-export-shifts').selectAll('*').remove();
        d3.select('#viz-concentration-comparison').selectAll('*').remove();

        createPortConcentration();
        createDeficitSankey();
        createExportGrowth();
        createExportShifts();
        createConcentrationComparison();
    }, 250);
});
