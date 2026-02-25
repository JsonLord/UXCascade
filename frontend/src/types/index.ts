// ─── Experiment ───────────────────────────────────────────────────────────────

export type ExperimentStatus =
  | 'created'
  | 'running'
  | 'annotating'
  | 'completed'
  | 'failed';

export interface TraitConfig {
  name: string; // e.g. "Price Sensitivity"
  key: string; // e.g. "price_sensitivity"
  values: string[]; // e.g. ["budget", "flexible"]
}

export interface Experiment {
  id: string;
  name: string;
  targetUrl: string;
  status: ExperimentStatus;
  traits: TraitConfig[];
  goals: string[];
  agentCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateExperimentInput {
  name: string;
  targetUrl: string;
  agentsPerCombination: number;
  traits: TraitConfig[];
  goals: string[];
}

// ─── Agent / Persona ──────────────────────────────────────────────────────────

export interface Persona {
  id: string;
  traits: Record<string, string>; // { price_sensitivity: "budget", ... }
}

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Action {
  type: 'click' | 'scroll' | 'type' | 'navigate';
  selector: string | null;
  value: string | null;
}

export interface TabMetadata {
  url: string;
  title: string;
}

export interface EventSnapshot {
  agentRunId: string;
  step: number;
  timestamp: string;
  rawHtml: string;
  screenshot: string; // URL to annotated PNG in MinIO
  tabMetadata: TabMetadata;
  reasoning: string;
  prompt: string;
  action: Action;
  actionResult: string;
  errors: string[];
}

export interface AgentRun {
  id: string;
  experimentId: string;
  persona: Persona;
  goal: string;
  status: RunStatus;
  success: boolean | null;
  eventSnapshots: EventSnapshot[];
  createdAt: string;
  completedAt: string | null;
}

// ─── Annotation / Issue ───────────────────────────────────────────────────────

export interface Issue {
  id: string;
  agentRunId: string;
  step: number;
  type: string; // e.g. "scroll_incorrect_area"
  element: string;
  reason: string;
  fix: string;
  uptCodes: string[]; // e.g. ["A1", "C2"]
  uptExplanation: string;
  severity: number; // 0–4 (Nielsen)
}

export interface IssueSnapshot {
  step: number;
  screenshot: string; // URL to annotated PNG in MinIO
  reasoning: string;
  rawHtml: string;
}

export interface IssueWithSnapshot extends Issue {
  snapshot: IssueSnapshot | null;
}

export interface StepAnnotation {
  agentRunId: string;
  step: number;
  tags: string[];
  issues: Issue[];
}

// ─── Goal / Trait summary ──────────────────────────────────────────────────────

export interface TraitDistribution {
  traitKey: string;
  traitValue: string;
  agentCount: number;
  successRate: number;
  issues: Issue[];
}

export interface GoalSummary {
  experimentId: string;
  goal: string;
  agentCount: number;
  successCount: number;
  successRate: number;
  issueCount: number;
  traitDistributions: TraitDistribution[];
}

// ─── Fix / Patch ──────────────────────────────────────────────────────────────

export type PatchAction =
  | 'replace_text'
  | 'set_attribute'
  | 'remove_attribute'
  | 'add_class'
  | 'remove_class'
  | 'insert_before'
  | 'insert_after'
  | 'replace_element'
  | 'remove_element'
  | 'append_child'
  | 'inject_style';

export interface HtmlPatch {
  selector: string;
  action: PatchAction;
  value: string | null;
  name: string | null; // for set_attribute / remove_attribute
  rationale: string;
}

export interface Fix {
  id: string;
  experimentId: string;
  issueId: string;
  instruction: string;
  patches: HtmlPatch[];
  status: 'ok' | 'ambiguous' | 'impossible';
  notes: string;
  createdAt: string;
}

export interface CreateFixInput {
  experimentId: string;
  issueId: string;
  instruction: string;
  snapshotStep: number;
}

// ─── Evaluation ───────────────────────────────────────────────────────────────

export interface EvaluationResult {
  fixId: string;
  agentRunId: string;
  step: number;
  actionChanged: boolean;
  issueResolved: boolean | null;
  summary: string;
  beforeAction: Action;
  afterAction: Action;
  createdAt: string;
}

// ─── Journey ──────────────────────────────────────────────────────────────────

export interface JourneyNode {
  id: string;
  label: string;
}

export interface JourneyLink {
  source: string;
  target: string;
  value: number;
}

export interface JourneyData {
  nodes: JourneyNode[];
  links: JourneyLink[];
}

// ─── Agent Run Steps (Journey Timeline) ───────────────────────────────────────

export interface AgentRunStep {
  step: number;
  screenshot: string; // MinIO URL
  reasoning: string; // think-aloud text
  actionType: string; // click / type / navigate / ...
  actionValue: string | null;
  tabUrl: string;
  tabTitle: string;
}

export interface AgentRunDetail {
  runId: string;
  goal: string;
  personaTraits: Record<string, string>;
  status: string;
  steps: AgentRunStep[];
}

// ─── WebSocket ────────────────────────────────────────────────────────────────

export interface SimulationEvent {
  experimentId: string;
  status: ExperimentStatus;
  completedAgents: number;
  totalAgents: number;
}
