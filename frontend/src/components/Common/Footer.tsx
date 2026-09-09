import { FaGithub } from "react-icons/fa"

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t py-4 px-6">
      <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
        <p className="text-muted-foreground text-sm">
          AI Evaluation Platform - {currentYear}
        </p>
        <a
          href="https://github.com/dame-ab/ai-evaluation-platform"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="GitHub repository"
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <FaGithub className="h-5 w-5" />
        </a>
      </div>
    </footer>
  )
}
