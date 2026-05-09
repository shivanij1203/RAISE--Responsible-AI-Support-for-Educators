import { useState, useEffect } from 'react';
import { fetchCheckpointComments, postCheckpointComment, resolveCheckpointComment } from '../services/api';

function CheckpointComments({ projectId, checkpointId }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    loadComments();
  }, [projectId, checkpointId]);

  async function loadComments() {
    try {
      const data = await fetchCheckpointComments(projectId, checkpointId);
      setComments(data);
    } catch (err) {
      console.error('Failed to load comments', err);
    } finally {
      setLoading(false);
    }
  }

  async function handlePost() {
    if (!newComment.trim()) return;
    setPosting(true);
    try {
      const comment = await postCheckpointComment(projectId, checkpointId, newComment.trim());
      setComments([...comments, comment]);
      setNewComment('');
    } catch (err) {
      console.error('Failed to post comment', err);
    } finally {
      setPosting(false);
    }
  }

  async function handleResolveToggle(commentId, nextResolved) {
    try {
      const updated = await resolveCheckpointComment(projectId, checkpointId, commentId, nextResolved);
      setComments(comments.map((c) => (c.id === commentId ? updated : c)));
    } catch (err) {
      console.error('Failed to update comment', err);
    }
  }

  return (
    <div className="checkpoint-comments">
      <div className="comments-header">Discussion ({comments.length})</div>
      {loading ? (
        <div className="comments-loading">Loading...</div>
      ) : (
        <>
          {comments.length === 0 && (
            <div className="comments-empty">No comments yet. Start the conversation.</div>
          )}
          <div className="comments-thread">
            {comments.map(c => (
              <div key={c.id} className={`comment-item ${c.resolved ? 'comment-resolved' : ''}`}>
                <div className="comment-meta">
                  <span className="comment-author">{c.userName}</span>
                  <span className={`comment-role ${c.userRole === 'faculty' ? 'role-faculty' : 'role-student'}`}>
                    {c.userRole === 'faculty' ? 'Faculty' : 'Student'}
                  </span>
                  <span className="comment-time">
                    {new Date(c.createdAt).toLocaleDateString()} at {new Date(c.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  {c.resolved && (
                    <span className="comment-resolved-tag" title={`Resolved by ${c.resolvedBy || 'a collaborator'}`}>Resolved</span>
                  )}
                  <button
                    className="btn-link comment-resolve-btn"
                    onClick={() => handleResolveToggle(c.id, !c.resolved)}
                  >
                    {c.resolved ? 'Reopen' : 'Mark resolved'}
                  </button>
                </div>
                <div className="comment-text">{c.text}</div>
              </div>
            ))}
          </div>
          <div className="comment-form">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              rows={2}
            />
            <button
              className="btn-primary btn-small"
              onClick={handlePost}
              disabled={!newComment.trim() || posting}
            >
              {posting ? 'Posting...' : 'Post'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default CheckpointComments;
