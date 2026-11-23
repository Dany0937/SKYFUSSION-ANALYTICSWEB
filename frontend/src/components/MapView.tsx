import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';

const COMBEIMA_CENTER: [number, number] = [4.4389, -75.2322];

export default function MapView() {
  return (
    <MapContainer center={COMBEIMA_CENTER} zoom={10} scrollWheelZoom className="h-80 w-full rounded-xl">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker position={COMBEIMA_CENTER}>
        <Popup>Cuenca del río Combeima · Ibagué, Tolima</Popup>
      </Marker>
    </MapContainer>
  );
}
