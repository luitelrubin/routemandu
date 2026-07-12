import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, ZoomControl, useMap } from "react-leaflet";
import L from "leaflet";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

// Vite bundles leaflet's default marker images under a hashed path, which
// breaks Leaflet's own icon URL detection - point it at the bundled
// assets explicitly.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const KATHMANDU_CENTER = [27.7172, 85.324];

/** Re-centers/fits the map whenever the given bounds change. */
const FitBounds = ({ bounds }) => {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [48, 48], maxZoom: 16 });
    }
  }, [bounds, map]);
  return null;
};

/**
 * Renders the base map, station search markers, an origin/destination
 * marker pair, and one colored polyline per merged "ride" (see
 * utils/journey.js) - i.e. one segment/color from the origin stop to the
 * first transfer, another from there to the next, and so on to the
 * destination.
 */
const MapView = ({ stations = [], origin, destination, rides = [] }) => {
  const points = [];
  if (origin?.lat && origin?.lon) points.push([origin.lat, origin.lon]);
  if (destination?.lat && destination?.lon) points.push([destination.lat, destination.lon]);
  rides.forEach((ride) => {
    (ride.coordinates || []).forEach(([lon, lat]) => points.push([lat, lon]));
  });

  return (
    <MapContainer
      center={KATHMANDU_CENTER}
      zoom={13}
      className="h-full w-full"
      scrollWheelZoom
      zoomControl={false}
    >
      <ZoomControl position="topright" />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {points.length > 0 && <FitBounds bounds={points} />}

      {rides.map((ride, i) =>
        ride.coordinates && ride.coordinates.length >= 2 ? (
          <GeoJSON
            key={`${ride.gtfs_trip_id}-${i}-${ride.coordinates.length}`}
            data={{ type: "LineString", coordinates: ride.coordinates }}
            style={{ color: ride.color, weight: 5, opacity: 0.85 }}
          />
        ) : null,
      )}

      {!origin &&
        !destination &&
        stations.map((station) =>
          station.lat && station.lon ? (
            <Marker key={station.id} position={[station.lat, station.lon]}>
              <Popup>{station.name}</Popup>
            </Marker>
          ) : null,
        )}

      {origin?.lat && origin?.lon && (
        <Marker position={[origin.lat, origin.lon]}>
          <Popup>Origin: {origin.name}</Popup>
        </Marker>
      )}

      {destination?.lat && destination?.lon && (
        <Marker position={[destination.lat, destination.lon]}>
          <Popup>Destination: {destination.name}</Popup>
        </Marker>
      )}
    </MapContainer>
  );
};

export default MapView;
