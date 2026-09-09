import { expect, test } from "@playwright/test"
import { randomProjectName } from "./utils/random.ts"

test.describe("Evaluation workflow", () => {
  test("create a project, add a task, add responses, and evaluate one", async ({
    page,
  }) => {
    const projectName = randomProjectName()

    await page.goto("/projects")
    await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible()

    await page.getByRole("button", { name: "New Project" }).click()
    await page.getByLabel("Name").fill(projectName)
    await page.getByLabel("Description").fill("An end-to-end test project")
    await page.getByRole("button", { name: "Create project" }).click()

    // AddProject navigates to the new project's detail page on success.
    await expect(page.getByRole("heading", { name: projectName })).toBeVisible()

    // The default rubric should already be attached.
    await page.getByRole("tab", { name: "Rubric" }).click()
    await expect(page.getByText("Standard Evaluation Rubric")).toBeVisible()
    await expect(page.getByText("Correctness", { exact: true })).toBeVisible()
    await expect(page.getByText("Safety", { exact: true })).toBeVisible()

    // Add a task.
    await page.getByRole("tab", { name: "Tasks" }).click()
    await page.getByRole("button", { name: "Add task" }).click()
    await page.getByLabel("Title").fill("What is the capital of France?")
    await page.getByLabel("Prompt").fill("What is the capital of France?")
    await page.getByRole("button", { name: "Save task" }).click()

    const taskLink = page.getByRole("link", { name: /capital of France/ })
    await expect(taskLink).toBeVisible()
    await taskLink.click()

    // Add two competing model responses.
    await page.getByRole("button", { name: "Add model response" }).click()
    await page.getByLabel("Model", { exact: true }).fill("Model A")
    await page
      .getByLabel("Response", { exact: true })
      .fill("The capital of France is Paris.")
    await page.getByRole("button", { name: "Add response" }).click()
    await expect(
      page.getByText("The capital of France is Paris."),
    ).toBeVisible()

    await page.getByRole("button", { name: "Add model response" }).click()
    await page.getByLabel("Model", { exact: true }).fill("Model B")
    await page
      .getByLabel("Response", { exact: true })
      .fill("The capital of France is Lyon.")
    await page.getByRole("button", { name: "Add response" }).click()
    await expect(page.getByText("The capital of France is Lyon.")).toBeVisible()

    // Evaluate the correct response as the winner.
    const responseCard = page.getByTestId("response-card-Model A")
    await responseCard.getByRole("button", { name: "Evaluate" }).click()
    await page.getByLabel("Justification").fill("Correct and to the point.")
    await page.getByLabel("This is the best response for this task").check()
    await page.getByRole("button", { name: "Save evaluation" }).click()

    await expect(responseCard.getByText("avg score")).toBeVisible()
    await expect(responseCard.getByText("Winner")).toBeVisible()

    // Analytics should now reflect the evaluation.
    await page.goBack()
    await page.getByRole("tab", { name: "Analytics" }).click()
    await expect(page.getByText("Model win rate")).toBeVisible()
    await expect(page.getByText("Average score by criterion")).toBeVisible()
  })
})
