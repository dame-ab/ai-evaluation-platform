import { Link } from "@tanstack/react-router"
import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

function Mark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      className={cn("size-5 shrink-0", className)}
      role="img"
      aria-label="AI Evaluation Platform"
    >
      <rect width="32" height="32" rx="7" className="fill-primary" />
      <rect
        x="7"
        y="17"
        width="4"
        height="8"
        rx="1.5"
        fill="white"
        fillOpacity="0.55"
      />
      <rect
        x="14"
        y="11"
        width="4"
        height="14"
        rx="1.5"
        fill="white"
        fillOpacity="0.8"
      />
      <rect x="21" y="7" width="4" height="18" rx="1.5" fill="white" />
    </svg>
  )
}

function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2", className)}>
      <Mark />
      <span className="font-semibold tracking-tight leading-none">
        Eval<span className="text-primary">Bench</span>
      </span>
    </span>
  )
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  let content: ReactNode
  if (variant === "icon") {
    content = <Mark className={className} />
  } else if (variant === "responsive") {
    content = (
      <>
        <Wordmark
          className={cn("group-data-[collapsible=icon]:hidden", className)}
        />
        <Mark
          className={cn(
            "hidden group-data-[collapsible=icon]:block",
            className,
          )}
        />
      </>
    )
  } else {
    content = <Wordmark className={className} />
  }

  if (!asLink) {
    return content
  }

  return (
    <Link to="/" className="group">
      {content}
    </Link>
  )
}
