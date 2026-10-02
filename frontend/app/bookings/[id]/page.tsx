import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";
import SuccessMessage from "@/components/SuccessMessage";

export default function BookingDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [booking, setBooking] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchBooking();
  }, [params.id]);

  const fetchBooking = async () => {
    if (!params.id) return;

    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.get(`/api/bookings/${params.id}/`);
      setBooking(data);
    } catch (err) {
      console.error("Failed to fetch booking:", err);
      setError("Failed to load booking details. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = async () => {
    if (!window.confirm("Are you sure you want to cancel this booking? This action cannot be undone.")) {
      return;
    }

    try {
      await apiClient.post(`/api/bookings/${params.id}/cancel/`);
      setSuccess("Booking cancelled successfully!");
      setTimeout(() => {
        router.push("/bookings");
      }, 1500);
    } catch (err) {
      console.error("Failed to cancel booking:", err);
      setError("Failed to cancel booking. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="space-y-4">
          <LoadingSpinner />
          <p className="text-muted-foreground">Loading booking details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <Link href="/bookings" className="text-sm text-muted-foreground hover:text-primary">
            ← Back to Bookings
          </Link>
          <h1 className="text-xl font-bold">Booking Details</h1>
        </div>
        <ErrorMessage message={error} onRetry={fetchBooking} />
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <p>Booking not found.</p>
          <Link
            href="/bookings"
            className="mt-4 inline-block bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
          >
            Back to Bookings
          </Link>
        </div>
      </div>
    );
  }

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
    <div className="p-6">
      {success && <SuccessMessage message={success} />}

      <div className="flex justify-between items-center mb-4">
        <Link href="/bookings" className="text-sm text-muted-foreground hover:text-primary">
          ← Back to Bookings
        </Link>
        <h1 className="text-xl font-bold">Booking Details</h1>
      </div>

      <div className="bg-card rounded-lg p-6 shadow-sm mb-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">Student Information</h2>
          <p className="text-muted-foreground">
            {booking.student_name || booking.student?.user?.get_full_name || 'Unknown Student'}
          </p>
          {booking.student_email && (
            <p className="text-muted-foreground mt-1">
              {booking.student_email}
            </p>
          )}
          {booking.student_phone && (
            <p className="text-muted-foreground mt-1">
              {booking.student_phone}
            </p>
          )}
        </div>

        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">Exam Details</h2>
          <p className="text-muted-foreground">
            <strong>Exam Date:</strong> {booking.exam_date}
          </p>
          <p className="text-muted-foreground">
            <strong>Exam Center:</strong> {booking.exam_center?.name || 'TBD'}
          </p>
          {booking.preferred_time && (
            <p className="text-muted-foreground">
              <strong>Preferred Time:</strong> {booking.preferred_time}
            </p>
          )}
          {booking.exam_type && (
            <p className="text-muted-foreground">
              <strong>Exam Type:</strong> {booking.exam_type}
            </p>
          )}
        </div>

        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">Payment Information</h2>
          <p className="text-muted-foreground">
            <strong>Amount:</strong> ${parseFloat(booking.total_amount || 0).toFixed(2)}
          </p>
          <p className="text-muted-foreground">
            <strong>Status:</strong>
            <span className={`${statusColors[booking.status as string] || 'bg-muted'} px-2 py-1 rounded text-xs`}>
              {statusLabels[booking.status as string] || booking.status}
            </span>
          </p>
          {booking.payment_date && (
            <p className="text-muted-foreground">
              <strong>Payment Date:</strong> {booking.payment_date}
            </p>
          )}
        </div>

        {booking.notes && (
          <div className="mb-4">
            <h2 className="text-lg font-semibold mb-2">Notes</h2>
            <p className="text-muted-foreground whitespace-pre-wrap">{booking.notes}</p>
          </div>
        )}
      </div>

      {booking.status !== 'cancelled' && booking.status !== 'completed' && (
        <div className="mb-6">
          <button
            onClick={handleCancelBooking}
            className="w-full bg-red-500 text-red-500 px-6 py-2 rounded-lg hover:bg-red-500/90 hover:text-white transition-colors border border-red-500"
          >
            Cancel Booking
          </button>
        </div>
      )}

      <div className="mt-6 text-center">
        <Link
          href="/bookings"
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
        >
          Back to All Bookings
        </Link>
      </div>
    </div>
  );
}