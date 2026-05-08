import { useEffect, useState } from 'react';
import { fetchActivityLibrary, fetchActivityLibraryDetail } from '../services/api';
import UserMenu from './UserMenu';
import NotificationBell from './NotificationBell';
import { USE_CASE_LABELS_SHORT } from '../constants/useCases';

function UseCaseDetailModal({ projectId, onClose, onUseAsTemplate }) {
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchActivityLibraryDetail(projectId)
      .then(setDetail)
      .catch(() => setError('Could not load this use case.'));
  }, [projectId]);

  if (error) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2>Use case</h2>
          <p className="error-text">{error}</p>
          <div className="modal-actions">
            <button className="btn-secondary" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2>Use case</h2>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  const useCaseLabel = USE_CASE_LABELS_SHORT[detail.aiUseCase] || detail.aiUseCase;
  const flagged = Object.entries(detail.riskContext || {}).filter(([, v]) => v).map(([k]) => k);
  const grouped = (detail.completedCheckpoints || []).reduce((acc, c) => {
    (acc[c.category] = acc[c.category] || []).push(c);
    return acc;
  }, {});

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide uc-detail" onClick={(e) => e.stopPropagation()}>
        <h2>{detail.name}</h2>
        <div className="uc-detail-meta">
          <span className="uc-badge uc-badge-usecase">{useCaseLabel}</span>
          {(detail.tools || []).map((t) => (
            <span key={t} className="uc-badge uc-badge-tool">{t}</span>
          ))}
          <span className="uc-detail-author">Faculty (anonymous) · {new Date(detail.createdAt).toLocaleDateString()}</span>
        </div>

        {detail.description && (
          <div className="uc-detail-section">
            <div className="uc-detail-section-title">Description</div>
            <p className="uc-detail-desc">{detail.description}</p>
          </div>
        )}

        {flagged.length > 0 && (
          <div className="uc-detail-section">
            <div className="uc-detail-section-title">Risk flags applied</div>
            <ul className="uc-detail-flags">
              {flagged.map((f) => (
                <li key={f}>{f.replace(/_/g, ' ')}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="uc-detail-section">
          <div className="uc-detail-section-title">
            Compliance checkpoints completed ({detail.completedCheckpoints.length} of {detail.completedCheckpoints.length + detail.pendingCheckpoints.length})
          </div>
          {Object.keys(grouped).length === 0 ? (
            <p className="uc-detail-empty">No checkpoints completed yet on this activity.</p>
          ) : (
            Object.entries(grouped).map(([category, items]) => (
              <div key={category} className="uc-checkpoint-group">
                <div className="uc-checkpoint-cat">{category}</div>
                <ul className="uc-checkpoint-list">
                  {items.map((c) => (
                    <li key={c.id}>{c.label}</li>
                  ))}
                </ul>
              </div>
            ))
          )}
        </div>

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Close</button>
          <button className="btn-primary" onClick={() => onUseAsTemplate(detail)}>Use as template</button>
        </div>
      </div>
    </div>
  );
}

function UseCases({ user, role, onLogout, onBack, onViewToolRegistry, onViewDashboard, onUseAsTemplate }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [useCaseFilter, setUseCaseFilter] = useState('');
  const [toolFilter, setToolFilter] = useState('');
  const [search, setSearch] = useState('');
  const [openId, setOpenId] = useState(null);

  useEffect(() => { load(); }, [useCaseFilter, toolFilter]);

  async function load() {
    setLoading(true);
    try {
      const data = await fetchActivityLibrary({ useCase: useCaseFilter, tool: toolFilter });
      setItems(data.items || []);
    } catch (err) {
      console.error('Failed to load use cases', err);
    } finally {
      setLoading(false);
    }
  }

  const filtered = items.filter((it) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      (it.name || '').toLowerCase().includes(q) ||
      (it.description || '').toLowerCase().includes(q) ||
      (it.tools || []).some((t) => t.toLowerCase().includes(q))
    );
  });

  const allTools = Array.from(new Set(items.flatMap((it) => it.tools || []))).sort();

  return (
    <div className="project-list">
      <div className="pl-topbar">
        <div className="pl-topbar-inner">
          <div className="pl-topbar-brand">
            <img src="/usf-logo.svg" alt="USF" className="pl-topbar-logo" />
            <div className="pl-topbar-text">
              <span className="pl-topbar-uni">University of South Florida</span>
              <span className="pl-topbar-app">RAISE Ethics Toolkit</span>
            </div>
          </div>
          <div className="pl-topbar-right">
            <NotificationBell />
            <UserMenu user={user} role={role} onLogout={onLogout} />
          </div>
        </div>
      </div>

      <div className="pl-nav">
        <div className="pl-nav-inner">
          <button className="pl-nav-tab" onClick={onBack}>My Activities</button>
          <button className="pl-nav-tab" onClick={onViewToolRegistry}>Tool Insights</button>
          <button className="pl-nav-tab active">Use Cases</button>
          <button className="pl-nav-tab" onClick={onViewDashboard}>Compliance Overview</button>
        </div>
      </div>

      <div className="pl-intro">
        <h2 className="pl-intro-title">Use Cases</h2>
        <p className="pl-intro-tagline">
          See how colleagues are using AI in their academic work, and start from a proven setup.
        </p>
        <p className="pl-intro-text">
          Each card below is an anonymized activity that the owner chose to share. Activities are
          private by default; only owners who explicitly opt in appear here. Browse by tool or by
          what people are doing with it. Click <em>Use as template</em> to start a new activity
          pre-filled with the same description, then edit it for your own work.
        </p>
      </div>

      <div className="uc-toolbar">
        <input
          type="text"
          className="uc-search"
          placeholder="Search use cases..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="uc-filter" value={useCaseFilter} onChange={(e) => setUseCaseFilter(e.target.value)}>
          <option value="">All use cases</option>
          {Object.entries(USE_CASE_LABELS_SHORT).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <select className="uc-filter" value={toolFilter} onChange={(e) => setToolFilter(e.target.value)}>
          <option value="">All tools</option>
          {allTools.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="uc-grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="uc-card skeleton-card">
              <div className="skeleton-line skeleton-title"></div>
              <div className="skeleton-line skeleton-text"></div>
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="uc-empty">
          {items.length === 0
            ? 'No shared use cases yet. Activities are private by default; this page fills up as faculty choose to share their work as anonymized examples.'
            : 'No use cases match your filters.'}
        </div>
      ) : (
        <div className="uc-grid">
          {filtered.map((it) => {
            const useCaseLabel = USE_CASE_LABELS_SHORT[it.aiUseCase] || it.aiUseCase;
            return (
              <div key={it.id} className="uc-card" onClick={() => setOpenId(it.id)}>
                <div className="uc-card-title">{it.name}</div>
                <div className="uc-card-badges">
                  <span className="uc-badge uc-badge-usecase">{useCaseLabel}</span>
                  {(it.tools || []).map((t) => (
                    <span key={t} className="uc-badge uc-badge-tool">{t}</span>
                  ))}
                </div>
                <div className="uc-card-author">Faculty (anonymous) · {new Date(it.createdAt).toLocaleDateString()}</div>
                {it.description && <p className="uc-card-desc">{it.description}</p>}
                <div className="uc-card-stats">
                  {it.totalCount > 0
                    ? `${it.completedCount} of ${it.totalCount} checkpoints complete (${it.completionPct}%)`
                    : 'No checkpoints yet'}
                </div>
                <div className="uc-card-actions" onClick={(e) => e.stopPropagation()}>
                  <button className="btn-secondary uc-btn" onClick={() => setOpenId(it.id)}>View use case</button>
                  <button className="btn-primary uc-btn" onClick={() => onUseAsTemplate({ description: it.description, tools: it.tools })}>
                    Use as template
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {openId && (
        <UseCaseDetailModal
          projectId={openId}
          onClose={() => setOpenId(null)}
          onUseAsTemplate={(detail) => {
            setOpenId(null);
            onUseAsTemplate({ description: detail.description, tools: detail.tools });
          }}
        />
      )}
    </div>
  );
}

export default UseCases;
