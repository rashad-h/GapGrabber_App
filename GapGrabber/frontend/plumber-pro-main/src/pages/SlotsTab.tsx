import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { listSlots, Slot } from "@/lib/api";
import { SlotCard } from "@/components/SlotCard";

export default function SlotsTab() {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadSlots();
  }, []);

  const loadSlots = async () => {
    try {
      setLoading(true);
      const data = await listSlots();
      setSlots(data);
    } catch (error) {
      console.error("Failed to load slots:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = (slotId: string) => {
    navigate(`/cancel-slot/${slotId}`);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh]">
        <Loader2 className="h-10 w-10 animate-spin text-foreground mb-4" />
        <p className="text-sm text-muted-foreground font-medium">Loading schedule...</p>
      </div>
    );
  }

  return (
    <div className="pb-20 min-h-screen">
      <div className="sticky top-0 z-10 glass-effect border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-foreground">
            📅 Schedule
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your appointments</p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {slots.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-20">📭</div>
            <p className="text-muted-foreground text-lg">No slots scheduled</p>
          </div>
        ) : (
          slots.map((slot) => (
            <SlotCard key={slot.id} slot={slot} onCancel={handleCancel} />
          ))
        )}
      </div>
    </div>
  );
}
