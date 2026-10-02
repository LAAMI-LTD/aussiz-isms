interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({
  message,
  onRetry
}: ErrorMessageProps) {
  return (
    <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
      <p className="text-red-800">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 inline-block bg-primary text-primary-foreground px-3 py-1 rounded text-sm hover:bg-primary/90"
        >
          Retry
        </button>
      )}
    </div>
  );
}