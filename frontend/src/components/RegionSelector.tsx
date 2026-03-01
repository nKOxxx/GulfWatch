import { useState } from 'react'

interface Region {
  id: string
  name: string
  country: string
  code: string
  lat: number
  lng: number
}

interface Props {
  regions: Region[]
  selected: Region | null
  onSelect: (region: Region) => void
}

export function RegionSelector({ regions, selected, onSelect }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="region-selector">
      <label>Location:</label>
      <select 
        value={selected?.code || ''}
        onChange={(e) => {
          const region = regions.find(r => r.code === e.target.value)
          if (region) onSelect(region)
        }}
      >
        {regions.map(region => (
          <option key={region.id} value={region.code}>
            {region.name}, {region.country}
          </option>
        ))}
      </select>
    </div>
  )
}
