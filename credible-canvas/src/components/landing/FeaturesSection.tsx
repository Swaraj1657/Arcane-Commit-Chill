import { 
  Scan, 
  Shield, 
  Database, 
  AlertTriangle, 
  Building2, 
  Lock 
} from "lucide-react";

const features = [
  {
    icon: Scan,
    title: "AI-Powered OCR",
    description: "Extract certificate details automatically using advanced optical character recognition technology.",
  },
  {
    icon: Shield,
    title: "Blockchain Verification",
    description: "Immutable hash verification ensures certificates cannot be tampered with or forged.",
  },
  {
    icon: Database,
    title: "Centralized Registry",
    description: "Access a unified database of verified certificates from institutions worldwide.",
  },
  {
    icon: AlertTriangle,
    title: "Fraud Detection",
    description: "Instantly flag anomalies like tampered grades, forged seals, or invalid certificate numbers.",
  },
  {
    icon: Building2,
    title: "Institution Integration",
    description: "Universities can upload and manage their certificate records in bulk or real-time.",
  },
  {
    icon: Lock,
    title: "Data Privacy",
    description: "Secure handling of student information with role-based access controls and encryption.",
  },
];

const FeaturesSection = () => {
  return (
    <section className="py-24 bg-background">
      <div className="container">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
            Comprehensive Verification
            <span className="gradient-text"> Features</span>
          </h2>
          <p className="text-muted-foreground text-lg">
            A complete ecosystem for authenticating academic credentials and protecting institutional integrity.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="group p-6 rounded-2xl bg-card border border-border hover:border-accent/30 hover:shadow-lg hover:shadow-accent/5 transition-all duration-300 animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="p-3 rounded-xl bg-accent/10 w-fit mb-4 group-hover:bg-accent/20 transition-colors">
                <feature.icon className="h-6 w-6 text-accent" />
              </div>
              <h3 className="font-display text-xl font-semibold mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
