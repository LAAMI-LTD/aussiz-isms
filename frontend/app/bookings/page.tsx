"use client"

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import BookingCard from "@/app/bookings/components/BookingCard";
import Link from "next/link";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";
import SuccessMessage from "@/components/SuccessMessage";

export default function BookingsPage() {
  const [bookings, setBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.get("/api/bookings/");
      setBookings(data);
    } catch (err) {
      console.error("Failed to fetch bookings:", err);
      setError("Failed to load bookings. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">IELTS Exam Bookings</h1>
        <div className="space-y-4">
          <LoadingSpinner />
          <p className="text-muted-foreground">Fetching your bookings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-wrap mb-6">
          <h1 className="text-2xl font-bold">IELTS Exam Bookings</h1>
          <Link
            href="/bookings/create"
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
          >
            Create New Booking
          </Link>
        </div>
        <ErrorMessage message={error} onRetry={fetchBookings} />
        {!bookings.length && (
          <div className="mt-6">
            <Link
              href="/bookings/create"
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
            >
              Create First Booking
            </Link>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-6">
      {success && <SuccessMessage message={success} />}

      <div className="flex justify-between items-wrap mb-6">
        <h1 className="text-2xl font-bold">IELTS Exam Bookings</h1>
        <Link
          href="/bookings/create"
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
        >
          Create New Booking
        </Link>
      </div>

      {bookings.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No bookings found. Create your first booking to get started.</p>
          <Link
            href="/bookings/create"
            className="mt-4 inline-block bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
          >
            Create Booking
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {bookings.map((booking) => (
            <BookingCard
              key={booking.id}
              id={booking.id}
              studentName={booking.student_name || booking.student?.user?.get_full_name || 'Unknown Student'}
              examDate={booking.exam_date}
              examCenter={booking.exam_center?.name || 'TBD'}
              status={booking.status as any}
              amount={booking.total_amount || 0}
            />
          ))}
        </div>
      )}
    </div>
  );
}