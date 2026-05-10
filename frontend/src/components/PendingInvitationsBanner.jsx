import { useState, useEffect } from 'react';
import { fetchPendingInvitations, acceptInvitation, declineInvitation } from '../services/api';

const ROLE_LABELS = {
  faculty_advisor: 'faculty advisor',
  student_collaborator: 'student collaborator',
};

function PendingInvitationsBanner({ onAccepted }) {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState('');

  async function loadPending() {
    setLoading(true);
    try {
      const rows = await fetchPendingInvitations();
      setPending(rows);
    } catch (err) {
      setPending([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPending();
  }, []);

  async function handleAccept(invitation) {
    setBusyId(invitation.id);
    setError('');
    try {
      await acceptInvitation(invitation.id);
      setPending(pending.filter((p) => p.id !== invitation.id));
      if (onAccepted) onAccepted(invitation);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not accept this invitation.');
    } finally {
      setBusyId(null);
    }
  }

  async function handleDecline(invitation) {
    setBusyId(invitation.id);
    setError('');
    try {
      await declineInvitation(invitation.id);
      setPending(pending.filter((p) => p.id !== invitation.id));
    } catch (err) {
      setError(err.response?.data?.error || 'Could not decline this invitation.');
    } finally {
      setBusyId(null);
    }
  }

  if (loading || pending.length === 0) return null;

  return (
    <div className="invitations-banner">
      <div className="invitations-banner-header">
        <h3>You have {pending.length} pending invitation{pending.length > 1 ? 's' : ''}</h3>
        <p>Someone wants to share access to an activity with you.</p>
      </div>
      {error && <div className="invitations-banner-error">{error}</div>}
      <ul className="invitations-banner-list">
        {pending.map((inv) => (
          <li key={inv.id} className="invitation-row">
            <div className="invitation-text">
              <div className="invitation-from">
                <strong>{inv.fromName}</strong>
                <span className="invitation-email">({inv.fromEmail})</span>
              </div>
              <div className="invitation-message">
                invited you to join <strong>{inv.projectName}</strong> as {ROLE_LABELS[inv.role] || inv.role}
              </div>
              {inv.note && <div className="invitation-note">"{inv.note}"</div>}
            </div>
            <div className="invitation-actions">
              <button
                className="btn-secondary"
                onClick={() => handleDecline(inv)}
                disabled={busyId === inv.id}
              >
                Decline
              </button>
              <button
                className="btn-primary"
                onClick={() => handleAccept(inv)}
                disabled={busyId === inv.id}
              >
                {busyId === inv.id ? 'Working…' : 'Accept'}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PendingInvitationsBanner;
