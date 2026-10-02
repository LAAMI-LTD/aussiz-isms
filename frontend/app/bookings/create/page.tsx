import { useState } from "react";
import { apiClient } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";
import SuccessMessage from "@/components/SuccessMessage";

export default function CreateBookingPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    student: "",
    exam_center: "",
    exam_date: "",
    preferred_time: "",
    notes: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // In a real app, we would fetch students and exam centers from APIs
  // For now, we'll use placeholder data
  const students = [
    { id: 1, name: "John Doe" },
    { id: 2, name: "Jane Smith" },
    { id: 3, name: "Michael Johnson" }
  ];

  const examCenters = [
    { id: 1, name: "AUSSIZ Main Campus - Room 101" },
    { id: 2, name: "AUSSIZ Downtown Branch - Room 205" },
    { id: 3, name: "AUSSIZ North Campus - Room 301" }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // In a real implementation, we would calculate the amount based on exam type, etc.
      const bookingData = {
        ...formData,
        amount: 250.00 // Placeholder amount
      };

      const response = await apiClient.post("/api/bookings/", bookingData);
      setSuccess("Booking created successfully!");
      setTimeout(() => {
        router.push(`/bookings/${response.id}`);
      }, 1500);
    } catch (err: any) {
      console.error("Failed to create booking:", err);
      setError(err.response?.data?.message || "Failed to create booking. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <Link href="/bookings" className="text-sm text-muted-foreground hover:text-primary">
          ← Back to Bookings
        </Link>
        <h1 className="text-2xl font-bold mt-2">Schedule IELTS Exam</h1>
        <p className="text-muted-foreground">Book an IELTS exam for a student</p>
      </div>

      {error && <ErrorMessage message={error} />}
      {success && <SuccessMessage message={success} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Student</label>
          <select
            value={formData.student}
            onChange={(e) => setFormData({ ...formData, student: e.target.value })}
            className="w-full px-4 py-2 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={loading}
          >
            <option value="">Select a student</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Exam Center</label>
          <select
            value={formData.exam_center}
            onChange={(e) => setFormData({ ...formData, exam_center: e.target.value })}
            className="w-full px-4 py-2 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={loading}
          >
            <option value="">Select an exam center</option>
            {examCenters.map((center) => (
              <option key={center.id} value={center.id}>
                {center.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium mb-2">Exam Date</label>
            <input
              type="date"
              value={formData.exam_date}
              onChange={(e) => setFormData({ ...formData, exam_date: e.target.value })}
              className="w-full px-4 py-2 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              min={new Date().toISOString().split('T')[0]}
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Preferred Time</label>
            <select
              value={formData.preferred_time}
              onChange={(e) => setFormData({ ...formData, preferred_time: e.target.value })}
              className="w-full px-4 py-2 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={loading}
            >
              <option value="">Select time</option>
              <option value="09:00">09:00 AM</option>
              <option value="11:00">11:00 AM</option>
              <option value="14:00">02:00 PM</option>
              <option value="16:00">04:00 PM</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Notes (Optional)</label>
          <textarea
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={4}
            className="w-full px-4 py-2 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={loading}
            placeholder="Any special requirements or notes..."
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="bg-primary text-primary-foreground px-6 py-2 rounded-lg hover:bg-primary/90 transition-colors"
          >
            {loading ? "Creating..." : "Schedule Exam"}
          </button>
        </div>
      </form>
    </div>
  );
}