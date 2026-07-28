(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const strategies = [
    { name: "Online internally", short: "Internal", discount: 0, clearance: -0.12, commission: "platform", complexity: 1 },
    { name: "Promotional markdown", short: "Markdown", discount: 0.08, clearance: 0.12, commission: "platform", complexity: 2 },
    { name: "Hybrid / partner", short: "Hybrid", discount: 0.03, clearance: 0.2, commission: "both", complexity: 4 },
    { name: "Bulk clearance", short: "Bulk", discount: 0.18, clearance: 0.27, commission: "none", complexity: 2 },
    { name: "Partial write-off", short: "Write-off", discount: 0.06, clearance: -0.04, commission: "platform", complexity: 1, writeOff: true }
  ];
  const ids = ["stock","unitCost","sellingPrice","discount","clearance","platformCommission","fulfilment","partnerCommission","writeOff","holdingCost","period","objective"];
  const value = id => Math.max(0, Number($(id).value) || 0);
  const money = n => `RM${formatNumber(n, 0)}`;
  const signedMoney = n => `${n < 0 ? "−" : ""}RM${formatNumber(Math.abs(n), 0)}`;
  const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

  function calculate(strategy) {
    const stock = value("stock"), unitCost = value("unitCost"), price = value("sellingPrice");
    const discountRate = clamp(value("discount") / 100 + strategy.discount, 0, .95);
    const effectivePrice = price * (1 - discountRate);
    const quantityCleared = Math.min(stock, Math.max(0, Math.round(stock * clamp(value("clearance") / 100 + strategy.clearance, 0, 1))));
    const beforeWriteOff = Math.max(0, stock - quantityCleared);
    const writtenOff = strategy.writeOff ? Math.min(beforeWriteOff, Math.round(beforeWriteOff * clamp(value("writeOff") / 100, 0, 1))) : 0;
    const residual = Math.max(0, stock - quantityCleared - writtenOff);
    const revenue = effectivePrice * quantityCleared;
    const platformRate = strategy.commission === "none" ? 0 : value("platformCommission") / 100;
    const partnerRate = strategy.commission === "both" ? value("partnerCommission") / 100 : 0;
    const commission = revenue * (platformRate + partnerRate);
    const fulfilment = strategy.commission === "none" ? 0 : quantityCleared * value("fulfilment");
    const holdingAvoided = (quantityCleared + writtenOff) * value("holdingCost") * value("period");
    const cash = Math.max(0, revenue - commission - fulfilment);
    const inventoryCost = (quantityCleared + writtenOff) * unitCost;
    const profit = revenue - commission - fulfilment - inventoryCost;
    const recovery = stock * unitCost > 0 ? cash / (stock * unitCost) * 100 : 0;
    const margin = revenue > 0 ? profit / revenue * 100 : 0;
    return { ...strategy, effectivePrice, quantityCleared, writtenOff, residual, revenue, discountValue: Math.max(0, price - effectivePrice) * quantityCleared, commission, fulfilment, holdingAvoided, cash, inventoryCost, profit, recovery, margin };
  }

  function choose(rows) {
    const objective = $("objective").value;
    const metric = {
      profit: r => r.profit, cash: r => r.cash,
      speed: r => r.quantityCleared + r.writtenOff,
      complexity: r => -r.complexity,
      balanced: r => r.profit * .35 + r.cash * .25 + r.recovery * 120 + (r.quantityCleared + r.writtenOff) * 4 - r.complexity * 300
    }[objective];
    return rows.slice().sort((a, b) => metric(b) - metric(a))[0];
  }
  function chart(id, rows, field) {
    svgBarChart($(id), rows.map(r => r.short), rows.map(r => Math.max(0, r[field])));
  }
  function render() {
    const rows = strategies.map(calculate), best = choose(rows);
    $("stockOut").textContent = formatNumber(value("stock"));
    $("discountOut").textContent = formatPercent(value("discount"), 0);
    $("clearanceOut").textContent = formatPercent(value("clearance"), 0);
    $("periodOut").textContent = `${value("period")} ${value("period") === 1 ? "month" : "months"}`;
    $("stockValue").textContent = money(value("stock") * value("unitCost"));
    $("recommendedStrategy").textContent = best.short;
    $("heroRecommendation").textContent = `${best.name} currently leads for ${$("objective").selectedOptions[0].text.toLowerCase()}.`;
    $("recommendationReason").textContent = $("objective").selectedOptions[0].text;
    $("bestCash").textContent = money(best.cash);
    $("bestProfit").textContent = signedMoney(best.profit);
    $("bestRecovery").textContent = formatPercent(best.recovery, 1);
    $("bestUnits").textContent = formatNumber(best.quantityCleared + best.writtenOff);
    $("bestResidual").textContent = formatNumber(best.residual);
    $("bestHolding").textContent = money(best.holdingAvoided);
    renderInsightCards($("pricingInsights"), [
      { kicker: "Recommendation", title: best.name, body: `${$("objective").selectedOptions[0].text} favours this route. It recovers ${money(best.cash)} and leaves ${formatNumber(best.residual)} units.` },
      { kicker: "Trade-off", title: best.profit >= 0 ? "Value is protected" : "An explicit loss is accepted", body: `${signedMoney(best.profit)} P/L, ${formatPercent(best.margin, 1)} margin and ${formatPercent(best.recovery, 1)} cost recovery.` }
    ]);
    $("scenarioRows").innerHTML = rows.map(r => `<tr class="${r.name === best.name ? "recommended-row" : ""}"><td><strong>${r.name}</strong>${r.name === best.name ? ' <span class="badge good">Recommended</span>' : ""}</td><td>${money(r.effectivePrice)}</td><td>${formatNumber(r.quantityCleared + r.writtenOff)}</td><td>${formatNumber(r.residual)}</td><td>${money(r.revenue)}</td><td>${money(r.discountValue)}</td><td>${money(r.commission)}</td><td>${money(r.fulfilment)}</td><td>${money(r.holdingAvoided)}</td><td>${money(r.cash)}</td><td>${money(r.inventoryCost)}</td><td class="${r.profit < 0 ? "negative" : ""}">${signedMoney(r.profit)}</td><td>${formatPercent(r.recovery, 1)}</td></tr>`).join("");
    chart("cashChart", rows, "cash"); chart("profitChart", rows, "profit"); chart("unitsChart", rows, "quantityCleared");
    chart("recoveryChart", rows, "recovery"); chart("residualChart", rows, "residual");
    svgGroupedBarChart($("balanceChart"), rows.map(r => r.short), [
      { name: "Recovery", values: rows.map(r => r.recovery), color: "#188593" },
      { name: "Margin", values: rows.map(r => Math.max(0, r.margin)), color: "#8fa3b8" }
    ]);
    window.__pricingRows = rows;
  }
  ids.forEach(id => { $(id).addEventListener("input", render); $(id).addEventListener("change", render); });
  render();
}());
