-- Remove Jharkhand as default state value
ALTER TABLE public.institutions ALTER COLUMN state DROP DEFAULT;