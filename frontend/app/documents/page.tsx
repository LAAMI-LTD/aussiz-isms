import Link from "next/link";

export default function DocumentsPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Document Management</h1>
        <p className="text-muted-foreground">
          Store, organize, and manage documents, templates, and files for the institution
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">📁</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">File Storage</h3>
          </div>
          <p className="text-muted-foreground">
            Securely store and organize documents, certificates, and important files
          </p>
          <Link
            href="/documents/files"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            Browse Files
          </Link>
        </div>

        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">📋</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">Templates</h3>
          </div>
          <p className="text-muted-foreground">
            Create and manage document templates for certificates, reports, and forms
          </p>
          <Link
            href="/documents/templates"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            Manage Templates
          </Link>
        </div>

        <div className="bg-card rounded-lg p-6 shadow-sm border border-muted">
          <div className="flex items-center mb-4">
            <div className="h-10 w-10 bg-primary/20 rounded-full flex items-center justify-center">
              <span className="text-primary">🔍</span>
            </div>
            <h3 className="text-lg font-semibold mb-0 ml-3">Document Types</h3>
          </div>
          <p className="text-muted-foreground">
            Define and categorize different types of documents for better organization
          </p>
          <Link
            href="/documents/types"
            className="mt-4 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
          >
            View Types
          </Link>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-bold mb-4">Recent Documents</h2>
        <div className="space-y-4">
          <div className="p-4 bg-muted rounded-lg">
            <div className="flex justify-between text-sm">
              <span className="font-medium">No documents uploaded yet</span>
              <span className="text-muted-foreground"> — </span>
            </div>
          </div>
        </div>
        <div className="mt-4 text-center">
          <Link
            href="/documents/upload"
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
          >
            Upload First Document
          </Link>
        </div>
      </div>
    </div>
  );
}