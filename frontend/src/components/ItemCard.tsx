"use client";

interface Item {
  id: number;
  title: string;
  type: string;
  due_date?: string | null;
  status: string;
  nag_policy?: string | null;
}

interface ItemCardProps {
  item: Item;
  onDone?: (id: number) => void;
}

const TYPE_CONFIG: Record<
  string,
  { label: string; barColor: string; tagBg: string; tagText: string }
> = {
  task: {
    label: "TASK",
    barColor: "bg-orange-500",
    tagBg: "bg-orange-500/15",
    tagText: "text-orange-400",
  },
  grocery: {
    label: "GROCERY",
    barColor: "bg-emerald-500",
    tagBg: "bg-emerald-500/15",
    tagText: "text-emerald-400",
  },
  link: {
    label: "LINK",
    barColor: "bg-blue-500",
    tagBg: "bg-blue-500/15",
    tagText: "text-blue-400",
  },
  read: {
    label: "READ",
    barColor: "bg-pink-500",
    tagBg: "bg-pink-500/15",
    tagText: "text-pink-400",
  },
  expense: {
    label: "EXPENSE",
    barColor: "bg-amber-400",
    tagBg: "bg-amber-400/15",
    tagText: "text-amber-300",
  },
  note: {
    label: "NOTE",
    barColor: "bg-purple-500",
    tagBg: "bg-purple-500/15",
    tagText: "text-purple-400",
  },
};

export default function ItemCard({ item, onDone }: ItemCardProps) {
  // Case-insensitive lookup (fixes all items defaulting to NOTE)
  const normalizedType = (item.type || "note").toLowerCase();
  const config = TYPE_CONFIG[normalizedType] || TYPE_CONFIG.note;
  const isDone = item.status === "done";

  return (
    <div
      className={`relative flex items-center gap-3 rounded-2xl border border-border-subtle bg-surface-1 p-3.5 pl-4 transition-all ${
        isDone ? "opacity-35" : ""
      }`}
    >
      {/* 3px Left Colored Indicator Line */}
      <div
        className={`absolute left-0 top-3 bottom-3 w-[3px] rounded-full ${config.barColor}`}
      />

      {/* Circle Checkbox (Click to mark Done) */}
      <button
        onClick={() => !isDone && onDone && onDone(item.id)}
        disabled={isDone}
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition ${
          isDone
            ? "border-emerald-500 bg-emerald-500 text-black"
            : "border-border-strong hover:border-emerald-400 hover:bg-emerald-500/10"
        }`}
      >
        {isDone && (
          <svg
            className="h-3 w-3 stroke-current stroke-[3]"
            fill="none"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4.5 12.75l6 6 9-13.5"
            />
          </svg>
        )}
      </button>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p
          className={`text-sm font-medium text-content-primary ${
            isDone ? "line-through text-content-tertiary" : ""
          }`}
        >
          {item.title}
        </p>

        {/* Badge & Metadata row */}
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <span
            className={`rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${config.tagBg} ${config.tagText}`}
          >
            {config.label}
          </span>

          {item.due_date && (
            <span className="text-[11px] text-content-tertiary">
              📅 {new Date(item.due_date).toLocaleDateString()}
            </span>
          )}

          {item.nag_policy && item.nag_policy !== "off" && (
            <span className="text-[11px] text-content-tertiary">
              🔔 {item.nag_policy}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}