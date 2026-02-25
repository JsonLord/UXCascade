import { Link } from 'react-router-dom';
import type { ExperimentStatus } from '../types';
import { useExperiments } from '../hooks/useExperiments';

const STATUS_LABEL: Record<ExperimentStatus, string> = {
  created: 'Created',
  running: 'Running',
  annotating: 'Annotating',
  completed: 'Completed',
  failed: 'Failed',
};

const STATUS_COLOR: Record<ExperimentStatus, string> = {
  created: 'bg-gray-100 text-gray-600',
  running: 'bg-blue-100 text-blue-700',
  annotating: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
};

export default function ExperimentListPage() {
  const { data: experiments, isLoading, isError } = useExperiments();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">UXCascade</h1>
            <p className="text-sm text-gray-500 mt-1">
              Simulated usability analysis
            </p>
          </div>
          <Link
            to="/experiments/new"
            className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + New Experiment
          </Link>
        </div>

        {isLoading && (
          <div className="text-center py-20 text-gray-400">
            Loading experiments…
          </div>
        )}

        {isError && (
          <div className="text-center py-20 text-red-500">
            Failed to load experiments.
          </div>
        )}

        {experiments && experiments.length === 0 && (
          <div className="text-center py-20">
            <p className="text-gray-400 mb-4">No experiments yet.</p>
            <Link
              to="/experiments/new"
              className="text-blue-600 hover:underline text-sm"
            >
              Create your first experiment →
            </Link>
          </div>
        )}

        {experiments && experiments.length > 0 && (
          <div className="space-y-3">
            {experiments.map((exp) => (
              <Link
                key={exp.id}
                to={`/experiments/${exp.id}`}
                className="block bg-white rounded-xl border border-gray-200 px-6 py-4 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-gray-900 truncate">
                        {exp.name}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLOR[exp.status]}`}
                      >
                        {STATUS_LABEL[exp.status]}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1 truncate">
                      {exp.targetUrl}
                    </p>
                  </div>
                  <div className="flex items-center gap-6 text-sm text-gray-500 ml-6 shrink-0">
                    <span>{exp.agentCount ?? 0} agents</span>
                    <span>{new Date(exp.createdAt).toLocaleDateString()}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
