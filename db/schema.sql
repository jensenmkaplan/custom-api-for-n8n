-- Enable if you wish to use pgvector instead of JSONB in the future
-- create extension if not exists vector;

-- Documents table stores uploaded file metadata
create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  file_name text not null,
  storage_path text not null,
  public_url text,
  size_bytes bigint,
  num_pages int,
  created_at timestamp with time zone default now()
);

-- Chunks table stores text slices and their embeddings (JSONB for portability)
create table if not exists document_chunks (
  id bigserial primary key,
  doc_id uuid not null references documents(id) on delete cascade,
  page_num int,
  chunk_index int,
  content text not null,
  embedding jsonb not null,
  created_at timestamp with time zone default now()
);

create index if not exists document_chunks_doc_id_idx on document_chunks(doc_id);
create index if not exists document_chunks_created_at_idx on document_chunks(created_at);
