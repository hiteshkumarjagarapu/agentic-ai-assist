const STYLES = {
  web_search: 'border-blue-300 bg-blue-50 text-blue-900 dark:border-blue-700 dark:bg-blue-950 dark:text-blue-100',
  get_weather: 'border-orange-300 bg-orange-50 text-orange-900 dark:border-orange-700 dark:bg-orange-950 dark:text-orange-100',
  calculate: 'border-green-300 bg-green-50 text-green-900 dark:border-green-700 dark:bg-green-950 dark:text-green-100',
  search_wikipedia: 'border-purple-300 bg-purple-50 text-purple-900 dark:border-purple-700 dark:bg-purple-950 dark:text-purple-100',
  get_datetime: 'border-teal-300 bg-teal-50 text-teal-900 dark:border-teal-700 dark:bg-teal-950 dark:text-teal-100',
};

const LABELS = {
  web_search: 'web search',
  get_weather: 'weather',
  calculate: 'calculator',
  search_wikipedia: 'Wikipedia',
  get_datetime: 'datetime',
};

export default function ToolIndicator({ tool }) {
  const style = STYLES[tool.name] || 'border-gray-300 bg-gray-50 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100';
  const done = tool.result !== null && tool.result !== undefined;
  return (
    <div className={`rounded-lg border px-3 py-2 text-sm transition-all ${style} ${done ? '' : 'animate-pulse'}`}>
      <div className="font-medium">
        🔧 {done ? 'Used' : 'Using'} {LABELS[tool.name] || tool.name} tool{done ? '' : '...'}{' '}
        <code className="ml-1 text-xs opacity-70">{JSON.stringify(tool.args)}</code>
      </div>
      {done && <div className="mt-1 whitespace-pre-wrap break-words text-xs">✅ Result: {tool.result}</div>}
    </div>
  );
}
