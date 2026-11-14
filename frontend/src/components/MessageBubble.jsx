import StreamingText from './StreamingText.jsx';
import ToolIndicator from './ToolIndicator.jsx';
import ThinkingStep from './ThinkingStep.jsx';

export default function MessageBubble({ message, isLast, streaming, thinking, thinkingText }) {
  const isUser = message.role === 'user';
  const live = isLast && streaming;
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] space-y-2 ${isUser ? '' : 'w-full max-w-[80%]'}`}>
        {!isUser && message.tools?.map((t, i) => <ToolIndicator key={i} tool={t} />)}
        {!isUser && live && thinking && <ThinkingStep text={thinkingText} />}
        {(isUser || message.content) && (
          <div
            className={`rounded-2xl px-4 py-2 ${
              isUser
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
            }`}
          >
            <StreamingText text={message.content} streaming={live && !isUser} />
          </div>
        )}
      </div>
    </div>
  );
}
