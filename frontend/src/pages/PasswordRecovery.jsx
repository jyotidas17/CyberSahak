import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';

export default function PasswordRecovery({ reset = false }) {
  const [params] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [message, setMessage] = useState('');
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    if (reset && password !== confirm) {
      setError('The passwords do not match.');
      return;
    }
    if (!reset && password !== confirm) {
      setError('The passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      const response = reset
        ? await api.post('/auth/reset-password', { token: params.get('token'), password })
        : await api.post('/auth/demo-reset-password', { email, password });
      setMessage(response.data.message);
      setPassword('');
      setConfirm('');
      if (!reset) setCompleted(true);
    } catch (requestError) {
      setError(requestError.response?.data?.message || 'The request could not be completed. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return <div className="auth-page">
    <Link to="/" className="brand auth-brand"><span className="brand-mark">C</span><span>cyber<span className="brand-light">sahak</span></span></Link>
    <section className="auth-card">
      <div className="eyebrow"><i /> ACCOUNT RECOVERY</div>
      <h1>{reset ? 'Choose a new password' : 'Forgot your password?'}</h1>
      <p>{reset ? 'Set a new password for your CyberSahak account.' : 'Enter your account email and choose a new password.'}</p>
      {!reset && <div className="disclaimer">Demo recovery: this local project does not verify account ownership. Anyone who knows an account email could change its password. Do not use this flow for real accounts.</div>}
      <form onSubmit={submit}>
        {reset ? <>
          <label>New password<input required type="password" minLength="8" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} /><small>At least 8 characters.</small></label>
          <label>Confirm new password<input required type="password" minLength="8" autoComplete="new-password" value={confirm} onChange={(event) => setConfirm(event.target.value)} /></label>
        </> : <>
          <label>Email address<input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>New password<input required type="password" minLength="8" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} /><small>At least 8 characters.</small></label>
          <label>Confirm new password<input required type="password" minLength="8" autoComplete="new-password" value={confirm} onChange={(event) => setConfirm(event.target.value)} /></label>
        </>}
        {error && <div className="error-box" role="alert">{error}</div>}
        {message && <div className="success-box" role="status">{message}</div>}
        {!completed && <button className="button full" disabled={busy}>{busy ? 'Please wait…' : reset ? 'Reset password' : 'Set new password'}</button>}
      </form>
      <div className="auth-switch"><Link to="/login">Back to sign in</Link></div>
    </section>
  </div>;
}
