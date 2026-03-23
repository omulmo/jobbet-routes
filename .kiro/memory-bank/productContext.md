# Product Context

## Purpose
A personal tool for a Stockholm commuter to quickly check the fastest public transit option between locations. Optimized for the "about to leave" moment — open the app, see when to walk out the door.

## Problems It Solves
- Compares multiple transit routes simultaneously (different stops, different modes)
- Accounts for walking time on both ends (origin stop + destination stop)
- Filters out trips you can't catch anymore
- Picks the two most useful options: fastest arrival and earliest departure

## User Experience
- Mobile-first: designed for quick phone checks before leaving
- Direction toggle: derived from first trip in ordered list, switch between trip and its reverse with one tap
- Route cards show leave-by time, arrive-by time, transit legs with mode icons, and transfer stations
- Settings view for managing locations, stops, and trips
- Stop discovery: find nearby stops from location coordinates, auto-calculate walking time
- Geo-location: use browser GPS or enter address to set location coordinates

## Domain Model
- **Location**: named place with geo-coordinates and associated transit stops (e.g. "Hemma", "Jobbet")
- **Stop**: transit stop/station belonging to a location, with SL global stop ID and walk_minutes from the location
- **Trip**: ordered pair of locations (origin → destination), with sort_order for user-defined ordering
- **Route**: a specific journey option derived at runtime by pairing origin stops with destination stops via SL API
