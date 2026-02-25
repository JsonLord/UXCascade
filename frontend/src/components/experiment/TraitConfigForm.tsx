import type { TraitConfig } from '../../types';

interface TraitConfigFormProps {
  value: TraitConfig[];
  onChange: (traits: TraitConfig[]) => void;
}

export default function TraitConfigForm({
  value,
  onChange,
}: TraitConfigFormProps) {
  function updateTrait(index: number, patch: Partial<TraitConfig>) {
    onChange(value.map((t, i) => (i === index ? { ...t, ...patch } : t)));
  }

  function addValue(index: number) {
    const trait = value[index];
    onChange(
      value.map((t, i) =>
        i === index ? { ...t, values: [...t.values, ''] } : t
      )
    );
    // suppress unused warning
    void trait;
  }

  function updateValue(traitIndex: number, valueIndex: number, v: string) {
    onChange(
      value.map((t, i) =>
        i === traitIndex
          ? {
              ...t,
              values: t.values.map((val, vi) => (vi === valueIndex ? v : val)),
            }
          : t
      )
    );
  }

  function removeValue(traitIndex: number, valueIndex: number) {
    onChange(
      value.map((t, i) =>
        i === traitIndex
          ? { ...t, values: t.values.filter((_, vi) => vi !== valueIndex) }
          : t
      )
    );
  }

  function addTrait() {
    onChange([...value, { name: '', key: '', values: [''] }]);
  }

  function removeTrait(index: number) {
    onChange(value.filter((_, i) => i !== index));
  }

  function toKey(name: string) {
    return name.toLowerCase().replace(/\s+/g, '_');
  }

  const totalCombinations = value.reduce(
    (acc, t) => acc * Math.max(t.values.filter((v) => v).length, 1),
    1
  );

  return (
    <div className="space-y-3">
      {value.map((trait, ti) => (
        <div
          key={ti}
          className="border border-gray-200 rounded-lg p-4 space-y-3"
        >
          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="Trait name (e.g. Price Sensitivity)"
              value={trait.name}
              onChange={(e) => {
                const name = e.target.value;
                updateTrait(ti, { name, key: toKey(name) });
              }}
              className="flex-1 text-sm border border-gray-200 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => removeTrait(ti)}
              className="text-gray-400 hover:text-red-500 text-sm"
            >
              Remove
            </button>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            {trait.values.map((v, vi) => (
              <div key={vi} className="flex items-center gap-1">
                <input
                  type="text"
                  value={v}
                  placeholder="value"
                  onChange={(e) => updateValue(ti, vi, e.target.value)}
                  className="text-sm border border-gray-200 rounded px-2 py-1 w-28 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {trait.values.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeValue(ti, vi)}
                    className="text-gray-300 hover:text-red-400 text-xs"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => addValue(ti)}
              className="text-xs text-blue-600 hover:underline"
            >
              + value
            </button>
          </div>
        </div>
      ))}

      <button
        type="button"
        onClick={addTrait}
        className="text-sm text-blue-600 hover:underline"
      >
        + Add trait
      </button>

      <p className="text-xs text-gray-500">
        {totalCombinations} trait combination
        {totalCombinations !== 1 ? 's' : ''}
      </p>
    </div>
  );
}
