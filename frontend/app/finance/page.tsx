import Link from "next/link";

export default function FinancePage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Finance Management</h1>
        <p className="text-muted-foreground">
          Complete financial workflow including fees, invoices, payments, and reconciliation
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">💳</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">Fee Management</h3>
          </div>
          <p className="text-muted-foreground">
            Define and manage different types of fees for courses, exams, and services
          </p>
          <Link
            href="/finance/fees"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            Manage Fees
          </Link>
        </div>

        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">📄</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">Invoicing</h3>
          </div>
          <p className="text-muted-foreground">
            Generate and manage invoices for students and services
          </p>
          <Link
            href="/finance/invoices"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            View Invoices
          </Link>
        </div>

        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">💰</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">Payments</h3>
          </div>
          <p className="text-muted-foreground">
            Track and process payments from students and other sources
          </p>
          <Link
            href="/finance/payments"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            View Payments
          </Link>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-bold mb-4">Financial Overview</h2>
        <div className="space-y-4">
          <div className="p-4 bg-muted rounded-lg">
            <div className="flex justify-between text-sm">
              <span className="font-medium">No financial data available yet</span>
              <span className="text-muted-foreground"> — </span>
            </div>
          </div>
        </div>
        <div className="mt-4 text-center">
          <Link
            href="/finance/dashboard"
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
          >
            View Financial Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}