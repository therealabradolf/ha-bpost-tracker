# Bpost Tracker for Home Assistant

Track any bpost shipment in Home Assistant using just its **tracking number
(barcode)** and **postal code** — the same two fields you'd fill in on the
[bpost track & trace website](https://track.bpost.cloud). No bpost account
needed.

## ⚠️ Disclaimer

This integration talks to the **public, unauthenticated JSON API** that
powers `track.bpost.cloud`. It is not an official, documented bpost API —
bpost could change or block it at any time without notice. Use at your own
risk. If it breaks, please open an issue.

## Features

- Add any number of shipments, each becomes its own device.
- A status sensor per shipment with:
  - Current status code (e.g. `delivered`, and other bpost step names)
  - Human-readable status description, in your Home Assistant language
    (Dutch, French or English — falls back to English)
  - Sender name
  - Expected delivery time window, when bpost provides one
  - Number of stops left on the delivery round, when available
- A camera entity showing the "safe place" delivery picture, when the
  courier left the parcel without a signature and bpost has a photo for it.
- Polling slows down automatically (every 6 hours instead of every 15
  minutes) once a shipment is marked as delivered.

## Installation

### Via HACS (custom repository)

1. In Home Assistant, go to **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/therealabradolf/ha-bpost-tracker`
   as an **Integration**.
3. Install "Bpost Tracker" from HACS, then restart Home Assistant.

### Manual

Copy `custom_components/bpost_tracker` into your Home Assistant
`custom_components` folder and restart Home Assistant.

## Adding a shipment

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Bpost Tracker**.
3. Enter the tracking number and postal code (and optionally a friendly
   name), exactly as you would on the bpost tracking website.
4. Repeat for each shipment you want to track — each one is added as a
   separate integration entry/device.

To stop tracking a shipment, remove its entry under **Settings → Devices &
Services**.

## Known limitations

- bpost's `activeStep` status codes are not officially documented, so the
  sensor state shows the raw code bpost returns. The `status_description`
  attribute contains the full, human-readable, localized text.
- This does **not** cover the "My bpost" app account features (automatic
  mail scans, parcels auto-linked to your account without a tracking
  number). That uses a different, authenticated mobile API that would need
  separate reverse-engineering.
