import { useSuspenseQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ClipboardCheck, FileQuestion, MessageSquare } from "lucide-react"
import { Suspense } from "react"

import { TasksService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

function getTasksQueryOptions(projectId: string) {
  return {
    queryFn: async () =>
      (
        await TasksService.readTasks({
          path: { project_id: projectId },
          query: { skip: 0, limit: 100 },
        })
      ).data,
    queryKey: ["tasks", projectId],
  }
}

function TaskListContent({ projectId }: { projectId: string }) {
  const { data } = useSuspenseQuery(getTasksQueryOptions(projectId))

  if (data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <FileQuestion className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No tasks yet</h3>
        <p className="text-muted-foreground">
          Add a prompt for models to answer and compare.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {data.data.map((task) => (
        <Link
          key={task.id}
          to="/projects/$projectId/tasks/$taskId"
          params={{ projectId, taskId: task.id }}
          className="flex items-center justify-between gap-4 rounded-lg border p-4 transition-colors hover:border-primary/50 hover:bg-accent/30"
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-medium">{task.title}</p>
              {task.category && (
                <Badge variant="secondary">{task.category}</Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground line-clamp-1">
              {task.prompt}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <MessageSquare className="size-4" />
              {task.response_count}
            </span>
            <span className="flex items-center gap-1">
              <ClipboardCheck className="size-4" />
              {task.evaluation_count}
            </span>
          </div>
        </Link>
      ))}
    </div>
  )
}

export function TaskList({ projectId }: { projectId: string }) {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <TaskListContent projectId={projectId} />
    </Suspense>
  )
}

export default TaskList
