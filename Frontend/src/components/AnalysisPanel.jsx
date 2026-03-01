import { useEffect, useRef } from "react";
import { useAutopilotStore } from "../store/useAutopilotStore";
import { useChatStore } from "../store/useChatStore";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  AlertTriangle,
  Clock,
  Copy,
  MessageCircle,
  Repeat,
  TrendingDown,
  TrendingUp,
  Minus,
  Zap,
  Hash,
} from "lucide-react";

const STATE_BADGE = {
  Active: "badge-success",
  Stagnant: "badge-warning",
  Debt: "badge-error",
};

const DRIFT_CLASSES = {
  Warmer: { icon: TrendingUp, cls: "text-success" },
  Stable: { icon: Minus, cls: "text-warning" },
  Colder: { icon: TrendingDown, cls: "text-error" },
};

const ACTION_COLORS = {
  Reaction: "badge-success",
  Nudge: "badge-warning",
  Deep_Reply: "badge-error",
};

// Helper to read a CSS custom property from the document
function getCSSColor(varName, fallback) {
  if (typeof document === "undefined") return fallback;
  const val = getComputedStyle(document.documentElement)
    .getPropertyValue(varName)
    .trim();
  return val || fallback;
}

const AnalysisPanel = () => {
  const { selectedUser } = useChatStore();
  const { profiles, verdicts, actions, isLoading, fetchAll } =
    useAutopilotStore();
  const containerRef = useRef(null);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // Read theme colors for recharts (which needs raw color strings)
  const getThemeColors = () => {
    const style = getComputedStyle(document.documentElement);
    // DaisyUI v4+ uses oklch, we need to read the resolved color
    const successColor = getCSSColor("--su", "#22c55e") !== "#22c55e"
      ? `oklch(${getCSSColor("--su", "0.75 0.18 150")})`
      : "#22c55e";
    const warningColor = getCSSColor("--wa", "#eab308") !== "#eab308"
      ? `oklch(${getCSSColor("--wa", "0.8 0.15 85")})`
      : "#eab308";
    const errorColor = getCSSColor("--er", "#ef4444") !== "#ef4444"
      ? `oklch(${getCSSColor("--er", "0.65 0.2 25")})`
      : "#ef4444";
    const primaryColor = getCSSColor("--p", "#6366f1") !== "#6366f1"
      ? `oklch(${getCSSColor("--p", "0.55 0.2 270")})`
      : "#6366f1";
    const baseContent = getCSSColor("--bc", "#374151") !== "#374151"
      ? `oklch(${getCSSColor("--bc", "0.3 0.02 250")})`
      : "#374151";
    return { successColor, warningColor, errorColor, primaryColor, baseContent };
  };

  if (isLoading) {
    return (
      <aside className="w-80 border-l border-base-300 p-4 overflow-y-auto">
        <div className="flex items-center justify-center h-full">
          <span className="loading loading-spinner loading-md"></span>
        </div>
      </aside>
    );
  }

  const contactName = selectedUser?.fullName;
  const profile = profiles.find((p) => p.contact_name === contactName);
  const verdict = verdicts.find((v) => v.contact_name === contactName);
  const action = actions.find((a) => a.contact_name === contactName);

  if (!profile) {
    return (
      <aside className="w-80 border-l border-base-300 p-4 overflow-y-auto">
        <p className="text-sm text-base-content/50 text-center mt-8">
          No analysis data available. Run the pipeline first.
        </p>
      </aside>
    );
  }

  const { successColor, warningColor, errorColor, primaryColor, baseContent } =
    getThemeColors();

  const stateChartColor =
    verdict?.state === "Active"
      ? successColor
      : verdict?.state === "Stagnant"
      ? warningColor
      : errorColor;

  // Pie chart data for relationship state
  const stateData = verdict
    ? [
        { name: verdict.state, value: verdict.priority },
        { name: "Remaining", value: 10 - verdict.priority },
      ]
    : [];

  // Bar chart data for behavioral stats
  const statsData = [
    { name: "Reciprocity", value: Math.round(profile.reciprocity_ratio * 100) },
    {
      name: "Emoji/msg",
      value: Math.round(profile.typing_style.emoji_density * 100),
    },
    { name: "Avg Words", value: profile.typing_style.avg_word_count },
  ];

  const formatLatency = (seconds) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
    return `${(seconds / 86400).toFixed(1)}d`;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const DriftIcon = DRIFT_CLASSES[verdict?.sentiment_drift]?.icon || Minus;
  const driftCls = DRIFT_CLASSES[verdict?.sentiment_drift]?.cls || "text-base-content";

  return (
    <aside className="w-80 border-l border-base-300 overflow-y-auto bg-base-100" ref={containerRef}>
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="text-center">
          <h2 className="font-bold text-lg">{contactName}</h2>
          <p className="text-xs text-base-content/60">Behavioral Analysis</p>
        </div>

        {/* Relationship State + Priority */}
        {verdict && (
          <div className="card bg-base-200 shadow-sm">
            <div className="card-body p-3">
              <h3 className="card-title text-sm">
                <Activity className="w-4 h-4" /> Relationship Health
              </h3>
              <div className="flex items-center gap-3">
                <div className="w-20 h-20">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={stateData}
                        innerRadius={22}
                        outerRadius={35}
                        dataKey="value"
                        startAngle={90}
                        endAngle={-270}
                      >
                        <Cell fill={stateChartColor} />
                        <Cell fill={baseContent} opacity={0.3} />
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`badge badge-sm ${STATE_BADGE[verdict.state] || ""}`}>
                      {verdict.state}
                    </span>
                    <span className="text-xs font-mono">
                      P{verdict.priority}/10
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs">
                    <DriftIcon className={`w-4 h-4 ${driftCls}`} />
                    <span>{verdict.sentiment_drift} drift</span>
                  </div>
                  {verdict.debt_type !== "None" && (
                    <div className="text-xs text-warning">
                      ⚠ {verdict.debt_type} debt
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Behavioral DNA Stats */}
        <div className="card bg-base-200 shadow-sm">
          <div className="card-body p-3">
            <h3 className="card-title text-sm">
              <Zap className="w-4 h-4" /> Behavioral DNA
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="stat p-2 bg-base-300 rounded-lg">
                <div className="stat-title text-xs">
                  <Repeat className="w-3 h-3 inline" /> Reciprocity
                </div>
                <div className="stat-value text-lg">
                  {(profile.reciprocity_ratio * 100).toFixed(0)}%
                </div>
              </div>
              <div className="stat p-2 bg-base-300 rounded-lg">
                <div className="stat-title text-xs">
                  <Clock className="w-3 h-3 inline" /> Avg Latency
                </div>
                <div className="stat-value text-lg">
                  {formatLatency(profile.avg_latency)}
                </div>
              </div>
              <div className="stat p-2 bg-base-300 rounded-lg">
                <div className="stat-title text-xs">
                  <MessageCircle className="w-3 h-3 inline" /> Style
                </div>
                <div className="stat-value text-sm">{profile.comm_style}</div>
              </div>
              <div className="stat p-2 bg-base-300 rounded-lg">
                <div className="stat-title text-xs">
                  <Hash className="w-3 h-3 inline" /> Formality
                </div>
                <div className="stat-value text-sm">
                  {profile.typing_style.formality_level}
                </div>
              </div>
            </div>

            {/* Stats Bar Chart */}
            <div className="h-28 mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statsData}>
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 10, fill: "currentColor" }}
                    stroke="currentColor"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "currentColor" }}
                    width={30}
                    stroke="currentColor"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--fallback-b2,oklch(var(--b2)/1))",
                      borderColor: "var(--fallback-b3,oklch(var(--b3)/1))",
                      color: "var(--fallback-bc,oklch(var(--bc)/1))",
                    }}
                  />
                  <Bar dataKey="value" fill={primaryColor} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Vibe Description */}
        <div className="card bg-base-200 shadow-sm">
          <div className="card-body p-3">
            <h3 className="card-title text-sm"> Vibe</h3>
            <p className="text-xs text-base-content/80">
              {profile.vibe_description}
            </p>
          </div>
        </div>

        {/* Anomalies */}
        {profile.anomalies?.length > 0 && (
          <div className="card bg-base-200 border border-warning/30 shadow-sm">
            <div className="card-body p-3">
              <h3 className="card-title text-sm text-warning">
                <AlertTriangle className="w-4 h-4" /> Anomalies Detected
              </h3>
              <ul className="space-y-1">
                {profile.anomalies.map((a, i) => (
                  <li key={i} className="text-xs">
                    ⚠ {a.description}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Core Topics */}
        {profile.core_topics?.length > 0 && (
          <div className="card bg-base-200 shadow-sm">
            <div className="card-body p-3">
              <h3 className="card-title text-sm"> Core Topics</h3>
              <div className="flex flex-wrap gap-1">
                {profile.core_topics.map((topic, i) => (
                  <span key={i} className="badge badge-outline badge-sm">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Recommended Action */}
        {action && (
          <div className="card bg-base-200 border border-primary/30 shadow-sm">
            <div className="card-body p-3">
              <h3 className="card-title text-sm">
                 Recommended Action
                {/* <span className={`badge badge-sm ${ACTION_COLORS[action.action_type] || ""}`}>
                  {action.action_type}
                </span> */}
              </h3>
              <div className="bg-base-300 rounded-lg p-2 mt-1 flex items-start gap-2">
                <p className="text-sm flex-1 font-mono">{action.quick_copy}</p>
                <button
                  className="btn btn-ghost btn-xs"
                  onClick={() => copyToClipboard(action.quick_copy)}
                  title="Copy to clipboard"
                >
                  <Copy className="w-3 h-3" />
                </button>
              </div>
              <p className="text-xs text-base-content/60 mt-1">
                {action.rationale}
              </p>
            </div>
          </div>
        )}

        {/* Strategy Reasoning */}
        {verdict && (
          <div className="card bg-base-200 shadow-sm">
            <div className="card-body p-3">
              <h3 className="card-title text-sm"> Strategy Reasoning</h3>
              <p className="text-xs text-base-content/80">
                {verdict.reasoning}
              </p>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

export default AnalysisPanel;
