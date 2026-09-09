import { useSuspenseQuery } from "@tanstack/react-query"
import { Suspense } from "react"

import { RubricsService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import AddCriterion from "./AddCriterion"
import EditCriterion from "./EditCriterion"

function getRubricsQueryOptions(projectId: string) {
  return {
    queryFn: async () =>
      (await RubricsService.readRubrics({ path: { project_id: projectId } }))
        .data,
    queryKey: ["rubrics", projectId],
  }
}

function RubricPanelContent({ projectId }: { projectId: string }) {
  const { data } = useSuspenseQuery(getRubricsQueryOptions(projectId))
  const rubric = data.data[0]

  if (!rubric) {
    return (
      <p className="text-muted-foreground py-8 text-center">
        No rubric defined for this project yet.
      </p>
    )
  }

  const sortedCriteria = [...(rubric.criteria ?? [])].sort(
    (a, b) => (a.order ?? 0) - (b.order ?? 0),
  )

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle>{rubric.name}</CardTitle>
          {rubric.description && (
            <p className="text-sm text-muted-foreground mt-1">
              {rubric.description}
            </p>
          )}
        </div>
        <AddCriterion rubricId={rubric.id} nextOrder={sortedCriteria.length} />
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {sortedCriteria.map((criterion) => (
          <div
            key={criterion.id}
            className="flex items-center justify-between gap-4 rounded-lg border p-3"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-medium">{criterion.name}</p>
                <Badge variant="secondary">weight {criterion.weight}</Badge>
                <Badge variant="outline">0–{criterion.max_score}</Badge>
              </div>
              {criterion.description && (
                <p className="text-sm text-muted-foreground line-clamp-1">
                  {criterion.description}
                </p>
              )}
            </div>
            <EditCriterion rubricId={rubric.id} criterion={criterion} />
          </div>
        ))}
        {sortedCriteria.length === 0 && (
          <p className="text-muted-foreground py-8 text-center">
            This rubric has no criteria yet. Add one to start scoring responses.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function RubricPanel({ projectId }: { projectId: string }) {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <RubricPanelContent projectId={projectId} />
    </Suspense>
  )
}

export default RubricPanel
