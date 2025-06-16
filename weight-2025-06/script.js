// Load and process data
async function loadData() {
  const [weightData, travelData] = await Promise.all([
    fetch("./weight.json").then((r) => r.json()),
    fetch("./travel.json").then((r) => r.json()),
  ]);
  return { weightData, travelData };
}

// Process weight data for 2025 only
function processWeightData(weightData) {
  const start2025 = new Date("2025-01-01").getTime() * 1000000;

  return weightData["Data Points"]
    .filter((point) => point.endTimeNanos >= start2025)
    .map((point) => ({
      x: new Date(point.endTimeNanos / 1000000),
      y: point.fitValue[0].value.fpVal,
    }))
    .sort((a, b) => a.x - b.x);
}

// Process travel data
function processTravelData(travelData) {
  return travelData.travel.map((trip) => ({
    date: new Date(trip.date),
    airport: trip.airport,
  }));
}

// Calculate moving average
function calculateMovingAverage(data, windowSize = 7) {
  const result = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - Math.floor(windowSize / 2));
    const end = Math.min(data.length, i + Math.ceil(windowSize / 2));
    const window = data.slice(start, end);
    const avg = window.reduce((sum, point) => sum + point.y, 0) / window.length;
    result.push({ x: data[i].x, y: avg });
  }
  return result;
}

// Find data gaps
function findDataGaps(data, maxGapDays = 3) {
  const gaps = [];
  for (let i = 1; i < data.length; i++) {
    const daysDiff = (data[i].x - data[i - 1].x) / (1000 * 60 * 60 * 24);
    if (daysDiff > maxGapDays) {
      gaps.push({
        start: data[i - 1].x,
        end: data[i].x,
        days: Math.round(daysDiff),
      });
    }
  }
  return gaps;
}

// Find milestones and mark significant changes
function findMilestonesAndChanges(data) {
  const milestones = [];
  const startWeight = data[0].y;

  // Find major milestones (every 10kg from start)
  for (let target = Math.floor(startWeight / 10) * 10; target >= 60; target -= 10) {
    if (target !== Math.floor(startWeight / 10) * 10) {
      for (let i = 0; i < data.length; i++) {
        if (data[i].y <= target && (!data[i - 1] || data[i - 1].y > target)) {
          milestones.push({ index: i, weight: target, type: "milestone" });
          break;
        }
      }
    }
  }

  // Find minor milestones (every 5kg)
  for (let target = Math.floor(startWeight / 5) * 5; target >= 60; target -= 5) {
    if (target !== Math.floor(startWeight / 5) * 5 && !milestones.some((m) => m.weight === target)) {
      for (let i = 0; i < data.length; i++) {
        if (data[i].y <= target && (!data[i - 1] || data[i - 1].y > target)) {
          milestones.push({ index: i, weight: target, type: "milestone" });
          break;
        }
      }
    }
  }

  // Find significant changes
  const changes = [];
  for (let i = 1; i < data.length; i++) {
    changes.push({ index: i, change: data[i].y - data[i - 1].y });
  }
  changes.sort((a, b) => Math.abs(b.change) - Math.abs(a.change));

  const increases = changes.filter((c) => c.change > 0).slice(0, 3);
  const decreases = changes.filter((c) => c.change < 0).slice(0, 3);

  return { milestones, increases, decreases };
}

// Calculate statistics
function calculateStats(weightPoints) {
  if (!weightPoints.length) return {};

  const startWeight = weightPoints[0].y;
  const currentWeight = weightPoints[weightPoints.length - 1].y;
  const weightLost = startWeight - currentWeight;
  const startDate = weightPoints[0].x;
  const endDate = weightPoints[weightPoints.length - 1].x;
  const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
  const weeksDiff = daysDiff / 7;
  const avgLossPerWeek = weightLost / weeksDiff;

  return {
    startWeight,
    currentWeight,
    weightLost,
    daysDiff,
    avgLossPerWeek,
    goalAchieved: currentWeight <= 64,
  };
}

// Update stats in UI
function updateStats(stats) {
  document.getElementById("weight-lost").textContent = stats.weightLost.toFixed(1);
  document.getElementById("days-elapsed").textContent = stats.daysDiff;
  document.getElementById("goal-achieved").textContent = stats.goalAchieved ? "✅" : "🎯";
  document.getElementById("avg-loss").textContent = stats.avgLossPerWeek.toFixed(2);
}

// Get current location based on last airport <= current date
function getCurrentLocation(date, travelData) {
  const sortedTravel = travelData.sort((a, b) => a.date - b.date);
  let currentLocation = null;

  for (const trip of sortedTravel) {
    if (trip.date <= date) {
      currentLocation = trip.airport;
    } else {
      break;
    }
  }

  return currentLocation;
}

// Customize point styles
function customizePointStyles(data, milestones, increases, decreases) {
  const pointColors = [];
  const pointRadius = [];

  for (let i = 0; i < data.length; i++) {
    if (milestones.find((m) => m.index === i)) {
      pointColors.push("#000000");
      pointRadius.push(8);
    } else if (increases.find((c) => c.index === i)) {
      pointColors.push("#e74c3c");
      pointRadius.push(4);
    } else if (decreases.find((c) => c.index === i)) {
      pointColors.push("#27ae60");
      pointRadius.push(4);
    } else {
      pointColors.push("#667eea");
      pointRadius.push(4);
    }
  }

  return { pointColors, pointRadius };
}

// Create data gap annotations
function createGapAnnotations(gaps) {
  return gaps.map((gap) => ({
    type: "box",
    xMin: gap.start,
    xMax: gap.end,
    backgroundColor: "rgba(149, 165, 166, 0.1)",
    borderColor: "#95a5a6",
    borderWidth: 1,
    borderDash: [3, 3],
    label: {
      enabled: true,
      content: `${gap.days}d gap`,
      position: "center",
      backgroundColor: "#95a5a6",
      color: "white",
      cornerRadius: 4,
      padding: 4,
      font: {
        size: 8,
      },
    },
  }));
}

// Create chart
async function createChart() {
  const { weightData, travelData } = await loadData();
  const weightPoints = processWeightData(weightData);
  const travelPoints = processTravelData(travelData);
  const movingAverage = calculateMovingAverage(weightPoints);
  const dataGaps = findDataGaps(weightPoints);
  const { milestones, increases, decreases } = findMilestonesAndChanges(weightPoints);
  const { pointColors, pointRadius } = customizePointStyles(weightPoints, milestones, increases, decreases);
  const stats = calculateStats(weightPoints);

  // Store data globally for tooltip access
  window.chartData = { milestones, increases, decreases };

  updateStats(stats);

  const ctx = document.getElementById("weight-chart").getContext("2d");

  // Create gradients
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, "rgba(102, 126, 234, 0.4)");
  gradient.addColorStop(1, "rgba(102, 126, 234, 0.05)");

  const avgGradient = ctx.createLinearGradient(0, 0, 0, 400);
  avgGradient.addColorStop(0, "rgba(102, 126, 234, 0.2)");
  avgGradient.addColorStop(1, "rgba(102, 126, 234, 0.02)");

  new Chart(ctx, {
    type: "line",
    data: {
      datasets: [
        {
          label: "Weight (kg)",
          data: weightPoints,
          borderColor: "#667eea",
          backgroundColor: gradient,
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: pointColors,
          pointBorderColor: "#ffffff",
          pointBorderWidth: 2,
          pointRadius: pointRadius,
          pointHoverRadius: pointRadius.map((r) => r + 4),
          pointHoverBorderWidth: 3,
          order: 2,
        },
        {
          label: "7-Day Moving Average",
          data: movingAverage,
          borderColor: "rgba(102, 126, 234, 0.6)",
          backgroundColor: avgGradient,
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 0,
          order: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: "index",
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: "rgba(0, 0, 0, 0.8)",
          titleColor: "#ffffff",
          bodyColor: "#ffffff",
          cornerRadius: 8,
          padding: 12,
          displayColors: false,
          callbacks: {
            title: (context) => {
              const date = new Date(context[0].parsed.x);
              return date.toLocaleDateString("en-US", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              });
            },
            label: (context) => {
              if (context.datasetIndex === 1) return null; // Skip moving average tooltips

              const weight = context.parsed.y.toFixed(1);
              const startWeight = stats.startWeight;
              const lost = (startWeight - context.parsed.y).toFixed(1);
              const date = new Date(context.parsed.x);
              const pointIndex = context.dataIndex;
              const location = getCurrentLocation(date, travelPoints);

              const labels = [
                `Weight: ${weight} kg`,
                `Lost: ${lost} kg`,
                `Goal: ${(64 - context.parsed.y).toFixed(1)} kg to go`,
              ];

              if (location) {
                labels.push(`✈️ Location: ${location}`);
              }

              // Check for milestone
              const milestone = window.chartData?.milestones?.find((m) => m.index === pointIndex);
              if (milestone) {
                labels.push(`🎯 Milestone: ${milestone.weight}kg reached!`);
              }

              return labels;
            },
          },
        },
        annotation: {
          annotations: {
            goalLine: {
              type: "line",
              mode: "horizontal",
              scaleID: "y",
              value: 64,
              borderColor: "#e74c3c",
              borderWidth: 3,
              borderDash: [10, 5],
              label: {
                enabled: true,
                content: "🎯 Goal: 64kg",
                position: "end",
                backgroundColor: "#e74c3c",
                color: "white",
                cornerRadius: 6,
                padding: 8,
                font: {
                  weight: "bold",
                },
              },
            },
            halfwayLine: {
              type: "line",
              mode: "horizontal",
              scaleID: "y",
              value: (stats.startWeight + 64) / 2,
              borderColor: "rgba(241, 196, 15, 0.6)",
              borderWidth: 2,
              borderDash: [5, 5],
              label: {
                enabled: true,
                content: "⭐ Halfway",
                position: "start",
                backgroundColor: "rgba(241, 196, 15, 0.8)",
                color: "white",
                cornerRadius: 4,
                padding: 6,
                font: {
                  size: 11,
                },
              },
            },
            ...createGapAnnotations(dataGaps),
          },
        },
      },
      scales: {
        x: {
          type: "time",
          time: {
            unit: "week",
            displayFormats: {
              week: "MMM dd",
            },
          },
          title: {
            display: true,
            text: "2025 Timeline",
            font: {
              size: 14,
              weight: "bold",
            },
            color: "#333",
          },
          grid: {
            color: "rgba(0, 0, 0, 0.05)",
            drawOnChartArea: true,
          },
          ticks: {
            color: "#666",
            font: {
              size: 11,
            },
          },
        },
        y: {
          beginAtZero: false,
          min: 62,
          max: Math.max(88, Math.max(...weightPoints.map((p) => p.y)) + 2),
          title: {
            display: true,
            text: "Weight (kg)",
            font: {
              size: 14,
              weight: "bold",
            },
            color: "#333",
          },
          grid: {
            color: "rgba(0, 0, 0, 0.05)",
            drawOnChartArea: true,
          },
          ticks: {
            color: "#666",
            font: {
              size: 11,
            },
            callback: function (value) {
              return value.toFixed(0) + " kg";
            },
          },
        },
      },
      elements: {
        point: {
          hoverBackgroundColor: "#667eea",
          hoverBorderColor: "#ffffff",
        },
      },
      animation: {
        duration: 2000,
        easing: "easeInOutQuart",
      },
    },
    plugins: [
      {
        id: "customCanvasBackgroundColor",
        beforeDraw: (chart) => {
          const ctx = chart.canvas.getContext("2d");
          ctx.save();
          ctx.globalCompositeOperation = "destination-over";
          ctx.fillStyle = "#ffffff";
          ctx.fillRect(0, 0, chart.width, chart.height);
          ctx.restore();
        },
      },
    ],
  });
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  // Register plugins first
  if (window.Chart && window.annotationPlugin) {
    Chart.register(window.annotationPlugin);
  }
  // Then create chart
  createChart();
});

// Add some interactive flourishes
document.addEventListener("DOMContentLoaded", () => {
  // Animate stat cards on load
  const statCards = document.querySelectorAll(".stat-card");
  statCards.forEach((card, index) => {
    setTimeout(() => {
      card.style.opacity = "0";
      card.style.transform = "translateY(20px)";
      card.style.transition = "all 0.6s ease";

      setTimeout(() => {
        card.style.opacity = "1";
        card.style.transform = "translateY(0)";
      }, 100);
    }, index * 200);
  });

  // Add success celebration if goal achieved
  setTimeout(() => {
    const goalElement = document.getElementById("goal-achieved");
    if (goalElement.textContent === "✅") {
      goalElement.style.animation = "pulse 2s infinite";

      // Add CSS for pulse animation
      const style = document.createElement("style");
      style.textContent = `
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                    100% { transform: scale(1); }
                }
            `;
      document.head.appendChild(style);
    }
  }, 2000);
});
