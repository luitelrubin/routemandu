import client from "./client";

/** Search stations by name for autocomplete + map markers. */
export const searchStations = async (query, limit = 10) => {
  const res = await client.get("/raptor/stations/", {
    params: { q: query, limit },
  });
  return res.data;
};

/** Run a trip query. Returns { origin, destination, legs, shapes, ... }. */
export const queryTrip = async ({ origin, destination, time, date, rounds }) => {
  const res = await client.get("/raptor/query/", {
    params: { origin, destination, time, date, rounds },
  });
  return res.data;
};
