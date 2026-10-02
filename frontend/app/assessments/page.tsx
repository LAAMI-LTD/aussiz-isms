import Link from "next/link";

export default function AssessmentsPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Assessments & Results</h1>
        <p className="text-muted-foreground">
          Manage IELTS practice tests, mock exams, and official results
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">📝</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">Practice Tests</h3>
          </div>
          <p className="text-muted-foreground">
            Create and manage IELTS practice exams for students
          </p>
          <Link
            href="/assessments/practice"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            View Practice Tests
          </Link>
        </div>

        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">📊</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">Official Results</h3>
          </div>
          <p className="text-muted-foreground">
            Track and manage official IELTS exam results for students
          </p>
          <Link
            href="/assessments/results"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            View Results
          </Link>
        </div>

        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">📈</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">Progress Tracking</h3>
          </div>
          <p className="text-muted-foreground">
            Monitor student progress across multiple exam attempts
          </p>
          <Link
            href="/assessments/progress"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            View Progress
          </Link>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-bold mb-4">Recent Assessments</h2>
        <div className="space-y-4">
          <div className="p-4 bg-muted rounded-lg">
            <div className="flex justify-between text-sm">
              <span className="font-medium">No assessments recorded yet</span>
              <span className="text-muted-foreground"> — </span>
            </div>
          </div>
        </div>
        <div className="mt-4 text-center">
          <Link
            href="/assessments/create"
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
          >
            Create First Assessment
          </Link>
        </div>
      </div>
    </div>
  );
}