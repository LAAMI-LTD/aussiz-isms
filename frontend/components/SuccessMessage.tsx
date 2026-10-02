interface SuccessMessageProps {
  message: string;
}

export default function SuccessMessage({
  message
}: SuccessMessageProps) {
  return (
    <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-6">
      <p className="text-green-800">{message}</p>
    </div>
  );
}