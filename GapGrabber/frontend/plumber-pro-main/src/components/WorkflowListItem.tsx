import { ChevronRight, Users } from "lucide-react";
import { Workflow } from "@/lib/api";
import { StatusPill } from "./StatusPill";
import { Card, CardContent } from "./ui/card";

interface WorkflowListItemProps {
  workflow: Workflow;
  onClick: (workflowId: string) => void;
}

export function WorkflowListItem({ workflow, onClick }: WorkflowListItemProps) {
  const acceptedCount = workflow.candidates.filter((c) => c.status === "accepted").length;
  const totalCount = workflow.candidates.length;

  const getCountText = () => {
    if (workflow.status === "succeeded") {
      return `${acceptedCount} accepted`;
    }
    return `${totalCount} contacted`;
  };

  return (
    <Card
      className="group overflow-hidden transition-all hover:shadow-lg hover:border-border/80 cursor-pointer active:scale-[0.98] duration-300 glass-effect"
      onClick={() => onClick(workflow.id)}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-base font-bold text-foreground flex-1 mr-2">
            {workflow.slotSummary}
          </h3>
          <StatusPill status={workflow.status} />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-sm text-muted-foreground font-medium">
            <Users className="h-4 w-4" />
            <span>{getCountText()}</span>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
        </div>
      </CardContent>
    </Card>
  );
}
