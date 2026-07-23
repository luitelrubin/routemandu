import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import StationAutocomplete from "../StationAutocomplete";
import { searchStations } from "../../api/raptor";

vi.mock("../../api/raptor", () => ({
  searchStations: vi.fn(),
}));

describe("StationAutocomplete", () => {
  beforeEach(() => {
    searchStations.mockReset();
    vi.useRealTimers();
  });

  it("renders the label and placeholder", () => {
    render(
      <StationAutocomplete
        label="Origin"
        placeholder="Where from?"
        value=""
        onSelect={vi.fn()}
      />
    );
    expect(screen.getByText("Origin")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Where from?")).toBeInTheDocument();
  });

  it("debounces the search and shows matching stations", async () => {
    searchStations.mockResolvedValue([
      { id: "1", name: "Ratnapark", lat: 27.7, lon: 85.31 },
      { id: "2", name: "Ratna Bus Park", lat: 27.71, lon: 85.32 },
    ]);

    render(
      <StationAutocomplete
        label="Origin"
        placeholder="Where from?"
        value=""
        onSelect={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText("Where from?");
    fireEvent.change(input, { target: { value: "ratna" } });

    await waitFor(() => expect(searchStations).toHaveBeenCalledWith("ratna", 8));

    expect(await screen.findByText("Ratnapark")).toBeInTheDocument();
    expect(screen.getByText("Ratna Bus Park")).toBeInTheDocument();
  });

  it("calls onSelect with the chosen station and fills the input", async () => {
    searchStations.mockResolvedValue([
      { id: "1", name: "Ratnapark", lat: 27.7, lon: 85.31 },
    ]);
    const onSelect = vi.fn();

    render(
      <StationAutocomplete
        label="Origin"
        placeholder="Where from?"
        value=""
        onSelect={onSelect}
      />
    );

    const input = screen.getByPlaceholderText("Where from?");
    fireEvent.change(input, { target: { value: "ratna" } });

    const option = await screen.findByText("Ratnapark");
    fireEvent.click(option);

    expect(onSelect).toHaveBeenCalledWith({
      id: "1",
      name: "Ratnapark",
      lat: 27.7,
      lon: 85.31,
    });
    expect(input.value).toBe("Ratnapark");
    expect(screen.queryByText("Ratnapark")).not.toBeInTheDocument();
  });

  it("shows 'No stations found' when the search returns nothing", async () => {
    searchStations.mockResolvedValue([]);

    render(
      <StationAutocomplete
        label="Origin"
        placeholder="Where from?"
        value=""
        onSelect={vi.fn()}
      />
    );

    fireEvent.change(screen.getByPlaceholderText("Where from?"), {
      target: { value: "xyz" },
    });

    expect(await screen.findByText("No stations found")).toBeInTheDocument();
  });

  it("clears results and swallows errors when the search fails", async () => {
    searchStations.mockRejectedValue(new Error("network down"));
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <StationAutocomplete
        label="Origin"
        placeholder="Where from?"
        value=""
        onSelect={vi.fn()}
      />
    );

    fireEvent.change(screen.getByPlaceholderText("Where from?"), {
      target: { value: "xyz" },
    });

    expect(await screen.findByText("No stations found")).toBeInTheDocument();
    consoleError.mockRestore();
  });

  it("syncs the input when the value prop changes externally", () => {
    const { rerender } = render(
      <StationAutocomplete
        label="Origin"
        placeholder="Where from?"
        value="Ratnapark"
        onSelect={vi.fn()}
      />
    );
    expect(screen.getByPlaceholderText("Where from?").value).toBe("Ratnapark");

    rerender(
      <StationAutocomplete
        label="Origin"
        placeholder="Where from?"
        value="Koteshowr"
        onSelect={vi.fn()}
      />
    );
    expect(screen.getByPlaceholderText("Where from?").value).toBe("Koteshowr");
  });
});
