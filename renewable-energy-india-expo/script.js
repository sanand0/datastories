// @ts-check

// Wait for Chart.js to be available
if (typeof Chart === 'undefined') {
  console.error('❌ Chart.js not loaded! Check script tag order.');
  document.body.innerHTML += '<div style="position:fixed;top:0;left:0;right:0;background:red;color:white;padding:20px;z-index:9999;">Error: Chart.js failed to load. Check console.</div>';
}

const colors = {
  solarYellow: '#FDB813',
  windBlue: '#1E88E5',
  batteryPurple: '#7B1FA2',
  indiaOrange: '#FF9933',
  indiaGreen: '#138808',
  china: '#DE2910',
  germany: '#000000',
  gray: '#666',
};

// Load data
async function loadData() {
  const [insights, sectors, countries, technologies] = await Promise.all([
    fetch('insights.json').then(r => r.json()),
    fetch('sectors.csv').then(r => r.text()).then(parseCSV),
    fetch('countries.csv').then(r => r.text()).then(parseCSV),
    fetch('technologies.csv').then(r => r.text()).then(parseCSV),
  ]);
  return { insights, sectors, countries, technologies };
}

function parseCSV(text) {
  const lines = text.trim().split('\n');
  const headers = lines[0].split(',');
  return lines.slice(1).map(line => {
    const values = line.split(',');
    const obj = {};
    headers.forEach((header, i) => {
      obj[header] = isNaN(values[i]) ? values[i] : Number(values[i]);
    });
    return obj;
  });
}

// Chart configurations
const chartDefaults = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: true,
      position: 'bottom',
      labels: {
        font: { size: 14, family: "'Source Serif 4', Georgia, serif" },
        padding: 20,
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0,0,0,0.8)',
      padding: 12,
      titleFont: { size: 14, family: "'Source Serif 4', Georgia, serif" },
      bodyFont: { size: 13, family: "'Source Serif 4', Georgia, serif" },
    }
  }
};

function createIndiaVsInternational(data) {
  const ctx = document.getElementById('india-vs-international');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['India', 'International'],
      datasets: [{
        data: [
          data.insights.geographic_distribution.india_vs_international.India,
          data.insights.geographic_distribution.india_vs_international.International
        ],
        backgroundColor: [colors.indiaOrange, colors.gray],
        borderWidth: 0,
      }]
    },
    options: {
      ...chartDefaults,
      cutout: '65%',
      plugins: {
        ...chartDefaults.plugins,
        tooltip: {
          ...chartDefaults.plugins.tooltip,
          callbacks: {
            label: (context) => {
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((context.parsed / total) * 100).toFixed(1);
              return `${context.label}: ${context.parsed} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

function createSectorDistribution(data) {
  const ctx = document.getElementById('sector-distribution');
  const topSectors = Object.entries(data.insights.sector_analysis.main_sectors)
    .slice(0, 6);
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: topSectors.map(([name]) => name),
      datasets: [{
        label: 'Mentions',
        data: topSectors.map(([, count]) => count),
        backgroundColor: [
          colors.solarYellow,
          colors.indiaGreen,
          colors.gray,
          colors.windBlue,
          colors.batteryPurple,
          colors.indiaOrange,
        ],
        borderRadius: 6,
      }]
    },
    options: {
      ...chartDefaults,
      indexAxis: 'y',
      plugins: {
        ...chartDefaults.plugins,
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 12 } }
        },
        y: {
          grid: { display: false },
          ticks: { 
            font: { size: 13, family: "'Source Serif 4', Georgia, serif" },
            crossAlign: 'far',
          }
        }
      }
    }
  });
}

function createSubcategories(data) {
  const ctx = document.getElementById('subcategories');
  const topSubs = Object.entries(data.insights.sector_analysis.top_subcategories)
    .slice(0, 8);
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: topSubs.map(([name]) => 
        name.length > 40 ? name.substring(0, 37) + '...' : name
      ),
      datasets: [{
        label: 'Companies',
        data: topSubs.map(([, count]) => count),
        backgroundColor: colors.indiaOrange,
        borderRadius: 6,
      }]
    },
    options: {
      ...chartDefaults,
      indexAxis: 'y',
      plugins: {
        ...chartDefaults.plugins,
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 12 } }
        },
        y: {
          grid: { display: false },
          ticks: { 
            font: { size: 12, family: "'Source Serif 4', Georgia, serif" },
            crossAlign: 'far',
          }
        }
      }
    }
  });
}

function createInternationalCountries(data) {
  const ctx = document.getElementById('international-countries');
  const international = Object.entries(data.insights.geographic_distribution.top_international)
    .slice(0, 8);
  
  const countryColors = {
    'China': colors.china,
    'Germany': colors.germany,
    'Taiwan': '#0E4C92',
    '中国': colors.china,
    'Japan': '#BC002D',
    'United Arab Emirates': '#00732F',
  };
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: international.map(([name]) => name),
      datasets: [{
        label: 'Exhibitors',
        data: international.map(([, count]) => count),
        backgroundColor: international.map(([name]) => countryColors[name] || colors.gray),
        borderRadius: 6,
      }]
    },
    options: {
      ...chartDefaults,
      plugins: {
        ...chartDefaults.plugins,
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { 
            font: { size: 13, family: "'Source Serif 4', Georgia, serif" } 
          }
        },
        y: {
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { font: { size: 12 } }
        }
      }
    }
  });
}

function createTechnologyTrends(data) {
  const ctx = document.getElementById('technology-trends');
  const techs = Object.entries(data.insights.technology_trends.technology_distribution);
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: techs.map(([name]) => name),
      datasets: [{
        label: 'Mentions',
        data: techs.map(([, count]) => count),
        backgroundColor: techs.map(([name]) => {
          if (name.includes('Solar')) return colors.solarYellow;
          if (name.includes('Wind')) return colors.windBlue;
          if (name.includes('Battery') || name.includes('Storage')) return colors.batteryPurple;
          if (name.includes('Hydrogen')) return colors.indiaGreen;
          return colors.indiaOrange;
        }),
        borderRadius: 6,
      }]
    },
    options: {
      ...chartDefaults,
      indexAxis: 'y',
      plugins: {
        ...chartDefaults.plugins,
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 12 } }
        },
        y: {
          grid: { display: false },
          ticks: { 
            font: { size: 13, family: "'Source Serif 4', Georgia, serif" },
            crossAlign: 'far',
          }
        }
      }
    }
  });
}

function createCompanyScale(data) {
  const ctx = document.getElementById('company-scale');
  const scale = Object.entries(data.insights.company_profiles);
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: scale.map(([name]) => name),
      datasets: [{
        label: 'Companies',
        data: scale.map(([, count]) => count),
        backgroundColor: [
          colors.indiaOrange,
          colors.indiaGreen,
          colors.solarYellow,
          colors.windBlue,
          colors.batteryPurple,
        ],
        borderRadius: 6,
      }]
    },
    options: {
      ...chartDefaults,
      plugins: {
        ...chartDefaults.plugins,
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { 
            font: { size: 13, family: "'Source Serif 4', Georgia, serif" } 
          }
        },
        y: {
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { font: { size: 12 } }
        }
      }
    }
  });
}

// Initialize all charts
async function init() {
  console.log('🔧 Initializing charts...');
  console.log('📊 Chart.js available?', typeof Chart !== 'undefined');
  
  try {
    console.log('📥 Loading data...');
    const data = await loadData();
    console.log('✅ Data loaded:', Object.keys(data));
    
    createIndiaVsInternational(data);
    createSectorDistribution(data);
    createSubcategories(data);
    createInternationalCountries(data);
    createTechnologyTrends(data);
    createCompanyScale(data);
    
    console.log('✅ All charts loaded successfully');
  } catch (error) {
    console.error('❌ Error loading data:', error);
  }
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
