-- SQLite Schema for Marking Engine
-- Enable foreign key constraints (SQLite default is OFF)
PRAGMA foreign_keys = ON;

-- Reference Tables

CREATE TABLE exam_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_board TEXT NOT NULL,
    exam_level TEXT NOT NULL,
    subject TEXT NOT NULL,
    paper_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exam_board, exam_level, subject, paper_code)
);

CREATE TABLE mark_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_type_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_type_id) REFERENCES exam_types(id) ON DELETE CASCADE,
    UNIQUE (exam_type_id, code)
);

CREATE TABLE llm_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_identifier TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    provider TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student submissions (created before marking)
CREATE TABLE question_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    submission_uuid TEXT NOT NULL UNIQUE,
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_submissions_student_question
ON question_submissions(student_id, question_id, submitted_at DESC);

-- Core Tables

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supabase_uid TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_supabase_uid ON students(supabase_uid);

CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_type_id INTEGER NOT NULL,
    exam_date DATE,
    total_marks INTEGER NOT NULL,
    exam_identifier TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_type_id) REFERENCES exam_types(id) ON DELETE CASCADE,
    UNIQUE (exam_type_id, exam_date),
    CHECK (total_marks > 0)
);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    total_marks INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    UNIQUE (paper_id, question_number),
    CHECK (total_marks > 0)
);

CREATE TABLE question_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    part_letter TEXT,
    sub_part_letter TEXT,
    display_order INTEGER NOT NULL,
    expected_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE (question_id, display_order),
    UNIQUE (question_id, part_letter, sub_part_letter)
);

CREATE TABLE question_content_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_part_id INTEGER NOT NULL,
    block_type TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    content_text TEXT,
    diagram_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_part_id) REFERENCES question_parts(id) ON DELETE CASCADE,
    UNIQUE (question_part_id, display_order),
    CHECK (block_type IN ('text', 'diagram')),
    CHECK (
        (block_type = 'text' AND content_text IS NOT NULL
            AND diagram_description IS NULL)
        OR
        (block_type = 'diagram' AND content_text IS NULL
            AND diagram_description IS NOT NULL)
    )
);

CREATE TABLE mark_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    question_part_id INTEGER NOT NULL,
    mark_type_id INTEGER NOT NULL,
    marks_available INTEGER NOT NULL,
    criterion_index INTEGER NOT NULL,
    depends_on_criterion_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_part_id) REFERENCES question_parts(id) ON DELETE CASCADE,
    FOREIGN KEY (mark_type_id) REFERENCES mark_types(id) ON DELETE RESTRICT,
    UNIQUE (question_id, criterion_index),
    CHECK (marks_available >= 0),
    CHECK (criterion_index >= 0),
    CHECK (depends_on_criterion_index IS NULL OR depends_on_criterion_index < criterion_index)
);

CREATE TABLE mark_criteria_content_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mark_criteria_id INTEGER NOT NULL,
    block_type TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    content_text TEXT,
    diagram_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mark_criteria_id) REFERENCES mark_criteria(id) ON DELETE CASCADE,
    UNIQUE (mark_criteria_id, display_order),
    CHECK (block_type IN ('text', 'diagram')),
    CHECK (
        (block_type = 'text' AND content_text IS NOT NULL
            AND diagram_description IS NULL)
        OR
        (block_type = 'diagram' AND content_text IS NULL
            AND diagram_description IS NOT NULL)
    )
);

-- Images linked to submission (before marking)
CREATE TABLE submission_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES question_submissions(id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    image_sequence INTEGER NOT NULL CHECK (image_sequence > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (submission_id, image_sequence)
);

CREATE INDEX idx_submission_images_submission ON submission_images(submission_id);

-- Index for artifact extraction by first image path
CREATE INDEX idx_submission_images_path_sequence
ON submission_images(image_path, image_sequence);

-- Marking attempts (all attempts - successful or failed)
CREATE TABLE marking_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES question_submissions(id) ON DELETE CASCADE,
    llm_model_id INTEGER NOT NULL REFERENCES llm_models(id) ON DELETE RESTRICT,
    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Always populated
    processing_time_ms INTEGER,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    raw_response TEXT,
    system_prompt TEXT NOT NULL,
    user_prompt TEXT NOT NULL,

    -- Result status
    status TEXT NOT NULL CHECK (status IN ('success', 'parse_error', 'rate_limit', 'timeout', 'llm_error')),

    -- Populated based on status
    error_message TEXT,
    response_received TEXT,

    -- Constraint: Must have EITHER error OR response
    CHECK (
        (status = 'success' AND response_received IS NOT NULL AND error_message IS NULL)
        OR
        (status != 'success' AND response_received IS NULL AND error_message IS NOT NULL)
    ),

    CHECK (processing_time_ms >= 0),
    CHECK (input_tokens >= 0),
    CHECK (output_tokens >= 0)
);

CREATE INDEX idx_attempts_submission ON marking_attempts(submission_id, attempted_at DESC);
CREATE INDEX idx_attempts_failures ON marking_attempts(status) WHERE status != 'success';

CREATE TABLE question_marking_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marking_attempt_id INTEGER NOT NULL REFERENCES marking_attempts(id) ON DELETE CASCADE,
    mark_criteria_id INTEGER NOT NULL,
    marks_awarded INTEGER NOT NULL,
    observation TEXT,
    feedback TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    FOREIGN KEY (mark_criteria_id) REFERENCES mark_criteria(id) ON DELETE RESTRICT,
    CHECK (marks_awarded >= 0),
    CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

-- Indexes

CREATE INDEX idx_exam_types_lookup ON exam_types(exam_board, exam_level, subject, paper_code);
CREATE INDEX idx_mark_types_exam_type ON mark_types(exam_type_id);
CREATE INDEX idx_mark_types_code ON mark_types(exam_type_id, code);
CREATE INDEX idx_llm_models_identifier ON llm_models(model_identifier);

CREATE INDEX idx_papers_exam_type ON papers(exam_type_id);

CREATE INDEX idx_marking_results_attempt ON question_marking_results(marking_attempt_id);
CREATE INDEX idx_qmr_criteria ON question_marking_results(mark_criteria_id);

CREATE INDEX idx_criteria_question_index ON mark_criteria(question_id, criterion_index);
CREATE INDEX idx_criteria_mark_type ON mark_criteria(mark_type_id);
CREATE INDEX idx_criteria_part ON mark_criteria(question_part_id);

CREATE INDEX idx_questions_paper ON questions(paper_id);

CREATE INDEX idx_question_parts_question ON question_parts(question_id, display_order);

CREATE INDEX idx_content_blocks_part ON question_content_blocks(question_part_id, display_order);

CREATE INDEX idx_criteria_content_blocks_criteria ON mark_criteria_content_blocks(mark_criteria_id, display_order);

-- M4: Paper Marking Tables

-- Paper attempts (container for paper sittings)
CREATE TABLE paper_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_uuid TEXT UNIQUE NOT NULL,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE RESTRICT,
    inherited_from_attempt INTEGER REFERENCES paper_attempts(id) ON DELETE SET NULL,
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES students(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (inherited_from_attempt IS NULL OR inherited_from_attempt != id),
    CHECK (submitted_at IS NULL OR submitted_at >= created_at),
    CHECK (completed_at IS NULL OR completed_at >= submitted_at)
);

CREATE UNIQUE INDEX idx_paper_attempts_uuid ON paper_attempts(attempt_uuid);

CREATE INDEX idx_paper_attempts_student_paper
    ON paper_attempts(student_id, paper_id, created_at DESC);

CREATE INDEX idx_paper_attempts_status
    ON paper_attempts(submitted_at, completed_at);

CREATE INDEX idx_paper_attempts_inheritance
    ON paper_attempts(inherited_from_attempt)
    WHERE inherited_from_attempt IS NOT NULL;

CREATE INDEX idx_paper_attempts_deleted
    ON paper_attempts(deleted_at)
    WHERE deleted_at IS NOT NULL;

-- Question attempts (links paper attempts to question submissions)
CREATE TABLE question_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_attempt_id INTEGER NOT NULL REFERENCES paper_attempts(id) ON DELETE CASCADE,
    submission_id INTEGER NOT NULL REFERENCES question_submissions(id) ON DELETE CASCADE,
    inherited_from_attempt INTEGER REFERENCES paper_attempts(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (inherited_from_attempt IS NULL OR inherited_from_attempt != paper_attempt_id)
);

CREATE INDEX idx_question_attempts_paper
    ON question_attempts(paper_attempt_id);

CREATE INDEX idx_question_attempts_submission
    ON question_attempts(submission_id);

CREATE INDEX idx_question_attempts_inheritance
    ON question_attempts(inherited_from_attempt)
    WHERE inherited_from_attempt IS NOT NULL;

-- Paper results (stores calculated grades)
CREATE TABLE paper_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_attempt_id INTEGER NOT NULL UNIQUE REFERENCES paper_attempts(id) ON DELETE CASCADE,
    total_marks_awarded INTEGER NOT NULL,
    total_marks_available INTEGER NOT NULL,
    percentage NUMERIC(5,2) NOT NULL,
    indicative_grade TEXT,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (total_marks_awarded >= 0),
    CHECK (total_marks_available > 0),
    CHECK (total_marks_awarded <= total_marks_available),
    CHECK (percentage >= 0.0 AND percentage <= 100.0),
    CHECK (indicative_grade IS NULL OR LENGTH(indicative_grade) <= 10)
);

CREATE INDEX idx_paper_results_attempt
    ON paper_results(paper_attempt_id);

-- Grade boundaries (notional component grade boundaries per paper)
CREATE TABLE grade_boundaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    grade TEXT NOT NULL,
    min_raw_marks INTEGER NOT NULL,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (min_raw_marks >= 0),
    CHECK (LENGTH(grade) <= 10),

    CONSTRAINT unique_boundary
        UNIQUE (paper_id, grade)
);

CREATE INDEX idx_grade_boundaries_paper
    ON grade_boundaries(paper_id);

-- Practice question attempts (practice context - student controls lifecycle)
CREATE TABLE practice_question_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_uuid TEXT NOT NULL UNIQUE,  -- External identifier (UUID v4, for API)
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    submission_id INTEGER NOT NULL REFERENCES question_submissions(id) ON DELETE CASCADE,
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES students(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_practice_submission UNIQUE (submission_id),
    CHECK (deleted_by IS NULL OR deleted_at IS NOT NULL)
);

CREATE UNIQUE INDEX idx_practice_attempts_uuid
    ON practice_question_attempts(attempt_uuid);

CREATE INDEX idx_practice_attempts_student
    ON practice_question_attempts(student_id, created_at DESC);

CREATE INDEX idx_practice_attempts_submission
    ON practice_question_attempts(submission_id);

CREATE INDEX idx_practice_attempts_deleted
    ON practice_question_attempts(deleted_at)
    WHERE deleted_at IS NOT NULL;

-- Triggers to prevent adjacent diagrams

-- For question content blocks
CREATE TRIGGER prevent_adjacent_diagrams
BEFORE INSERT ON question_content_blocks
BEGIN
    SELECT RAISE(ABORT, 'Cannot insert diagram: previous block is also a diagram. Combine diagrams or add text separator.')
    WHERE NEW.block_type = 'diagram'
    AND EXISTS (
        SELECT 1 FROM question_content_blocks
        WHERE question_part_id = NEW.question_part_id
        AND display_order = NEW.display_order - 1
        AND block_type = 'diagram'
    );
END;

-- For mark criteria content blocks
CREATE TRIGGER prevent_adjacent_diagrams_criteria
BEFORE INSERT ON mark_criteria_content_blocks
BEGIN
    SELECT RAISE(ABORT, 'Cannot insert diagram: previous block is also a diagram. Combine diagrams or add text separator.')
    WHERE NEW.block_type = 'diagram'
    AND EXISTS (
        SELECT 1 FROM mark_criteria_content_blocks
        WHERE mark_criteria_id = NEW.mark_criteria_id
        AND display_order = NEW.display_order - 1
        AND block_type = 'diagram'
    );
END;
