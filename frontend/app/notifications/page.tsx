"use client"

import { useState, useEffect } from "react";
import Link from "next/link";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      // In a real app, we would fetch from the API
      // For now, we'll use placeholder data or handle gracefully if API not ready
      const data = []; // Would come from API
      setNotifications(data);
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
      setError("Failed to load notifications. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Notifications</h1>
        <div className="space-y-4">
          <LoadingSpinner />
          <p className="text-muted-foreground">Loading your notifications...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Notifications</h1>
        <ErrorMessage message={error} />
        <div className="mt-4 text-center">
          <Link
            href="/notifications/settings"
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
          >
            Notification Settings
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Notifications</h1>
        <p className="text-muted-foreground">
          Manage notifications and communications for students, staff, and administrators
        </p>
      </div>

      <div className="mb-6 flex justify-between items-wrap">
        <Link
          href="/notifications/create"
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
        >
          Create Notification
        </Link>
        <Link
          href="/notifications/templates"
          className="ml-4 bg-muted text-muted-foreground hover:bg-muted/80 px-4 py-2 rounded-md"
        >
          Templates
          </Link>
        <Link
          href="/notifications/settings"
          className="ml-4 bg-muted text-muted-foreground hover:bg-muted/80 px-4 py-2 rounded-md"
        >
          Settings
        </Link>
      </div>

      {notifications.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No notifications found.</p>
          <div className="mt-6">
            <Link
              href="/notifications/create"
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
            >
              Create First Notification
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <div key={notification.id} className="p-4 bg-card rounded-lg shadow-sm border border-muted">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold">{notification.title || 'Notification'}</h3>
                  <p className="text-muted-foreground">{notification.content || ''}</p>
                </div>
                <div className="text-sm space-x-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${notification.read ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}`}>
                    {notification.read ? 'Read' : 'Unread'}
                  </span>
                  <span className="text-muted-foreground">
                    {new Date(notification.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}