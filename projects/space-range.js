const SR_GROUPS = ['Premium', 'Core', 'Value', 'Family packs', 'Travel sizes'];

const SR_CLUSTERS = {
  urban: {
    label: 'Urban premium',
    sales: 528000, gp: 181000, shelfMetres: 113.5, cover: 7.1, review: 14, slow: 52000,
    shares: { sales: [28, 32, 14, 16, 10], profit: [36, 32, 10, 14, 8], space: [22, 32, 20, 18, 8] },
    productivity: { sales: [5920, 4650, 3260, 4140, 5810], gp: [2920, 1590, 810, 1250, 1980] },
    relevance: ['High', 'Essential', 'Supporting', 'Selective', 'Low'],
    coverByGroup: [5.2, 4.1, 9.5, 6.4, 13.8]
  },
  family: {
    label: 'Family residential',
    sales: 612000, gp: 202000, shelfMetres: 138.5, cover: 6.8, review: 11, slow: 49000,
    shares: { sales: [18, 31, 15, 28, 8], profit: [24, 32, 12, 25, 7], space: [20, 32, 17, 24, 7] },
    productivity: { sales: [3970, 4200, 3890, 5150, 5040], gp: [1750, 1435, 980, 1510, 1415] },
    relevance: ['Medium', 'Essential', 'Supporting', 'High', 'Low'],
    coverByGroup: [7.0, 4.2, 7.8, 4.5, 13.0]
  },
  value: {
    label: 'Value-focused neighbourhood',
    sales: 474000, gp: 142000, shelfMetres: 113.4, cover: 7.5, review: 17, slow: 55000,
    shares: { sales: [10, 30, 38, 17, 5], profit: [18, 32, 30, 15, 5], space: [16, 32, 34, 14, 4] },
    productivity: { sales: [2610, 3920, 4665, 5075, 5210], gp: [1410, 1250, 1095, 1340, 1625] },
    relevance: ['Low', 'Essential', 'High', 'Medium', 'Low'],
    coverByGroup: [10.5, 4.5, 3.8, 6.2, 15.0]
  }
};

const SR_STRATEGIES = {
  balanced: { label: 'Balanced', sales: 1.000, gp: 1.000, cover: 1.000, review: 0, slow: 1.000, spaceShift: 0 },
  growth: { label: 'Growth focused', sales: 1.026, gp: 1.018, cover: 1.045, review: -1, slow: 1.025, spaceShift: 3 },
  margin: { label: 'Margin focused', sales: 0.998, gp: 1.032, cover: 0.985, review: 2, slow: 0.965, spaceShift: 2 },
  recovery: { label: 'Inventory recovery', sales: 0.991, gp: 1.008, cover: 0.905, review: 4, slow: 0.875, spaceShift: -1 }
};

let srCurrentRows = [];
let srSort = { column: 0, direction: 1 };

function srMoney(value, compact = false) {
  if (compact) return `RM${Math.round(value / 1000)}K`;
  return `RM${Math.round(value).toLocaleString()}`;
}

function srPercent(value) {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

function srBadge(action) {
  const key = action === 'Expand' ? 'good' : action === 'Retain' ? 'neutral' : action === 'Reduce' ? 'warn' : 'bad';
  return `<span class="badge ${key}">${action}</span>`;
}

function srAction(index, cluster, strategy) {
  const sales = cluster.shares.sales[index];
  const profit = cluster.shares.profit[index];
  const space = cluster.shares.space[index];
  const cover = cluster.coverByGroup[index];
  if (strategy === 'recovery' && cover >= 9) return 'Review';
  if (strategy === 'margin' && profit - space >= 4) return 'Expand';
  if (strategy === 'growth' && sales - space >= 3) return 'Expand';
  if (cover >= 12 || (sales < space && profit < space)) return 'Review';
  if (sales - space >= 4 || profit - space >= 5) return 'Expand';
  if (space - sales >= 4) return 'Reduce';
  return 'Retain';
}

function srBuildRows(clusterKey, strategyKey) {
  const cluster = SR_CLUSTERS[clusterKey];
  const reasons = {
    Expand: 'Contribution and productivity indicate under-allocation.',
    Retain: 'Balanced contribution and an important category role.',
    Reduce: 'Space exceeds demand or profit productivity.',
    Review: 'Slow movement, duplication or weak cluster relevance.'
  };
  const risks = {
    Expand: 'Availability and replenishment capacity',
    Retain: 'Monitor substitution and service level',
    Reduce: 'Customer choice and supplier commitments',
    Review: 'Delist cost and customer substitution'
  };
  return SR_GROUPS.map((group, index) => {
    const action = srAction(index, cluster, strategyKey);
    return {
      group,
      salesShare: cluster.shares.sales[index],
      profitShare: cluster.shares.profit[index],
      spaceShare: cluster.shares.space[index],
      salesMetre: cluster.productivity.sales[index],
      gpMetre: cluster.productivity.gp[index],
      cover: cluster.coverByGroup[index],
      relevance: cluster.relevance[index],
      action,
      reason: reasons[action],
      risk: risks[action]
    };
  });
}

function srRenderTable() {
  const filter = document.getElementById('actionFilter').value;
  const visible = srCurrentRows
    .filter(row => filter === 'all' || row.action === filter)
    .sort((a, b) => {
      const keys = ['group', 'salesShare', 'profitShare', 'spaceShare', 'salesMetre', 'gpMetre', 'cover'];
      const key = keys[srSort.column] || 'group';
      return (typeof a[key] === 'string' ? a[key].localeCompare(b[key]) : a[key] - b[key]) * srSort.direction;
    });
  document.getElementById('actionRows').innerHTML = visible.map(row => `<tr>
    <td>${row.group}</td><td>${row.salesShare}%</td><td>${row.profitShare}%</td><td>${row.spaceShare}%</td>
    <td>${srMoney(row.salesMetre)}</td><td>${srMoney(row.gpMetre)}</td><td>${row.cover.toFixed(1)} weeks</td>
    <td>${row.relevance}</td><td class="status-cell">${srBadge(row.action)}</td><td>${row.reason}</td><td>${row.risk}</td>
  </tr>`).join('');
  document.getElementById('tableStatus').textContent = `${visible.length} of ${srCurrentRows.length} product groups shown`;
}

function srSetMetric(id, value) {
  const element = document.getElementById(id);
  if (!element) return;
  if (typeof animateTextValue === 'function') animateTextValue(element, value);
  else element.textContent = value;
}

function srRenderInsights(clusterKey, strategyKey) {
  const rows = srCurrentRows;
  const priority = [...rows].sort((a, b) => {
    const rank = { Expand: 0, Review: 1, Reduce: 2, Retain: 3 };
    return rank[a.action] - rank[b.action];
  }).slice(0, 4);
  document.getElementById('insightCards').innerHTML = priority.map(row => `<article class="insight-card">
    <div class="insight-top"><span>${SR_CLUSTERS[clusterKey].label}</span>${srBadge(row.action)}</div>
    <h3>${row.group} range: ${row.action.toLowerCase()}</h3>
    <dl><div><dt>Sales</dt><dd>${row.salesShare}%</dd></div><div><dt>Profit</dt><dd>${row.profitShare}%</dd></div><div><dt>Space</dt><dd>${row.spaceShare}%</dd></div><div><dt>Cover</dt><dd>${row.cover.toFixed(1)}w</dd></div></dl>
    <p>${row.reason} The ${SR_STRATEGIES[strategyKey].label.toLowerCase()} strategy applies cluster relevance and implementation risk before action.</p>
  </article>`).join('');
}

function srRenderCharts(clusterKey, strategyKey) {
  const cluster = SR_CLUSTERS[clusterKey];
  const strategy = SR_STRATEGIES[strategyKey];
  svgGroupedBarChart(document.getElementById('clusterChart'), ['Premium', 'Core', 'Value', 'Family packs'], [
    { name: 'Urban', values: [38, 32, 14, 16] },
    { name: 'Family', values: [20, 34, 18, 28] },
    { name: 'Value', values: [12, 32, 38, 18] }
  ], '%');
  svgGroupedBarChart(document.getElementById('spaceChart'), SR_GROUPS, [
    { name: 'Sales share', values: cluster.shares.sales },
    { name: 'Profit share', values: cluster.shares.profit },
    { name: 'Space share', values: cluster.shares.space }
  ], '%');
  svgBarChart(document.getElementById('salesProductivityChart'), SR_GROUPS, cluster.productivity.sales);
  svgBarChart(document.getElementById('gpProductivityChart'), SR_GROUPS, cluster.productivity.gp);
  const proposed = cluster.shares.space.map((value, index) => {
    const row = srCurrentRows[index];
    const shift = row.action === 'Expand' ? strategy.spaceShift + 2 : row.action === 'Reduce' ? -2 : row.action === 'Review' ? -3 : 0;
    return Math.max(2, value + shift);
  });
  const total = proposed.reduce((sum, value) => sum + value, 0);
  const normalised = proposed.map(value => Math.round(value / total * 100));
  normalised[1] += 100 - normalised.reduce((sum, value) => sum + value, 0);
  svgGroupedBarChart(document.getElementById('allocationChart'), SR_GROUPS, [
    { name: 'Current', values: cluster.shares.space },
    { name: 'Proposed', values: normalised }
  ], '%');
}

function srScenarioChanges(strategyKey, space, sku) {
  const profiles = {
    balanced: { sales: [0.5, .18, .05], gp: [0.8, .20, .07], slow: [-4, -.45, -.75], productivity: [0.6, .20, .06], gpProductivity: [0.8, .22, .07], cover: [-.05, -.012, -.025] },
    growth: { sales: [1.2, .25, .05], gp: [1.0, .20, .05], slow: [-1.5, -.25, -.45], productivity: [1.1, .24, .05], gpProductivity: [1.0, .20, .05], cover: [.12, .008, -.015] },
    margin: { sales: [.2, .12, .03], gp: [1.8, .28, .07], slow: [-3, -.30, -.65], productivity: [.4, .16, .04], gpProductivity: [1.7, .27, .07], cover: [-.08, -.008, -.022] },
    recovery: { sales: [-.4, .08, .02], gp: [.5, .12, .04], slow: [-8, -.35, -1.0], productivity: [.1, .12, .03], gpProductivity: [.5, .14, .04], cover: [-.3, -.012, -.04] }
  };
  const calculate = values => values[0] + space * values[1] + sku * values[2];
  const profile = profiles[strategyKey];
  return {
    sales: Math.min(7.5, calculate(profile.sales)),
    gp: Math.min(9.5, calculate(profile.gp)),
    slow: Math.max(-32, calculate(profile.slow)),
    productivity: Math.min(10, calculate(profile.productivity)),
    gpProductivity: Math.min(12, calculate(profile.gpProductivity)),
    cover: Math.max(-1.8, calculate(profile.cover))
  };
}

function srRenderSimulator() {
  const clusterKey = document.getElementById('storeType').value;
  const strategyKey = document.getElementById('simStrategy').value;
  const cluster = SR_CLUSTERS[clusterKey];
  const space = Number(document.getElementById('spaceRange').value);
  const sku = Number(document.getElementById('skuRange').value);
  const changes = srScenarioChanges(strategyKey, space, sku);
  document.getElementById('spaceOutput').textContent = `${space}%`;
  document.getElementById('skuOutput').textContent = `${sku} SKUs`;
  const currentSalesMetre = cluster.sales / cluster.shelfMetres;
  const currentGpMetre = cluster.gp / cluster.shelfMetres;
  const measures = [
    ['Category sales', cluster.sales, changes.sales, 'money'],
    ['Gross profit', cluster.gp, changes.gp, 'money'],
    ['Slow-moving stock', cluster.slow, changes.slow, 'money'],
    ['Sales / shelf metre', currentSalesMetre, changes.productivity, 'money'],
    ['GP / shelf metre', currentGpMetre, changes.gpProductivity, 'money'],
    ['Stock cover', cluster.cover, changes.cover, 'weeks']
  ];
  document.getElementById('simulatorRows').innerHTML = measures.map(([label, current, change, format]) => {
    const proposed = current * (1 + change / 100);
    const display = value => format === 'weeks' ? `${value.toFixed(1)} weeks` : srMoney(value);
    return `<tr><td>${label}</td><td>${display(current)}</td><td>${display(proposed)}</td><td class="${change >= 0 || label.includes('Slow') || label.includes('cover') ? 'positive' : 'negative'}">${srPercent(change)}</td></tr>`;
  }).join('');
  document.getElementById('impactCards').innerHTML = [
    ['Estimated sales change', changes.sales],
    ['Estimated gross-profit change', changes.gp],
    ['Estimated shelf-productivity change', changes.productivity],
    ['Estimated slow-moving-stock change', changes.slow]
  ].map(([label, value]) => `<article><span>${label}</span><strong>${srPercent(value)}</strong></article>`).join('');
  const interpretations = {
    balanced: 'The balanced strategy improves productivity while protecting core range breadth and limiting execution risk.',
    growth: 'The growth-focused strategy increases projected sales but requires stronger availability and replenishment execution.',
    margin: 'The margin-focused strategy generates stronger gross-profit productivity but may reduce range breadth.',
    recovery: 'The inventory-recovery strategy produces the largest slow-stock reduction, with a modest near-term sales trade-off.'
  };
  document.getElementById('impactInterpretation').textContent = interpretations[strategyKey];
  svgGroupedBarChart(document.getElementById('outcomesChart'), ['Sales', 'Gross profit', 'Shelf productivity', 'Slow stock'], [
    { name: 'Estimated change', values: [Math.abs(changes.sales), Math.abs(changes.gp), Math.abs(changes.productivity), Math.abs(changes.slow)] }
  ], '%');
}

function srRenderCase() {
  const clusterKey = document.getElementById('storeType').value;
  const strategyKey = document.getElementById('strategyType').value;
  const cluster = SR_CLUSTERS[clusterKey];
  const strategy = SR_STRATEGIES[strategyKey];
  const sales = cluster.sales * strategy.sales;
  const gp = cluster.gp * strategy.gp;
  const salesMetre = sales / cluster.shelfMetres;
  const gpMetre = gp / cluster.shelfMetres;
  srSetMetric('salesKpi', srMoney(sales, true));
  srSetMetric('gpKpi', srMoney(gp, true));
  srSetMetric('marginKpi', `${(gp / sales * 100).toFixed(1)}%`);
  srSetMetric('spaceKpi', srMoney(salesMetre));
  srSetMetric('gpSpaceKpi', srMoney(gpMetre));
  srSetMetric('coverKpi', `${(cluster.cover * strategy.cover).toFixed(1)} weeks`);
  srSetMetric('reviewKpi', String(Math.max(0, cluster.review + strategy.review)));
  srSetMetric('slowKpi', srMoney(cluster.slow * strategy.slow, true));
  document.getElementById('salesNote').textContent = `${cluster.label} estimate`;
  document.getElementById('gpNote').textContent = `${(gp / sales * 100).toFixed(1)}% gross margin`;
  document.getElementById('spaceNote').textContent = `${strategy.label} allocation`;
  document.getElementById('filterStatus').textContent = `${cluster.label} · ${strategy.label} strategy`;
  srCurrentRows = srBuildRows(clusterKey, strategyKey);
  srRenderTable();
  srRenderInsights(clusterKey, strategyKey);
  srRenderCharts(clusterKey, strategyKey);
  document.getElementById('simStrategy').value = strategyKey;
  const recommendation = srCurrentRows.find(row => row.action === 'Expand') || srCurrentRows[0];
  document.getElementById('clusterRecommendation').innerHTML = `<strong>${cluster.label} recommendation</strong>Prioritise ${recommendation.group.toLowerCase()} while protecting core availability and validating supplier, substitution and operational constraints.`;
  document.getElementById('finalRecommendationTitle').textContent = `${strategy.label}: rebalance selectively and validate through controlled pilots.`;
  document.getElementById('finalRecommendationCopy').textContent = `For ${cluster.label.toLowerCase()} stores, prioritise ${recommendation.group.toLowerCase()} and review low-productivity duplication before wider rollout.`;
  const baseSales = cluster.sales / 1.056;
  const baseGp = cluster.gp / 1.097;
  document.getElementById('impactRows').innerHTML = [
    ['Category sales', srMoney(baseSales), srMoney(sales), srPercent((sales / baseSales - 1) * 100)],
    ['Gross profit', srMoney(baseGp), srMoney(gp), srPercent((gp / baseGp - 1) * 100)],
    ['Slow-moving stock', srMoney(cluster.slow / .743), srMoney(cluster.slow * strategy.slow), srPercent((cluster.slow * strategy.slow / (cluster.slow / .743) - 1) * 100)],
    ['Sales per shelf metre', srMoney(baseSales / cluster.shelfMetres), srMoney(salesMetre), srPercent((sales / baseSales - 1) * 100)]
  ].map(row => `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td><td class="positive">${row[3]}</td></tr>`).join('');
  srRenderSimulator();
}

document.getElementById('storeType').addEventListener('change', srRenderCase);
document.getElementById('strategyType').addEventListener('change', srRenderCase);
document.getElementById('actionFilter').addEventListener('change', srRenderTable);
document.querySelectorAll('[data-sort]').forEach(button => button.addEventListener('click', () => {
  const column = Number(button.dataset.sort);
  srSort.direction = srSort.column === column ? srSort.direction * -1 : 1;
  srSort.column = column;
  srRenderTable();
}));
['spaceRange', 'skuRange', 'simStrategy'].forEach(id => document.getElementById(id).addEventListener('input', srRenderSimulator));
document.getElementById('simulatorControls').addEventListener('submit', event => event.preventDefault());
srRenderCase();
