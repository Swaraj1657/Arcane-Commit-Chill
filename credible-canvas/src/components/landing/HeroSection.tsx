import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Shield, ArrowRight, CheckCircle2, Scan, Lock } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="relative min-h-[90vh] flex items-center overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 hero-gradient" />
      <div className="absolute inset-0 pattern-grid opacity-50" />
      
      {/* Floating elements */}
      <div className="absolute top-20 right-[15%] w-64 h-64 bg-accent/10 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-20 left-[10%] w-80 h-80 bg-accent/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }} />

      <div className="container relative z-10 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="text-center lg:text-left animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/10 text-white/80 text-sm mb-6">
              <Shield className="h-4 w-4 text-accent" />
              <span>Trusted by 50+ Institutions Worldwide</span>
            </div>

            <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
              Secure Certificate
              <span className="block mt-2">
                <span className="gradient-text">Verification</span> System
              </span>
            </h1>

            <p className="text-lg md:text-xl text-white/70 max-w-xl mx-auto lg:mx-0 mb-8">
              Protect academic integrity with blockchain-powered verification. 
              Detect fake degrees instantly using AI-driven OCR and cryptographic validation.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Link to="/user">
                <Button variant="hero" size="xl" className="w-full sm:w-auto group">
                  Upload Certificate
                  <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Link to="/recruiter">
                <Button variant="glass" size="xl" className="w-full sm:w-auto">
                  Recruiter Portal
                </Button>
              </Link>
            </div>

            {/* Trust indicators */}
            <div className="flex flex-wrap gap-6 mt-10 justify-center lg:justify-start text-white/60 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-accent" />
                <span>Blockchain Secured</span>
              </div>
              <div className="flex items-center gap-2">
                <Scan className="h-4 w-4 text-accent" />
                <span>AI-Powered OCR</span>
              </div>
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-accent" />
                <span>End-to-End Encrypted</span>
              </div>
            </div>
          </div>

          {/* Right Content - Illustration */}
          <div className="hidden lg:block relative">
            <div className="relative animate-float">
              {/* Main card */}
              <div className="glass-card rounded-2xl p-6 max-w-sm ml-auto">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2.5 rounded-xl bg-success/20">
                    <CheckCircle2 className="h-6 w-6 text-success" />
                  </div>
                  <div>
                    <p className="font-semibold text-foreground">Certificate Verified</p>
                    <p className="text-sm text-muted-foreground">Hash matched successfully</p>
                  </div>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between py-2 border-b border-border/50">
                    <span className="text-muted-foreground">Student Name</span>
                    <span className="font-medium">Rahul Kumar</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-border/50">
                    <span className="text-muted-foreground">Degree</span>
                    <span className="font-medium">B.Tech CSE</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-border/50">
                    <span className="text-muted-foreground">Institution</span>
                    <span className="font-medium">BIT Mesra</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">Year</span>
                    <span className="font-medium">2024</span>
                  </div>
                </div>
                <div className="mt-4 p-3 rounded-lg bg-success/10 border border-success/20">
                  <p className="text-xs font-mono text-success break-all">
                    0x8a7b...3f2e ✓ Blockchain Verified
                  </p>
                </div>
              </div>

              {/* Floating badge */}
              <div className="absolute -left-8 top-1/2 -translate-y-1/2 glass-card rounded-xl p-4 animate-float" style={{ animationDelay: '1s' }}>
                <div className="flex items-center gap-2">
                  <Shield className="h-8 w-8 text-accent" />
                  <div>
                    <p className="text-xs text-muted-foreground">Verified Today</p>
                    <p className="font-bold text-lg">1,247</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
