import { useState, useEffect } from 'react';
import { fetchTools, createTool, updateTool, fetchToolDetail } from '../services/api';
import UserMenu from './UserMenu';
import NotificationBell from './NotificationBell';

const AI_CATEGORIES = [
  { value: 'chatbot', label: 'Chatbot' },
  { value: 'code_assistant', label: 'Code Assistant' },
  { value: 'grading', label: 'Grading' },
  { value: 'writing', label: 'Writing' },
  { value: 'image_gen', label: 'Image Generation' },
  { value: 'data_analysis', label: 'Data Analysis' },
  { value: 'research', label: 'Research' },
  { value: 'other', label: 'Other' },
];

const GENERAL_CATEGORIES = [
  { value: 'survey', label: 'Survey & Forms' },
  { value: 'statistics', label: 'Statistics' },
  { value: 'qualitative', label: 'Qualitative Analysis' },
  { value: 'reference', label: 'Reference Management' },
  { value: 'collaboration', label: 'Collaboration' },
  { value: 'lms', label: 'Learning Management' },
  { value: 'visualization', label: 'Data Visualization' },
  { value: 'other', label: 'Other' },
];

const ALL_CATEGORIES = [...AI_CATEGORIES, ...GENERAL_CATEGORIES.filter(g => !AI_CATEGORIES.find(a => a.value === g.value))];

function AIToolRegistry({ user, role, onLogout, onBack, onViewDashboard }) {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingTool, setEditingTool] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '', vendor: '', category: '', tool_type: 'ai', risk_notes: '', website_url: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [selectedTool, setSelectedTool] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const isFaculty = role === 'pi';

  useEffect(() => { loadTools(); }, []);

  async function loadTools() {
    try {
      const data = await fetchTools();
      setTools(data);
    } catch (err) {
      console.error('Failed to load tools', err);
    } finally {
      setLoading(false);
    }
  }

  async function openToolDetail(toolId) {
    setLoadingDetail(true);
    try {
      const data = await fetchToolDetail(toolId);
      setSelectedTool(data);
    } catch (err) {
      console.error('Failed to load tool detail', err);
    } finally {
      setLoadingDetail(false);
    }
  }

  async function handleSave() {
    if (!formData.name.trim() || !formData.category) return;
    setSaving(true);
    setError('');
    try {
      if (editingTool) {
        const updated = await updateTool(editingTool.id, formData);
        setTools(tools.map(t => t.id === updated.id ? updated : t));
      } else {
        const created = await createTool(formData);
        setTools([created, ...tools]);
      }
      setShowAddModal(false);
      setEditingTool(null);
      setFormData({ name: '', description: '', vendor: '', category: '', tool_type: 'ai', risk_notes: '', website_url: '' });
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save tool.');
    } finally {
      setSaving(false);
    }
  }

  function openEdit(tool) {
    setEditingTool(tool);
    setFormData({
      name: tool.name,
      description: tool.description,
      vendor: tool.vendor,
      category: tool.category,
      tool_type: tool.toolType || 'ai',
      risk_notes: tool.riskNotes || '',
      website_url: tool.websiteUrl || '',
    });
    setShowAddModal(true);
  }

  function openAddModal(type) {
    setEditingTool(null);
    setFormData({ name: '', description: '', vendor: '', category: '', tool_type: type, risk_notes: '', website_url: '' });
    setShowAddModal(true);
  }

  const filtered = tools.filter(t => {
    if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (categoryFilter && t.category !== categoryFilter) return false;
    if (typeFilter !== 'all' && t.toolType !== typeFilter) return false;
    return true;
  });

  const aiTools = filtered.filter(t => t.toolType === 'ai');
  const generalTools = filtered.filter(t => (t.toolType || 'ai') === 'general');

  const currentCategories = formData.tool_type === 'ai' ? AI_CATEGORIES : GENERAL_CATEGORIES;

  if (loading) {
    return (
      <div className="tool-registry">
        <div className="pl-topbar">
          <div className="pl-topbar-inner">
            <div className="pl-topbar-brand">
              <img src="/usf-logo.svg" alt="USF" className="pl-topbar-logo" />
              <div className="pl-topbar-text">
                <span className="pl-topbar-uni">University of South Florida</span>
                <span className="pl-topbar-app">RAISE Ethics Toolkit</span>
              </div>
            </div>
          </div>
        </div>
        <div className="pl-nav">
          <div className="pl-nav-inner">
            <button className="pl-nav-tab" onClick={onBack}>My Activities</button>
            <button className="pl-nav-tab active">Tool Library</button>
          </div>
        </div>
        <div className="tool-registry-content">
          <div className="tool-grid">
            {[1, 2, 3].map(i => (
              <div key={i} className="tool-card skeleton-card">
                <div className="skeleton-line skeleton-title"></div>
                <div className="skeleton-line skeleton-text"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="tool-registry">
      {/* USF-style top bar */}
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

      {/* Tab navigation */}
      <div className="pl-nav">
        <div className="pl-nav-inner">
          <button className="pl-nav-tab" onClick={onBack}>My Activities</button>
          <button className="pl-nav-tab active">Tool Library</button>
          <button className="pl-nav-tab" onClick={onViewDashboard}>Compliance Overview</button>
        </div>
      </div>

      {/* Content */}
      <div className="tool-registry-content">
        <div className="tool-registry-title-row">
          <div>
            <h2 className="tool-registry-heading">Tool Library</h2>
            <p className="tool-subtitle">A reference library of AI and productivity tools commonly used in higher education. Each tool includes data handling details, compliance guidance by use case, and a record of how faculty and students have used it.</p>
          </div>
        </div>

        {/* Filters */}
        <div className="tool-filters">
          <input
            type="text"
            placeholder="Search tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="tool-search"
          />
          <div className="tool-type-toggle">
            <button className={`type-btn ${typeFilter === 'all' ? 'active' : ''}`} onClick={() => setTypeFilter('all')}>All</button>
            <button className={`type-btn ${typeFilter === 'ai' ? 'active' : ''}`} onClick={() => setTypeFilter('ai')}>AI Tools</button>
            <button className={`type-btn ${typeFilter === 'general' ? 'active' : ''}`} onClick={() => setTypeFilter('general')}>Productivity & Research</button>
          </div>
          {isFaculty && (
            <button className="pl-add-btn" onClick={() => openAddModal('ai')}>+ Add Tool</button>
          )}
        </div>

        {filtered.length === 0 ? (
          <div className="tool-empty">
            {tools.length === 0
              ? 'No tools registered yet. Faculty can add tools used at the institution.'
              : 'No tools match your filters.'}
          </div>
        ) : (
          <>
            {/* AI Tools Section */}
            {aiTools.length > 0 && (typeFilter === 'all' || typeFilter === 'ai') && (
              <div className="tool-section">
                {typeFilter === 'all' && <h3 className="tool-section-heading">AI Tools</h3>}
                <div className="tool-grid">
                  {aiTools.map(tool => (
                    <div key={tool.id} className="tool-card" onClick={() => openToolDetail(tool.id)}>
                      <h3 className="tool-name">{tool.name}</h3>
                      {tool.vendor && <div className="tool-vendor">{tool.vendor} &middot; {tool.categoryDisplay}</div>}
                      {tool.description && <p className="tool-description">{tool.description}</p>}
                      <div className="tool-data-flags">
                        {tool.ferpaCompliant && <span className="data-flag good">FERPA Compliant</span>}
                        {tool.hipaaCompliant && <span className="data-flag good">HIPAA Compliant</span>}
                        {!tool.retainsData && <span className="data-flag good">No Data Retention</span>}
                        {tool.retainsData && <span className="data-flag neutral">Data Retained</span>}
                      </div>
                      <div className="tool-card-footer">
                        <span className="tool-view-details">View details &rarr;</span>
                        {isFaculty && (
                          <button className="btn-secondary btn-small" onClick={(e) => { e.stopPropagation(); openEdit(tool); }}>Edit</button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Productivity & Research Tools Section */}
            {generalTools.length > 0 && (typeFilter === 'all' || typeFilter === 'general') && (
              <div className="tool-section">
                {typeFilter === 'all' && <h3 className="tool-section-heading">Productivity & Research Tools</h3>}
                <div className="tool-grid">
                  {generalTools.map(tool => (
                    <div key={tool.id} className="tool-card tool-card-general" onClick={() => openToolDetail(tool.id)}>
                      <h3 className="tool-name">{tool.name}</h3>
                      {tool.vendor && <div className="tool-vendor">{tool.vendor} &middot; {tool.categoryDisplay}</div>}
                      {tool.description && <p className="tool-description">{tool.description}</p>}
                      {tool.websiteUrl && (
                        <a
                          className="tool-website-link"
                          href={tool.websiteUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Visit website &rarr;
                        </a>
                      )}
                      <div className="tool-card-footer">
                        <span className="tool-view-details">View details &rarr;</span>
                        {isFaculty && (
                          <button className="btn-secondary btn-small" onClick={(e) => { e.stopPropagation(); openEdit(tool); }}>Edit</button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingTool ? 'Edit Tool' : 'Add New Tool'}</h2>

            {!editingTool && (
              <div className="form-group">
                <label>Tool Type *</label>
                <div className="tool-type-toggle compact">
                  <button
                    type="button"
                    className={`type-btn ${formData.tool_type === 'ai' ? 'active' : ''}`}
                    onClick={() => setFormData({ ...formData, tool_type: 'ai', category: '' })}
                  >AI Tool</button>
                  <button
                    type="button"
                    className={`type-btn ${formData.tool_type === 'general' ? 'active' : ''}`}
                    onClick={() => setFormData({ ...formData, tool_type: 'general', category: '' })}
                  >Productivity & Research</button>
                </div>
              </div>
            )}

            <div className="form-group">
              <label>Tool Name *</label>
              <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="e.g., ChatGPT, Qualtrics" />
            </div>
            <div className="form-group">
              <label>Vendor</label>
              <input type="text" value={formData.vendor} onChange={(e) => setFormData({ ...formData, vendor: e.target.value })} placeholder="e.g., OpenAI, IBM" />
            </div>
            <div className="form-group">
              <label>Category *</label>
              <select value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value })}>
                <option value="">Select category...</option>
                {currentCategories.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            {formData.tool_type === 'general' && (
              <div className="form-group">
                <label>Website URL</label>
                <input type="url" value={formData.website_url} onChange={(e) => setFormData({ ...formData, website_url: e.target.value })} placeholder="https://..." />
              </div>
            )}
            <div className="form-group">
              <label>Description</label>
              <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} placeholder="What does this tool do?" rows={2} />
            </div>
            <div className="form-group">
              <label>{formData.tool_type === 'ai' ? 'Risk Notes' : 'Notes'}</label>
              <textarea value={formData.risk_notes} onChange={(e) => setFormData({ ...formData, risk_notes: e.target.value })} placeholder={formData.tool_type === 'ai' ? 'Any data privacy or compliance concerns...' : 'Any tips or notes about using this tool...'} rows={2} />
            </div>

            {error && <p className="error-text">{error}</p>}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleSave} disabled={!formData.name.trim() || !formData.category || saving}>
                {saving ? 'Saving...' : editingTool ? 'Update Tool' : 'Add Tool'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tool Detail Modal */}
      {selectedTool && (
        <div className="modal-overlay" onClick={() => setSelectedTool(null)}>
          <div className="modal modal-wide td-modal" onClick={(e) => e.stopPropagation()}>

            {/* Header */}
            <div className="td-header">
              <h2 className="td-title">{selectedTool.name}</h2>
              <p className="td-meta">
                {selectedTool.vendor}
                {selectedTool.categoryDisplay && <> &middot; {selectedTool.categoryDisplay}</>}
                {selectedTool.websiteUrl && (
                  <> &middot; <a href={selectedTool.websiteUrl} target="_blank" rel="noopener noreferrer">Website</a></>
                )}
              </p>
            </div>

            {selectedTool.description && <p className="td-desc">{selectedTool.description}</p>}

            {/* Data & Privacy — simple table */}
            <div className="td-section">
              <h3 className="td-section-title">Data & Privacy</h3>
              <table className="td-info-table">
                <tbody>
                  <tr>
                    <td className="td-label">FERPA compliant</td>
                    <td className="td-value">{selectedTool.ferpaCompliant ? 'Yes' : 'No'}</td>
                  </tr>
                  <tr>
                    <td className="td-label">HIPAA compliant</td>
                    <td className="td-value">{selectedTool.hipaaCompliant ? 'Yes' : 'No'}</td>
                  </tr>
                  <tr>
                    <td className="td-label">Retains user data</td>
                    <td className="td-value">{selectedTool.retainsData ? 'Yes' : 'No'}</td>
                  </tr>
                  <tr>
                    <td className="td-label">Sends data to third parties</td>
                    <td className="td-value">{selectedTool.sendsToThirdParty ? 'Yes' : 'No'}</td>
                  </tr>
                  <tr>
                    <td className="td-label">Enterprise/institutional plan</td>
                    <td className="td-value">{selectedTool.hasEnterprisePlan ? 'Available' : 'Not available'}</td>
                  </tr>
                </tbody>
              </table>
              {selectedTool.dataRetentionDetails && (
                <p className="td-note">{selectedTool.dataRetentionDetails}</p>
              )}
              {selectedTool.riskNotes && (
                <p className="td-note td-note-warn">{selectedTool.riskNotes}</p>
              )}
            </div>

            {/* Usage Guidelines */}
            {selectedTool.complianceGuidance && Object.keys(selectedTool.complianceGuidance).length > 0 && (
              <div className="td-section">
                <h3 className="td-section-title">Usage Guidelines</h3>
                <dl className="td-guidelines">
                  {Object.entries(selectedTool.complianceGuidance).map(([useCase, guidance]) => (
                    <div key={useCase} className="td-guideline-row">
                      <dt>{useCase.replace(/_/g, ' ')}</dt>
                      <dd>{guidance}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}

            {/* Institutional Usage */}
            {selectedTool.activityHistory && selectedTool.activityHistory.length > 0 && (
              <div className="td-section">
                <h3 className="td-section-title">Institutional Usage ({selectedTool.activityHistory.length})</h3>
                <table className="td-usage-table">
                  <thead>
                    <tr>
                      <th>Activity</th>
                      <th>Owner</th>
                      <th>Use Case</th>
                      <th>Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedTool.activityHistory.map(a => (
                      <tr key={a.id}>
                        <td>{a.name}</td>
                        <td>{a.owner}</td>
                        <td>{a.aiUseCase.replace(/_/g, ' ')}</td>
                        <td>{a.compliancePct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setSelectedTool(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AIToolRegistry;
