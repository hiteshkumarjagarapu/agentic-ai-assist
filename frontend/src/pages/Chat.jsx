import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ChatWindow from '../components/ChatWindow.jsx';
import Sidebar from '../components/Sidebar.jsx';
import { useAgentChat } from '../hooks/useAgentChat';
import { useAuth } from '../hooks/useAuth';

export default function Chat() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [input, setInput] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const [dark, setDark] = useState(document.documentElement.classList.contains('dark'));

  const { messages, thinking, thinkingText, streaming, sendMessage, loadSession } = useAgentChat((id) =>
    navigate(`/chat/${id}`, { replace: true })
  );

  useEffect(() => {
    loadSession(sessionId || null);
  }, [sessionId, loadSession]);

  useEffect(() => {
    if (!streaming) setRefreshKey((k) => k + 1);
  }, [streaming]);

  const toggleTheme = () => {
    const next = !dark;
    document.documentElement.classList.toggle('dark', next);
    localStorage.setItem('theme', next ? 'dark' : 'light');
    setDark(next);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const submit = (e) => {
    e.preventDefault();
    const text = input;
    setInput('');
    sendMessage(text);
  };

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900">
      <Sidebar
        activeId={sessionId}
        refreshKey={refreshKey}
        user={user}
        onLogout={handleLogout}
        dark={dark}
        onToggleTheme={toggleTheme}
      />
      <main className="flex flex-1 flex-col">
        <ChatWindow messages={messages} streaming={streaming} thinking={thinking} thinkingText={thinkingText} />
        <form onSubmit={submit} className="border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="mx-auto flex max-w-3xl gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Message the assistant..."
              className="flex-1 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              disabled={streaming || !input.trim()}
              className="rounded-xl bg-blue-600 px-5 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
