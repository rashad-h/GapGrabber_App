import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import SlotsTab from "./pages/SlotsTab";
import WorkflowsTab from "./pages/WorkflowsTab";
import CancelSlot from "./pages/CancelSlot";
import WorkflowDetail from "./pages/WorkflowDetail";
import CustomerMessages from "./pages/CustomerMessages";
import NotFound from "./pages/NotFound";
import { BottomNav } from "./components/BottomNav";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <div className="min-h-screen bg-background">
          <Routes>
            <Route path="/" element={<SlotsTab />} />
            <Route path="/workflows" element={<WorkflowsTab />} />
            <Route path="/cancel-slot/:slotId" element={<CancelSlot />} />
            <Route path="/workflow/:workflowId" element={<WorkflowDetail />} />
            <Route path="/workflow/:workflowId/customer/:customerId" element={<CustomerMessages />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
          <BottomNav />
        </div>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
