/**
 * Categorical color assignment for model names in charts.
 *
 * Colors are assigned by identity (a model keeps its color across every
 * chart in a project) rather than by rank, and drawn in a fixed order from
 * the validated 8-slot categorical palette (see the dataviz skill's
 * references/palette.md) so adjacent series stay distinguishable under
 * color-vision deficiency. A 9th+ model folds back to a muted gray.
 *
 * These are plain hex values rather than the `--chart-N` CSS custom
 * properties index.css also defines: recharts sets `fill` as an SVG
 * presentation attribute, and in practice that does not reliably resolve
 * `var(...)` references the way a CSS property assignment would -- so
 * charts need the resolved value, keyed by the active theme.
 */
const LIGHT_PALETTE = [
  "#2a78d6", // blue
  "#eb6834", // orange
  "#1baf7a", // aqua
  "#eda100", // yellow
  "#e87ba4", // magenta
  "#008300", // green
  "#4a3aa7", // violet
  "#e34948", // red
]

const DARK_PALETTE = [
  "#3987e5", // blue
  "#d95926", // orange
  "#199e70", // aqua
  "#c98500", // yellow
  "#d55181", // magenta
  "#008300", // green
  "#9085e9", // violet
  "#e66767", // red
]

const MUTED = { light: "#898781", dark: "#898781" }

export function buildModelColorScale(
  modelNames: string[],
  theme: "light" | "dark" = "light",
): Map<string, string> {
  const palette = theme === "dark" ? DARK_PALETTE : LIGHT_PALETTE
  const uniqueInOrder = Array.from(new Set(modelNames)).sort()
  const scale = new Map<string, string>()
  uniqueInOrder.forEach((name, index) => {
    scale.set(name, index < palette.length ? palette[index] : MUTED[theme])
  })
  return scale
}
