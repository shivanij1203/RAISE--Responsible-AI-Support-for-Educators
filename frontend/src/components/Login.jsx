import { useState } from 'react';
import { loginUser, registerUser } from '../services/api';

function Login({ onLogin, onBack, prefillDemo = false }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState(prefillDemo ? 'demo.faculty@usf.edu' : '');
  const [password, setPassword] = useState(prefillDemo ? 'TestPass123' : '');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('faculty');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (isRegister && !email.toLowerCase().endsWith('@usf.edu')) {
      setError('Registration is restricted to USF email addresses (@usf.edu).');
      return;
    }

    setLoading(true);

    try {
      let data;
      if (isRegister) {
        data = await registerUser(email, password, fullName, role);
      } else {
        data = await loginUser(email, password);
      }
      onLogin(data.user);
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      {/* Green header */}
      <header className="lp-header">
        <div className="lp-header-inner">
          <div className="lp-header-brand">
            <img src="/usf-logo.svg" alt="USF" className="lp-header-logo" />
            <div className="lp-header-text">
              <span className="lp-header-uni">University of South Florida</span>
              <span className="lp-header-app">RAISE Ethics Toolkit</span>
            </div>
          </div>
          {onBack && (
            <button className="lp-signin-btn" onClick={onBack}>Back to Home</button>
          )}
        </div>
      </header>
      <div className="lp-accent-bar"></div>

      {/* Login form */}
      <div className="login-body">
        <div className="login-form-card">
          <h1 className="login-heading">{isRegister ? 'Create Account' : 'Sign In'}</h1>
          <p className="login-subtext">
            {isRegister
              ? 'Register with your USF email address to get started.'
              : 'Sign in with your USF account to continue.'}
          </p>

          <form onSubmit={handleSubmit}>
            {isRegister && (
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  placeholder="Your full name"
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@usf.edu"
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                required
              />
            </div>

            {isRegister && (
              <div className="form-group">
                <label>Role</label>
                <select value={role} onChange={e => setRole(e.target.value)}>
                  <option value="faculty">Faculty / PI</option>
                  <option value="student">Student</option>
                </select>
              </div>
            )}

            {error && <p className="error-text">{error}</p>}

            <button type="submit" className="btn-primary login-submit" disabled={loading}>
              {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
            </button>

            {isRegister && (
              <p className="login-consent">
                By creating an account, you agree that anonymized aggregate stats (such as which tools
                are used, how many activities are registered, and overall checkpoint pass rates) may
                contribute to ongoing research at the USF Behavioral AI Research Lab on responsible AI
                use in higher education. Your individual activity descriptions stay private by default;
                you can choose to share any specific activity as an anonymized example for other faculty
                from the activity itself.
              </p>
            )}
          </form>

          <p className="login-switch">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}
            {' '}
            <button className="btn-text" onClick={() => { setIsRegister(!isRegister); setError(''); }}>
              {isRegister ? 'Sign In' : 'Register'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
