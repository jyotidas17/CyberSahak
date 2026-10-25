import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

const INDIA_STATES_AND_UTS = [
  'Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh',
  'Chhattisgarh', 'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 'Goa', 'Gujarat', 'Haryana',
  'Himachal Pradesh', 'Jammu and Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep',
  'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry',
  'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
  'West Bengal'
];

function PageHead({ kicker, title, desc }) {
  return <div className="page-head"><div><div className="eyebrow"><i/>{kicker}</div><h1>{title}</h1><p>{desc}</p></div></div>;
}

export default function ReportGuide() {
  const [category, setCategory] = useState('Suspicious message or link');
  const [state, setState] = useState('');
  const [district, setDistrict] = useState('');
  const [date, setDate] = useState('');
  const [details, setDetails] = useState('');
  const [reference, setReference] = useState('');
  const [portalConsent, setPortalConsent] = useState(false);
  const [status, setStatus] = useState('');
  const draft = useMemo(() => [
    'I would like to report a cyber incident.',
    `Incident type: ${category}`,
    state || district ? `Incident location: ${[district, state].filter(Boolean).join(', ')}` : 'Incident location: [add district and state/UT]',
    `When it happened: ${date || '[add date and approximate time]'}`,
    `What happened: ${details.trim() || '[describe what happened in your own words]'}`,
    reference.trim() ? `Transaction/reference ID: ${reference.trim()}` : '',
    '',
    'This draft was prepared with CyberSahak and reviewed by me. I will verify and submit it through the official portal.'
  ].filter(Boolean).join('\n'), [category, date, details, district, reference, state]);

  async function copyDraft() {
    try {
      await navigator.clipboard.writeText(draft);
      setStatus('Draft copied. Review and edit it on the official portal before submitting.');
    } catch {
      setStatus('Copy was unavailable. Select the draft text and copy it manually.');
    }
  }

  function openPortal() {
    if (!portalConsent) return;
    window.open('https://www.cybercrime.gov.in/', '_blank', 'noopener,noreferrer');
    setStatus('Official portal opened. CyberSahak did not send your draft; review and enter the details on the portal yourself.');
  }

  return <>
    <PageHead kicker="USER-CONTROLLED REPORTING" title={<>Prepare a report, <em>your way.</em></>} desc="Organize your notes and location. You review and submit them yourself through the official channel." />
    <div className="report-guide-grid">
      <section className="panel report-draft-panel">
        <div className="panel-head"><div><small>PRIVATE DRAFT</small><h2>What happened?</h2></div></div>
        <label>Incident type<select value={category} onChange={e=>setCategory(e.target.value)}><option>Suspicious message or link</option><option>Online financial fraud</option><option>Account or identity misuse</option><option>Other cyber incident</option></select></label>
        <label>State or Union Territory<select value={state} onChange={e=>setState(e.target.value)}><option value="">Select your state/UT</option>{INDIA_STATES_AND_UTS.map(item=><option key={item}>{item}</option>)}</select><small>Choose the incident or victim location as appropriate on the official portal.</small></label>
        <label>District<input type="text" maxLength="100" placeholder="Enter district" value={district} onChange={e=>setDistrict(e.target.value)}/></label>
        <label>Approximate date and time<input type="datetime-local" value={date} onChange={e=>setDate(e.target.value)}/></label>
        <label>Describe what happened<textarea rows="5" maxLength="2000" placeholder="Explain what you received or did, and what happened next. Do not include passwords, OTPs, PINs, or full card details." value={details} onChange={e=>setDetails(e.target.value)}/><small>{details.length}/2,000 characters</small></label>
        <label>Transaction/reference ID (optional)<input type="text" maxLength="100" placeholder="Only if relevant to a financial incident" value={reference} onChange={e=>setReference(e.target.value)}/><small>Do not enter an OTP, PIN, password, or full card/account number.</small></label>
        <label>Draft for you to review<textarea className="draft-output" rows="9" readOnly value={draft}/></label>
        <div className="report-actions"><button className="button" type="button" onClick={copyDraft}>Copy draft <span>↗</span></button></div>
        <label className="portal-consent"><input type="checkbox" checked={portalConsent} onChange={e=>setPortalConsent(e.target.checked)}/> I reviewed this draft and want to open the official portal. I understand CyberSahak will not submit it for me.</label>
        <div className="report-actions"><button className="button outline" type="button" disabled={!portalConsent} onClick={openPortal}>Open official portal <span>↗</span></button></div>
        {status&&<p className="copy-status" role="status">{status}</p>}
        <div className="disclaimer">Your draft stays in this page unless you copy it. Opening the portal does not transmit your information. You must review, enter, and submit the complaint there.</div>
      </section>
      <aside className="panel report-help-panel">
        <span className="quick-icon">⌑</span><h2>Where to go next</h2>
        <p>The National Cyber Crime Reporting Portal asks the complainant to register with a mobile number and OTP and to select incident details, including state and district. Follow its current instructions and submit the report yourself.</p>
        <a className="official-link" href="https://www.cybercrime.gov.in/Webform/FAQ.aspx" target="_blank" rel="noreferrer">Read the official portal instructions ↗</a>
        {category === 'Online financial fraud' && <div className="helpline-card"><small>IF MONEY WAS LOST</small><b>Call 1930 promptly</b><span>Contact your bank through a number you independently trust as well.</span><a href="tel:1930">Call 1930 ↗</a></div>}
        <div className="report-steps"><b>01 <span>Review every detail</span></b><b>02 <span>Copy your draft if useful</span></b><b>03 <span>Register and submit on the portal</span></b></div>
        <div className="disclaimer">CyberSahak does not file complaints, contact authorities, or receive a government complaint number.</div>
        <Link className="text-link report-back" to="/history">← Back to your saved checks</Link>
      </aside>
    </div>
  </>;
}
