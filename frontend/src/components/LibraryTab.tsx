"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import ItemCard from "./ItemCard";

export default function LibraryTab({ onDoneItem }: { onDoneItem: (id: number) => void }) {
  const [items, setItems] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const TYPES = ["task", "grocery", "link", "read", "expense", "note"];

  const fetchLibrary = async () => {
    setLoading(true);
    try {
      let url = "/items?";
      if (search) url += `q=${search}&`;
      if (filter) url += `item_type=${filter}&`;
      const res = await apiFetch(url);
      setItems(Array.isArray(res) ? res : []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => fetchLibrary(), 300);
    return () => clearTimeout(timer);
  }, [search, filter]);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="p-4 border-b border-border-subtle bg-surface-1">
        <input
          type="text"
          placeholder="Search anything..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg bg-surface-2 p-2 text-sm text-content-primary placeholder-content-tertiary outline-none focus:border focus:border-brand"
        />
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          <button
            onClick={() => setFilter("")}
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${!filter ? "bg-brand text-white" : "bg-surface-2 text-content-secondary"}`}
          >
            All
          </button>
          {TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t === filter ? "" : t)}
              className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
                filter === t ? "bg-brand text-white" : "bg-surface-2 text-content-secondary"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        {loading ? (
          <div className="text-center text-sm text-content-tertiary">Searching...</div>
        ) : items.length === 0 ? (
          <div className="text-center text-sm text-content-tertiary">No items found.</div>
        ) : (
          items.map((item) => <ItemCard key={item.id} item={item} onDone={onDoneItem} />)
        )}
      </div>
    </div>
  );
}