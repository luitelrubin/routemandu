export const ROUTE_COLORS = [
  "#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2",
];

export const colorForRideIndex = (i) => ROUTE_COLORS[i % ROUTE_COLORS.length];

/**
 * Join two adjacent LineString coordinate arrays into one continuous path,
 * dropping the duplicate point at the seam if the two segments touch.
 */
const concatCoordinates = (a = [], b = []) => {
  if (a.length === 0) return b;
  if (b.length === 0) return a;
  const [lastLon, lastLat] = a[a.length - 1];
  const [firstLon, firstLat] = b[0];
  const touching = lastLon === firstLon && lastLat === firstLat;
  return [...a, ...(touching ? b.slice(1) : b)];
};

/**
 * Consecutive legs that share the same trip_hint are the same physical
 * bus ride (RAPTOR reports each stop-to-stop hop as its own leg). Collapse
 * those runs into a single "ride": one card in the itinerary, one colored
 * polyline on the map (built by stitching together each hop's own
 * boarding-stop-to-alighting-stop geometry), only splitting into a new
 * ride when the trip_hint actually changes - i.e. a transfer is required.
 */
export const mergeLegsByTrip = (legs = []) => {
  const rides = [];
  for (const leg of legs) {
    const current = rides[rides.length - 1];
    if (current && current.trip_hint === leg.trip_hint) {
      current.to_station = leg.to_station;
      current.to_stop = leg.to_stop;
      current.to_platform_code = leg.to_platform_code;
      current.arrival_time = leg.arrival_time;
      current.stopCount += 1;
      if (leg.geometry?.coordinates) {
        current.coordinates = concatCoordinates(current.coordinates, leg.geometry.coordinates);
      }
    } else {
      rides.push({
        ...leg,
        stopCount: 1,
        coordinates: leg.geometry?.coordinates || [],
      });
    }
  }
  return rides.map((ride, i) => ({ ...ride, color: colorForRideIndex(i) }));
};
