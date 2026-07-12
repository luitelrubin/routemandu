import { useEffect, useRef, useState } from "react";
import { searchStations } from "../api/raptor";

/**
 * Text input with a debounced dropdown of matching stations.
 * Calls onSelect(station) with { id, name, lat, lon } when the user picks one.
 */
const StationAutocomplete = ({ label, placeholder, value, onSelect }) => {
  const [query, setQuery] = useState(value || "");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const boxRef = useRef(null);

  useEffect(() => {
    setQuery(value || "");
  }, [value]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleChange = (e) => {
    const text = e.target.value;
    setQuery(text);
    setOpen(true);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchStations(text, 8);
        setResults(data);
      } catch (err) {
        console.error(err);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
  };

  const handleSelect = (station) => {
    setQuery(station.name);
    setOpen(false);
    onSelect(station);
  };

  return (
    <div className="relative" ref={boxRef}>
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
        {label}
      </label>
      <input
        type="text"
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
        placeholder={placeholder}
        value={query}
        onFocus={() => query && setOpen(true)}
        onChange={handleChange}
        autoComplete="off"
      />
      {open && (query.length > 0) && (
        <div className="absolute z-[1100] mt-1 w-full max-h-64 overflow-auto rounded-md border border-slate-200 bg-white shadow-lg">
          {loading && (
            <div className="px-3 py-2 text-sm text-slate-400">Searching…</div>
          )}
          {!loading && results.length === 0 && (
            <div className="px-3 py-2 text-sm text-slate-400">No stations found</div>
          )}
          {!loading &&
            results.map((station) => (
              <button
                type="button"
                key={station.id}
                onClick={() => handleSelect(station)}
                className="block w-full text-left px-3 py-2 text-sm hover:bg-blue-50 transition-colors"
              >
                {station.name}
              </button>
            ))}
        </div>
      )}
    </div>
  );
};

export default StationAutocomplete;
