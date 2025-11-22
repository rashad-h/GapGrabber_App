// Real API client for backend integration
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type SlotStatus = "scheduled" | "cancelled" | "filling" | "filled";
export type JobType = "Boiler service" | "Radiator issue" | "Bathroom refit" | "Drain unblock" | string;
export type CandidateStatus = "pending" | "accepted" | "declined" | "not_needed" | "sent" | "notified_filled";
export type WorkflowStatus = "running" | "succeeded" | "failed" | "active" | "filled" | "expired";

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

// Backend API types
interface BackendAppointment {
  id: number;
  customer: {
    id: number;
    name: string;
    phone: string;
  };
  scheduled_time: string;
  service_type: string;
  status: string;
}

interface BackendCampaign {
  id: number;
  status: string;
  cancelled_slot_time: string;
  service_type: string;
  discount_percentage: number;
  wait_time_minutes: number;
  custom_context?: string;
  current_batch: number;
  total_contacted: number;
  outreach_attempts: Array<{
    customer: {
      id: number;
      name: string;
      phone: string;
    };
    status: string;
    batch_number: number;
    message_sent: string;
    sent_at: string;
    responded_at?: string;
  }>;
}

// Helper function to map backend appointment to frontend slot
function mapAppointmentToSlot(apt: BackendAppointment): Slot {
  const startTime = new Date(apt.scheduled_time);
  const endTime = new Date(startTime.getTime() + 2 * 60 * 60 * 1000); // Assume 2 hour duration
  
  let status: SlotStatus = "scheduled";
  if (apt.status === "cancelled") status = "cancelled";
  
  return {
    id: `slot-${apt.id}`,
    startTime: startTime.toISOString(),
    endTime: endTime.toISOString(),
    jobType: apt.service_type,
    status,
    customerName: apt.customer.name,
    address: "", // Not in backend, empty for now
    description: `${apt.service_type} appointment`,
  };
}

// Helper function to map backend campaign to frontend workflow
function mapCampaignToWorkflow(campaign: BackendCampaign, slotId: string): Workflow {
  const startTime = new Date(campaign.cancelled_slot_time);
  const timeStr = startTime.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  const endTime = new Date(startTime.getTime() + 2 * 60 * 60 * 1000);
  const endTimeStr = endTime.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  
  let status: WorkflowStatus = "running";
  if (campaign.status === "filled") status = "succeeded";
  else if (campaign.status === "expired") status = "failed";
  else if (campaign.status === "active") status = "running";
  
  const candidates: CandidateContact[] = (campaign.outreach_attempts || []).map((outreach, idx) => {
    let candidateStatus: CandidateStatus = "pending";
    if (outreach.status === "accepted") candidateStatus = "accepted";
    else if (outreach.status === "declined") candidateStatus = "declined";
    else if (outreach.status === "notified_filled") candidateStatus = "not_needed";
    else if (outreach.status === "sent") candidateStatus = "pending";
    
    return {
      id: `cand-${outreach.customer.id}`,
      name: outreach.customer.name,
      phone: outreach.customer.phone,
      status: candidateStatus,
      messagePreview: outreach.message_sent,
      contactedAt: outreach.sent_at,
      willContactAt: idx > 0 ? new Date(new Date(outreach.sent_at).getTime() + campaign.wait_time_minutes * 60 * 1000).toISOString() : undefined,
    };
  });
  
  return {
    id: `workflow-${campaign.id}`,
    slotId,
    slotSummary: `${timeStr}–${endTimeStr}`,
    status,
    candidates,
  };
}

// API functions
export async function listSlots(): Promise<Slot[]> {
  const response = await fetch(`${API_BASE_URL}/api/appointments?status=scheduled`);
  if (!response.ok) {
    throw new Error(`Failed to fetch appointments: ${response.statusText}`);
  }
  const data = await response.json();
  return data.appointments.map(mapAppointmentToSlot);
}

export async function cancelSlot(slotId: string): Promise<Slot> {
  // Note: cancel-and-fill endpoint handles cancellation, so this just returns the slot
  // Extract appointment ID from slotId (format: "slot-{id}")
  const appointmentId = parseInt(slotId.replace("slot-", ""));
  
  // Fetch appointment to return (cancel-and-fill will handle the actual cancellation)
  const response = await fetch(`${API_BASE_URL}/api/appointments?status=scheduled`);
  if (!response.ok) {
    throw new Error(`Failed to fetch appointments: ${response.statusText}`);
  }
  const data = await response.json();
  const appointment = data.appointments.find((apt: BackendAppointment) => apt.id === appointmentId);
  if (!appointment) {
    throw new Error(`Appointment ${appointmentId} not found`);
  }
  return mapAppointmentToSlot(appointment);
}

export async function startFillWorkflow(
  slotId: string,
  reason: string,
  discountPercent: number = 0,
  waitingMinutes: number = 5
): Promise<Workflow> {
  // Extract appointment ID from slotId
  const appointmentId = parseInt(slotId.replace("slot-", ""));
  
  // Cancel appointment and trigger fill campaign
  const response = await fetch(`${API_BASE_URL}/api/appointments/${appointmentId}/cancel-and-fill`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      discount_percentage: discountPercent,
      wait_time_minutes: waitingMinutes,
      custom_context: reason,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to start fill workflow: ${error.detail || response.statusText}`);
  }
  
  const data = await response.json();
  const campaignId = data.campaign_id;
  
  // Fetch campaign details
  const campaignResponse = await fetch(`${API_BASE_URL}/api/campaigns/${campaignId}`);
  if (!campaignResponse.ok) {
    throw new Error(`Failed to fetch campaign: ${campaignResponse.statusText}`);
  }
  
  const campaign: BackendCampaign = await campaignResponse.json();
  return mapCampaignToWorkflow(campaign, slotId);
}

export async function listWorkflows(): Promise<Workflow[]> {
  console.log(`[API] Fetching campaigns from ${API_BASE_URL}/api/campaigns`);
  const response = await fetch(`${API_BASE_URL}/api/campaigns`);
  if (!response.ok) {
    console.error(`[API] Failed to fetch campaigns: ${response.status} ${response.statusText}`);
    throw new Error(`Failed to fetch campaigns: ${response.statusText}`);
  }
  
  const data = await response.json();
  console.log(`[API] Received ${data.campaigns?.length || 0} campaigns`);
  const campaignSummaries = data.campaigns || [];
  
  if (campaignSummaries.length === 0) {
    console.log(`[API] No campaigns found`);
    return [];
  }
  
  // Fetch full campaign details for each campaign (to get outreach_attempts)
  console.log(`[API] Fetching details for ${campaignSummaries.length} campaigns...`);
  const workflows = await Promise.all(
    campaignSummaries.map(async (summary: any) => {
      try {
        console.log(`[API] Fetching campaign ${summary.id} details...`);
        const detailResponse = await fetch(`${API_BASE_URL}/api/campaigns/${summary.id}`);
        if (!detailResponse.ok) {
          console.error(`[API] Failed to fetch campaign ${summary.id} details: ${detailResponse.status}`);
          return null;
        }
        const campaign: BackendCampaign = await detailResponse.json();
        console.log(`[API] Campaign ${summary.id} has ${campaign.outreach_attempts?.length || 0} outreach attempts`);
        const slotId = `slot-${campaign.id}`;
        const workflow = mapCampaignToWorkflow(campaign, slotId);
        console.log(`[API] Mapped campaign ${summary.id} to workflow with ${workflow.candidates.length} candidates`);
        return workflow;
      } catch (error) {
        console.error(`[API] Error fetching campaign ${summary.id}:`, error);
        return null;
      }
    })
  );
  
  // Filter out any null results
  const validWorkflows = workflows.filter((w): w is Workflow => w !== null);
  console.log(`[API] Returning ${validWorkflows.length} valid workflows`);
  return validWorkflows;
}

export async function getWorkflow(id: string): Promise<Workflow> {
  // Extract campaign ID from workflow ID (format: "workflow-{id}")
  const campaignId = parseInt(id.replace("workflow-", ""));
  
  const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch workflow: ${response.statusText}`);
  }
  
  const campaign: BackendCampaign = await response.json();
  const slotId = `slot-${campaignId}`;
  return mapCampaignToWorkflow(campaign, slotId);
}

// Get messages for a specific customer
export interface Message {
  id: number;
  direction: "inbound" | "outbound";
  content: string;
  timestamp: string;
}

export interface CustomerMessages {
  customer: {
    id: number;
    name: string;
    phone: string;
  };
  messages: Message[];
}

export async function getCustomerMessages(customerId: number, campaignId?: number): Promise<CustomerMessages> {
  let url = `${API_BASE_URL}/api/messages?customer_id=${customerId}`;
  if (campaignId) {
    url = `${API_BASE_URL}/api/messages?campaign_id=${campaignId}`;
  }
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch messages: ${response.statusText}`);
  }
  
  const data = await response.json();
  // Find the customer's messages in the grouped response
  const customerGroup = data.messages_by_customer.find(
    (group: any) => group.customer.id === customerId
  );
  
  if (!customerGroup) {
    throw new Error(`No messages found for customer ${customerId}`);
  }
  
  return customerGroup;
}

