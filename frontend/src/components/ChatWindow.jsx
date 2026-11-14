import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble.jsx';

export default function ChatWindow({ messages, streaming, thinking, thinkingText }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking]);

  if (!messages.length) {
    return (
      <div className="flex flex-1 items-center justify-center text-gray-500 dark:text-gray-400">
        <div className="text-center">
          <div className="text-4xl mb-2">🤖</div>
          <p>Ask about the weather, news, math, Wikipedia, or the time anywhere.</p>
        </div>
      </div>
    );
  }
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((m, i) => (
        <MessageBubble
          key={i}
          message={m}
          isLast={i === messages.length - 1}
          streaming={streaming}
          thinking={thinking}
          thinkingText={thinkingText}
        />
      ))}
      <div ref={endRef} />
    </div>
  );
}
