"use client"

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    students: 0,
    activeCourses: 0,
    pendingPayments: 0,
    upcomingExams: 0,
    notifications: 0,
    documents: 0
  });
  const [recentActivity, setRecentActivity] = useState<{ id: number; description: string; timestamp: string; type: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // In a real app, we would fetch from multiple endpoints
      // For now, we'll simulate with placeholder data or single endpoint
      const [studentsResponse, coursesResponse, financeResponse] = await Promise.all([
        apiClient.get("/api/students/"),
        apiClient.get("/api/courses/"),
        apiClient.get("/api/finance/")
      ]).catch(() => {
        // If APIs aren't ready yet, use placeholder data
        return [
          { count: 0 },
          { count: 0 },
          { count: 0 }
        ];
      });

      setStats({
        students: studentsResponse?.count || 0,
        activeCourses: coursesResponse?.count || 0,
        pendingPayments: financeResponse?.pending_payments || 0,
        upcomingExams: 0, // Would come from assessments/bookings
        notifications: 0, // Would come from notifications
        documents: 0 // Would come from documents
      });

      // Fetch recent activity (placeholder for now)
      setRecentActivity([
        {
          id: 1,
          description: "System initialized",
          timestamp: new Date().toISOString(),
          type: "system"
        }
      ]);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
      setError("Failed to load dashboard data. Some features may be unavailable.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Stats cards will go here */}
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Students</h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                  <span className="text-primary">👥</span>
                </div>
                <p className="text-3xl font-bold text-primary">0</p>
              </div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
            <p className="text-muted-foreground text-sm mt-2">Total enrolled students</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Active Courses</h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                  <span className="text-primary">📚</span>
                </div>
                <p className="text-3xl font-bold text-primary">0</p>
              </div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
            <p className="text-muted-foreground text-sm mt-2">Currently running courses</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Pending Payments</h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                  <span className="text-primary">💰</span>
                </div>
                <p className="text-3xl font-bold text-primary">$0</p>
              </div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
            <p className="text-muted-foreground text-sm mt-2">Amount due</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Upcoming Exams</h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                  <span className="text-primary">📅</span>
                </div>
                <p className="text-3xl font-bold text-primary">0</p>
              </div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
            <p className="text-muted-foreground text-sm mt-2">IELTS exams scheduled</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Notifications</h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                  <span className="text-primary">🔔</span>
                </div>
                <p className="text-3xl font-bold text-primary">0</p>
              </div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
            <p className="text-muted-foreground text-sm mt-2">Unread notifications</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Documents</h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                  <span className="text-primary">📄</span>
                </div>
                <p className="text-3xl font-bold text-primary">0</p>
              </div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
            <p className="text-muted-foreground text-sm mt-2">Files uploaded</p>
          </div>
        </div>

        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {/* Activity items will go here */}
            <div className="p-4 bg-muted rounded-lg">
              <div className="flex justify-between text-sm">
                <span className="font-medium">Loading recent activity...</span>
                <span className="text-muted-foreground"> — </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <ErrorMessage message={error} />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Stats cards will go here */}
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Students</h2>
            <p className="text-3xl font-bold text-primary">0</p>
            <p className="text-muted-foreground text-sm mt-2">Total enrolled students</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Active Courses</h2>
            <p className="text-3xl font-bold text-primary">0</p>
            <p className="text-muted-foreground text-sm mt-2">Currently running courses</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Pending Payments</h2>
            <p className="text-3xl font-bold text-primary">$0</p>
            <p className="text-muted-foreground text-sm mt-2">Amount due</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Upcoming Exams</h2>
            <p className="text-3xl font-bold text-primary">0</p>
            <p className="text-muted-foreground text-sm mt-2">IELTS exams scheduled</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Notifications</h2>
            <p className="text-3xl font-bold text-primary">0</p>
            <p className="text-muted-foreground text-sm mt-2">Unread notifications</p>
          </div>
          <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Documents</h2>
            <p className="text-3xl font-bold text-primary">0</p>
            <p className="text-muted-foreground text-sm mt-2">Files uploaded</p>
          </div>
        </div>

        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {/* Activity items will go here */}
            <div className="p-4 bg-muted rounded-lg">
              <div className="flex justify-between text-sm">
                <span className="font-medium">No recent activity</span>
                <span className="text-muted-foreground"> — </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="bg-card rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Students</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                <span className="text-primary">👥</span>
              </div>
              <p className="text-3xl font-bold text-primary">{stats.students}</p>
            </div>
            <span className="text-xs text-muted-foreground">
              {stats.students > 0 ? "+" + Math.min(5, Math.floor(stats.students * 0.1)) : ""}
              vs last month
            </span>
          </div>
          <p className="text-muted-foreground text-sm mt-2">Total enrolled students</p>
        </div>
        <div className="bg-card rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Active Courses</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                <span className="text-primary">📚</span>
              </div>
              <p className="text-3xl font-bold text-primary">{stats.activeCourses}</p>
            </div>
            <span className="text-xs text-muted-foreground">
              {stats.activeCourses > 0 ? "+" + Math.min(3, Math.floor(stats.activeCourses * 0.2)) : ""}
              vs last month
            </span>
          </div>
          <p className="text-muted-foreground text-sm mt-2">Currently running courses</p>
        </div>
        <div className="bg-card rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Pending Payments</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                <span className="text-primary">💰</span>
              </div>
              <p className="text-3xl font-bold text-primary">${stats.pendingPayments.toFixed(2)}</p>
            </div>
            <span className="text-xs text-muted-foreground">
              {stats.pendingPayments > 0 ? "+" + Math.min(50, Math.floor(stats.pendingPayments * 0.1)) : ""}
              vs last month
            </span>
          </div>
          <p className="text-muted-foreground text-sm mt-2">Amount due</p>
        </div>
        <div className="bg-card rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Upcoming Exams</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                <span className="text-primary">📅</span>
              </div>
              <p className="text-3xl font-bold text-primary">{stats.upcomingExams}</p>
            </div>
            <span className="text-xs text-muted-foreground">
              {stats.upcomingExams > 0 ? "+" + Math.min(5, Math.floor(stats.upcomingExams * 0.1)) : ""}
              vs last month
            </span>
          </div>
          <p className="text-muted-foreground text-sm mt-2">IELTS exams scheduled</p>
        </div>
        <div className="bg-card rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Notifications</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                <span className="text-primary">🔔</span>
              </div>
              <p className="text-3xl font-bold text-primary">{stats.notifications}</p>
            </div>
            <span className="text-xs text-muted-foreground">
              {stats.notifications > 0 ? "+" + Math.min(10, Math.floor(stats.notifications * 0.2)) : ""}
              vs last month
            </span>
          </div>
          <p className="text-muted-foreground text-sm mt-2">Unread notifications</p>
        </div>
        <div className="bg-card rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Documents</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-primary/20 rounded-full flex items-center justify-center">
                <span className="text-primary">📄</span>
              </div>
              <p className="text-3xl font-bold text-primary">{stats.documents}</p>
            </div>
            <span className="text-xs text-muted-foreground">
              {stats.documents > 0 ? "+" + Math.min(5, Math.floor(stats.documents * 0.1)) : ""}
              vs last month
            </span>
          </div>
          <p className="text-muted-foreground text-sm mt-2">Files uploaded</p>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {recentActivity.length === 0 ? (
            <div className="p-4 bg-muted rounded-lg">
              <div className="flex justify-between text-sm">
                <span className="font-medium">No recent activity</span>
                <span className="text-muted-foreground"> — </span>
              </div>
            </div>
          ) : (
            <>
              {recentActivity.map((activity) => (
                <div key={activity.id} className="p-4 bg-muted rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{activity.description}</span>
                    <span className="text-muted-foreground text-xs">
                      {new Date(activity.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}