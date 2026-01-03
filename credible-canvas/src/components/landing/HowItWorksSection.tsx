import { Upload, Scan, Database, CheckCircle } from "lucide-react";

const steps = [
  {
    icon: Upload,
    step: "01",
    title: "Upload Certificate",
    description: "Upload your certificate in PDF, JPEG, or PNG format through our secure portal.",
  },
  {
    icon: Scan,
    step: "02",
    title: "OCR Extraction",
    description: "Our AI extracts key details like name, roll number, marks, and certificate ID.",
  },
  {
    icon: Database,
    step: "03",
    title: "Database Matching",
    description: "Details are cross-verified against our centralized registry of authentic certificates.",
  },
  {
    icon: CheckCircle,
    step: "04",
    title: "Instant Result",
    description: "Receive immediate verification status with blockchain hash confirmation.",
  },
];

const HowItWorksSection = () => {
  return (
    <section className="py-24 bg-secondary/30">
      <div className="container">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
            How It <span className="gradient-text">Works</span>
          </h2>
          <p className="text-muted-foreground text-lg">
            A simple four-step process to verify any academic certificate in seconds.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((item, index) => (
            <div
              key={item.step}
              className="relative animate-fade-in"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-12 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-accent/50 to-transparent" />
              )}
              
              <div className="relative z-10 text-center">
                <div className="inline-flex items-center justify-center w-24 h-24 rounded-2xl bg-card border border-border shadow-lg mb-6 group hover:border-accent/50 hover:shadow-glow transition-all duration-300">
                  <item.icon className="h-10 w-10 text-accent" />
                </div>
                <div className="absolute top-0 right-1/4 transform translate-x-1/2 -translate-y-1/4">
                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent text-accent-foreground text-sm font-bold">
                    {item.step}
                  </span>
                </div>
                <h3 className="font-display text-xl font-semibold mb-2">
                  {item.title}
                </h3>
                <p className="text-muted-foreground text-sm">
                  {item.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
