-- Create enum for user roles
CREATE TYPE public.app_role AS ENUM ('student', 'recruiter', 'institution_admin');

-- Create enum for certificate status
CREATE TYPE public.certificate_status AS ENUM ('pending', 'verified', 'flagged', 'rejected');

-- Create enum for certificate type
CREATE TYPE public.certificate_type AS ENUM ('degree', 'diploma', 'certificate', 'transcript', 'marksheet', 'other');

-- Create profiles table
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  phone TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create user_roles table (separate from profiles for security)
CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role app_role NOT NULL DEFAULT 'student',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id, role)
);

-- Create institutions table
CREATE TABLE public.institutions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  code TEXT UNIQUE,
  address TEXT,
  city TEXT,
  state TEXT DEFAULT 'Jharkhand',
  is_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create certificates table (supports multiple per student)
CREATE TABLE public.certificates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  institution_id UUID REFERENCES public.institutions(id),
  certificate_type certificate_type NOT NULL DEFAULT 'certificate',
  title TEXT NOT NULL,
  certificate_number TEXT,
  roll_number TEXT,
  degree_name TEXT,
  field_of_study TEXT,
  grade TEXT,
  cgpa DECIMAL(4,2),
  issue_date DATE,
  expiry_date DATE,
  file_url TEXT,
  file_hash TEXT,
  blockchain_hash TEXT,
  status certificate_status NOT NULL DEFAULT 'pending',
  ocr_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create verification_records table
CREATE TABLE public.verification_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  certificate_id UUID NOT NULL REFERENCES public.certificates(id) ON DELETE CASCADE,
  verified_by UUID NOT NULL REFERENCES auth.users(id),
  verification_status certificate_status NOT NULL,
  verification_method TEXT,
  blockchain_tx_hash TEXT,
  notes TEXT,
  verified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_records ENABLE ROW LEVEL SECURITY;

-- Security definer function to check user role
CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role app_role)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.user_roles
    WHERE user_id = _user_id
      AND role = _role
  )
$$;

-- Function to get user role
CREATE OR REPLACE FUNCTION public.get_user_role(_user_id UUID)
RETURNS app_role
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT role
  FROM public.user_roles
  WHERE user_id = _user_id
  LIMIT 1
$$;

-- Profiles policies
CREATE POLICY "Users can view their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Recruiters can view all profiles"
  ON public.profiles FOR SELECT
  USING (public.has_role(auth.uid(), 'recruiter'));

-- User roles policies
CREATE POLICY "Users can view their own role"
  ON public.user_roles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own role"
  ON public.user_roles FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Institutions policies (public read)
CREATE POLICY "Anyone can view institutions"
  ON public.institutions FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Institution admins can update their institution"
  ON public.institutions FOR UPDATE
  USING (public.has_role(auth.uid(), 'institution_admin'));

-- Certificates policies
CREATE POLICY "Students can view their own certificates"
  ON public.certificates FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Students can insert their own certificates"
  ON public.certificates FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Students can update their own certificates"
  ON public.certificates FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Students can delete their own certificates"
  ON public.certificates FOR DELETE
  USING (auth.uid() = user_id);

CREATE POLICY "Recruiters can view all certificates"
  ON public.certificates FOR SELECT
  USING (public.has_role(auth.uid(), 'recruiter'));

-- Verification records policies
CREATE POLICY "Recruiters can create verification records"
  ON public.verification_records FOR INSERT
  WITH CHECK (public.has_role(auth.uid(), 'recruiter'));

CREATE POLICY "Recruiters can view verification records"
  ON public.verification_records FOR SELECT
  USING (public.has_role(auth.uid(), 'recruiter'));

CREATE POLICY "Certificate owners can view their verification records"
  ON public.verification_records FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.certificates
      WHERE certificates.id = verification_records.certificate_id
      AND certificates.user_id = auth.uid()
    )
  );

-- Function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data ->> 'full_name'
  );
  
  INSERT INTO public.user_roles (user_id, role)
  VALUES (
    NEW.id,
    COALESCE((NEW.raw_user_meta_data ->> 'role')::app_role, 'student')
  );
  
  RETURN NEW;
END;
$$;

-- Trigger for new user signup
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_institutions_updated_at
  BEFORE UPDATE ON public.institutions
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_certificates_updated_at
  BEFORE UPDATE ON public.certificates
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert some sample institutions
INSERT INTO public.institutions (name, code, city, is_verified) VALUES
  ('Birla Institute of Technology, Mesra', 'BITM', 'Ranchi', true),
  ('National Institute of Technology, Jamshedpur', 'NITJSR', 'Jamshedpur', true),
  ('XLRI - Xavier School of Management', 'XLRI', 'Jamshedpur', true),
  ('Birla Institute of Technology, Sindri', 'BITS', 'Dhanbad', true),
  ('RVS College of Engineering', 'RVSCE', 'Jamshedpur', true),
  ('Central University of Jharkhand', 'CUJ', 'Ranchi', true),
  ('Indian School of Mines', 'ISM', 'Dhanbad', true),
  ('Ranchi University', 'RU', 'Ranchi', true);