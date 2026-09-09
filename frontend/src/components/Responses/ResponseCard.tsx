import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import { Trash2 } from "lucide-react"
import { Suspense } from "react"

import {
  EvaluationsService,
  type ModelResponsePublic,
  type RubricPublic,
  TasksService,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { FAILURE_CLASSIFICATION_LABELS, formatScore } from "@/lib/format"
import { handleError } from "@/utils"
import EvaluateResponseDialog from "./EvaluateResponseDialog"

function getEvaluationsQueryOptions(responseId: string) {
  return {
    queryFn: async () =>
      (
        await EvaluationsService.readEvaluations({
          path: { response_id: responseId },
        })
      ).data,
    queryKey: ["evaluations", responseId],
  }
}

function EvaluationSummary({
  responseId,
  rubric,
}: {
  responseId: string
  rubric: RubricPublic
}) {
  const { user: currentUser } = useAuth()
  const { data } = useSuspenseQuery(getEvaluationsQueryOptions(responseId))
  const myEvaluation = data.data.find((e) => e.evaluator_id === currentUser?.id)

  const overallScores = data.data.map((evaluation) => {
    const scores = evaluation.scores ?? []
    const total = scores.reduce((sum, s) => sum + s.score, 0)
    return scores.length ? total / scores.length : 0
  })
  const avgScore = overallScores.length
    ? overallScores.reduce((a, b) => a + b, 0) / overallScores.length
    : null

  return (
    <div className="flex flex-col gap-3">
      {data.data.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          {avgScore !== null && (
            <Badge variant="secondary">avg score {formatScore(avgScore)}</Badge>
          )}
          {data.data.some((e) => e.is_winner) && (
            <Badge className="bg-emerald-600 text-white hover:bg-emerald-600/90">
              Winner
            </Badge>
          )}
          {data.data
            .filter((e) => (e.failure_classification ?? "none") !== "none")
            .map((e) => (
              <Badge key={e.id} variant="destructive">
                {
                  FAILURE_CLASSIFICATION_LABELS[
                    e.failure_classification ?? "none"
                  ]
                }
              </Badge>
            ))}
        </div>
      )}
      {myEvaluation?.justification && (
        <p className="text-sm text-muted-foreground italic">
          "{myEvaluation.justification}"
        </p>
      )}
      <div>
        <EvaluateResponseDialog
          responseId={responseId}
          rubric={rubric}
          existingEvaluation={myEvaluation}
        />
      </div>
    </div>
  )
}

export function ResponseCard({
  response,
  modelColor,
  rubric,
  taskId,
}: {
  response: ModelResponsePublic
  modelColor?: string
  rubric?: RubricPublic
  taskId: string
}) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: () =>
      TasksService.deleteResponse({ path: { response_id: response.id } }),
    onSuccess: () => showSuccessToast("Response removed"),
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["responses", taskId] }),
  })

  return (
    <Card
      data-testid={`response-card-${response.model_name}`}
      style={
        modelColor
          ? { borderTopColor: modelColor, borderTopWidth: 3 }
          : undefined
      }
    >
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          {modelColor && (
            <span
              className="inline-block size-2.5 rounded-full"
              style={{ backgroundColor: modelColor }}
            />
          )}
          {response.model_name}
        </CardTitle>
        <Button
          variant="ghost"
          size="icon"
          className="size-7 text-muted-foreground hover:text-destructive"
          onClick={() => deleteMutation.mutate()}
        >
          <Trash2 className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="whitespace-pre-wrap text-sm">{response.response_text}</p>
        {rubric && (
          <Suspense fallback={<Skeleton className="h-8 w-full" />}>
            <EvaluationSummary responseId={response.id} rubric={rubric} />
          </Suspense>
        )}
      </CardContent>
    </Card>
  )
}

export default ResponseCard
