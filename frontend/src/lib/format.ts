import type { FailureClassification } from "@/client"

export const FAILURE_CLASSIFICATION_LABELS: Record<
  FailureClassification,
  string
> = {
  none: "None",
  hallucination: "Hallucination",
  factual_error: "Factual error",
  incomplete_answer: "Incomplete answer",
  unsafe_content: "Unsafe content",
  off_topic: "Off-topic",
  formatting_error: "Formatting error",
  other: "Other",
}

export const FAILURE_CLASSIFICATION_OPTIONS = Object.entries(
  FAILURE_CLASSIFICATION_LABELS,
) as [FailureClassification, string][]

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—"
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function formatScore(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}
