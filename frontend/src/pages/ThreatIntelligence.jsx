import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';

const statusLabels = {
  urlhaus_known_malware_url: ['Known threat match', 'high'],
  urlhaus_no_match: ['No record found', 'low'],
  threat_intelligence_unavailable: ['Feed unavailable', 'medium'],
  threat_intelligence_not_configured: ['API key not configured', 'medium'],
  threat_intelligence_not_checked: ['Not checked', 'neutral'],
};

export default function ThreatIntelligence() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/dashboard/threat-intelligence')
      .then((response) => setData(response.data))
      .catch(() => setError('Your threat intelligence summary could not be loaded.'));
  }, []);

  const summary = data?.summary;

  return <>
    <div className="page-head">
      <div>
        <div className="eyebrow"><i /> YOUR PRIVATE THREAT INTELLIGENCE</div>
        <h1>Your link checks, <em>with context.</em></h1>
        <p>Review your own URL checks and see which ones were compared with URLhaus.</p>
      </div>
      <Link className="button" to="/analyze/url">Check a link <span>↗</span></Link>
    </div>

    {error && <div className="error-box" role="alert">{error}</div>}

    <div className="ti-stat-grid">
      <section className="stat-card"><small>YOUR URL CHECKS</small><strong>{summary?.urls_reviewed ?? '—'}</strong><span>Saved to your account</span></section>
      <section className="stat-card"><small>KNOWN THREAT MATCHES</small><strong>{summary?.known_threat_matches ?? '—'}</strong><span>Listed by URLhaus</span></section>
      <section className="stat-card"><small>NO FEED MATCH</small><strong>{summary?.no_feed_match ?? '—'}</strong><span>No URLhaus record returned</span></section>
      <section className="stat-card"><small>NOT CHECKED / UNAVAILABLE</small><strong>{summary ? summary.not_checked + summary.lookup_unavailable : '—'}</strong><span>No completed feed result</span></section>
    </div>

    <section className="panel ti-history-panel">
      <div className="panel-head"><div><small>YOUR RECENT RESULTS</small><h2>URLhaus lookup history</h2></div><span className="subtle">Source: URLhaus</span></div>
      {!data ? <div className="empty-row">Loading your checks…</div> : data.recent_checks.length ? <div className="ti-check-list">
        {data.recent_checks.map((check) => {
          const [label, tone] = statusLabels[check.intel_status] || ['Not checked', 'neutral'];
          return <Link className="ti-check-row" to={`/analysis/${check.analysis_id}`} key={check.analysis_id}>
            <span className="ti-check-copy"><b>{check.threat_type}</b><small>{new Date(check.created_at).toLocaleString()}</small></span>
            <span className={`ti-status ${tone}`}>{label}</span>
            <span className="row-arrow">↗</span>
          </Link>;
        })}
      </div> : <div className="empty-row">You have no saved URL checks yet. Start with <Link className="text-link" to="/analyze/url">Check a link ↗</Link></div>}
    </section>

    <section className="ti-note">
      <b>How to read these results</b>
      <p>A match means URLhaus has a record for the URL as a malware-distribution link. “No record found” means only that URLhaus returned no match. New or unreported threats may be missing, so a feed miss does not prove a link is safe. These counts and checks belong to your account only.</p>
    </section>
  </>;
}
