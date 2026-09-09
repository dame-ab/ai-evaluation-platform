/** Resolved (non-CSS-variable) chart chrome colors, matching index.css's
 * --chart-grid / --chart-axis / --chart-muted tokens -- see the comment in
 * modelColors.ts for why charts need resolved values rather than var(...). */
export const CHART_CHROME = {
  light: { grid: "#e1e0d9", axis: "#c3c2b7", muted: "#898781" },
  dark: { grid: "#2c2c2a", axis: "#383835", muted: "#898781" },
} as const
