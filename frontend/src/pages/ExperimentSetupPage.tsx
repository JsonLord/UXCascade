import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import type { TraitConfig, Experiment } from '../types';
import GoalInput from '../components/experiment/GoalInput';
import TraitConfigForm from '../components/experiment/TraitConfigForm';
import { useCreateExperiment } from '../hooks/useExperiments';
import { apiClient } from '../lib/api';

const DEFAULT_TRAITS: TraitConfig[] = [
  {
    name: 'Price Sensitivity',
    key: 'price_sensitivity',
    values: ['budget', 'flexible'],
  },
  { name: 'Time Pressure', key: 'time_pressure', values: ['rushed', 'normal'] },
  { name: 'Age Cohort', key: 'age_cohort', values: ['18-34', '55+'] },
  { name: 'User Type', key: 'user_type', values: ['new', 'returning'] },
];

const DEFAULT_GOALS = [
  'Save as much as possible using bundles or coupons',
  'Find a specific item under a price target, compare options, and select one using filters',
];

export default function ExperimentSetupPage() {
  const navigate = useNavigate();
  const createExperiment = useCreateExperiment();

  const [name, setName] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [agentsPerCombination, setAgentsPerCombination] = useState(2);
  const [traits, setTraits] = useState<TraitConfig[]>(DEFAULT_TRAITS);
  const [goals, setGoals] = useState<string[]>(DEFAULT_GOALS);

  const runMutation = useMutation({
    mutationFn: (experimentId: string) =>
      apiClient.post(`/experiments/${experimentId}/run`).then((r) => r.data),
  });

  const totalCombinations = traits.reduce(
    (acc, t) => acc * Math.max(t.values.filter((v) => v).length, 1),
    1
  );
  const totalAgents = totalCombinations * agentsPerCombination;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const exp: Experiment = await createExperiment.mutateAsync({
      name,
      targetUrl,
      agentsPerCombination,
      traits,
      goals: goals.filter((g) => g.trim()),
    });
    await runMutation.mutateAsync(exp.id);
    navigate(`/experiments/${exp.id}`);
  }

  const isSubmitting = createExperiment.isPending || runMutation.isPending;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-6 py-10">
        <div className="mb-8">
          <Link to="/" className="text-sm text-gray-400 hover:text-gray-600">
            ← Back
          </Link>
          <h1 className="text-xl font-bold text-gray-900 mt-4">
            New Experiment
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Configure persona traits and goals, then start the simulation.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Basic info */}
          <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Basic Info
            </h2>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Experiment name
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Cascada Tees — Spring Evaluation"
                className="w-full text-sm border border-gray-200 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Target URL
              </label>
              <input
                type="url"
                required
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full text-sm border border-gray-200 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Agents per trait combination
              </label>
              <select
                value={agentsPerCombination}
                onChange={(e) =>
                  setAgentsPerCombination(Number(e.target.value))
                }
                className="text-sm border border-gray-200 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-1">
                {totalCombinations} combinations × {agentsPerCombination} ={' '}
                <strong>{totalAgents} agents</strong>
              </p>
            </div>
          </section>

          {/* Traits */}
          <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Persona Traits
            </h2>
            <TraitConfigForm value={traits} onChange={setTraits} />
          </section>

          {/* Goals */}
          <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Agent Goals
            </h2>
            <GoalInput value={goals} onChange={setGoals} />
          </section>

          {/* Submit */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-blue-600 text-white text-sm font-medium px-6 py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Starting…' : 'Start Experiment'}
            </button>
          </div>

          {(createExperiment.isError || runMutation.isError) && (
            <p className="text-sm text-red-500 text-right">
              Something went wrong. Please try again.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
