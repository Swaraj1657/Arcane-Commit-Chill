-- Enable realtime for certificates table
ALTER TABLE public.certificates REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE public.certificates;