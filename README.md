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

## Adding a shipment from a dashboard

The integration also exposes a `bpost_tracker.add_shipment` service
(`tracking_number`, `postal_code`, optional `name`), so you can add
shipments without leaving a dashboard. A simple way to wire it up:

1. Create three `input_text` helpers (**Settings → Devices & Services →
   Helpers**): one each for tracking number, postal code, and name.
2. Create a script that calls `bpost_tracker.add_shipment` with those
   helpers' values, then clears them:

   ```yaml
   sequence:
     - action: bpost_tracker.add_shipment
       data:
         tracking_number: "{{ states('input_text.bpost_new_tracking_number') }}"
         postal_code: "{{ states('input_text.bpost_new_postal_code') }}"
         name: "{{ states('input_text.bpost_new_name') }}"
     - action: input_text.set_value
       target:
         entity_id: input_text.bpost_new_tracking_number
       data:
         value: ""
     - action: input_text.set_value
       target:
         entity_id: input_text.bpost_new_postal_code
       data:
         value: ""
     - action: input_text.set_value
       target:
         entity_id: input_text.bpost_new_name
       data:
         value: ""
   ```

3. Add an **entities** card with the three helpers and the script — tapping
   the script's icon runs it.

If the tracking number/postal code combination is invalid, the service call
fails with an error (shown in Home Assistant's UI / logs) instead of
silently doing nothing.

Prefer not to build any of that? A single dashboard button can jump
straight to the normal "Add integration" form instead, skipping the search
step:

```yaml
type: button
name: Nieuw pakje toevoegen
icon: mdi:package-variant-plus
tap_action:
  action: url
  url_path: https://my.home-assistant.io/redirect/config_flow_start/?domain=bpost_tracker
```

## Known limitations

- bpost's `activeStep` status codes are not officially documented, so the
  sensor state shows the raw code bpost returns. The `status_description`
  attribute contains the full, human-readable, localized text.
- This does **not** cover the "My bpost" app account features (automatic
  mail scans, parcels auto-linked to your account without a tracking
  number). That uses a different, authenticated mobile API that would need
  separate reverse-engineering.
