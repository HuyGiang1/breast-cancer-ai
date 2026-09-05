export function probabilityBar(probability, threshold, label = 'Model probability') {
  const value = Math.max(0, Math.min(1, Number(probability) || 0));
  return `<div class="probability" aria-label="${label}: ${(value * 100).toFixed(1)}%"><div class="probability-fill" style="width:${value * 100}%"></div><span class="probability-marker" style="left:${threshold * 100}%" title="Raw threshold ${threshold}"></span></div>`;
}
