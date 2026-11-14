export default function StreamingText({ text, streaming }) {
  return (
    <span className={`whitespace-pre-wrap break-words ${streaming ? 'typing-cursor' : ''}`}>{text}</span>
  );
}
