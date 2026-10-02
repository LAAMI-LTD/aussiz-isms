import Link from "next/link";

interface BookingCardProps {
  id: string;
  studentName: string;
  examDate: string;
  examCenter: string;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled';
  amount: number;
}

export default function BookingCard({
  id,
  studentName,
  examDate,
  examCenter,
  status,
  amount
}: BookingCardProps) {
  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    confirmed: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800'
  };

  const statusLabels: Record<string, string> = {
    pending: 'Pending',
    confirmed: 'Confirmed',
    completed: 'Completed',
    cancelled: 'Cancelled'
  };

  return (
    <Link href={`/bookings/${id}`} className="group">
      <div className="bg-card rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow duration-200 border border-muted">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-semibold text-lg">{studentName}</h3>
            <p className="text-muted-foreground text-sm">
              Exam: {examDate} • Center: {examCenter}
            </p>
          </div>
          <span
            className={`px-3 py-1 text-xs font-medium rounded-full ${statusColors[status]}`}
          >
            {statusLabels[status]}
          </span>
        </div>

        <div className="flex justify-between items-center mt-4 pt-3 border-t border-muted/50">
          <p className="text-lg font-semibold text-primary">${amount.toFixed(2)}</p>
          <Link
            href={`/bookings/${id}`}
            className="text-sm font-medium text-primary hover:underline"
          >
            View Details
          </Link>
        </div>
      </div>
    </Link>
  );
}