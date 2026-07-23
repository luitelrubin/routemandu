import { describe, it, expect } from "vitest";
import { ROUTE_COLORS, colorForRideIndex, mergeLegsByTrip } from "../journey";

describe("colorForRideIndex", () => {
  it("returns the color at the given index", () => {
    expect(colorForRideIndex(0)).toBe(ROUTE_COLORS[0]);
    expect(colorForRideIndex(1)).toBe(ROUTE_COLORS[1]);
  });

  it("wraps around when the index exceeds the palette length", () => {
    expect(colorForRideIndex(ROUTE_COLORS.length)).toBe(ROUTE_COLORS[0]);
    expect(colorForRideIndex(ROUTE_COLORS.length + 2)).toBe(ROUTE_COLORS[2]);
  });
});

describe("mergeLegsByTrip", () => {
  it("returns an empty array for no legs", () => {
    expect(mergeLegsByTrip([])).toEqual([]);
    expect(mergeLegsByTrip(undefined)).toEqual([]);
  });

  it("keeps a single leg as its own ride", () => {
    const legs = [
      {
        trip_hint: "Route 1",
        from_station: "A",
        to_station: "B",
        departure_time: "08:00",
        arrival_time: "08:30",
        geometry: { coordinates: [[85.3, 27.7], [85.31, 27.71]] },
      },
    ];
    const rides = mergeLegsByTrip(legs);
    expect(rides).toHaveLength(1);
    expect(rides[0].stopCount).toBe(1);
    expect(rides[0].to_station).toBe("B");
    expect(rides[0].coordinates).toEqual(legs[0].geometry.coordinates);
  });

  it("merges consecutive legs sharing the same trip_hint into one ride", () => {
    const legs = [
      {
        trip_hint: "Route 1",
        from_station: "A",
        to_station: "B",
        arrival_time: "08:30",
        geometry: { coordinates: [[0, 0], [1, 1]] },
      },
      {
        trip_hint: "Route 1",
        from_station: "B",
        to_station: "C",
        arrival_time: "09:00",
        geometry: { coordinates: [[1, 1], [2, 2]] },
      },
    ];
    const rides = mergeLegsByTrip(legs);
    expect(rides).toHaveLength(1);
    expect(rides[0].stopCount).toBe(2);
    expect(rides[0].to_station).toBe("C");
    expect(rides[0].arrival_time).toBe("09:00");
    // Duplicate seam point [1, 1] is not repeated.
    expect(rides[0].coordinates).toEqual([[0, 0], [1, 1], [2, 2]]);
  });

  it("starts a new ride when trip_hint changes (a transfer)", () => {
    const legs = [
      {
        trip_hint: "Route 1",
        from_station: "A",
        to_station: "B",
        geometry: { coordinates: [[0, 0], [1, 1]] },
      },
      {
        trip_hint: "Route 2",
        from_station: "B",
        to_station: "C",
        geometry: { coordinates: [[1, 1], [2, 2]] },
      },
    ];
    const rides = mergeLegsByTrip(legs);
    expect(rides).toHaveLength(2);
    expect(rides[0].trip_hint).toBe("Route 1");
    expect(rides[1].trip_hint).toBe("Route 2");
  });

  it("assigns a distinct color to each ride in order", () => {
    const legs = [
      { trip_hint: "Route 1", geometry: { coordinates: [] } },
      { trip_hint: "Route 2", geometry: { coordinates: [] } },
      { trip_hint: "Route 3", geometry: { coordinates: [] } },
    ];
    const rides = mergeLegsByTrip(legs);
    expect(rides.map((r) => r.color)).toEqual([
      colorForRideIndex(0),
      colorForRideIndex(1),
      colorForRideIndex(2),
    ]);
  });

  it("handles legs with no geometry gracefully", () => {
    const legs = [
      { trip_hint: "Route 1", to_station: "B" },
      { trip_hint: "Route 1", to_station: "C" },
    ];
    const rides = mergeLegsByTrip(legs);
    expect(rides).toHaveLength(1);
    expect(rides[0].coordinates).toEqual([]);
  });

  it("does not concatenate a duplicate point when segments don't touch", () => {
    const legs = [
      {
        trip_hint: "Route 1",
        geometry: { coordinates: [[0, 0], [1, 1]] },
      },
      {
        trip_hint: "Route 1",
        geometry: { coordinates: [[5, 5], [6, 6]] },
      },
    ];
    const rides = mergeLegsByTrip(legs);
    expect(rides[0].coordinates).toEqual([[0, 0], [1, 1], [5, 5], [6, 6]]);
  });
});
