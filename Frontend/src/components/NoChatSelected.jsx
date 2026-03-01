import { useEffect } from "react";
import { useAutopilotStore } from "../store/useAutopilotStore";
import { useChatStore } from "../store/useChatStore";
import {
  Activity,
  Clock,
  MessageSquare,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  AlertTriangle,
} from "lucide-react";

const DRIFT_CONFIG = {
  Warmer: { icon: TrendingUp, cls: "text-success" },
  Stable: { icon: Minus, cls: "text-warning" },
  Colder: { icon: TrendingDown, cls: "text-error" },
};

const STATE_COLORS = {
  Active: "badge-success",
  Stagnant: "badge-warning",
  Debt: "badge-error",
};

const ACTION_BADGE = {
  Reaction: "badge-success",
  Nudge: "badge-warning",
  Deep_Reply: "badge-error",
};

const formatLatency = (seconds) => {
  if (!seconds) return "N/A";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
  return `${(seconds / 86400).toFixed(1)}d`;
};

const NoChatSelected = () => {
  const { profiles, verdicts, actions, isLoading, fetchAll } =
    useAutopilotStore();
  const { setSelectedUser } = useChatStore();

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  if (isLoading) {
    return (
      <div className="w-full flex flex-1 flex-col items-center justify-center bg-base-100/50">
        <span className="loading loading-spinner loading-lg"></span>
        <p className="mt-2 text-sm text-base-content/60">Loading analysis...</p>
      </div>
    );
  }

  // Sort verdicts by priority for the queue
  const sortedVerdicts = [...verdicts].sort((a, b) => b.priority - a.priority);

  return (
    <div className="w-full flex-1 overflow-y-auto bg-base-100/50 p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-1">
          <h2 className="text-2xl font-bold flex items-center justify-center gap-2">
            <Activity className="w-6 h-6 text-primary" /> Relationship Dashboard
          </h2>
          <p className="text-sm text-base-content/60">
            Click a contact to view their chat and detailed analysis
          </p>
        </div>

        {/* Priority Queue */}
        {sortedVerdicts.length > 0 && (
          <div className="card bg-base-200 shadow-sm">
            <div className="card-body p-4">
              <h3 className="card-title text-sm mb-2">
                <Zap className="w-4 h-4 text-warning" /> Priority Queue
              </h3>
              <div className="space-y-2">
                {sortedVerdicts.map((v, i) => {
                  const profile = profiles.find(
                    (p) => p.contact_name === v.contact_name
                  );
                  const action = actions.find(
                    (a) => a.contact_name === v.contact_name
                  );
                  const DriftIcon = DRIFT_CONFIG[v.sentiment_drift]?.icon || Minus;
                  const driftCls = DRIFT_CONFIG[v.sentiment_drift]?.cls || "text-base-content";

                  return (
                    <div
                      key={v.contact_name}
                      className="flex items-center gap-3 p-3 bg-base-300 rounded-lg hover:bg-base-100 transition-colors cursor-pointer"
                      onClick={() =>
                        setSelectedUser({
                          _id: profile?.contact_id || "u2",
                          fullName: v.contact_name,
                        })
                      }
                    >
                      {/* Rank */}
                      <div className="text-lg font-bold text-base-content/40 w-6 text-center">
                        {i + 1}
                      </div>

                      {/* Avatar */}
                      <div className="avatar">
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                          <span className="text-sm font-bold">
                            {v.contact_name.charAt(0)}
                          </span>
                        </div>
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium truncate">
                            {v.contact_name}
                          </span>
                          <span
                            className={`badge badge-xs ${STATE_COLORS[v.state] || ""}`}
                          >
                            {v.state}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-base-content/60 mt-0.5">
                          <span className="flex items-center gap-1">
                            <DriftIcon className={`w-3 h-3 ${driftCls}`} />
                            {v.sentiment_drift}
                          </span>
                          {v.debt_type !== "None" && (
                            <span className="text-warning">
                              ⚠ {v.debt_type} debt
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="flex items-center gap-3 text-sm">
                        <div className="text-center">
                          <div className="font-mono font-bold">
                            P{v.priority}
                          </div>
                          <div className="text-[10px] text-base-content/50">
                            priority
                          </div>
                        </div>
                        {profile && (
                          <div className="text-center">
                            <div className="font-mono font-bold">
                              {formatLatency(profile.avg_latency)}
                            </div>
                            <div className="text-[10px] text-base-content/50">
                              resp time
                            </div>
                          </div>
                        )}
                        {action && (
                          <span
                            className={`badge badge-sm ${ACTION_BADGE[action.action_type] || ""}`}
                          >
                            {action.action_type}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats Grid */}
        {profiles.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="stat bg-base-200 rounded-lg p-3 shadow-sm">
              <div className="stat-title text-xs">Total Contacts</div>
              <div className="stat-value text-2xl">{profiles.length}</div>
            </div>
            <div className="stat bg-base-200 rounded-lg p-3 shadow-sm">
              <div className="stat-title text-xs">
                <AlertTriangle className="w-3 h-3 inline text-warning" /> Anomalies
              </div>
              <div className="stat-value text-2xl">
                {profiles.reduce(
                  (sum, p) => sum + (p.anomalies?.length || 0),
                  0
                )}
              </div>
            </div>
            <div className="stat bg-base-200 rounded-lg p-3 shadow-sm">
              <div className="stat-title text-xs">
                <Clock className="w-3 h-3 inline" /> Avg Response
              </div>
              <div className="stat-value text-2xl">
                {profiles.length > 0
                  ? formatLatency(
                      profiles.reduce((s, p) => s + p.avg_latency, 0) /
                        profiles.length
                    )
                  : "N/A"}
              </div>
            </div>
            <div className="stat bg-base-200 rounded-lg p-3 shadow-sm">
              <div className="stat-title text-xs">
                <MessageSquare className="w-3 h-3 inline" /> Actions Pending
              </div>
              <div className="stat-value text-2xl">{actions.length}</div>
            </div>
          </div>
        )}

        {/* Empty state fallback */}
        {profiles.length === 0 && verdicts.length === 0 && (
          <div className="text-center text-base-content/50 py-12">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No analysis data yet. Run the pipeline first.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NoChatSelected;
