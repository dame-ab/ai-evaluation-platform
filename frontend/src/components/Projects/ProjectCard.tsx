import { Link } from "@tanstack/react-router"
import { ClipboardList, FileText, MessageSquare } from "lucide-react"

import type { ProjectSummary } from "@/client"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { formatDate } from "@/lib/format"

export function ProjectCard({ project }: { project: ProjectSummary }) {
  return (
    <Link to="/projects/$projectId" params={{ projectId: project.id }}>
      <Card className="h-full transition-colors hover:border-primary/50 hover:bg-accent/30">
        <CardHeader>
          <CardTitle className="line-clamp-1">{project.name}</CardTitle>
          <CardDescription className="line-clamp-2 min-h-10">
            {project.description || "No description"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-3 gap-2 text-center">
            <div className="flex flex-col items-center gap-1 rounded-md bg-muted/50 py-2">
              <FileText className="size-4 text-muted-foreground" />
              <dd className="text-lg font-semibold leading-none">
                {project.task_count}
              </dd>
              <dt className="text-xs text-muted-foreground">Tasks</dt>
            </div>
            <div className="flex flex-col items-center gap-1 rounded-md bg-muted/50 py-2">
              <MessageSquare className="size-4 text-muted-foreground" />
              <dd className="text-lg font-semibold leading-none">
                {project.response_count}
              </dd>
              <dt className="text-xs text-muted-foreground">Responses</dt>
            </div>
            <div className="flex flex-col items-center gap-1 rounded-md bg-muted/50 py-2">
              <ClipboardList className="size-4 text-muted-foreground" />
              <dd className="text-lg font-semibold leading-none">
                {project.evaluation_count}
              </dd>
              <dt className="text-xs text-muted-foreground">Evaluations</dt>
            </div>
          </dl>
        </CardContent>
        <CardFooter>
          <p className="text-xs text-muted-foreground">
            Created {formatDate(project.created_at)}
          </p>
        </CardFooter>
      </Card>
    </Link>
  )
}

export default ProjectCard
