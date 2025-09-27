import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Chart dimensions and setup - square aspect ratio
const margin = { top: 80, right: 80, bottom: 80, left: 80 };
const width = 600 - margin.left - margin.right;
const height = 1600 - margin.bottom - margin.top;

// Box office buckets for color scale - using diverging palette for better differentiation
const boxOfficeBuckets = [
  { min: 0, max: 10, color: "#2166ac", label: "0-10 cr" },
  { min: 10, max: 20, color: "#4393c3", label: "10-20 cr" },
  { min: 20, max: 50, color: "#92c5de", label: "20-50 cr" },
  { min: 50, max: 100, color: "#d1e5f0", label: "50-100 cr" },
  { min: 100, max: 200, color: "#fdbf6f", label: "100-200 cr" },
  { min: 200, max: 500, color: "#ff7f00", label: "200-500 cr" },
  { min: 500, max: 1000, color: "#e31a1c", label: "500-1000 cr" },
  { min: 1000, max: 2000, color: "#b10026", label: "1000-2000 cr" },
  { min: 2000, max: 5000, color: "#800026", label: "2000-5000 cr" },
  { min: 5000, max: Infinity, color: "#4d0013", label: "5000+ cr" },
];

// Global variables for data and inflation
let rawData = [];
let inflationData = new Map();
let isInflationAdjusted = false;

// Load and process data
async function loadData() {
  try {
    const [moviesData, inflationCsv] = await Promise.all([d3.csv("highest_grossing.csv"), d3.csv("inflation.csv")]);

    // Process inflation data
    inflationCsv.forEach((d) => {
      inflationData.set(+d.year, +d.inflation);
    });

    // Filter for top 10 ranks only and convert numeric values
    rawData = moviesData
      .filter((d) => +d.rank <= 10)
      .map((d) => ({
        year: +d.year,
        rank: +d.rank,
        title: d.title,
        link: d.link,
        worldwide_gross: +d.worldwide_gross,
        worldwide_gross_original: +d.worldwide_gross,
      }))
      .filter((d) => !isNaN(d.year) && !isNaN(d.rank) && !isNaN(d.worldwide_gross));

    return rawData;
  } catch (error) {
    console.error("Error loading data:", error);
    return [];
  }
}

// Calculate cumulative inflation factor to adjust to 2024 terms
function calculateInflationFactor(year) {
  if (year === 2024) return 1;

  let factor = 1;
  for (let y = year + 1; y <= 2024; y++) {
    const inflationRate = inflationData.get(y) || 0;
    factor *= 1 + inflationRate / 100;
  }
  return factor;
}

// Get color for box office value
function getBoxOfficeColor(value) {
  for (const bucket of boxOfficeBuckets) {
    if (value >= bucket.min && value < bucket.max) {
      return bucket.color;
    }
  }
  return boxOfficeBuckets[boxOfficeBuckets.length - 1].color;
}

// Apply inflation adjustment
function adjustForInflation(data, adjust) {
  return data.map((d) => ({
    ...d,
    worldwide_gross: adjust
      ? d.worldwide_gross_original * calculateInflationFactor(d.year)
      : d.worldwide_gross_original,
  }));
}

// Create scales
function createScales(data) {
  const years = [...new Set(data.map((d) => d.year))].sort();
  const ranks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  const xScale = d3.scaleBand().domain(ranks).range([0, width]).padding(0.1);

  const yScale = d3.scaleBand().domain(years).range([0, height]).padding(0.05);

  const radiusScale = d3
    .scaleSqrt()
    .domain([0, d3.max(data, (d) => d.worldwide_gross)])
    .range([2, Math.min(xScale.bandwidth(), yScale.bandwidth()) / 1.5]);

  return { xScale, yScale, radiusScale, years, ranks };
}

// Create tooltip
function createTooltip() {
  return d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);
}

// Format currency
function formatCurrency(value) {
  if (value >= 1000) {
    return `₹${(value / 1000).toFixed(1)}k cr`;
  }
  return `₹${value.toFixed(1)} cr`;
}

// Create the main chart
async function createChart() {
  const data = await loadData();
  if (data.length === 0) {
    console.error("No data loaded");
    return;
  }

  drawChart(data);
}

// Draw chart function (can be called for updates)
function drawChart(data) {
  const { xScale, yScale, radiusScale, years, ranks } = createScales(data);
  const tooltip = createTooltip();

  // Clear existing chart
  d3.select("#chart").selectAll("*").remove();

  // Create SVG
  const svg = d3
    .select("#chart")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .style("display", "block")
    .style("margin", "auto");

  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  // Add title
  svg
    .append("text")
    .attr("x", (width + margin.left + margin.right) / 2)
    .attr("y", 30)
    .attr("text-anchor", "middle")
    .attr("class", "chart-main-title")
    .style("font-size", "16px")
    .style("font-weight", "bold")
    .style("fill", "#2c3e50");

  // Add axes labels
  g.append("text")
    .attr("x", width / 2)
    .attr("y", height + 50)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Box Office Rank (1 = Highest Grossing)");

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -height / 2)
    .attr("y", -50)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Year");

  // Add rank labels (x-axis)
  g.selectAll(".rank-label")
    .data(ranks)
    .enter()
    .append("text")
    .attr("class", "rank-label")
    .attr("x", (d) => xScale(d) + xScale.bandwidth() / 2)
    .attr("y", height + 25)
    .text((d) => d);

  // Add year labels (y-axis)
  g.selectAll(".year-label")
    .data(years)
    .enter()
    .append("text")
    .attr("class", "year-label")
    .attr("x", -15)
    .attr("y", (d) => yScale(d) + yScale.bandwidth() / 2 + 4)
    .text((d) => d);

  // Add grid lines for better readability
  g.selectAll(".grid-line-x")
    .data(ranks.slice(1))
    .enter()
    .append("line")
    .attr("class", "grid-line-x")
    .attr("x1", (d) => xScale(d))
    .attr("x2", (d) => xScale(d))
    .attr("y1", 0)
    .attr("y2", height)
    .style("stroke", "#e0e0e0")
    .style("stroke-width", 0.5);

  g.selectAll(".grid-line-y")
    .data(years.slice(1))
    .enter()
    .append("line")
    .attr("class", "grid-line-y")
    .attr("x1", 0)
    .attr("x2", width)
    .attr("y1", (d) => yScale(d))
    .attr("y2", (d) => yScale(d))
    .style("stroke", "#e0e0e0")
    .style("stroke-width", 0.5);

  // Create circles for each movie
  g.selectAll(".circle")
    .data(data)
    .enter()
    .append("circle")
    .attr("class", "circle")
    .attr("cx", (d) => xScale(d.rank) + xScale.bandwidth() / 2)
    .attr("cy", (d) => yScale(d.year) + yScale.bandwidth() / 2)
    .attr("r", (d) => radiusScale(d.worldwide_gross))
    .attr("fill", (d) => getBoxOfficeColor(d.worldwide_gross))
    .attr("opacity", 0.8)
    .on("mouseover", function (event, d) {
      // Highlight the circle
      d3.select(this).attr("opacity", 1).attr("stroke", "#333").attr("stroke-width", 2);

      // Show tooltip
      tooltip.transition().duration(200).style("opacity", 1);

      const tooltipContent = isInflationAdjusted
        ? `<strong>${d.title}</strong><br/>
                   Year: ${d.year}<br/>
                   Rank: #${d.rank}<br/>
                   Box Office: ${formatCurrency(d.worldwide_gross)} (2024 terms)<br/>
                   Original: ${formatCurrency(d.worldwide_gross_original)} (${d.year} terms)<br/>
                   <em>Click to view on Wikipedia</em>`
        : `<strong>${d.title}</strong><br/>
                   Year: ${d.year}<br/>
                   Rank: #${d.rank}<br/>
                   Box Office: ${formatCurrency(d.worldwide_gross)}<br/>
                   <em>Click to view on Wikipedia</em>`;

      tooltip
        .html(tooltipContent)
        .style("left", event.pageX + 15 + "px")
        .style("top", event.pageY - 10 + "px");
    })
    .on("mousemove", function (event) {
      tooltip.style("left", event.pageX + 15 + "px").style("top", event.pageY - 10 + "px");
    })
    .on("mouseout", function () {
      // Remove highlight
      d3.select(this).attr("opacity", 0.8).attr("stroke", "none");

      // Hide tooltip
      tooltip.transition().duration(500).style("opacity", 0);
    })
    .on("click", function (event, d) {
      window.open(d.link, "_blank");
    });

  // Add staggered animation on load
  g.selectAll(".circle")
    .attr("r", 0)
    .attr("opacity", 0)
    .transition()
    .duration(400)
    .delay((d, i) => i * 5)
    .attr("r", (d) => radiusScale(d.worldwide_gross))
    .attr("opacity", 0.8)
    .ease(d3.easeElastic.period(0.3));

  console.log(`Loaded ${data.length} movies across ${years.length} years`);
}

// Toggle inflation adjustment
function toggleInflation() {
  const adjustedData = adjustForInflation(rawData, isInflationAdjusted);
  drawChart(adjustedData);

  // Update explanation text
  const explanationText = document.getElementById("inflation-explanation");
  explanationText.textContent = isInflationAdjusted
    ? "Currently showing inflation-adjusted values (2024 terms)"
    : "Currently showing nominal values (original year prices)";
}

// Initialize the chart and event listeners when the page loads
document.addEventListener("DOMContentLoaded", () => {
  createChart();

  // Add event listener for inflation toggle
  setTimeout(() => {
    const toggleCheckbox = document.getElementById("inflation-toggle");
    if (toggleCheckbox) {
      console.log("Toggle checkbox found, adding event listener");
      toggleCheckbox.addEventListener("change", (e) => {
        console.log("Toggle changed, checked:", e.target.checked);
        isInflationAdjusted = e.target.checked;
        toggleInflation();
      });
    } else {
      console.error("Toggle checkbox not found");
    }
  }, 100);
});

// Handle toggle click manually
function handleToggleClick() {
  const toggleCheckbox = document.getElementById("inflation-toggle");
  if (toggleCheckbox) {
    toggleCheckbox.checked = !toggleCheckbox.checked;
    isInflationAdjusted = toggleCheckbox.checked;
    console.log("Manual toggle clicked, checked:", isInflationAdjusted);
    toggleInflation();
  }
}

// Expose functions globally
window.toggleInflation = toggleInflation;
window.handleToggleClick = handleToggleClick;
