import { useState } from "react";
import SearchPanel from "../components/SearchPanel";
import MapView from "../components/MapView";
import { mergeLegsByTrip } from "../utils/journey";

const Home = () => {
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [journey, setJourney] = useState(null);

  const rides = journey ? mergeLegsByTrip(journey.legs) : [];

  return (
    <>
      {/*
        Fixed (viewport-anchored) rather than absolute: this guarantees a
        concrete, non-zero height straight from the browser regardless of
        how the surrounding flex layout resolves, which is what Leaflet
        needs to actually paint tiles instead of rendering blank. top-14
        matches the navbar's h-14.
      */}
      <div className="fixed inset-x-0 bottom-0 top-14 z-0">
        <MapView
          origin={origin}
          destination={destination}
          rides={rides}
        />
      </div>

      {/*
        Search panel: on mobile it's a capped-height sheet stacked above
        the map (map remains visible below it); on sm+ it floats as a
        card over the top-left of the full-bleed map.
      */}
      <aside
        className="fixed inset-x-0 top-14 z-[500] h-[45vh] overflow-y-auto bg-white shadow-xl
                   sm:inset-x-auto sm:left-4 sm:top-[4.5rem] sm:bottom-4 sm:h-auto sm:w-[380px] sm:rounded-xl"
      >
        <SearchPanel
          onOriginChange={setOrigin}
          onDestinationChange={setDestination}
          onResult={setJourney}
        />
      </aside>
    </>
  );
};

export default Home;
