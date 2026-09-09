import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, MessageSquareOff } from "lucide-react"
import { Suspense } from "react"

import { RubricsService, TasksService } from "@/client"
import AddResponse from "@/components/Responses/AddResponse"
import ResponseCard from "@/components/Responses/ResponseCard"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { buildModelColorScale } from "@/lib/modelColors"

export const Route = createFileRoute(
  "/_layout/projects/$projectId/tasks/$taskId",
)({
  component: TaskDetailPage,
  head: () => ({
    meta: [{ title: "Task - AI Evaluation Platform" }],
  }),
})

function getTaskQueryOptions(taskId: string) {
  return {
    queryFn: async () =>
      (await TasksService.readTask({ path: { task_id: taskId } })).data,
    queryKey: ["task", taskId],
  }
}

function getResponsesQueryOptions(taskId: string) {
  return {
    queryFn: async () =>
      (await TasksService.readResponses({ path: { task_id: taskId } })).data,
    queryKey: ["responses", taskId],
  }
}

function getRubricsQueryOptions(projectId: string) {
  return {
    queryFn: async () =>
      (await RubricsService.readRubrics({ path: { project_id: projectId } }))
        .data,
    queryKey: ["rubrics", projectId],
  }
}

function TaskDetailContent({
  projectId,
  taskId,
}: {
  projectId: string
  taskId: string
}) {
  const { data: task } = useSuspenseQuery(getTaskQueryOptions(taskId))
  const { data: responses } = useSuspenseQuery(getResponsesQueryOptions(taskId))
  const { data: rubrics } = useSuspenseQuery(getRubricsQueryOptions(projectId))
  const rubric = rubrics.data[0]

  const colorScale = buildModelColorScale(
    responses.data.map((r) => r.model_name),
  )

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          to="/projects/$projectId"
          params={{ projectId }}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back to project
        </Link>
      </div>

      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{task.title}</h1>
            {task.category && (
              <Badge variant="secondary">{task.category}</Badge>
            )}
          </div>
        </div>
        <AddResponse taskId={taskId} />
      </div>

      <Card>
        <CardContent className="flex flex-col gap-3">
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">
              Prompt
            </p>
            <p className="whitespace-pre-wrap text-sm">{task.prompt}</p>
          </div>
          {task.reference_answer && (
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">
                Reference answer
              </p>
              <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                {task.reference_answer}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {!rubric && (
        <p className="text-sm text-muted-foreground">
          This project has no rubric yet -- add one from the project's Rubric
          tab before evaluating responses.
        </p>
      )}

      {responses.data.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center py-12">
          <div className="rounded-full bg-muted p-4 mb-4">
            <MessageSquareOff className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No responses yet</h3>
          <p className="text-muted-foreground">
            Add each model's response to compare them side-by-side.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {responses.data.map((response) => (
            <ResponseCard
              key={response.id}
              response={response}
              modelColor={colorScale.get(response.model_name)}
              rubric={rubric}
              taskId={taskId}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function TaskDetailPage() {
  const { projectId, taskId } = Route.useParams()
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <TaskDetailContent projectId={projectId} taskId={taskId} />
    </Suspense>
  )
}
