import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ClipboardCheck } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"

import {
  type EvaluationPublic,
  EvaluationsService,
  type FailureClassification,
  type RubricPublic,
} from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { FAILURE_CLASSIFICATION_OPTIONS } from "@/lib/format"
import { handleError } from "@/utils"

interface FormData {
  scores: Record<string, number>
  justification: string
  failure_classification: FailureClassification
  is_winner: boolean
}

export function EvaluateResponseDialog({
  responseId,
  rubric,
  existingEvaluation,
}: {
  responseId: string
  rubric: RubricPublic
  existingEvaluation?: EvaluationPublic
}) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const sortedCriteria = [...(rubric.criteria ?? [])].sort(
    (a, b) => (a.order ?? 0) - (b.order ?? 0),
  )

  const defaultScores = Object.fromEntries(
    sortedCriteria.map((c) => {
      const existing = (existingEvaluation?.scores ?? []).find(
        (s) => s.criterion_id === c.id,
      )
      const maxScore = c.max_score ?? 5
      return [c.id, existing?.score ?? Math.round(maxScore / 2)]
    }),
  )

  const { register, handleSubmit, watch, setValue } = useForm<FormData>({
    defaultValues: {
      scores: defaultScores,
      justification: existingEvaluation?.justification ?? "",
      failure_classification:
        existingEvaluation?.failure_classification ?? "none",
      is_winner: existingEvaluation?.is_winner ?? false,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const scores = sortedCriteria.map((c) => ({
        criterion_id: c.id,
        score: Number(data.scores[c.id]),
      }))
      if (existingEvaluation) {
        return EvaluationsService.updateEvaluation({
          path: { evaluation_id: existingEvaluation.id },
          body: {
            justification: data.justification,
            failure_classification: data.failure_classification,
            is_winner: data.is_winner,
            scores,
          },
        })
      }
      return EvaluationsService.addEvaluation({
        path: { response_id: responseId },
        body: {
          rubric_id: rubric.id,
          justification: data.justification,
          failure_classification: data.failure_classification,
          is_winner: data.is_winner,
          scores,
        },
      })
    },
    onSuccess: () => {
      showSuccessToast(
        existingEvaluation ? "Evaluation updated" : "Evaluation recorded",
      )
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["evaluations", responseId] }),
  })

  const failureClassification = watch("failure_classification")

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant={existingEvaluation ? "outline" : "default"}>
          <ClipboardCheck className="mr-1.5" />
          {existingEvaluation ? "Edit evaluation" : "Evaluate"}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Score this response</DialogTitle>
          <DialogDescription>
            Rate it against each criterion in "{rubric.name}", note anything
            that went wrong, and say whether it's the best of the compared
            responses.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="grid gap-5 py-4">
            <div className="grid gap-3">
              {sortedCriteria.map((criterion) => (
                <div
                  key={criterion.id}
                  className="flex items-center justify-between gap-4"
                >
                  <Label htmlFor={`score-${criterion.id}`} className="flex-1">
                    <span>{criterion.name}</span>
                    {criterion.description && (
                      <span className="block text-xs font-normal text-muted-foreground">
                        {criterion.description}
                      </span>
                    )}
                  </Label>
                  <Input
                    id={`score-${criterion.id}`}
                    type="number"
                    min={0}
                    max={criterion.max_score}
                    step={1}
                    className="w-20 shrink-0"
                    {...register(`scores.${criterion.id}`, {
                      valueAsNumber: true,
                    })}
                  />
                  <span className="w-10 shrink-0 text-xs text-muted-foreground">
                    / {criterion.max_score}
                  </span>
                </div>
              ))}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="justification">Justification</Label>
              <Textarea
                id="justification"
                rows={3}
                placeholder="Why did you score it this way?"
                {...register("justification")}
              />
            </div>

            <div className="grid gap-2">
              <Label>Failure classification</Label>
              <Select
                value={failureClassification}
                onValueChange={(value) =>
                  setValue(
                    "failure_classification",
                    value as FailureClassification,
                  )
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FAILURE_CLASSIFICATION_OPTIONS.map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                id="is_winner"
                checked={watch("is_winner")}
                onCheckedChange={(checked) =>
                  setValue("is_winner", checked === true)
                }
              />
              <Label htmlFor="is_winner" className="font-normal">
                This is the best response for this task
              </Label>
            </div>
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" disabled={mutation.isPending}>
                Cancel
              </Button>
            </DialogClose>
            <LoadingButton type="submit" loading={mutation.isPending}>
              Save evaluation
            </LoadingButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default EvaluateResponseDialog
