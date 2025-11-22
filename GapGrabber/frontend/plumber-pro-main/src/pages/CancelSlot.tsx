import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { listSlots, Slot, cancelSlot, startFillWorkflow } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

export default function CancelSlot() {
  const { slotId } = useParams<{ slotId: string }>();
  const navigate = useNavigate();
  const [slot, setSlot] = useState<Slot | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reason, setReason] = useState("");
  const [discount, setDiscount] = useState(0);
  const [waitingMinutes, setWaitingMinutes] = useState(5);

  useEffect(() => {
    loadSlot();
  }, [slotId]);

  const loadSlot = async () => {
    try {
      setLoading(true);
      const slots = await listSlots();
      const found = slots.find((s) => s.id === slotId);
      if (!found) {
        toast.error("Slot not found");
        navigate("/");
        return;
      }
      setSlot(found);
    } catch (error) {
      console.error("Failed to load slot:", error);
      toast.error("Failed to load slot");
    } finally {
      setLoading(false);
    }
  };

  const handleFillGap = async () => {
    if (!slot || !reason.trim()) {
      toast.error("Please provide a reason for cancellation");
      return;
    }

    try {
      setSubmitting(true);
      
      // Cancel the slot
      await cancelSlot(slot.id);
      
      // Start fill workflow
      const workflow = await startFillWorkflow(slot.id, reason, discount, waitingMinutes);
      
      toast.success("Started contacting people to fill this slot");
      
      // Navigate to workflow detail
      navigate(`/workflow/${workflow.id}`);
    } catch (error) {
      console.error("Failed to start fill gap:", error);
      toast.error("Failed to start gap filling");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <Loader2 className="h-10 w-10 animate-spin text-foreground mb-4" />
        <p className="text-sm text-muted-foreground font-medium">Loading...</p>
      </div>
    );
  }

  if (!slot) {
    return null;
  }

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="sticky top-0 z-10 glass-effect border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 py-5 flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/")}
            className="rounded-full hover:bg-muted transition-all"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl font-bold text-foreground">
            🎯 Fill Empty Slot
          </h1>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        <Card className="glass-effect border-border/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              Empty Slot Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">Time</p>
              <p className="font-medium">
                {formatTime(slot.startTime)} – {formatTime(slot.endTime)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Original Job Type</p>
              <p className="font-medium">{slot.jobType}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Original Customer</p>
              <p className="font-medium">{slot.customerName}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Description</p>
              <p className="font-medium text-sm">{slot.description}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-effect border-border/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              Fill This Gap
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reason">Reason for gap *</Label>
              <Textarea
                id="reason"
                placeholder="e.g., Customer cancelled, Schedule conflict..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="discount">Discount (%)</Label>
              <div className="flex items-center gap-3">
                <Input
                  id="discount"
                  type="number"
                  min="0"
                  max="100"
                  value={discount}
                  onChange={(e) => setDiscount(Number(e.target.value))}
                  className="w-24"
                />
                <span className="text-sm text-muted-foreground">
                  {discount > 0 
                    ? `${discount}% discount for quick response`
                    : "No discount"
                  }
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="waitingMinutes">Contact next person after (minutes)</Label>
              <div className="flex items-center gap-3">
                <Input
                  id="waitingMinutes"
                  type="number"
                  min="1"
                  max="60"
                  value={waitingMinutes}
                  onChange={(e) => setWaitingMinutes(Number(e.target.value))}
                  className="w-24"
                />
                <span className="text-sm text-muted-foreground">
                  {waitingMinutes === 1 
                    ? "1 minute waiting period"
                    : `${waitingMinutes} minutes waiting period`
                  }
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <button
          className="w-full inline-flex items-center justify-center rounded-full px-4 py-2.5 text-sm font-bold transition-all duration-300 bg-success/20 text-success border border-success/40 hover:bg-success/30 hover:border-success/60 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleFillGap}
          disabled={submitting || !reason.trim()}
        >
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Contacting people...
            </>
          ) : (
            "Start Contacting"
          )}
        </button>
      </div>
    </div>
  );
}
