import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Upload,
  FileText,
  Shield,
  CheckCircle2,
  Hash,
  Copy,
  AlertTriangle,
  Loader2,
  X,
  Plus,
  GraduationCap,
  Trash2,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Certificate {
  id: string;
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
  institution_id: string | null;
  created_at: string;
  institutions?: { name: string } | null;
}

interface Institution {
  id: string;
  name: string;
}

const StudentDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    title: "",
    certificate_type: "certificate",
    certificate_number: "",
    roll_number: "",
    degree_name: "",
    field_of_study: "",
    grade: "",
    cgpa: "",
    issue_date: "",
    institution_id: "",
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileHash, setFileHash] = useState("");

  useEffect(() => {
    if (!user) {
      navigate("/auth");
      return;
    }
    fetchCertificates();
    fetchInstitutions();
  }, [user, navigate]);

  const fetchCertificates = async () => {
    try {
      const { data, error } = await supabase
        .from("certificates")
        .select(`
          *,
          institutions (name)
        `)
        .eq("user_id", user?.id)
        .order("created_at", { ascending: false });

      if (error) throw error;
      setCertificates(data || []);
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

  const fetchInstitutions = async () => {
    try {
      const { data, error } = await supabase
        .from("institutions")
        .select("id, name")
        .eq("is_verified", true)
        .order("name");

      if (error) throw error;
      setInstitutions(data || []);
    } catch (error) {
      console.error("Error fetching institutions:", error);
    }
  };

  const generateHash = async (file: File): Promise<string> => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const hash = await generateHash(file);
      setFileHash(hash);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setIsUploading(true);
    try {
      const { error } = await supabase.from("certificates").insert({
        user_id: user.id,
        title: formData.title,
        certificate_type: formData.certificate_type as any,
        certificate_number: formData.certificate_number || null,
        roll_number: formData.roll_number || null,
        degree_name: formData.degree_name || null,
        field_of_study: formData.field_of_study || null,
        grade: formData.grade || null,
        cgpa: formData.cgpa ? parseFloat(formData.cgpa) : null,
        issue_date: formData.issue_date || null,
        institution_id: formData.institution_id || null,
        file_hash: fileHash || null,
        status: "pending",
      });

      if (error) throw error;

      toast({
        title: "Certificate Added",
        description: "Your certificate has been submitted for verification.",
      });

      setShowAddDialog(false);
      resetForm();
      fetchCertificates();
    } catch (error) {
      console.error("Error adding certificate:", error);
      toast({
        title: "Error",
        description: "Failed to add certificate. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const { error } = await supabase.from("certificates").delete().eq("id", id);
      if (error) throw error;

      toast({
        title: "Certificate Deleted",
        description: "The certificate has been removed.",
      });
      fetchCertificates();
    } catch (error) {
      console.error("Error deleting certificate:", error);
      toast({
        title: "Error",
        description: "Failed to delete certificate.",
        variant: "destructive",
      });
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      certificate_type: "certificate",
      certificate_number: "",
      roll_number: "",
      degree_name: "",
      field_of_study: "",
      grade: "",
      cgpa: "",
      issue_date: "",
      institution_id: "",
    });
    setSelectedFile(null);
    setFileHash("");
  };

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    toast({
      title: "Copied!",
      description: "Hash copied to clipboard.",
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "verified":
        return <Badge variant="verified"><CheckCircle2 className="h-3 w-3 mr-1" />Verified</Badge>;
      case "pending":
        return <Badge variant="pending"><Loader2 className="h-3 w-3 mr-1" />Pending</Badge>;
      case "flagged":
        return <Badge variant="flagged"><AlertTriangle className="h-3 w-3 mr-1" />Flagged</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const certificateTypes = [
    { value: "degree", label: "Degree" },
    { value: "diploma", label: "Diploma" },
    { value: "certificate", label: "Certificate" },
    { value: "transcript", label: "Transcript" },
    { value: "marksheet", label: "Marksheet" },
    { value: "other", label: "Other" },
  ];

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
        <div className="max-w-5xl mx-auto">
          {/* Page Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-10 animate-fade-in">
            <div>
              <h1 className="font-display text-3xl md:text-4xl font-bold mb-2">
                My Certificates
              </h1>
              <p className="text-muted-foreground text-lg">
                Manage and track your academic credentials
              </p>
            </div>
            <Button variant="hero" onClick={() => setShowAddDialog(true)}>
              <Plus className="h-4 w-4" />
              Add Certificate
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{certificates.length}</p>
                    <p className="text-xs text-muted-foreground">Total</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-success/10">
                    <CheckCircle2 className="h-5 w-5 text-success" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {certificates.filter((c) => c.status === "verified").length}
                    </p>
                    <p className="text-xs text-muted-foreground">Verified</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-warning/10">
                    <Loader2 className="h-5 w-5 text-warning" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {certificates.filter((c) => c.status === "pending").length}
                    </p>
                    <p className="text-xs text-muted-foreground">Pending</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-danger/10">
                    <AlertTriangle className="h-5 w-5 text-danger" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {certificates.filter((c) => c.status === "flagged").length}
                    </p>
                    <p className="text-xs text-muted-foreground">Flagged</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Certificates List */}
          {certificates.length === 0 ? (
            <Card className="text-center py-16">
              <CardContent>
                <GraduationCap className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Certificates Yet</h3>
                <p className="text-muted-foreground mb-6">
                  Add your academic certificates to get them verified
                </p>
                <Button variant="hero" onClick={() => setShowAddDialog(true)}>
                  <Plus className="h-4 w-4" />
                  Add Your First Certificate
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {certificates.map((cert) => (
                <Card key={cert.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className="p-3 rounded-xl bg-accent/10 shrink-0">
                          <FileText className="h-6 w-6 text-accent" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <h3 className="font-semibold text-lg">{cert.title}</h3>
                            {getStatusBadge(cert.status)}
                          </div>
                          <p className="text-muted-foreground text-sm mb-2">
                            {cert.institutions?.name || "Institution not specified"}
                            {cert.issue_date && ` • ${new Date(cert.issue_date).getFullYear()}`}
                          </p>
                          <div className="flex flex-wrap gap-2 text-xs">
                            <Badge variant="secondary" className="capitalize">
                              {cert.certificate_type}
                            </Badge>
                            {cert.degree_name && (
                              <Badge variant="outline">{cert.degree_name}</Badge>
                            )}
                            {cert.cgpa && (
                              <Badge variant="outline">CGPA: {cert.cgpa}</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {cert.file_hash && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => copyHash(cert.file_hash!)}
                          >
                            <Hash className="h-3 w-3" />
                            <span className="hidden sm:inline ml-1">Copy Hash</span>
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(cert.id)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Add Certificate Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-accent" />
              Add New Certificate
            </DialogTitle>
            <DialogDescription>
              Enter the details of your academic certificate
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label htmlFor="title">Certificate Title *</Label>
                <Input
                  id="title"
                  placeholder="e.g., Bachelor of Technology"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="type">Type *</Label>
                  <Select
                    value={formData.certificate_type}
                    onValueChange={(value) => setFormData({ ...formData, certificate_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {certificateTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="institution">Institution</Label>
                  <Select
                    value={formData.institution_id}
                    onValueChange={(value) => setFormData({ ...formData, institution_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select institution" />
                    </SelectTrigger>
                    <SelectContent>
                      {institutions.map((inst) => (
                        <SelectItem key={inst.id} value={inst.id}>
                          {inst.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="roll_number">Roll Number</Label>
                  <Input
                    id="roll_number"
                    placeholder="e.g., 2020BTCS1234"
                    value={formData.roll_number}
                    onChange={(e) => setFormData({ ...formData, roll_number: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="certificate_number">Certificate Number</Label>
                  <Input
                    id="certificate_number"
                    placeholder="e.g., CERT-2024-001"
                    value={formData.certificate_number}
                    onChange={(e) => setFormData({ ...formData, certificate_number: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="degree_name">Degree/Course Name</Label>
                  <Input
                    id="degree_name"
                    placeholder="e.g., Computer Science"
                    value={formData.degree_name}
                    onChange={(e) => setFormData({ ...formData, degree_name: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="field_of_study">Field of Study</Label>
                  <Input
                    id="field_of_study"
                    placeholder="e.g., Engineering"
                    value={formData.field_of_study}
                    onChange={(e) => setFormData({ ...formData, field_of_study: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="grade">Grade</Label>
                  <Input
                    id="grade"
                    placeholder="e.g., First Class"
                    value={formData.grade}
                    onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cgpa">CGPA</Label>
                  <Input
                    id="cgpa"
                    type="number"
                    step="0.01"
                    placeholder="e.g., 8.5"
                    value={formData.cgpa}
                    onChange={(e) => setFormData({ ...formData, cgpa: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="issue_date">Issue Date</Label>
                  <Input
                    id="issue_date"
                    type="date"
                    value={formData.issue_date}
                    onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="file">Certificate File (Optional)</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileChange}
                />
                {fileHash && (
                  <div className="p-3 rounded-lg bg-success/10 border border-success/20">
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-success" />
                      <span className="font-medium text-success">Hash Generated</span>
                    </div>
                    <p className="text-xs font-mono text-muted-foreground mt-1 break-all">
                      {fileHash.slice(0, 32)}...
                    </p>
                  </div>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowAddDialog(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="hero" disabled={isUploading || !formData.title}>
                {isUploading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Adding...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Add Certificate
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Footer />
    </div>
  );
};

export default StudentDashboard;
