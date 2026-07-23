import { describe, it, expect, vi, beforeEach } from "vitest";
import client from "../client";
import { searchStations, queryTrip } from "../raptor";

vi.mock("../client", () => ({
  default: { get: vi.fn() },
}));

describe("searchStations", () => {
  beforeEach(() => {
    client.get.mockReset();
  });

  it("calls the stations endpoint with q and limit params", async () => {
    client.get.mockResolvedValue({ data: [{ id: "1", name: "Ratnapark" }] });
    const results = await searchStations("ratna", 5);
    expect(client.get).toHaveBeenCalledWith("/raptor/stations/", {
      params: { q: "ratna", limit: 5 },
    });
    expect(results).toEqual([{ id: "1", name: "Ratnapark" }]);
  });

  it("defaults limit to 10 when not provided", async () => {
    client.get.mockResolvedValue({ data: [] });
    await searchStations("kote");
    expect(client.get).toHaveBeenCalledWith("/raptor/stations/", {
      params: { q: "kote", limit: 10 },
    });
  });
});

describe("queryTrip", () => {
  beforeEach(() => {
    client.get.mockReset();
  });

  it("calls the query endpoint with all trip params", async () => {
    const payload = { legs: [] };
    client.get.mockResolvedValue({ data: payload });
    const result = await queryTrip({
      origin: "A",
      destination: "B",
      time: "08:00:00",
      date: "20260712",
      rounds: 5,
    });
    expect(client.get).toHaveBeenCalledWith("/raptor/query/", {
      params: {
        origin: "A",
        destination: "B",
        time: "08:00:00",
        date: "20260712",
        rounds: 5,
      },
    });
    expect(result).toEqual(payload);
  });

  it("propagates errors from the client", async () => {
    client.get.mockRejectedValue(new Error("Network error"));
    await expect(
      queryTrip({ origin: "A", destination: "B" })
    ).rejects.toThrow("Network error");
  });
});
