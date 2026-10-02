"use client"

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex max-w-screen-xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-between py-4">
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-2 rtl:space-x-reverse">
              <img
                src="/aussiz-logo.png"
                alt="AUSSIZ-ISMS Logo"
                className="h-8 w-auto"
              />
              <span className="self-center text-xl font-semibold whitespace-nowrap">
                AUSSIZ-ISMS
              </span>
            </Link>
          </div>
          <div className="hidden md:flex md:items-center md:space-x-6">
            <Link
              href="/"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium",
                pathname === "/" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
              ].join(" ")}
            >
              Dashboard
            </Link>
            <Link
              href="/students"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium",
                pathname === "/students"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              ].join(" ")}
            >
              Students
            </Link>
            <Link
              href="/courses"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium",
                pathname === "/courses"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              ].join(" ")}
            >
              Courses & Classes
            </Link>
            <Link
              href="/assessments"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium",
                pathname === "/assessments"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              ].join(" ")}
            >
              Assessments
            </Link>
            <Link
              href="/bookings"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium",
                pathname === "/bookings"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              ].join(" ")}
            >
              IELTS Bookings
            </Link>
            <Link
              href="/finance"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium",
                pathname === "/finance"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              ].join(" ")}
            >
              Finance
            </Link>
            <Link
              href="/notifications"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium",
                pathname === "/notifications"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              ].join(" ")}
            >
              Notifications
            </Link>
            <Link
              href="/documents"
              className={[
                "rounded-md px-3 py-2 text-sm font-medium",
                pathname === "/documents"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              ].join(" ")}
            >
              Documents
            </Link>
          </div>
          <div className="md:hidden">
            <button
              className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted"
              aria-label="Open menu"
            >
              Menu
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}