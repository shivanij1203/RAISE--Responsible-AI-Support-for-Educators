import { useState, useEffect } from 'react';
import { sendInvitation, fetchProjectInvitations, cancelInvitation } from '../../services/api';

const ROLE_LABELS = {
  faculty_advisor: 'Faculty advisor',
  student_collaborator: 'Student collaborator',
};

function InviteCollaboratorModal({ project, onClose, onInvited }) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('student_collaborator');
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);
  const [pending, setPending] = useState([]);
  const [loadingPending, setLoadingPending] = useState(true);

  useEffect(() => {
    fetchProjectInvitations(project.id)
      .then((rows) => setPending(rows.filter((r) => r.status === 'pending')))
      .catch(() => setPending([]))
      .finally(() => setLoadingPending(false));
  }, [project.id]);

  async function handleSend(e) {
    e.preventDefault();
    setError('');

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setError('Enter the collaborator email.');
      return;
    }
    if (!cleanEmail.endsWith('@usf.edu')) {
      setError('Collaborator must have a USF email address (@usf.edu).');
      return;
    }

    setSending(true);
    try {
      const created = await sendInvitation(project.id, cleanEmail, role, note.trim());
      setPending([created, ...pending]);
      setEmail('');
      setNote('');
      if (onInvited) onInvited(created);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not send invitation.');
    } finally {
      setSending(false);
    }
  }

  async function handleCancel(invitationId) {
    try {
      await cancelInvitation(invitationId);
      setPending(pending.filter((p) => p.id !== invitationId));
    } catch (err) {
      console.error('Cancel failed', err);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2>Invite a collaborator</h2>
        <p className="modal-subtitle">
          Share access to this activity with another USF user. They get an in-app
          notification and can accept or decline. Only the activity owner can invite.
        </p>

        <form onSubmit={handleSend} className="invite-form">
          <label className="invite-label">
            <span>USF email</span>
            <input
              type="email"
              placeholder="name@usf.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>

          <label className="invite-label">
            <span>Their role on this activity</span>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="student_collaborator">Student collaborator</option>
              <option value="faculty_advisor">Faculty advisor</option>
            </select>
          </label>

          <label className="invite-label">
            <span>Optional note <em>(visible to them when they receive the invite)</em></span>
            <textarea
              rows={3}
              placeholder="e.g. Hey, can you join as my advisor on this IRB activity?"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={300}
            />
          </label>

          {error && <div className="invite-error">{error}</div>}

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={sending}>Close</button>
            <button type="submit" className="btn-primary" disabled={sending}>
              {sending ? 'Sending…' : 'Send invitation'}
            </button>
          </div>
        </form>

        <div className="invite-pending">
          <h3 className="invite-pending-title">Pending invitations</h3>
          {loadingPending ? (
            <p className="invite-empty">Loading…</p>
          ) : pending.length === 0 ? (
            <p className="invite-empty">No pending invitations on this activity yet.</p>
          ) : (
            <ul className="invite-pending-list">
              {pending.map((inv) => (
                <li key={inv.id} className="invite-pending-row">
                  <div className="invite-pending-text">
                    <strong>{inv.toEmail}</strong>
                    <span className="invite-pending-role"> as {ROLE_LABELS[inv.role] || inv.role}</span>
                  </div>
                  <button className="btn-link-danger" onClick={() => handleCancel(inv.id)}>
                    Cancel
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default InviteCollaboratorModal;
