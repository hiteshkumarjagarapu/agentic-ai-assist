import { useCallback, useRef, useState } from 'react';
import api, { API_URL } from '../api/api';

/**
 * Streams /agent/chat (SSE over fetch, since EventSource cannot POST) and parses event types:
 * thinking, tool_start, tool_result, token, session, error, done.
 */
export function useAgentChat(onSession = () => {}) {
  const [messages, setMessages] = useState([]);
  const [thinking, setThinking] = useState(false);
  const [thinkingText, setThinkingText] = useState('');
  const [activeTool, setActiveTool] = useState(null);
  const [streaming, setStreaming] = useState(false);
  const sessionRef = useRef(null);

  const loadSession = useCallback(async (sessionId) => {
    if (sessionRef.current === sessionId) return; // already in sync (e.g. just created)
    sessionRef.current = sessionId;
    if (!sessionId) return setMessages([]);
    try {
      const { data } = await api.get(`/agent/conversations/${sessionId}/messages`);
      setMessages(data.map((m) => ({ role: m.role, content: m.content, tools: m.tools || [] })));
    } catch {
      setMessages([]);
    }
  }, []);

  const updateLast = (fn) =>
    setMessages((prev) => {
      if (!prev.length) return prev;
      const copy = [...prev];
      copy[copy.length - 1] = fn(copy[copy.length - 1]);
      return copy;
    });

  const handleEvent = (evt) => {
    switch (evt.type) {
      case 'session':
        sessionRef.current = evt.session_id;
        onSession(evt.session_id);
        break;
      case 'thinking':
        setThinking(true);
        setThinkingText(evt.content);
        break;
      case 'tool_start':
        setThinking(false);
        setActiveTool({ name: evt.tool, args: evt.args });
        updateLast((m) => ({ ...m, tools: [...m.tools, { name: evt.tool, args: evt.args, result: null }] }));
        break;
      case 'tool_result':
        setActiveTool(null);
        updateLast((m) => {
          const tools = [...m.tools];
          for (let i = tools.length - 1; i >= 0; i--) {
            if (tools[i].name === evt.tool && tools[i].result === null) {
              tools[i] = { ...tools[i], result: evt.result };
              break;
            }
          }
          return { ...m, tools };
        });
        break;
      case 'token':
        setThinking(false);
        updateLast((m) => ({ ...m, content: m.content + evt.content }));
        break;
      case 'error':
        updateLast((m) => ({ ...m, content: m.content + `\n⚠️ ${evt.content}` }));
        break;
      case 'done':
        setStreaming(false);
        setThinking(false);
        setActiveTool(null);
        break;
      default:
    }
  };

  const sendMessage = async (input) => {
    if (!input.trim() || streaming) return;
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: input, tools: [] },
      { role: 'assistant', content: '', tools: [] },
    ]);
    setStreaming(true);
    setThinking(true);
    setThinkingText('Thinking...');
    try {
      const res = await fetch(`${API_URL}/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ message: input, session_id: sessionRef.current }),
      });
      if (res.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
        return;
      }
      if (!res.ok) {
        const detail = (await res.json().catch(() => ({}))).detail || `Request failed (${res.status})`;
        throw new Error(detail);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop();
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data:')) continue;
          try {
            handleEvent(JSON.parse(line.slice(5).trim()));
          } catch {
            /* ignore malformed chunk */
          }
        }
      }
    } catch (e) {
      updateLast((m) => ({ ...m, content: m.content || `⚠️ ${e.message}` }));
    } finally {
      setStreaming(false);
      setThinking(false);
      setActiveTool(null);
    }
  };

  return { messages, thinking, thinkingText, activeTool, streaming, sendMessage, loadSession };
}
