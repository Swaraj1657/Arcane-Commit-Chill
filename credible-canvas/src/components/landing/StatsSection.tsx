const stats = [
  { value: "50+", label: "Partner Institutions" },
  { value: "1.2M+", label: "Certificates Verified" },
  { value: "99.9%", label: "Detection Accuracy" },
  { value: "< 3s", label: "Verification Time" },
];

const StatsSection = () => {
  return (
    <section className="py-16 bg-primary">
      <div className="container">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div
              key={stat.label}
              className="text-center animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <p className="font-display text-4xl md:text-5xl font-bold text-accent mb-2">
                {stat.value}
              </p>
              <p className="text-primary-foreground/70">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
