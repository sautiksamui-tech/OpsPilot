import { useState, useEffect, useRef, useCallback } from 'react';

export function useAgentRun() {
  const [currentRunId, setCurrentRunId] = useState(null);
  const [runState, setRunState] = useState(null);
  const [events, setEvents] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeScenario, setActiveScenario] = useState('scenario_1_success');
  const [demoMode, setDemoMode] = useState(true);

  const eventSourceRef = useRef(null);

  const API_BASE = import.meta.env.VITE_API_URL || '';

  const fetchEvents = useCallback(async (runId) => {
    try {
      const res = await fetch(`${API_BASE}/api/runs/${runId}/events/list`);
      if (res.ok) {
        const data = await res.json();
        if (data.events && Array.isArray(data.events)) {
          setEvents(data.events);
        }
      }
    } catch (e) {
      console.error('Failed to fetch events list:', e);
    }
  }, [API_BASE]);

  const fetchRunState = useCallback(async (runId) => {
    try {
      const res = await fetch(`${API_BASE}/api/runs/${runId}`);
      if (res.ok) {
        const data = await res.json();
        setRunState(data);
        if (
          ['APPROVAL_REQUIRED', 'AWAITING_APPROVAL', 'PAID', 'COMPLETED', 'BLOCKED', 'FAILED', 'CANCELLED'].includes(
            data.payment_state
          ) ||
          ['APPROVAL_REQUIRED', 'AWAITING_APPROVAL', 'COMPLETED', 'BLOCKED', 'FAILED', 'CANCELLED'].includes(data.status)
        ) {
          setIsLoading(false);
        }
      }
    } catch (e) {
      console.error('Failed to fetch run state:', e);
    }
  }, [API_BASE]);

  const fetchAuditLogs = useCallback(async (runId) => {
    try {
      const res = await fetch(`${API_BASE}/api/runs/${runId}/audit`);
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data.audit_trail || []);
      }
    } catch (e) {
      console.error('Failed to fetch audit logs:', e);
    }
  }, [API_BASE]);

  const startRun = async (prompt, scenarioId = activeScenario, isDemo = demoMode, autoApprove = false) => {
    setIsLoading(true);
    setError(null);
    setEvents([]);
    setAuditLogs([]);
    setRunState(null);

    try {
      const res = await fetch(`${API_BASE}/api/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          scenario_id: scenarioId,
          demo_mode: isDemo,
          auto_approve: autoApprove,
        }),
      });

      if (!res.ok) {
        throw new Error(`Failed to start run: ${res.statusText}`);
      }

      const data = await res.json();
      setCurrentRunId(data.run_id);
      await Promise.all([
        fetchRunState(data.run_id),
        fetchAuditLogs(data.run_id),
        fetchEvents(data.run_id),
      ]);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const handleApproval = async (approved, comment = '') => {
    const runId = currentRunId || runState?.run_id;
    if (!runId) {
      setError('No active run identifier found for authorization.');
      return;
    }
    setIsLoading(true);

    try {
      const endpoint = approved ? `${API_BASE}/api/runs/${runId}/approve` : `${API_BASE}/api/runs/${runId}/reject`;
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved,
          comment: comment || (approved ? 'Authorized by Operations Lead' : 'Rejected by Operations Lead'),
          approver_name: 'Operations Director (Human)',
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Approval submission failed' }));
        throw new Error(errData.detail || 'Approval submission failed');
      }

      const updated = await res.json();
      await Promise.all([
        fetchRunState(runId),
        fetchAuditLogs(runId),
        fetchEvents(runId),
      ]);
    } catch (err) {
      console.error('Approval submission error:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // SSE Stream Listener
  useEffect(() => {
    if (!currentRunId) return;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const sse = new EventSource(`${API_BASE}/api/runs/${currentRunId}/events`);
    eventSourceRef.current = sse;

    sse.addEventListener('agent_event', (e) => {
      try {
        const eventData = JSON.parse(e.data);
        setEvents((prev) => {
          // Deduplicate by event_id
          if (prev.some((ev) => ev.event_id === eventData.event_id)) return prev;
          return [...prev, eventData];
        });

        // Refresh state when major steps finish
        if (
          [
            'run.started',
            'tool.completed',
            'decision.created',
            'approval.required',
            'approval.received',
            'approval.rejected',
            'execution.locked',
            'action.completed',
            'exception.detected',
            'reconciliation.completed',
            'run.completed',
            'run.failed',
          ].includes(eventData.event_type)
        ) {
          fetchRunState(currentRunId);
          fetchAuditLogs(currentRunId);
        }

        if (eventData.event_type === 'approval.required') {
          setIsLoading(false);
        }

        if (eventData.event_type === 'run.completed' || eventData.event_type === 'run.failed') {
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    });

    sse.onerror = () => {
      // EventSource reconnects automatically
    };

    return () => {
      if (sse) {
        sse.close();
      }
    };
  }, [currentRunId, fetchRunState, fetchAuditLogs, fetchEvents]);

  // Periodic polling fallback while in flight or awaiting confirmation
  useEffect(() => {
    if (!currentRunId) return;

    const isDone =
      runState &&
      ['PAID', 'COMPLETED', 'BLOCKED', 'FAILED', 'CANCELLED', 'APPROVAL_REQUIRED', 'AWAITING_APPROVAL'].includes(
        runState.payment_state
      );

    if (isDone) return;

    const interval = setInterval(() => {
      fetchRunState(currentRunId);
      fetchAuditLogs(currentRunId);
      fetchEvents(currentRunId);
    }, 2000);

    return () => clearInterval(interval);
  }, [currentRunId, runState, fetchRunState, fetchAuditLogs, fetchEvents]);

  return {
    currentRunId,
    runState,
    events,
    auditLogs,
    isLoading,
    error,
    activeScenario,
    setActiveScenario,
    demoMode,
    setDemoMode,
    startRun,
    handleApproval,
    fetchRunState,
    fetchEvents,
  };
}
