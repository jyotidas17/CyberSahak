import { useEffect, useRef, useState } from 'react';
import api from '../api/client.js';

const SUGGESTIONS = [
  'I shared an OTP. What should I do now?',
  'How can I check if a job offer is genuine?',
  'Help me understand a suspicious bank message.'
];

function PageHead() {
  return <div className="page-head"><div><div className="eyebrow"><i/> CYBERSAHAK AI ASSISTANT</div><h1>Let’s work through it <em>together.</em></h1><p>Ask about a suspicious message, online fraud, account safety, or what to do next.</p></div></div>;
}

export default function AssistantChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [consented, setConsented] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const endOfChat = useRef(null);

  useEffect(() => {
    endOfChat.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, busy]);

  async function send(text = input) {
    const content = text.trim();
    if (!content || !consented || busy) return;
    const userMessage = { role: 'user', content };
    const context = [...messages, userMessage].slice(-21);
    setMessages(previous => [...previous, userMessage]);
    setInput('');
    setError('');
    setBusy(true);
    try {
      const { data } = await api.post('/assistant/chat', {
        messages: context,
        consent_to_gemini: true
      });
      setMessages(previous => [...previous, { role: 'assistant', content: data.reply }]);
    } catch (requestError) {
      setMessages(previous => previous.slice(0, -1));
      setInput(content);
      setError(requestError.response?.data?.message || 'The assistant could not respond. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  function clearChat() {
    setMessages([]);
    setInput('');
    setError('');
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  }

  return <>
    <PageHead />
    <section className="panel assistant-chat-panel">
      <div className="assistant-chat-top"><div><span className="assistant-status-dot"/> CyberSahak safety assistant</div><button className="quiet-link" type="button" onClick={clearChat} disabled={!messages.length || busy}>New chat</button></div>
      <div className="assistant-messages" aria-live="polite" aria-label="Chat messages">
        {!messages.length && <div className="assistant-welcome"><span className="assistant-welcome-mark">C</span><h2>What’s worrying you?</h2><p>Tell me what happened. I can help you understand the risk and choose a safer next step.</p><div className="assistant-suggestions">{SUGGESTIONS.map(item=><button type="button" key={item} disabled={!consented || busy} onClick={()=>send(item)}>{item}<span>↗</span></button>)}</div></div>}
        {messages.map((message, index)=><div className={`chat-message ${message.role}`} key={`${index}-${message.role}`}><span className="chat-message-label">{message.role === 'user' ? 'You' : 'CyberSahak AI'}</span><div className="chat-bubble">{message.content}</div></div>)}
        {busy && <div className="chat-message assistant"><span className="chat-message-label">CyberSahak AI</span><div className="chat-bubble chat-thinking">Thinking through the safest next step…</div></div>}
        <div ref={endOfChat}/>
      </div>
      {error && <div className="error-box chat-error" role="alert">{error}</div>}
      <div className="assistant-composer">
        <textarea rows="3" maxLength="3000" value={input} onChange={event=>setInput(event.target.value)} onKeyDown={handleKeyDown} disabled={!consented || busy} placeholder={consented ? 'Type your question… (Enter to send, Shift+Enter for a new line)' : 'Agree to the sharing notice below to start chatting.'}/>
        <div className="assistant-compose-bottom"><small>{input.length}/3,000</small><button className="button" type="button" disabled={!consented || busy || !input.trim()} onClick={()=>send()}>{busy ? 'Sending…' : 'Send'} <span>↗</span></button></div>
      </div>
      <label className="chat-consent"><input type="checkbox" checked={consented} onChange={event=>setConsented(event.target.checked)} /> I agree that each message and recent chat context will be sent to Google Gemini when I send it.</label>
      <div className="disclaimer chat-privacy-note">CyberSahak keeps this chat only in the current page and does not save it to your account. Google may use requests on the unpaid Gemini tier to improve its products, and human reviewers may process them. Use fictional examples; never share private or sensitive information, including OTPs, passwords, PINs, account numbers, or personal details.</div>
      <div className="disclaimer">This assistant offers general safety guidance, not a verdict or official advice. It cannot file complaints or contact your bank or authorities.</div>
    </section>
  </>;
}
