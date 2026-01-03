import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowRight, Shield } from "lucide-react";

const CTASection = () => {
  return (
    <section className="py-24 relative overflow-hidden">
      <div className="absolute inset-0 hero-gradient opacity-95" />
      <div className="absolute inset-0 pattern-dots" />
      
      <div className="container relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent/20 mb-6">
            <Shield className="h-8 w-8 text-accent" />
          </div>
          
          <h2 className="font-display text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
            Ready to Verify Your
            <span className="block mt-2 gradient-text">Academic Credentials?</span>
          </h2>
          
          <p className="text-lg text-white/70 mb-10 max-w-xl mx-auto">
            Join thousands of institutions and employers who trust CertVerify for authentic certificate verification.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/user">
              <Button variant="hero" size="xl" className="group">
                Start Verification
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/recruiter">
              <Button variant="glass" size="xl">
                Access Recruiter Portal
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
