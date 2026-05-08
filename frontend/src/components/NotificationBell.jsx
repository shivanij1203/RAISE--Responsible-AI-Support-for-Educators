import { useState, useRef, useEffect, useCallback } from 'react';
import {
  fetchNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from '../services/api';

const POLL_INTERVAL_MS = 30000;

function timeAgo(iso) {
  const then = new Date(iso).getTime();
  const secs = Math.max(1, Math.floor((Date.now() - then) / 1000));
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function NotificationBell({ onOpenProject }) {
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchNotifications();
      setUnreadCount(data.unreadCount || 0);
      setNotifications(data.notifications || []);
    } catch {
      // silent — user may not be logged in yet
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [load]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = async () => {
    const next = !open;
    setOpen(next);
    if (next) {
      setLoading(true);
      await load();
      setLoading(false);
    }
  };

  const handleItemClick = async (n) => {
    if (!n.read) {
      try {
        await markNotificationRead(n.id);
      } catch {
        // ignore — optimistic update below
      }
    }
    setNotifications((prev) =>
      prev.map((x) => (x.id === n.id ? { ...x, read: true } : x))
    );
    setUnreadCount((c) => (n.read ? c : Math.max(0, c - 1)));
    if (onOpenProject && n.projectId) {
      onOpenProject(n.projectId);
      setOpen(false);
    }
  };

  const handleMarkAll = async () => {
    try {
      await markAllNotificationsRead();
    } catch {
      return;
    }
    setNotifications((prev) => prev.map((x) => ({ ...x, read: true })));
    setUnreadCount(0);
  };

  return (
    <div className="nb-wrapper" ref={ref}>
      <button
        className="nb-trigger tooltip-host"
        onClick={handleToggle}
        aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
        data-tip="Notifications"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="nb-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
        )}
      </button>
      {open && (
        <div className="nb-dropdown">
          <div className="nb-header">
            <span className="nb-title">Notifications</span>
            {unreadCount > 0 && (
              <button className="nb-markall" onClick={handleMarkAll}>
                Mark all read
              </button>
            )}
          </div>
          <div className="nb-list">
            {loading && notifications.length === 0 && (
              <div className="nb-empty">Loading…</div>
            )}
            {!loading && notifications.length === 0 && (
              <div className="nb-empty">No notifications yet</div>
            )}
            {notifications.map((n) => (
              <button
                key={n.id}
                className={`nb-item ${n.read ? 'nb-item-read' : 'nb-item-unread'}`}
                onClick={() => handleItemClick(n)}
              >
                <span className="nb-message">{n.message}</span>
                <span className="nb-time">{timeAgo(n.createdAt)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default NotificationBell;
