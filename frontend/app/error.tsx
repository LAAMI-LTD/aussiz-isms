"use client"
import Link from "next/link";

export default function ErrorPage({
  statusCode,
  title
}: {
  statusCode: number;
  title: string;
}) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-muted/50">
      <div className="text-center">
        <div className="mb-6">
          <div className="h-20 w-20 bg-primary/20 rounded-full flex items-center justify-center">
            <span className="text-primary">{statusCode}</span>
          </div>
        </div>
        <h1 className="text-3xl font-bold mb-4">{title}</h1>
        <p className="text-muted-foreground mb-6">
          Something went wrong while processing your request.
        </p>
        <Link
          href="/dashboard"
          className="bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary/90 transition-colors"
        >
          Go to Dashboard
        </Link>
      </div>
    </div>
  );
}