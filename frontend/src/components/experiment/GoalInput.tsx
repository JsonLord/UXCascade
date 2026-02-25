interface GoalInputProps {
  value: string[];
  onChange: (goals: string[]) => void;
}

export default function GoalInput({ value, onChange }: GoalInputProps) {
  function update(index: number, text: string) {
    onChange(value.map((g, i) => (i === index ? text : g)));
  }

  function add() {
    onChange([...value, '']);
  }

  function remove(index: number) {
    onChange(value.filter((_, i) => i !== index));
  }

  return (
    <div className="space-y-2">
      {value.map((goal, i) => (
        <div key={i} className="flex items-start gap-2">
          <span className="mt-2 text-gray-400 text-sm">○</span>
          <textarea
            value={goal}
            onChange={(e) => update(i, e.target.value)}
            placeholder="Describe a high-level agent goal…"
            rows={2}
            className="flex-1 text-sm border border-gray-200 rounded-md px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {value.length > 1 && (
            <button
              type="button"
              onClick={() => remove(i)}
              className="mt-2 text-gray-300 hover:text-red-400 text-xs"
            >
              ×
            </button>
          )}
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="text-sm text-blue-600 hover:underline"
      >
        + Add goal
      </button>
    </div>
  );
}
