import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { Issue } from '../types';
import GoalSummaryList from '../components/analysis/GoalSummaryList';
import IssueDetail from '../components/analysis/IssueDetail';
import IssueList from '../components/analysis/IssueList';
import TraitDistributionChart from '../components/analysis/TraitDistributionChart';
import AgentRunTimeline from '../components/journey/AgentRunTimeline';
import SankeyDiagram from '../components/journey/SankeyDiagram';
import { useExperiment } from '../hooks/useExperiments';
import { useGoalSummaries, useTraitDistributions } from '../hooks/useGoals';
import { useIssues } from '../hooks/useIssues';
import { useJourneys, useAgentRunSteps } from '../hooks/useJourneys';

type Tab = 'goals' | 'traits' | 'journey';
type JourneySubTab = 'flow' | 'timeline';
type TraitMode = 'trait-centric' | 'single-persona';

interface AnalysisPageProps {
  initialTab?: Tab;
}

const STATUS_COLOR: Record<string, string> = {
  created: 'bg-gray-100 text-gray-600',
  running: 'bg-blue-100 text-blue-700 animate-pulse',
  annotating: 'bg-yellow-100 text-yellow-700 animate-pulse',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
};

export default function AnalysisPage({
  initialTab = 'goals',
}: AnalysisPageProps) {
  const { id = '' } = useParams();
  const [activeTab, setActiveTab] = useState<Tab>(initialTab);
  const [selectedGoal, setSelectedGoal] = useState<string | undefined>();
  const [traitMode, setTraitMode] = useState<TraitMode>('trait-centric');
  const [selectedIssue, setSelectedIssue] = useState<Issue | undefined>();
  const [journeySubTab, setJourneySubTab] = useState<JourneySubTab>('timeline');

  const { data: experiment, isLoading: expLoading } = useExperiment(id);
  const { data: goals, isLoading: goalsLoading } = useGoalSummaries(id);

  // Auto-select the first goal on initial load
  useEffect(() => {
    if (!selectedGoal && goals && goals.length > 0) {
      setSelectedGoal(goals[0].goal);
    }
  }, [goals, selectedGoal]);
  const { data: distributions } = useTraitDistributions(id, selectedGoal ?? '');
  const { data: issues } = useIssues(id, selectedGoal);
  const { data: journeyData } = useJourneys(id);
  const { data: agentRuns } = useAgentRunSteps(id);

  if (expLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  if (!experiment) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">
        Experiment not found.
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'goals', label: 'Goals & Outcomes' },
    { id: 'traits', label: 'Trait Analysis' },
    { id: 'journey', label: 'Agent Journey' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3 mb-3">
            <Link to="/" className="text-sm text-gray-400 hover:text-gray-600">
              ← Experiments
            </Link>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-bold text-gray-900">
                {experiment.name}
              </h1>
              <p className="text-sm text-gray-400 mt-0.5">
                {experiment.targetUrl}
              </p>
            </div>
            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLOR[experiment.status] ?? ''}`}
            >
              {experiment.status}
            </span>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-4 border-b border-transparent">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-gray-50 border border-b-gray-50 border-gray-200 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* ── Goals & Outcomes ─────────────────────────────────────── */}
        {activeTab === 'goals' && (
          <div>
            {goalsLoading ? (
              <div className="text-center py-10 text-gray-400">
                Loading goals…
              </div>
            ) : goals && goals.length > 0 ? (
              <GoalSummaryList
                goals={goals}
                selectedGoal={selectedGoal}
                onSelectGoal={(goal) => {
                  setSelectedGoal(goal);
                  setActiveTab('traits');
                }}
              />
            ) : (
              <div className="text-center py-10 text-gray-400 text-sm">
                {experiment.status === 'completed'
                  ? 'No goal data found.'
                  : 'Waiting for simulation to complete…'}
              </div>
            )}
          </div>
        )}

        {/* ── Trait Analysis ────────────────────────────────────────── */}
        {activeTab === 'traits' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Goal selector + mode toggle */}
            <div className="space-y-4">
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Goal
                </h3>
                <div className="space-y-1">
                  {goals?.map((g) => (
                    <button
                      key={g.goal}
                      onClick={() => setSelectedGoal(g.goal)}
                      className={`w-full text-left text-sm px-3 py-2 rounded-lg transition-colors ${
                        selectedGoal === g.goal
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <span className="line-clamp-2">{g.goal}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  View Mode
                </h3>
                <div className="flex gap-2">
                  {(['trait-centric', 'single-persona'] as const).map((m) => (
                    <button
                      key={m}
                      onClick={() => setTraitMode(m)}
                      className={`flex-1 text-xs px-2 py-1.5 rounded border transition-colors ${
                        traitMode === m
                          ? 'border-blue-600 text-blue-600 bg-blue-50'
                          : 'border-gray-200 text-gray-500 hover:border-gray-300'
                      }`}
                    >
                      {m === 'trait-centric'
                        ? 'Trait Centric'
                        : 'Single Persona'}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Center: Chart */}
            <div className="lg:col-span-2 bg-white border border-gray-200 rounded-xl p-5">
              {distributions && distributions.length > 0 ? (
                <TraitDistributionChart
                  distributions={distributions}
                  mode={traitMode}
                />
              ) : (
                <div className="flex items-center justify-center h-40 text-sm text-gray-400">
                  {selectedGoal
                    ? 'No distribution data.'
                    : 'Select a goal to view trait analysis.'}
                </div>
              )}
            </div>

            {/* Issue list below chart */}
            {issues && issues.length > 0 && (
              <div className="lg:col-span-3 grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                    Issues ({issues.length})
                  </h3>
                  <IssueList
                    issues={issues}
                    experimentId={id}
                    selectedIssueId={selectedIssue?.id}
                    onSelectIssue={setSelectedIssue}
                  />
                </div>
                {selectedIssue && (
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                      Issue Detail
                    </h3>
                    <IssueDetail issue={selectedIssue} experimentId={id} />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Agent Journey ─────────────────────────────────────────── */}
        {activeTab === 'journey' && (
          <div className="space-y-4">
            {/* Sub-tab toggle */}
            <div className="flex gap-2">
              {[
                { id: 'timeline' as const, label: 'Step Timeline' },
                { id: 'flow' as const, label: 'Navigation Flow' },
              ].map((sub) => (
                <button
                  key={sub.id}
                  onClick={() => setJourneySubTab(sub.id)}
                  className={`px-4 py-1.5 text-sm rounded-lg border transition-colors ${
                    journeySubTab === sub.id
                      ? 'border-blue-500 bg-blue-50 text-blue-600 font-medium'
                      : 'border-gray-200 text-gray-500 hover:border-gray-300'
                  }`}
                >
                  {sub.label}
                </button>
              ))}
            </div>

            {journeySubTab === 'flow' && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">
                  Agent Navigation Paths
                </h3>
                <SankeyDiagram data={journeyData} onNodeClick={() => {}} />
              </div>
            )}

            {journeySubTab === 'timeline' && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <AgentRunTimeline runs={agentRuns ?? []} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
