import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { listWorkflows, Workflow } from "@/lib/api";
import { WorkflowListItem } from "@/components/WorkflowListItem";

export default function WorkflowsTab() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      console.log("Loading workflows...");
      const data = await listWorkflows();
      console.log("Workflows loaded:", data);
      setWorkflows(data);
    } catch (error) {
      console.error("Failed to load gaps:", error);
      // Show error to user
      alert(`Failed to load campaigns: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleWorkflowClick = (workflowId: string) => {
    navigate(`/workflow/${workflowId}`);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh]">
        <Loader2 className="h-10 w-10 animate-spin text-foreground mb-4" />
        <p className="text-sm text-muted-foreground font-medium">Loading gaps...</p>
      </div>
    );
  }

  return (
    <div className="pb-20 min-h-screen">
      <div className="sticky top-0 z-10 glass-effect border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-foreground">
            🔄 Gaps
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Track your gap-filling progress</p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {workflows.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-20">✨</div>
            <p className="text-muted-foreground text-lg">No active gaps</p>
          </div>
        ) : (
          workflows.map((workflow) => (
            <WorkflowListItem
              key={workflow.id}
              workflow={workflow}
              onClick={handleWorkflowClick}
            />
          ))
        )}
      </div>
    </div>
  );
}
