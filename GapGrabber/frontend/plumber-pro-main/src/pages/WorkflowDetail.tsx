import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, Loader2, Phone, MessageSquare, Clock, ChevronRight } from "lucide-react";
import { getWorkflow, Workflow } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusPill } from "@/components/StatusPill";
import { toast } from "sonner";

export default function WorkflowDetail() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWorkflow();
  }, [workflowId]);

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      if (!workflowId) return;
      const data = await getWorkflow(workflowId);
      setWorkflow(data);
    } catch (error) {
      console.error("Failed to load gap:", error);
      toast.error("Failed to load gap");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <Loader2 className="h-10 w-10 animate-spin text-foreground mb-4" />
        <p className="text-sm text-muted-foreground font-medium">Loading gap...</p>
      </div>
    );
  }

  if (!workflow) {
    return null;
  }

  const acceptedCandidate = workflow.candidates.find((c) => c.status === "accepted");
  const hasAccepted = !!acceptedCandidate;

  const formatTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = Date.now();
    const diffMs = now - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "just now";
    if (diffMins === 1) return "1 minute ago";
    if (diffMins < 60) return `${diffMins} minutes ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return "1 hour ago";
    return `${diffHours} hours ago`;
  };

  const formatTimeUntil = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = Date.now();
    const diffMs = date.getTime() - now;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 0) return "contacting now";
    if (diffMins < 1) return "in less than a minute";
    if (diffMins === 1) return "in 1 minute";
    if (diffMins < 60) return `in ${diffMins} minutes`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return "in 1 hour";
    return `in ${diffHours} hours`;
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="sticky top-0 z-10 glass-effect border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 py-5 flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/workflows")}
            className="rounded-full hover:bg-muted transition-all"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl font-bold text-foreground">
            Gap Details
          </h1>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        <Card className="glass-effect border-border/50">
          <CardHeader className="pb-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-xl mb-2 font-bold">{workflow.slotSummary}</CardTitle>
              </div>
              <StatusPill status={workflow.status} />
            </div>
          </CardHeader>
        </Card>

        {hasAccepted ? (
          <Card className="glass-effect border-success/30 bg-success/5">
            <CardHeader>
              <div className="flex items-start gap-3">
                <div className="p-2 bg-success/10 rounded-full">
                  <CheckCircle2 className="h-6 w-6 text-success" />
                </div>
                <div className="flex-1">
                  <CardTitle className="text-xl text-success mb-2 font-bold">
                    Slot Filled Successfully!
                  </CardTitle>
                  <p className="text-sm text-foreground/80 font-medium">
                    {acceptedCandidate.name} accepted this slot. Other candidates will be
                    notified that it's no longer available.
                  </p>
                </div>
              </div>
            </CardHeader>
          </Card>
        ) : (
          <Card className="glass-effect border-border/50 bg-muted/20">
            <CardHeader>
              <div className="flex items-start gap-3">
                <div className="p-2 bg-muted rounded-full">
                  <Loader2 className="h-6 w-6 text-foreground animate-spin" />
                </div>
                <div className="flex-1">
                  <CardTitle className="text-xl mb-2 font-bold">
                    Filling This Gap
                  </CardTitle>
                  <p className="text-sm text-foreground/80 font-medium">
                    Waiting for replies from contacted people. This may take a few minutes.
                  </p>
                </div>
              </div>
            </CardHeader>
          </Card>
        )}

        <div>
          <h2 className="text-lg font-bold text-foreground mb-4 px-1 flex items-center gap-2">
            Contacted People ({workflow.candidates.length})
          </h2>
          <div className="space-y-3">
            {workflow.candidates.map((candidate) => {
              // Extract customer ID from candidate ID (format: "cand-{id}")
              const customerId = parseInt(candidate.id.replace("cand-", ""));
              const campaignId = parseInt(workflowId!.replace("workflow-", ""));
              
              return (
                <Card 
                  key={candidate.id} 
                  className="overflow-hidden glass-effect border-border/50 cursor-pointer hover:border-border transition-all active:scale-[0.98]"
                  onClick={() => navigate(`/workflow/${workflowId}/customer/${customerId}`)}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                        <h3 className="font-semibold text-foreground">{candidate.name}</h3>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                          <Phone className="h-3.5 w-3.5" />
                          <span>{candidate.phone}</span>
                        </div>
                        {candidate.contactedAt && (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                            <Clock className="h-3 w-3" />
                            <span>Contacted {formatTimeAgo(candidate.contactedAt)}</span>
                          </div>
                        )}
                      </div>
                      <StatusPill status={candidate.status} />
                    </div>

                    <div className="bg-muted/50 rounded-lg p-3 border border-border">
                      <div className="flex items-start gap-2 mb-1.5">
                        <MessageSquare className="h-3.5 w-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
                        <span className="text-xs font-medium text-muted-foreground">
                          Message sent:
                        </span>
                      </div>
                      <p className="text-sm text-foreground pl-5">{candidate.messagePreview}</p>
                    </div>
                    
                    <div className="mt-3 flex items-center justify-end gap-2 text-xs text-muted-foreground">
                      <span>View conversation</span>
                      <ChevronRight className="h-3.5 w-3.5" />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
