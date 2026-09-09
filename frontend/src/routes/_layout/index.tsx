import { useQueries, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowRight, Trophy } from "lucide-react"
import { Suspense } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { AnalyticsService, ProjectsService } from "@/client"
import ProjectCard from "@/components/Projects/ProjectCard"
import { useTheme } from "@/components/theme-provider"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { CHART_CHROME } from "@/lib/chartTheme"
import { buildModelColorScale } from "@/lib/modelColors"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [{ title: "Dashboard - AI Evaluation Platform" }],
  }),
})

function getProjectsQueryOptions() {
  return {
    queryFn: async () =>
      (await ProjectsService.readProjects({ query: { skip: 0, limit: 100 } }))
        .data,
    queryKey: ["projects"],
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

function Leaderboard({ projectIds }: { projectIds: string[] }) {
  const { resolvedTheme } = useTheme()
  const results = useQueries({
    queries: projectIds.map((projectId) => ({
      queryKey: ["analytics", projectId],
      queryFn: async () =>
        (
          await AnalyticsService.projectAnalytics({
            path: { project_id: projectId },
          })
        ).data,
    })),
  })

  const isLoading = results.some((r) => r.isLoading)
  if (isLoading) return <Skeleton className="h-64 w-full" />

  const totals = new Map<string, { wins: number; total: number }>()
  for (const result of results) {
    for (const winRate of result.data?.win_rates ?? []) {
      const bucket = totals.get(winRate.model_name) ?? { wins: 0, total: 0 }
      bucket.wins += winRate.win_count
      bucket.total += winRate.evaluation_count
      totals.set(winRate.model_name, bucket)
    }
  }

  const rows = Array.from(totals.entries())
    .map(([model_name, { wins, total }]) => ({
      model_name,
      win_rate_pct: total ? Math.round((wins / total) * 100) : 0,
      evaluations: total,
    }))
    .sort((a, b) => b.win_rate_pct - a.win_rate_pct)

  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        Evaluate some responses to see a model leaderboard here.
      </p>
    )
  }

  const colorScale = buildModelColorScale(
    rows.map((r) => r.model_name),
    resolvedTheme,
  )

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          vertical={false}
          stroke={CHART_CHROME[resolvedTheme].grid}
        />
        <XAxis
          dataKey="model_name"
          tick={{ fill: CHART_CHROME[resolvedTheme].muted, fontSize: 12 }}
          axisLine={{ stroke: CHART_CHROME[resolvedTheme].axis }}
          tickLine={false}
        />
        <YAxis
          unit="%"
          domain={[0, 100]}
          tick={{ fill: CHART_CHROME[resolvedTheme].muted, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={40}
        />
        <Tooltip
          cursor={{ fill: CHART_CHROME[resolvedTheme].grid }}
          formatter={(value: number, _name, props) => [
            `${value}% win rate (${props.payload.evaluations} evaluations)`,
            props.payload.model_name,
          ]}
        />
        <Bar dataKey="win_rate_pct" name="Win rate" radius={[4, 4, 0, 0]}>
          {rows.map((row) => (
            <Cell key={row.model_name} fill={colorScale.get(row.model_name)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

function DashboardContent() {
  const { data } = useSuspenseQuery(getProjectsQueryOptions())
  const projects = data.data

  const totals = projects.reduce(
    (acc, p) => ({
      tasks: acc.tasks + (p.task_count ?? 0),
      responses: acc.responses + (p.response_count ?? 0),
      evaluations: acc.evaluations + (p.evaluation_count ?? 0),
    }),
    { tasks: 0, responses: 0, evaluations: 0 },
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Projects" value={projects.length} />
        <StatTile label="Tasks" value={totals.tasks} />
        <StatTile label="Responses" value={totals.responses} />
        <StatTile label="Evaluations" value={totals.evaluations} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="size-5 text-muted-foreground" />
            Model leaderboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Leaderboard projectIds={projects.map((p) => p.id)} />
        </CardContent>
      </Card>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent projects</h2>
          <Link
            to="/projects"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            View all
            <ArrowRight className="size-4" />
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.slice(0, 3).map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      </div>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-20 w-full" />
      ))}
    </div>
  )
}

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          Hi, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">
          Here's how your model evaluations are shaping up.
        </p>
      </div>
      <Suspense fallback={<DashboardSkeleton />}>
        <DashboardContent />
      </Suspense>
    </div>
  )
}
