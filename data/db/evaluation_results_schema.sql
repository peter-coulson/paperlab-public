-- SQLite Schema for Evaluation Results Database
-- Enable foreign key constraints (SQLite default is OFF)
PRAGMA foreign_keys = ON;

-- Ground Truth Tables

CREATE TABLE validation_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_suites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_case_json_path TEXT NOT NULL UNIQUE,
  paper_identifier TEXT NOT NULL,
  question_number INTEGER NOT NULL,
  validation_type_id INTEGER NOT NULL,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (validation_type_id) REFERENCES validation_types(id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_question_number_positive CHECK (question_number > 0)
);

CREATE TABLE test_suite_cases (
  test_suite_id INTEGER NOT NULL,
  test_case_id INTEGER NOT NULL,
  PRIMARY KEY (test_suite_id, test_case_id),
  FOREIGN KEY (test_suite_id) REFERENCES test_suites(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE test_case_images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_case_id INTEGER NOT NULL,
  image_path TEXT NOT NULL,
  image_sequence INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE,
  UNIQUE (test_case_id, image_sequence),
  CHECK (image_sequence > 0)
);

CREATE TABLE test_case_marks (
  test_case_id INTEGER NOT NULL,
  criterion_index INTEGER NOT NULL,
  marks_awarded_human INTEGER NOT NULL,
  PRIMARY KEY (test_case_id, criterion_index),
  FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT chk_marks_non_negative CHECK (marks_awarded_human >= 0),
  CONSTRAINT chk_criterion_index_non_negative CHECK (criterion_index >= 0)
);

-- Test Execution Tables

CREATE TABLE test_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_suite_id INTEGER NOT NULL,
  model_identifier TEXT NOT NULL,
  git_commit_hash TEXT NOT NULL,
  run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  notes TEXT,
  FOREIGN KEY (test_suite_id) REFERENCES test_suites(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE test_question_executions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_run_id INTEGER NOT NULL,
  test_case_id INTEGER NOT NULL,
  system_prompt TEXT NOT NULL,
  user_prompt TEXT NOT NULL,
  llm_response TEXT NOT NULL,
  input_tokens INTEGER NOT NULL,
  output_tokens INTEGER NOT NULL,
  response_time_seconds REAL NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (test_run_id) REFERENCES test_runs(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE RESTRICT ON UPDATE CASCADE,
  UNIQUE (test_run_id, test_case_id),
  CONSTRAINT chk_input_tokens_non_negative CHECK (input_tokens >= 0),
  CONSTRAINT chk_output_tokens_non_negative CHECK (output_tokens >= 0),
  CONSTRAINT chk_response_time_non_negative CHECK (response_time_seconds >= 0)
);

CREATE TABLE test_criterion_results (
  test_question_execution_id INTEGER NOT NULL,
  criterion_index INTEGER NOT NULL,
  marks_awarded_predicted INTEGER NOT NULL,
  feedback TEXT NOT NULL,
  confidence_score REAL NOT NULL,
  PRIMARY KEY (test_question_execution_id, criterion_index),
  FOREIGN KEY (test_question_execution_id) REFERENCES test_question_executions(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT chk_predicted_marks_non_negative CHECK (marks_awarded_predicted >= 0),
  CONSTRAINT chk_confidence_range CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
  CONSTRAINT chk_criterion_index_result_non_negative CHECK (criterion_index >= 0)
);

-- Indexes

-- Foreign key indexes (critical for join performance)
CREATE INDEX idx_test_cases_validation_type ON test_cases(validation_type_id);
CREATE INDEX idx_test_suite_cases_suite ON test_suite_cases(test_suite_id);
CREATE INDEX idx_test_suite_cases_case ON test_suite_cases(test_case_id);
CREATE INDEX idx_test_case_images_case ON test_case_images(test_case_id);
CREATE INDEX idx_test_case_marks_case ON test_case_marks(test_case_id);
CREATE INDEX idx_test_runs_suite ON test_runs(test_suite_id);
CREATE INDEX idx_test_executions_run ON test_question_executions(test_run_id);
CREATE INDEX idx_test_executions_case ON test_question_executions(test_case_id);
CREATE INDEX idx_test_criterion_results_execution ON test_criterion_results(test_question_execution_id);

-- Query optimization indexes
CREATE INDEX idx_test_suites_name ON test_suites(name);
CREATE INDEX idx_test_cases_paper ON test_cases(paper_identifier, question_number);
CREATE INDEX idx_test_runs_timestamp ON test_runs(run_timestamp);
CREATE INDEX idx_test_runs_model_identifier ON test_runs(model_identifier);
CREATE INDEX idx_test_runs_commit ON test_runs(git_commit_hash);

-- Test case images indexes
CREATE INDEX idx_test_case_images_lookup ON test_case_images(test_case_id, image_sequence);

-- CRITICAL: Enforce first image uniqueness (prevents correlation collisions)
-- First image (sequence = 1) is the correlation anchor for matching marking responses to test cases
CREATE UNIQUE INDEX idx_test_case_images_first_image
ON test_case_images(image_path)
WHERE image_sequence = 1;  -- ImageSequence.FIRST constant (see src/paperlab/config/constants.py)
