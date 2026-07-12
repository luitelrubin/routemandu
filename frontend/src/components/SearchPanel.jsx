import { useState } from "react";
import StationAutocomplete from "./StationAutocomplete";
import { queryTrip } from "../api/raptor";
import { mergeLegsByTrip } from "../utils/journey";

const todayYyyyMmDd = () => {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
};

const nowHhMmSs = () => {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:00`;
};

const formatSeconds = (secs) => {
  if (secs === null || secs === undefined) return "—";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const period = h >= 12 ? "PM" : "AM";
  const h12 = ((h + 11) % 12) + 1;
  return `${h12}:${String(m).padStart(2, "0")} ${period}`;
};

const formatDuration = (secs) => {
  if (!secs && secs !== 0) return "—";
  const m = Math.round(secs / 60);
  if (m < 60) return `${m} min`;
  return `${Math.floor(m / 60)} hr ${m % 60} min`;
};

/**
 * Left-hand search panel: origin/destination autocomplete, date/time, and
 * the resulting itinerary. Reports selections up via callbacks so the
 * parent page (Home) can drive the map.
 */
const SearchPanel = ({ onOriginChange, onDestinationChange, onResult }) => {
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [time, setTime] = useState(nowHhMmSs());
  const [date, setDate] = useState(todayYyyyMmDd());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [journey, setJourney] = useState(null);

  const handleOriginSelect = (station) => {
    setOrigin(station);
    onOriginChange?.(station);
  };

  const handleDestinationSelect = (station) => {
    setDestination(station);
    onDestinationChange?.(station);
  };

  const handleSwap = () => {
    const nextOrigin = destination;
    const nextDestination = origin;
    setOrigin(nextOrigin);
    setDestination(nextDestination);
    onOriginChange?.(nextOrigin);
    onDestinationChange?.(nextDestination);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!origin || !destination) {
      setError("Choose both an origin and a destination.");
      return;
    }

    setLoading(true);
    setError(null);
    setJourney(null);
    try {
      const data = await queryTrip({
        origin: origin.name,
        destination: destination.name,
        time,
        date,
        rounds: 5,
      });
      setJourney(data);
      onResult?.(data);
    } catch (err) {
      const detail = err?.response?.data?.detail || "Something went wrong finding that trip.";
      setError(detail);
      onResult?.(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto bg-white">
      <div className="border-b border-slate-100 px-5 py-4">
        <h1 className="text-xl font-bold text-slate-900">Plan Your Trip</h1>
        <p className="mt-1 text-sm text-slate-500">
          Get transit directions across the city.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4 px-5 py-4">
        <StationAutocomplete
          label="From"
          placeholder="Origin station"
          value={origin?.name}
          onSelect={handleOriginSelect}
        />

        <div className="-my-2 flex justify-center">
          <button
            type="button"
            onClick={handleSwap}
            className="rounded-full border border-slate-200 p-1.5 text-slate-400 hover:text-blue-600 hover:border-blue-300 transition-colors"
            aria-label="Swap origin and destination"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4M16 17H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </button>
        </div>

        <StationAutocomplete
          label="To"
          placeholder="Destination station"
          value={destination?.name}
          onSelect={handleDestinationSelect}
        />

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
              Date
            </label>
            <input
              type="date"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              value={`${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`}
              onChange={(e) => setDate(e.target.value.replaceAll("-", ""))}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
              Time
            </label>
            <input
              type="time"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              value={time.slice(0, 5)}
              onChange={(e) => setTime(`${e.target.value}:00`)}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors"
        >
          {loading ? "Searching…" : "Get Directions"}
        </button>

        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}
      </form>

      {journey && (
        <div className="flex-1 border-t border-slate-100 px-5 py-4">
          <div className="mb-3 flex items-baseline justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">
                {formatSeconds(journey.departure_time)} – {formatSeconds(journey.arrival_time)}
              </p>
              <p className="text-xs text-slate-500">
                {formatDuration(journey.duration)} · {journey.number_of_trips} trip
                {journey.number_of_trips === 1 ? "" : "s"}
              </p>
            </div>
          </div>

          <ol className="space-y-3">
            {mergeLegsByTrip(journey.legs).map((ride, i, rides) => (
              <li key={i}>
                {i > 0 && (
                  <p className="mb-3 flex items-center gap-2 text-xs font-medium text-amber-600">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4M16 17H4m0 0l4 4m-4-4l4-4" />
                    </svg>
                    Switch buses at {rides[i - 1].to_station}
                  </p>
                )}
                <div className="rounded-md border border-slate-200 p-3">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{formatSeconds(ride.departure_time)}</span>
                    <span>{formatSeconds(ride.arrival_time)}</span>
                  </div>
                  <p className="mt-1 flex items-center gap-2 text-sm text-slate-800">
                    <span
                      className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: ride.color }}
                    />
                    <span>
                      <span className="font-medium">{ride.from_station}</span>
                      {" → "}
                      <span className="font-medium">{ride.to_station}</span>
                    </span>
                  </p>
                  <div className="mt-1 flex items-center justify-between text-xs text-slate-500">
                    <span>{ride.trip_hint ? `Trip ${ride.trip_hint}` : "Walk"}</span>
                    {ride.stopCount > 1 && <span>{ride.stopCount} stops</span>}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
};

export default SearchPanel;
