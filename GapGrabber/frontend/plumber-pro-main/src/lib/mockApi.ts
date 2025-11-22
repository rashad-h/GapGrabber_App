// Mock API for plumbing schedule management
// DEPRECATED: Use api.ts instead for real backend integration
// This file is kept for reference but should be replaced with api.ts imports

export type SlotStatus = "scheduled" | "cancelled" | "filling" | "filled";
export type JobType = "Boiler service" | "Radiator issue" | "Bathroom refit" | "Drain unblock";
export type CandidateStatus = "pending" | "accepted" | "declined" | "not_needed";
export type WorkflowStatus = "running" | "succeeded" | "failed";

export interface Slot {
  id: string;
  startTime: string;
  endTime: string;
  jobType: JobType | string;
  status: SlotStatus;
  customerName: string;
  address: string;
  description: string;
}

export interface CandidateContact {
  id: string;
  name: string;
  phone: string;
  status: CandidateStatus;
  messagePreview: string;
  contactedAt?: string;
  willContactAt?: string;
}

export interface Workflow {
  id: string;
  slotId: string;
  slotSummary: string;
  status: WorkflowStatus;
  candidates: CandidateContact[];
}

// In-memory mock data
let mockSlots: Slot[] = [
  {
    id: "slot-1",
    startTime: "2025-11-22T09:00:00Z",
    endTime: "2025-11-22T11:00:00Z",
    jobType: "Boiler service",
    status: "scheduled",
    customerName: "John Smith",
    address: "45 High Street, N1 8QT",
    description: "Annual boiler service and safety check",
  },
  {
    id: "slot-2",
    startTime: "2025-11-22T11:30:00Z",
    endTime: "2025-11-22T13:00:00Z",
    jobType: "Radiator issue",
    status: "scheduled",
    customerName: "Emma Wilson",
    address: "12 Oak Avenue, N1 5PL",
    description: "Cold radiator not heating properly",
  },
  {
    id: "slot-3",
    startTime: "2025-11-22T14:00:00Z",
    endTime: "2025-11-22T16:00:00Z",
    jobType: "Bathroom refit",
    status: "filling",
    customerName: "Michael Brown",
    address: "78 Park Road, N1 3QR",
    description: "Replace taps and install new shower head",
  },
  {
    id: "slot-4",
    startTime: "2025-11-22T16:30:00Z",
    endTime: "2025-11-22T18:00:00Z",
    jobType: "Drain unblock",
    status: "scheduled",
    customerName: "Sarah Davis",
    address: "23 Green Lane, N1 7RT",
    description: "Kitchen sink drain completely blocked",
  },
  {
    id: "slot-5",
    startTime: "2025-11-22T19:00:00Z",
    endTime: "2025-11-22T20:30:00Z",
    jobType: "Boiler service",
    status: "scheduled",
    customerName: "Jennifer Lee",
    address: "56 Church Street, N1 2WX",
    description: "Emergency boiler repair (rescheduled)",
  },
];

let mockWorkflows: Workflow[] = [
  {
    id: "workflow-1",
    slotId: "slot-3",
    slotSummary: "Today 14:00–16:00",
    status: "running",
    candidates: [
      {
        id: "cand-1",
        name: "Lisa Anderson",
        phone: "+44 7700 900123",
        status: "pending",
        messagePreview: "Hi Lisa! I have an opening today 14:00–16:00. Would you like to move your appointment to this slot?",
        contactedAt: new Date(Date.now() - 3 * 60 * 1000).toISOString(), // 3 minutes ago
      },
      {
        id: "cand-2",
        name: "Tom Roberts",
        phone: "+44 7700 900456",
        status: "pending",
        messagePreview: "Hi Tom! I have an opening today 14:00–16:00. Would you like to move your appointment to this slot?",
        willContactAt: new Date(Date.now() + 2 * 60 * 1000).toISOString(), // in 2 minutes
      },
      {
        id: "cand-3",
        name: "Rachel Green",
        phone: "+44 7700 900789",
        status: "pending",
        messagePreview: "Hi Rachel! I have an opening today 14:00–16:00. Would you like to move your appointment to this slot?",
        willContactAt: new Date(Date.now() + 7 * 60 * 1000).toISOString(), // in 7 minutes
      },
    ],
  },
  {
    id: "workflow-2",
    slotId: "slot-5",
    slotSummary: "Today 19:00–20:30",
    status: "succeeded",
    candidates: [
      {
        id: "cand-4",
        name: "Peter Thompson",
        phone: "+44 7700 901234",
        status: "not_needed",
        messagePreview: "Hi Peter! I have an opening today 19:00–20:30. 10% discount for quick response. Would you like to move your appointment?",
        contactedAt: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
      },
      {
        id: "cand-5",
        name: "Jennifer Lee",
        phone: "+44 7700 901567",
        status: "accepted",
        messagePreview: "Hi Jennifer! I have an opening today 19:00–20:30. 10% discount for quick response. Would you like to move your appointment?",
        contactedAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      },
      {
        id: "cand-6",
        name: "Mark Williams",
        phone: "+44 7700 901890",
        status: "not_needed",
        messagePreview: "Hi Mark! I have an opening today 19:00–20:30. 10% discount for quick response. Would you like to move your appointment?",
      },
    ],
  },
];

// Simulate network delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function listSlots(): Promise<Slot[]> {
  await delay(300);
  return [...mockSlots].sort((a, b) => 
    new Date(a.startTime).getTime() - new Date(b.startTime).getTime()
  );
}

export async function cancelSlot(slotId: string): Promise<Slot> {
  await delay(400);
  const slot = mockSlots.find((s) => s.id === slotId);
  if (!slot) throw new Error("Slot not found");
  
  slot.status = "cancelled";
  return { ...slot };
}

export async function startFillWorkflow(
  slotId: string,
  reason: string,
  discountPercent: number = 0,
  waitingMinutes: number = 5
): Promise<Workflow> {
  await delay(500);
  
  const slot = mockSlots.find((s) => s.id === slotId);
  if (!slot) throw new Error("Slot not found");
  
  // Update slot status
  slot.status = "filling";
  
  // Check if workflow already exists
  let workflow = mockWorkflows.find((w) => w.slotId === slotId);
  
  if (!workflow) {
    // Create new workflow
    const startTime = new Date(slot.startTime);
    const timeStr = startTime.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
    const endTime = new Date(slot.endTime);
    const endTimeStr = endTime.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
    
    workflow = {
      id: `workflow-${Date.now()}`,
      slotId: slot.id,
      slotSummary: `Today ${timeStr}–${endTimeStr}`,
      status: "running",
      candidates: generateMockCandidates(slot, discountPercent, waitingMinutes),
    };
    
    mockWorkflows.push(workflow);
  } else {
    // Update existing workflow
    workflow.status = "running";
    workflow.candidates = generateMockCandidates(slot, discountPercent, waitingMinutes);
  }
  
  return { ...workflow };
}

function generateMockCandidates(slot: Slot, discountPercent: number, waitingMinutes: number = 5): CandidateContact[] {
  const startTime = new Date(slot.startTime);
  const timeStr = startTime.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  const endTime = new Date(slot.endTime);
  const endTimeStr = endTime.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  const discountText = discountPercent > 0 ? ` ${discountPercent}% discount for quick response.` : "";
  
  const names = [
    "Alex Johnson", "Sophie Martin", "Chris Baker", 
    "Emma Clarke", "Daniel Wright", "Olivia Harris"
  ];
  
  const now = Date.now();
  
  return names.slice(0, 3 + Math.floor(Math.random() * 2)).map((name, i) => ({
    id: `cand-${Date.now()}-${i}`,
    name,
    phone: `+44 7700 ${900000 + Math.floor(Math.random() * 100000)}`,
    status: "pending" as CandidateStatus,
    messagePreview: `Hi ${name.split(" ")[0]}! I have an opening today ${timeStr}–${endTimeStr}.${discountText} Would you like to move your appointment to this slot?`,
    contactedAt: i === 0 ? new Date(now).toISOString() : undefined,
    willContactAt: i > 0 ? new Date(now + i * waitingMinutes * 60 * 1000).toISOString() : undefined,
  }));
}

export async function listWorkflows(): Promise<Workflow[]> {
  await delay(300);
  return [...mockWorkflows].sort((a, b) => {
    // Sort by status priority and then by ID (newest first)
    const statusPriority = { running: 1, failed: 2, succeeded: 3 };
    const aPriority = statusPriority[a.status] || 99;
    const bPriority = statusPriority[b.status] || 99;
    if (aPriority !== bPriority) return aPriority - bPriority;
    return b.id.localeCompare(a.id);
  });
}

export async function getWorkflow(id: string): Promise<Workflow> {
  await delay(200);
  const workflow = mockWorkflows.find((w) => w.id === id);
  if (!workflow) throw new Error("Workflow not found");
  return { ...workflow };
}
