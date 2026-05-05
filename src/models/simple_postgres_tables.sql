
CREATE TABLE IF NOT EXISTS counters (
    name TEXT PRIMARY KEY,
    seq BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS materials (
    _id BIGINT PRIMARY KEY,
    data JSONB
);

CREATE TABLE IF NOT EXISTS tasks (
    _id BIGINT PRIMARY KEY,
    stimulus_ids JSONB,
    solution_ids JSONB,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS task_collection (
    _id BIGINT PRIMARY KEY,
    task_ids JSONB,
    name TEXT
);

-- Optionally add indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_tasks_metadata ON tasks USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_materials_data ON materials USING gin (data);

