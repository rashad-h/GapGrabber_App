import { cn } from "@/lib/utils";
import { SlotStatus, WorkflowStatus, CandidateStatus } from "@/lib/api";

type StatusType = SlotStatus | WorkflowStatus | CandidateStatus;

interface StatusPillProps {
  status: StatusType;
  className?: string;
}

export function StatusPill({ status, className }: StatusPillProps) {
  const getStatusStyles = (status: StatusType) => {
    switch (status) {
      case "scheduled":
        return "bg-muted/50 text-foreground/90 border border-border";
      case "cancelled":
        return "bg-warning/20 text-warning border border-warning/40";
      case "filling":
        return "bg-info/20 text-info border border-info/40";
      case "filled":
        return "bg-success/20 text-success border border-success/40";
      case "running":
        return "bg-info/20 text-info border border-info/40";
      case "succeeded":
        return "bg-success/20 text-success border border-success/40";
      case "failed":
        return "bg-destructive/20 text-destructive border border-destructive/40";
      case "pending":
        return "bg-muted/50 text-muted-foreground border border-border";
      case "accepted":
        return "bg-success/20 text-success border border-success/40";
      case "declined":
        return "bg-destructive/20 text-destructive border border-destructive/40";
      case "not_needed":
        return "bg-muted/30 text-muted-foreground/70 border border-border/50";
      default:
        return "bg-muted/50 text-muted-foreground border border-border";
    }
  };

  const getStatusLabel = (status: StatusType) => {
    switch (status) {
      case "not_needed":
        return "Not needed";
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-bold transition-all duration-300",
        getStatusStyles(status),
        className
      )}
    >
      {getStatusLabel(status)}
    </span>
  );
}
