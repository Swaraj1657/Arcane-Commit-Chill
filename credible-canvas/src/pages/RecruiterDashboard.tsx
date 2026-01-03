import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Users,
  Search,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Clock,
  FileText,
  Hash,
  Building2,
  GraduationCap,
  Calendar,
  Loader2,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Certificate {
  id: string;
  user_id: string;
  certificate_type: string;
  title: string;
  certificate_number: string | null;
  roll_number: string | null;
  degree_name: string | null;
  field_of_study: string | null;
  grade: string | null;
  cgpa: number | null;
  issue_date: string | null;
  file_hash: string | null;
  blockchain_hash: string | null;
  status: string;
  ocr_data: any;
  created_at: string;
  institutions?: { name: string } | null;
  profiles?: { full_name: string; email: string } | null;
}

interface StudentWithCertificates {
  id: string;
  full_name: string;
  email: string;
  certificates: Certificate[];
}

const RecruiterDashboard = () => {
  const { user, userRole } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [students, setStudents] = useState<StudentWithCertificates[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCertificate, setSelectedCertificate] = useState<Certificate | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<"success" | "failed" | null>(null);

  useEffect(() => {
    if (!user) {
      navigate("/auth");
      return;
    }
    if (userRole && userRole !== "recruiter") {
      navigate("/student");
      return;
    }
    fetchCertificates();

    // Subscribe to realtime updates for certificates
    const channel = supabase
      .channel("certificates-realtime")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "certificates",
        },
        (payload) => {
          console.log("Certificate change detected:", payload);
          fetchCertificates();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [user, userRole, navigate]);

  const fetchCertificates = async () => {
    try {
      // Fetch certificates with institutions
      const { data: certificatesData, error: certError } = await supabase
        .from("certificates")
        .select(`*, institutions (name)`)
        .order("created_at", { ascending: false });

      if (certError) throw certError;

      // Get unique user IDs and fetch their profiles
      const userIds = [...new Set((certificatesData || []).map((c) => c.user_id))];
      
      const { data: profilesData, error: profilesError } = await supabase
        .from("profiles")
        .select("id, full_name, email")
        .in("id", userIds);

      if (profilesError) throw profilesError;

      // Create a map of profiles by user ID
      const profilesMap = new Map(
        (profilesData || []).map((p) => [p.id, p])
      );

      // Group certificates by student
      const studentMap = new Map<string, StudentWithCertificates>();
      
      (certificatesData || []).forEach((cert: any) => {
        const userId = cert.user_id;
        const profile = profilesMap.get(userId);
        
        if (!studentMap.has(userId)) {
          studentMap.set(userId, {
            id: userId,
            full_name: profile?.full_name || "Unknown",
            email: profile?.email || "",
            certificates: [],
          });
        }
        studentMap.get(userId)!.certificates.push(cert);
      });

      setStudents(Array.from(studentMap.values()));
    } catch (error) {
      console.error("Error fetching certificates:", error);
      toast({
        title: "Error",
        description: "Failed to load certificates",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!selectedCertificate || !user) return;
    
    setIsVerifying(true);
    setVerificationResult(null);

    // Simulate blockchain verification
    await new Promise((resolve) => setTimeout(resolve, 2500));

    const isSuccess = selectedCertificate.status !== "flagged";
    setVerificationResult(isSuccess ? "success" : "failed");
    
    // Record verification
    try {
      await supabase.from("verification_records").insert({
        certificate_id: selectedCertificate.id,
        verified_by: user.id,
        verification_status: isSuccess ? "verified" : "flagged",
        verification_method: "blockchain_hash",
        notes: isSuccess ? "Hash verified successfully" : "Hash mismatch detected",
      });

      // Update certificate status
      await supabase
        .from("certificates")
        .update({ status: isSuccess ? "verified" : "flagged" })
        .eq("id", selectedCertificate.id);

      fetchCertificates();
    } catch (error) {
      console.error("Error recording verification:", error);
    }

    setIsVerifying(false);

    toast({
      title: isSuccess ? "Verification Successful" : "Verification Failed",
      description: isSuccess
        ? "Certificate hash matched with blockchain record."
        : "Certificate hash mismatch detected. Possible forgery.",
      variant: isSuccess ? "default" : "destructive",
    });
  };

  const filteredStudents = students.filter(
    (student) =>
      student.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      student.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      student.certificates.some(
        (cert) =>
          cert.roll_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          cert.title.toLowerCase().includes(searchQuery.toLowerCase())
      )
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "verified":
        return <CheckCircle2 className="h-4 w-4" />;
      case "pending":
        return <Clock className="h-4 w-4" />;
      case "flagged":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const stats = {
    totalStudents: students.length,
    totalCertificates: students.reduce((sum, s) => sum + s.certificates.length, 0),
    verified: students.reduce(
      (sum, s) => sum + s.certificates.filter((c) => c.status === "verified").length,
      0
    ),
    pending: students.reduce(
      (sum, s) => sum + s.certificates.filter((c) => c.status === "pending").length,
      0
    ),
    flagged: students.reduce(
      (sum, s) => sum + s.certificates.filter((c) => c.status === "flagged").length,
      0
    ),
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-10 w-10 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container py-12">
        {/* Page Header */}
        <div className="mb-10 animate-fade-in">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="font-display text-3xl md:text-4xl font-bold mb-2">
                Recruiter Portal
              </h1>
              <p className="text-muted-foreground text-lg">
                Verify student credentials and authenticate certificates
              </p>
            </div>
            <div className="relative max-w-sm w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search students or certificates..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8 animate-slide-up">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-primary/10">
                  <Users className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.totalStudents}</p>
                  <p className="text-sm text-muted-foreground">Students</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-accent/10">
                  <FileText className="h-6 w-6 text-accent" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.totalCertificates}</p>
                  <p className="text-sm text-muted-foreground">Certificates</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-success/10">
                  <CheckCircle2 className="h-6 w-6 text-success" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.verified}</p>
                  <p className="text-sm text-muted-foreground">Verified</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-warning/10">
                  <Clock className="h-6 w-6 text-warning" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.pending}</p>
                  <p className="text-sm text-muted-foreground">Pending</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-danger/10">
                  <AlertTriangle className="h-6 w-6 text-danger" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.flagged}</p>
                  <p className="text-sm text-muted-foreground">Flagged</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Students with Certificates */}
        <Card className="animate-slide-up" style={{ animationDelay: "100ms" }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-accent" />
              Student Records
            </CardTitle>
            <CardDescription>
              Click on a student to view their certificates and verify authenticity
            </CardDescription>
          </CardHeader>
          <CardContent>
            {filteredStudents.length === 0 ? (
              <div className="text-center py-16">
                <Users className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Students Found</h3>
                <p className="text-muted-foreground">
                  {searchQuery ? "Try adjusting your search query" : "No certificates have been submitted yet"}
                </p>
              </div>
            ) : (
              <Accordion type="single" collapsible className="space-y-4">
                {filteredStudents.map((student) => (
                  <AccordionItem
                    key={student.id}
                    value={student.id}
                    className="border rounded-xl px-4 hover:shadow-md transition-shadow"
                  >
                    <AccordionTrigger className="hover:no-underline py-4">
                      <div className="flex items-center gap-4 text-left">
                        <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center shrink-0">
                          <span className="text-lg font-bold text-accent">
                            {student.full_name.charAt(0)}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold">{student.full_name}</p>
                          <p className="text-sm text-muted-foreground">{student.email}</p>
                        </div>
                        <Badge variant="secondary" className="ml-auto mr-2">
                          {student.certificates.length} certificate{student.certificates.length !== 1 ? "s" : ""}
                        </Badge>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4">
                      <div className="space-y-3">
                        {student.certificates.map((cert) => (
                          <div
                            key={cert.id}
                            className="flex items-center justify-between p-4 rounded-xl bg-muted/50 hover:bg-muted cursor-pointer transition-colors"
                            onClick={() => {
                              setSelectedCertificate(cert);
                              setVerificationResult(null);
                            }}
                          >
                            <div className="flex items-center gap-3">
                              <div className="p-2 rounded-lg bg-accent/10">
                                <FileText className="h-5 w-5 text-accent" />
                              </div>
                              <div>
                                <p className="font-medium">{cert.title}</p>
                                <p className="text-sm text-muted-foreground">
                                  {cert.institutions?.name || "Unknown Institution"}
                                  {cert.issue_date && ` • ${new Date(cert.issue_date).getFullYear()}`}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <Badge
                                variant={
                                  cert.status === "verified"
                                    ? "verified"
                                    : cert.status === "pending"
                                    ? "pending"
                                    : "flagged"
                                }
                              >
                                {getStatusIcon(cert.status)}
                                <span className="ml-1 capitalize">{cert.status}</span>
                              </Badge>
                              <ChevronRight className="h-4 w-4 text-muted-foreground" />
                            </div>
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </CardContent>
        </Card>

        {/* Certificate Detail Dialog */}
        <Dialog open={!!selectedCertificate} onOpenChange={() => setSelectedCertificate(null)}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-accent" />
                Certificate Details
              </DialogTitle>
              <DialogDescription>
                Review certificate data and verify blockchain authenticity
              </DialogDescription>
            </DialogHeader>

            {selectedCertificate && (
              <div className="space-y-6 mt-4">
                {/* Certificate Info Header */}
                <div className="flex items-start gap-4 p-4 rounded-xl bg-muted/50">
                  <div className="p-3 rounded-xl bg-accent/20">
                    <FileText className="h-6 w-6 text-accent" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{selectedCertificate.title}</h3>
                    <p className="text-muted-foreground capitalize">
                      {selectedCertificate.certificate_type}
                    </p>
                  </div>
                  <Badge
                    variant={
                      selectedCertificate.status === "verified"
                        ? "verified"
                        : selectedCertificate.status === "pending"
                        ? "pending"
                        : "flagged"
                    }
                  >
                    {getStatusIcon(selectedCertificate.status)}
                    <span className="ml-1 capitalize">{selectedCertificate.status}</span>
                  </Badge>
                </div>

                {/* Certificate Details */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <FileText className="h-4 w-4 text-accent" />
                      Certificate Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-3">
                      {selectedCertificate.roll_number && (
                        <div className="flex justify-between py-2 border-b border-border">
                          <span className="text-muted-foreground">Roll Number</span>
                          <span className="font-medium font-mono">{selectedCertificate.roll_number}</span>
                        </div>
                      )}
                      {selectedCertificate.certificate_number && (
                        <div className="flex justify-between py-2 border-b border-border">
                          <span className="text-muted-foreground">Certificate Number</span>
                          <span className="font-medium font-mono">{selectedCertificate.certificate_number}</span>
                        </div>
                      )}
                      {selectedCertificate.degree_name && (
                        <div className="flex justify-between py-2 border-b border-border">
                          <span className="text-muted-foreground">Degree/Course</span>
                          <span className="font-medium">{selectedCertificate.degree_name}</span>
                        </div>
                      )}
                      {selectedCertificate.field_of_study && (
                        <div className="flex justify-between py-2 border-b border-border">
                          <span className="text-muted-foreground">Field of Study</span>
                          <span className="font-medium">{selectedCertificate.field_of_study}</span>
                        </div>
                      )}
                      {selectedCertificate.grade && (
                        <div className="flex justify-between py-2 border-b border-border">
                          <span className="text-muted-foreground">Grade</span>
                          <span className="font-medium">{selectedCertificate.grade}</span>
                        </div>
                      )}
                      {selectedCertificate.cgpa && (
                        <div className="flex justify-between py-2 border-b border-border">
                          <span className="text-muted-foreground">CGPA</span>
                          <span className="font-medium">{selectedCertificate.cgpa}</span>
                        </div>
                      )}
                      {selectedCertificate.issue_date && (
                        <div className="flex justify-between py-2">
                          <span className="text-muted-foreground">Issue Date</span>
                          <span className="font-medium">
                            {new Date(selectedCertificate.issue_date).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Blockchain Verification */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Hash className="h-4 w-4 text-accent" />
                      Blockchain Verification
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {selectedCertificate.file_hash && (
                      <div className="p-3 rounded-lg bg-muted/50">
                        <p className="text-xs text-muted-foreground mb-1">Certificate Hash</p>
                        <p className="font-mono text-xs break-all">
                          {selectedCertificate.file_hash}
                        </p>
                      </div>
                    )}

                    {verificationResult && (
                      <div
                        className={`p-4 rounded-xl border ${
                          verificationResult === "success"
                            ? "bg-success/5 border-success/20"
                            : "bg-danger/5 border-danger/20"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {verificationResult === "success" ? (
                            <>
                              <CheckCircle2 className="h-5 w-5 text-success" />
                              <span className="font-medium text-success">
                                Blockchain Verified
                              </span>
                            </>
                          ) : (
                            <>
                              <AlertTriangle className="h-5 w-5 text-danger" />
                              <span className="font-medium text-danger">
                                Verification Failed - Possible Forgery
                              </span>
                            </>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-2">
                          {verificationResult === "success"
                            ? "Hash matches the record stored on the blockchain. Certificate is authentic."
                            : "Hash does not match blockchain record. This certificate may be forged or tampered."}
                        </p>
                      </div>
                    )}

                    <Button
                      variant="hero"
                      className="w-full"
                      onClick={handleVerify}
                      disabled={isVerifying}
                    >
                      {isVerifying ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Verifying on Blockchain...
                        </>
                      ) : (
                        <>
                          <Shield className="h-4 w-4" />
                          Authenticate Certificate
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>

                {/* Institution Info */}
                {selectedCertificate.institutions && (
                  <div className="flex items-center gap-3 p-4 rounded-xl border">
                    <Building2 className="h-5 w-5 text-muted-foreground" />
                    <div className="flex-1">
                      <p className="font-medium">{selectedCertificate.institutions.name}</p>
                      <p className="text-sm text-muted-foreground">Issuing Institution</p>
                    </div>
                    {selectedCertificate.issue_date && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        <span>{new Date(selectedCertificate.issue_date).getFullYear()}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </main>
      <Footer />
    </div>
  );
};

export default RecruiterDashboard;
