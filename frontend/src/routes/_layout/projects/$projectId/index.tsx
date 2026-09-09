import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"

import { ProjectsService } from "@/client"
import ProjectAnalyticsView from "@/components/Analytics/ProjectAnalyticsView"
import DeleteProject from "@/components/Projects/DeleteProject"
import RubricPanel from "@/components/Rubric/RubricPanel"
import AddTask from "@/components/Tasks/AddTask"
import TaskList from "@/components/Tasks/TaskList"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

function getProjectQueryOptions(projectId: string) {
  return {
    queryFn: async () =>
      (await ProjectsService.readProject({ path: { project_id: projectId } }))
        .data,
    queryKey: ["project", projectId],
  }
}

export const Route = createFileRoute("/_layout/projects/$projectId/")({
  component: ProjectDetailPage,
  head: () => ({
    meta: [{ title: "Project - AI Evaluation Platform" }],
  }),
})

function ProjectHeader({ projectId }: { projectId: string }) {
  const { data: project } = useSuspenseQuery(getProjectQueryOptions(projectId))
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
        {project.description && (
          <p className="text-muted-foreground max-w-2xl">
            {project.description}
          </p>
        )}
      </div>
      <DeleteProject projectId={project.id} projectName={project.name} />
    </div>
  )
}

function ProjectDetailPage() {
  const { projectId } = Route.useParams()

  return (
    <div className="flex flex-col gap-6">
      <Suspense fallback={<Skeleton className="h-14 w-full" />}>
        <ProjectHeader projectId={projectId} />
      </Suspense>

      <Tabs defaultValue="tasks">
        <TabsList>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="rubric">Rubric</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>
        <TabsContent value="tasks" className="flex flex-col gap-4 pt-2">
          <div className="flex justify-end">
            <AddTask projectId={projectId} />
          </div>
          <TaskList projectId={projectId} />
        </TabsContent>
        <TabsContent value="rubric" className="pt-2">
          <RubricPanel projectId={projectId} />
        </TabsContent>
        <TabsContent value="analytics" className="pt-2">
          <ProjectAnalyticsView projectId={projectId} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
