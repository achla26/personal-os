"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import ItemCard from "./ItemCard";

export default function NowTab({ onDoneItem }: { onDoneItem: (id: number) => void }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchNow = async () => {
    try {
      const res = await apiFetch("/items/grouped?status=open");
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNow();
  }, []);

  const handleDone = async (id: number) => {
    onDoneItem(id);
    // Optimistically remove from view
    fetchNow(); 
  };

  if (loading) return <div className="p-6 text-center text-sm text-content-tertiary">Loading loops...</div>;

  const total = (data?.overdue?.length || 0) + (data?.today?.length || 0) + (data?.this_week?.length || 0) + (data?.someday?.length || 0);

  if (total === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-6 text-center">
        <span className="text-4xl mb-2">✨</span>
        <p className="text-content-secondary font-medium">Sab clear hai!</p>
        <p className="text-xs text-content-tertiary mt-1">Nothing to do right now.</p>
      </div>
    );
  }

  const renderSection = (title: string, items: any[], color: string) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="mb-6">
        <h3 className={`mb-3 text-xs font-bold uppercase tracking-wider ${color}`}>
          ▲ {title} ({items.length})
        </h3>
        <div className="flex flex-col gap-3">
          {items.map((item) => (
            <ItemCard key={item.id} item={item} onDone={handleDone} />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {renderSection("Overdue", data?.overdue, "text-red-400")}
      {renderSection("Today", data?.today, "text-orange-400")}
      {renderSection("This Week", data?.this_week, "text-blue-400")}
      {renderSection("Someday", data?.someday, "text-content-tertiary")}
    </div>
  );
}