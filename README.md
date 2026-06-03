# TTV_Automations

**Problem Statement**\
In the current Monday.com workflow, tasks are structured sequentially (e.g., subtask 1 must be completed before subtask 2 begins).\
However, employees often lack real-time visibility into when upstream tasks are completed. This leads to delays where downstream assignees are unaware that they can start working, resulting in wasted time.

**Objective**\
To improve task flow efficiency by:
- Notifying employees when they can start a task
- Reminding assignees about stale tasks ('Working On It' > 1day) to maintain progress visibility

**System Overview**\
This automation connects Monday.com with Supabase and a WhatsApp bot via Twilio, mapping Monday user accounts to WhatsApp numbers for real-time notifications and responses.

### Workflow Logic
If the main task status is "Working on it", a subtask assignee will be notified in the following cases:
1. The subtask is the first in the sequence and is marked "Not Started"
2. The previous subtask is marked "Done", and the current subtask is "Not Started"
3. The subtask is "Working on it", but has not been updated for more than 24 hours (stale task reminder)

<img width="1402" height="660" alt="Screenshot 2026-06-03 121716" src="https://github.com/user-attachments/assets/fafc7101-1d82-4c80-a11b-9a94f5ad1595" />
<img width="1386" height="205" alt="Screenshot 2026-06-03 121731" src="https://github.com/user-attachments/assets/68106fec-c5c0-41c4-93f1-918b7b2683c1" />

**Initial Task Notification (Cases 1 & 2)**\
When a task becomes available, the assignee receives a WhatsApp notification and must respond using one of the following options:
- **"Working on it"**: Updates task status to Working on it in Monday.com
- **"Pending Info"**: Updates task status to Pending Info in Monday.com if dependencies are blocking progress
  
If no response is received, the system will resend the notification every hour.

*Concern: hourly notifications may feel excessive*\
*Why it is not an issue: reminders continue only until action is taken, which directly addresses the original visibility gap rather than creating unnecessary spam.*

**Stale Task Reminder (Case 3)**\
For tasks marked "Working on it" for more than 24 hours without updates, the assignee receives a reminder via WhatsApp.
The assignee must reply with a progress update, which is automatically attached onto the Monday board's 'Notes' column.

*Concern:  Since tasks may remain in Working on it status even after the assignee has provided a progress update, it seems that the automation would continue sending the same reminder every hour.*\
*Why it is not an issue: a message will be attached onto monday board after the assignee reply to the reminder, which refreshes the task's Last Updated timestamp. Since stale tasks are identified based on whether the last update was more than 24 hours ago, the task will not be flagged again until another 24 hours pass without an update.*

Once a task is marked "Done" in Monday.com:
- No further notifications will be sent for that task
- The next dependent assignee in the workflow will be notified automatically

<img width="1260" height="1500" alt="workflow" src="https://github.com/user-attachments/assets/7474966e-6055-4804-a607-b3c5c0843e78" />
