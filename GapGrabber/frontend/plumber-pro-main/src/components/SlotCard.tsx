import { Clock, MapPin, User } from "lucide-react";
import { Slot } from "@/lib/api";
import { Card, CardContent } from "./ui/card";

interface SlotCardProps {
  slot: Slot;
  onCancel: (slotId: string) => void;
}

export function SlotCard({ slot, onCancel }: SlotCardProps) {
  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-GB", {
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatEndTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Card className="group overflow-hidden transition-all hover:shadow-lg hover:border-border/80 duration-300 glass-effect">
      <CardContent className="p-5">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground mb-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg border border-border">
            <Clock className="h-3.5 w-3.5 text-muted-foreground" />
            <span>
              {formatDateTime(slot.startTime)} – {formatEndTime(slot.endTime)}
            </span>
          </div>
        </div>

        <h3 className="text-lg font-bold text-foreground mb-3">
          {slot.jobType}
        </h3>

        <div className="space-y-2 mb-3">
          <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
            <User className="h-4 w-4" />
            <span className="font-medium">{slot.customerName}</span>
          </div>
          <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
            <MapPin className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">{slot.address}</span>
          </div>
        </div>

        <p className="text-sm text-muted-foreground/80 mb-4 line-clamp-2">{slot.description}</p>

        {slot.status === "filling" && (
          <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
            <div className="h-1.5 w-1.5 rounded-full bg-info animate-pulse" />
            <p className="font-medium">Finding someone to fill this slot...</p>
          </div>
        )}

        {slot.status === "scheduled" && (
          <button
            className="w-full inline-flex items-center justify-center rounded-full px-4 py-2.5 text-sm font-bold transition-all duration-300 bg-destructive/20 text-destructive border border-destructive/40 hover:bg-destructive/30 hover:border-destructive/60 active:scale-[0.98]"
            onClick={() => onCancel(slot.id)}
          >
            Cancel Slot
          </button>
        )}
      </CardContent>
    </Card>
  );
}
