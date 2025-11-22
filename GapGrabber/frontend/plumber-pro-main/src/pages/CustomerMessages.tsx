import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Loader2, MessageSquare, Phone, Send, Inbox } from "lucide-react";
import { getCustomerMessages, CustomerMessages as CustomerMessagesType } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

export default function CustomerMessagesPage() {
  const { workflowId, customerId } = useParams<{ workflowId: string; customerId: string }>();
  const navigate = useNavigate();
  const [customerMessages, setCustomerMessages] = useState<CustomerMessagesType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMessages();
  }, [customerId, workflowId]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      if (!customerId) return;
      
      const campaignId = workflowId ? parseInt(workflowId.replace("workflow-", "")) : undefined;
      const data = await getCustomerMessages(parseInt(customerId), campaignId);
      setCustomerMessages(data);
    } catch (error) {
      console.error("Failed to load messages:", error);
      toast.error("Failed to load messages");
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString("en-GB", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <Loader2 className="h-10 w-10 animate-spin text-foreground mb-4" />
        <p className="text-sm text-muted-foreground font-medium">Loading messages...</p>
      </div>
    );
  }

  if (!customerMessages) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="sticky top-0 z-10 glass-effect border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 py-5 flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(`/workflow/${workflowId}`)}
            className="rounded-full hover:bg-muted transition-all"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-foreground">
              {customerMessages.customer.name}
            </h1>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-0.5">
              <Phone className="h-3.5 w-3.5" />
              <span>{customerMessages.customer.phone}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {customerMessages.messages.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-20">💬</div>
            <p className="text-muted-foreground text-lg">No messages yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {customerMessages.messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.direction === "outbound" ? "justify-end" : "justify-start"}`}
              >
                <Card
                  className={`max-w-[85%] glass-effect border-border/50 ${
                    message.direction === "outbound"
                      ? "bg-primary/10 border-primary/30"
                      : "bg-muted/50"
                  }`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-2 mb-2">
                      {message.direction === "outbound" ? (
                        <Send className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                      ) : (
                        <Inbox className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm text-foreground whitespace-pre-wrap break-words">
                          {message.content}
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                          {formatTime(message.timestamp)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

