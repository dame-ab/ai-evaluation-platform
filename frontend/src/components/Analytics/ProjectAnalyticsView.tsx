import { useSuspenseQuery } from "@tanstack/react-query"
import { BarChart3 } from "lucide-react"
import { Suspense } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { AnalyticsService } from "@/client"
import { useTheme } from "@/components/theme-provider"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { CHART_CHROME } from "@/lib/chartTheme"
import { FAILURE_CLASSIFICATION_LABELS } from "@/lib/format"
import { buildModelColorScale } from "@/lib/modelColors"

function getAnalyticsQueryOptions(projectId: string) {
  return {
    queryFn: async () =>
      (
        await AnalyticsService.projectAnalytics({
          path: { project_id: projectId },
        })
      ).data,
    queryKey: ["analytics", projectId],
  }
}

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="py-4">
        <p className="text-3xl font-bold tabular-nums">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  )
}

function ChartTooltip({
  active,
  payload,
  label,
  formatValue,
}: {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
  formatValue: (value: number) => string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-sm shadow-md">
      <p className="font-medium mb-1">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} className="flex items-center gap-2">
          <span
            className="inline-block size-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="tabular-nums font-medium">
            {formatValue(entry.value)}
          </span>
        </p>
      ))}
    </div>
  )
}

function AnalyticsContent({ projectId }: { projectId: string }) {
  const { data } = useSuspenseQuery(getAnalyticsQueryOptions(projectId))
  const { resolvedTheme } = useTheme()
  const chrome = CHART_CHROME[resolvedTheme]

  const modelNames = data.win_rates.map((w) => w.model_name)
  const colorScale = buildModelColorScale(modelNames, resolvedTheme)

  if (data.total_evaluations === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <BarChart3 className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No evaluations yet</h3>
        <p className="text-muted-foreground">
          Score at least one response to see analytics here.
        </p>
      </div>
    )
  }

  const winRateData = [...data.win_rates]
    .sort((a, b) => b.win_rate - a.win_rate)
    .map((w) => ({ ...w, win_rate_pct: Math.round(w.win_rate * 100) }))

  const criterionNames = Array.from(
    new Set(data.criterion_averages.map((c) => c.criterion_name)),
  )
  const criterionData = criterionNames.map((criterionName) => {
    const row: Record<string, string | number> = { criterion: criterionName }
    for (const model of modelNames) {
      const match = data.criterion_averages.find(
        (c) => c.criterion_name === criterionName && c.model_name === model,
      )
      if (match) row[model] = match.average_score
    }
    return row
  })

  const failuresByModel = data.failure_breakdown
    .filter((f) => f.failure_classification !== "none")
    .reduce<Record<string, { classification: string; count: number }[]>>(
      (acc, f) => {
        acc[f.model_name] ??= []
        acc[f.model_name].push({
          classification: f.failure_classification,
          count: f.count,
        })
        return acc
      },
      {},
    )

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-3 gap-4">
        <StatTile label="Tasks" value={data.total_tasks} />
        <StatTile label="Responses" value={data.total_responses} />
        <StatTile label="Evaluations" value={data.total_evaluations} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Model win rate</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={winRateData}
              margin={{ top: 8, right: 8, left: 0, bottom: 8 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke={chrome.grid}
              />
              <XAxis
                dataKey="model_name"
                tick={{ fill: chrome.muted, fontSize: 12 }}
                axisLine={{ stroke: chrome.axis }}
                tickLine={false}
              />
              <YAxis
                unit="%"
                domain={[0, 100]}
                tick={{ fill: chrome.muted, fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={40}
              />
              <Tooltip
                cursor={{ fill: chrome.grid }}
                content={<ChartTooltip formatValue={(v) => `${v}% win rate`} />}
              />
              <Bar dataKey="win_rate_pct" name="Win rate" radius={[4, 4, 0, 0]}>
                {winRateData.map((entry) => (
                  <Cell
                    key={entry.model_name}
                    fill={colorScale.get(entry.model_name)}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Average score by criterion</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={criterionData}
              margin={{ top: 8, right: 8, left: 0, bottom: 8 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke={chrome.grid}
              />
              <XAxis
                dataKey="criterion"
                tick={{ fill: chrome.muted, fontSize: 12 }}
                axisLine={{ stroke: chrome.axis }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: chrome.muted, fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={30}
              />
              <Tooltip
                cursor={{ fill: chrome.grid }}
                content={<ChartTooltip formatValue={(v) => v.toFixed(1)} />}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {modelNames.map((model) => (
                <Bar
                  key={model}
                  dataKey={model}
                  name={model}
                  fill={colorScale.get(model)}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {Object.keys(failuresByModel).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Failure classifications</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Failure types observed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(failuresByModel).map(([model, failures]) => (
                  <TableRow key={model}>
                    <TableCell className="font-medium">{model}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1.5">
                        {failures.map((f) => (
                          <Badge key={f.classification} variant="destructive">
                            {
                              FAILURE_CLASSIFICATION_LABELS[
                                f.classification as keyof typeof FAILURE_CLASSIFICATION_LABELS
                              ]
                            }{" "}
                            × {f.count}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export function ProjectAnalyticsView({ projectId }: { projectId: string }) {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <AnalyticsContent projectId={projectId} />
    </Suspense>
  )
}

export default ProjectAnalyticsView
