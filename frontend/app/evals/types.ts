export interface TestResults {
  created: number;
  duration: number;
  exitcode: number;
  root: string;
  environment: Record<string, unknown>;
  summary: TestSummary;
  collectors: TestCollector[];
  tests: TestCase[];
  warnings?: TestWarning[];
}

export interface TestSummary {
  failed: number;
  passed: number;
  total: number;
  collected: number;
}

export interface TestCollector {
  nodeid: string;
  outcome: string;
  result: TestCollectorResult[];
}

export interface TestCollectorResult {
  nodeid: string;
  type: string;
  lineno?: number;
}

export interface TestCase {
  nodeid: string;
  lineno: number;
  outcome: 'passed' | 'failed';
  keywords: string[];
  setup: TestPhase;
  call: TestPhase;
  teardown: TestPhase;
  agent_test_case: AgentTestCase;
}

export interface TestPhase {
  duration: number;
  outcome: 'passed' | 'failed';
  crash?: TestCrash;
  traceback?: TestTraceback[];
  longrepr?: string;
}

export interface TestCrash {
  path: string;
  lineno: number;
  message: string;
}

export interface TestTraceback {
  path: string;
  lineno: number;
  message: string;
}

export interface TestWarning {
  message: string;
  category: string;
  when: string;
  filename: string;
  lineno: number;
}

export interface AgentTestCase {
  name: string;
  agent: {
    name: string;
    version: string | null;
  };
  prompt_kwargs: Record<string, string>;
  expected_output: ExpectedOutput;
  actual_outputs: ActualOutput[];
  evaluation_config: EvaluationConfig;
  evaluation_result: EvaluationResult;
  session_id?: string | null;
}

export type ExpectedOutput = Record<string, string | number | boolean | undefined>;

export type ActualOutput = Record<string, string | number | boolean | undefined>;

// Pydantic IncEx interface
export type IncEx = string[] | IncExDict;
export interface IncExDict {
  [key: string]: IncEx | boolean;
  [key: number]: IncEx | boolean;
}

export interface EvaluationConfig {
  strict_fields: IncEx;
  llm_fields: IncEx;
  evaluator_model: string;
  run_count: number;
}

export interface EvaluationResult {
  passed: boolean;
  rationale: string;
}
