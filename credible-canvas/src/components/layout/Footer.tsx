import { Link } from "react-router-dom";
import { Shield } from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-primary text-primary-foreground py-12">
      <div className="container">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div className="md:col-span-2">
            <Link to="/" className="flex items-center gap-2.5 mb-4">
              <div className="p-2 rounded-xl bg-accent text-accent-foreground">
                <Shield className="h-5 w-5" />
              </div>
              <span className="font-display font-bold text-xl">CertVerify</span>
            </Link>
            <p className="text-primary-foreground/70 max-w-sm">
              Your trusted platform for academic certificate verification. 
              Protecting institutional integrity through blockchain technology.
            </p>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-primary-foreground/70">
              <li><Link to="/" className="hover:text-accent transition-colors">Home</Link></li>
              <li><Link to="/user" className="hover:text-accent transition-colors">Upload Certificate</Link></li>
              <li><Link to="/recruiter" className="hover:text-accent transition-colors">Recruiter Portal</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Contact</h4>
            <ul className="space-y-2 text-primary-foreground/70">
              <li>Higher Education Department</li>
              <li>support@certverify.com</li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-primary-foreground/10 pt-8 text-center text-primary-foreground/50 text-sm">
          <p>© 2024 CertVerify. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
