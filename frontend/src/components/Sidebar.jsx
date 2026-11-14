import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/api';

export default function Sidebar({ activeId, refreshKey, user, onLogout, dark, onToggleTheme }) {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);

  useEffect(() => {
    api.get('/agent/conversations').then((r) => setItems(r.data)).catch(() => {});
  }, [refreshKey]);

  const remove = async (e, id) => {
    e.stopPropagation();
    await api.delete(`/agent/conversations/${id}`).catch(() => {});
    setItems((prev) => prev.filter((c) => c.id !== id));
    if (id === activeId) navigate('/chat');
  };

  return (
    <aside className="hidden md:flex w-64 flex-col bg-gray-900 text-gray-100">
      <button
        onClick={() => navigate('/chat')}
        className="m-3 rounded-lg border border-gray-600 px-3 py-2 text-left text-sm hover:bg-gray-800"
      >
        + New chat
      </button>
      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        {items.map((c) => (
          <div
            key={c.id}
            onClick={() => navigate(`/chat/${c.id}`)}
            className={`group flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-gray-800 ${
              c.id === activeId ? 'bg-gray-800' : ''
            }`}
          >
            <span className="truncate">{c.title}</span>
            <button onClick={(e) => remove(e, c.id)} className="hidden text-gray-400 hover:text-red-400 group-hover:block">
              ✕
            </button>
          </div>
        ))}
      </div>
      <div className="border-t border-gray-700 p-3 text-sm space-y-2">
        <div className="truncate text-gray-400">{user?.name || user?.email}</div>
        <div className="flex gap-2">
          <button onClick={onToggleTheme} className="flex-1 rounded bg-gray-800 py-1 hover:bg-gray-700">
            {dark ? '☀️ Light' : '🌙 Dark'}
          </button>
          <button onClick={onLogout} className="flex-1 rounded bg-gray-800 py-1 hover:bg-gray-700">
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
}
