import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { FolderKanban } from "lucide-react"
import { Suspense } from "react"

import { ProjectsService } from "@/client"
import AddProject from "@/components/Projects/AddProject"
import ProjectCard from "@/components/Projects/ProjectCard"
import { Skeleton } from "@/components/ui/skeleton"

function getProjectsQueryOptions() {
  return {
    queryFn: async () =>
      (await ProjectsService.readProjects({ query: { skip: 0, limit: 100 } }))
        .data,
    queryKey: ["projects"],
  }
}

export const Route = createFileRoute("/_layout/projects/")({
  component: ProjectsPage,
  head: () => ({
    meta: [{ title: "Projects - AI Evaluation Platform" }],
  }),
})

function ProjectsGridContent() {
  const { data } = useSuspenseQuery(getProjectsQueryOptions())

  if (data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <FolderKanban className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No projects yet</h3>
        <p className="text-muted-foreground">
          Create a project to start comparing model responses.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.data.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  )
}

function ProjectsGridSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <Skeleton key={i} className="h-48 w-full" />
      ))}
    </div>
  )
}

function ProjectsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground">
            Organize evaluations by product surface, model comparison, or
            benchmark
          </p>
        </div>
        <AddProject />
      </div>
      <Suspense fallback={<ProjectsGridSkeleton />}>
        <ProjectsGridContent />
      </Suspense>
    </div>
  )
}
