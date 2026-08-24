-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. Profiles Table
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  email text unique,
  allergies text[] default '{}',
  dietary_flags text[] default '{}',
  skin_type text default 'Normal',
  is_pregnant boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Scanned Products History
create table if not exists public.scanned_products (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete set null,
  product_name text not null,
  raw_ingredients text not null,
  safety_score int not null,
  overall_verdict text not null,
  flagged_count int default 0,
  analysis_json jsonb not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.profiles enable row level security;
alter table public.scanned_products enable row level security;

-- RLS Policies
create policy "Users can view and edit own profile"
  on public.profiles for all
  using (auth.uid() = id);

create policy "Users can view and insert own scans"
  on public.scanned_products for all
  using (auth.uid() = user_id or user_id is null);

-- Indexing for fast search
create index if not exists idx_scanned_products_user on public.scanned_products(user_id);
create index if not exists idx_scanned_products_created on public.scanned_products(created_at desc);