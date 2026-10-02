"use client"
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function NotFoundPage() {
  const pathname = usePathname();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-muted/50">
      <div className="text-center">
        <div className="mb-6">
          <div className="h-16 w-16 bg-primary/20 rounded-full flex items-center justify-center">
            <span className="text-primary">🔍</span>
          </div>
        </div>
        <h1 className="text-3xl font-bold mb-4">Page Not Found</h1>
        <p className="text-muted-foreground mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex space-x-4">
          <Link
            href="/"
            className="bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary/90 transition-colors"
          >
            Go to Home
          </Link>
          <Link
            href="/dashboard"
            className="bg-muted text-muted-foreground hover:bg-muted/80 px-6 py-3 rounded-lg hover:bg-muted/90 transition-colors"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}