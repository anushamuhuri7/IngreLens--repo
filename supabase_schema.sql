-- Run this SQL in your Supabase SQL Editor (https://supabase.com/dashboard/project/lvdgyqsmnooweyqamyhr/sql/new)

CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS public.health_profiles (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES public.users(id) ON DELETE CASCADE,
    diabetes BOOLEAN DEFAULT FALSE,
    hypertension BOOLEAN DEFAULT FALSE,
    lactose_intolerant BOOLEAN DEFAULT FALSE,
    gluten_allergy BOOLEAN DEFAULT FALSE,
    nut_allergy BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS public.scan_history (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES public.users(id) ON DELETE CASCADE,
    product_name TEXT,
    safety_score FLOAT,
    risk_message TEXT,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.medicine_scans (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES public.users(id) ON DELETE CASCADE,
    medicine_name TEXT,
    batch_number TEXT,
    qr_verified BOOLEAN,
    packaging_score FLOAT,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
