import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/** Plain text for user messages; markdown for assistant messages (with typing cursor while streaming). */
export default function StreamingText({ text, streaming, markdown = false }) {
  if (!markdown) {
    return <span className="whitespace-pre-wrap break-words">{text}</span>;
  }
  return (
    <div className={`md break-words ${streaming ? 'typing-cursor' : ''}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{ a: ({ node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" /> }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
