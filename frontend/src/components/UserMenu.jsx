import { useState, useRef, useEffect } from 'react';

function getInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return parts[0][0].toUpperCase();
}

function UserMenu({ user, role, onLogout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const initials = getInitials(user?.full_name || user?.email);
  const displayName = user?.full_name || user?.email || '';
  const roleLabel = role === 'pi' ? 'Faculty' : 'Student';

  return (
    <div className="um-wrapper" ref={ref}>
      <button className="um-trigger tooltip-host" onClick={() => setOpen(!open)} data-tip="Account" aria-label={`Account menu for ${displayName}`}>
        <span className="um-avatar">{initials}</span>
        <span className="um-caret">&#9662;</span>
      </button>
      {open && (
        <div className="um-dropdown">
          <div className="um-user-info">
            <div className="um-name">{displayName}</div>
            <div className="um-role">{roleLabel}</div>
            <div className="um-email">{user?.email}</div>
          </div>
          <div className="um-divider"></div>
          <button className="um-item" onClick={onLogout}>Sign Out</button>
        </div>
      )}
    </div>
  );
}

export default UserMenu;
