import { useState, useEffect } from 'react';
import { fetchActivityTimeline } from '../services/api';

/**
 * Visual + label config per audit event type. Keeping this in one map means
 * an unknown event type degrades gracefully to a neutral dot.
 * @type {Record<string, { icon: string, tone: string }>}
 */
const EVENT_STYLES = {
  activity_created: { icon: '✦', tone: 'neutral' },
  activity_updated: { icon: '✎', tone: 'neutral' },
  checkpoint_completed: { icon: '✓', tone: 'positive' },
  checkpoint_reopened: { icon: '↺', tone: 'warning' },
  decision_logged: { icon: '📝', tone: 'positive' },
  comment_added: { icon: '💬', tone: 'neutral' },
  comment_resolved: { icon: '✔', tone: 'positive' },
  comment_reopened: { icon: '↺', tone: 'warning' },
  verification_run: { icon: '🔍', tone: 'info' },
  shared_as_example: { icon: '🌐', tone: 'info' },
  unshared_as_example: { icon: '🔒', tone: 'neutral' },
  invite_sent: { icon: '✉', tone: 'neutral' },
  invite_accepted: { icon: '🤝', tone: 'positive' },
  invite_declined: { icon: '✕', tone: 'warning' },
};

const DEFAULT_STYLE = { icon: '•', tone: 'neutral' };

/**
 * @param {string} isoString
 * @returns {string}
 */
function relativeTime(isoString) {
  const then = new Date(isoString).getTime();
  const diffMs = Date.now() - then;
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return new Date(isoString).toLocaleDateString();
}

/**
 * @param {string} isoString
 * @returns {string}
 */
function fullTimestamp(isoString) {
  const d = new Date(isoString);
  return `${d.toLocaleDateString()} at ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

/**
 * @typedef {Object} ActivityTimelineProps
 * @property {number} projectId
 */

/**
 * Chronological, read-only audit log for one activity.
 * @param {ActivityTimelineProps} props
 */
function ActivityTimeline({ projectId }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function loadTimeline() {
      setLoading(true);
      setError('');
      try {
        const data = await fetchActivityTimeline(projectId);
        if (!cancelled) setEvents(data);
      } catch (err) {
        console.error('Failed to load activity timeline', err);
        if (!cancelled) setError('Could not load the activity log. Please try again.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadTimeline();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  if (loading) {
    return <div className="timeline-state">Loading activity log...</div>;
  }

  if (error) {
    return <div className="timeline-state timeline-state-error">{error}</div>;
  }

  if (events.length === 0) {
    return (
      <div className="timeline-state">
        No activity recorded yet. Actions on this activity will appear here.
      </div>
    );
  }

  return (
    <div className="activity-timeline">
      <p className="timeline-intro">
        A permanent, chronological record of every action on this activity — the audit
        trail for your compliance work.
      </p>
      <ol className="timeline-list">
        {events.map((event) => {
          const style = EVENT_STYLES[event.eventType] || DEFAULT_STYLE;
          return (
            <li key={event.id} className="timeline-item">
              <span className={`timeline-marker timeline-tone-${style.tone}`} aria-hidden="true">
                {style.icon}
              </span>
              <div className="timeline-body">
                <p className="timeline-summary">{event.summary}</p>
                <div className="timeline-meta">
                  <time dateTime={event.createdAt} title={fullTimestamp(event.createdAt)}>
                    {relativeTime(event.createdAt)}
                  </time>
                  {event.checkpointLabel && (
                    <span className="timeline-chip">{event.checkpointLabel}</span>
                  )}
                  {event.metadata?.backfilled && (
                    <span className="timeline-chip timeline-chip-muted" title="Reconstructed from earlier records">
                      historical
                    </span>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export default ActivityTimeline;
