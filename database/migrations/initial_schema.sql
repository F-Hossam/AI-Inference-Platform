BEGIN;

CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email varchar(320) NOT NULL,
    name varchar(120) NOT NULL,
    password_hash varchar(255) NOT NULL,
    role varchar(20) NOT NULL DEFAULT 'user',
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT users_email_not_blank CHECK (btrim(email) <> ''),
    CONSTRAINT users_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT users_password_hash_not_blank CHECK (btrim(password_hash) <> ''),
    CONSTRAINT users_role_valid CHECK (role IN ('tester', 'user'))
);

CREATE UNIQUE INDEX users_email_unique_ci ON users (lower(email));

CREATE TABLE use_cases (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name varchar(120) NOT NULL UNIQUE,
    description text,
    is_ready boolean NOT NULL DEFAULT false
);

CREATE TABLE models (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    use_case_id bigint NOT NULL REFERENCES use_cases(id) ON DELETE RESTRICT,
    name varchar(120) NOT NULL,
    version varchar(100) NOT NULL,
    service_url varchar(500) NOT NULL UNIQUE,
    is_active boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT models_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT models_version_not_blank CHECK (btrim(version) <> ''),
    CONSTRAINT models_service_url_valid CHECK (
        service_url ~ '^https?://[^[:space:]]+$'
    ),
    CONSTRAINT models_name_version_unique UNIQUE (name, version)
);

CREATE INDEX models_use_case_id_idx ON models (use_case_id);

CREATE TABLE inference_requests (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    model_id bigint NOT NULL REFERENCES models(id) ON DELETE RESTRICT,
    requested_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX inference_requests_user_time_idx
    ON inference_requests (user_id, requested_at DESC);

CREATE INDEX inference_requests_model_time_idx
    ON inference_requests (model_id, requested_at DESC);

INSERT INTO use_cases (name, description, is_ready)
VALUES
    (
        'Chat with LLM',
        'Generate conversational responses from a large language model.',
        true
    ),
    (
        'Phishing Email Detection',
        'Classify email or URL content as legitimate or phishing.',
        true
    )
ON CONFLICT (name) DO UPDATE
SET description = EXCLUDED.description,
    is_ready = EXCLUDED.is_ready;

INSERT INTO models (use_case_id, name, version, service_url, is_active)
VALUES
    (
        (SELECT id FROM use_cases WHERE name = 'Chat with LLM'),
        'Mistral 7B Instruct',
        '0.3-GPTQ-4bit',
        'http://vllm-service:5000/v1/chat/completions',
        true
    ),
    (
        (SELECT id FROM use_cases WHERE name = 'Phishing Email Detection'),
        'Phishing Email Detection DistilBERT',
        '2.4.1-ONNX-fp16',
        'http://email-detection-service:6000/predict',
        true
    )
ON CONFLICT (name, version) DO UPDATE
SET use_case_id = EXCLUDED.use_case_id,
    service_url = EXCLUDED.service_url,
    is_active = EXCLUDED.is_active;

COMMIT;
