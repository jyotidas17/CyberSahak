import { useState } from 'react';
import api from '../api/client.js';

export default function AIExplainPanel({ analysisId }) {
  const [consented, setConsented] = useState(false);
  const [busy, setBusy] = useState(false);
  const [explanation, setExplanation] = useState('');
  const [error, setError] = useState('');

  async function explain() {
    setBusy(true);
    setError('');
    setExplanation('');
    try {
      const { data } = await api.post(`/analysis/${analysisId}/explanation`, { share_with_gemini: true });
      setExplanation(data.explanation);
    } catch (requestError) {
      setError(requestError.response?.data?.message || 'The AI explanation could not be generated.');
    } finally {
      setBusy(false);
    }
  }

  return <section className="panel ai-explanation-panel">
    <div className="panel-head"><div><small>OPTIONAL AI EXPLANATION</small><h2>Understand these signals</h2></div></div>
    <p>When you request an explanation, CyberSahak sends this saved analysis and its detected signals to Google Gemini. The response is not saved in CyberSahak.</p>
    <label className="ai-consent"><input type="checkbox" checked={consented} onChange={event => setConsented(event.target.checked)} /> I agree to send this analysis to Google Gemini for an explanation.</label>
    <div className="disclaimer">On the unpaid Gemini tier, Google may use submitted content to improve its products, and human reviewers may process it. Avoid real personal, financial, or confidential information.</div>
    <button className="button" type="button" disabled={!consented || busy} onClick={explain}>{busy ? 'Generating…' : 'Explain with AI'} <span>↗</span></button>
    {error && <div className="error-box" role="alert">{error}</div>}
    {explanation && <div className="ai-explanation-result" aria-live="polite"><strong>AI explanation</strong><p>{explanation}</p><small>AI can make mistakes. Use this as guidance, not proof or official advice.</small></div>}
  </section>;
}
