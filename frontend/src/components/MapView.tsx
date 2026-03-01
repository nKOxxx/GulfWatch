import { useEffect, useRef } from 'react'
import Map from 'react-map-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

interface Region {
  id: string
  name: string
  code: string
  lat: number
  lng: number
}

interface Props {
  region: Region | null
}

export function MapView({ region }: Props) {
  const mapRef = useRef<any>(null)

  useEffect(() => {
    if (region && mapRef.current) {
      mapRef.current.flyTo({
        center: [region.lng, region.lat],
        zoom: 11,
        duration: 1500
      })
    }
  }, [region])

  if (!region) {
    return <div className="map-loading">Loading map...</div>
  }

  return (
    <Map
      ref={mapRef}
      initialViewState={{
        longitude: region.lng,
        latitude: region.lat,
        zoom: 11
      }}
      style={{ width: '100%', height: '100%' }}
      mapStyle="mapbox://styles/mapbox/dark-v11"
      mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
    >
      {/* Incident markers would go here */}
    </Map>
  )
}
