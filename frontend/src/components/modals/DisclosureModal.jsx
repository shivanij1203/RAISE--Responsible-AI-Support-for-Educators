import { useState } from 'react';

function DisclosureModal({ initialText, filename, onClose, onCopied }) {
  const [text, setText] = useState(initialText);

  function handleCopy() {
    navigator.clipboard.writeText(text);
    if (onCopied) onCopied();
  }

  function handleDownload() {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2>Disclosure Statement</h2>
        <p className="modal-subtitle">Auto-generated from your activity data. Edit as needed, then copy.</p>
        <textarea
          className="disclosure-textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={16}
        />
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Close</button>
          <button className="btn-secondary" onClick={handleCopy}>Copy</button>
          <button className="btn-primary" onClick={handleDownload}>Download</button>
        </div>
      </div>
    </div>
  );
}

export default DisclosureModal;
