# Bpost Tracker for Home Assistant

Track any bpost shipment in Home Assistant using just its **tracking number
(barcode)** and **postal code** — the same two fields you'd fill in on the
[bpost track & trace website](https://track.bpost.cloud). No bpost account
needed.

Add as many shipments as you like — each gets its own status sensor (and a
delivery-picture camera when bpost provides one). New shipments can be added
through the normal Home Assistant UI, or straight from a dashboard using the
integration's own `add_shipment` service. An `auto-entities` card can keep a
dashboard showing every tracked shipment automatically, with no manual
editing every time you add one.

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
- Shipments can be removed automatically a configurable number of days after
  delivery (10 days by default, 0 to disable) — set when adding a shipment,
  or changed later via the entry's **Configure** button under
  **Settings → Devices & Services**.

## Installation

### Via HACS (custom repository)

1. In Home Assistant, go to **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/therealabradolf/ha-bpost-tracker`
   as an **Integration**.
3. Install "Bpost Tracker" from HACS, then restart Home Assistant.

### Manual

Copy `custom_components/bpost_tracker` into your Home Assistant
`custom_components` folder and restart Home Assistant.

## Usage

There are three ways to add a shipment, from least to most setup required.

### Option A: the standard Home Assistant UI

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Bpost Tracker**.
3. Enter the tracking number and postal code (and optionally a friendly
   name), exactly as you would on the bpost tracking website.
4. Repeat for each shipment you want to track — each one is added as a
   separate integration entry/device.

To stop tracking a shipment, remove its entry under **Settings → Devices &
Services**.

### Option B: a dashboard button that jumps to that same form

No integration code needed for this — Home Assistant can deep-link straight
into the "Add integration" form for a specific integration, skipping the
search step. Add this card to a dashboard:

```yaml
type: button
name: Add new shipment
icon: mdi:package-variant-plus
tap_action:
  action: url
  url_path: https://my.home-assistant.io/redirect/config_flow_start/?domain=bpost_tracker
```

You'll still need to type in the tracking number and postal code yourself —
this just removes the search step.

### Option C: fill in and submit from the dashboard itself, no popup

The integration exposes a `bpost_tracker.add_shipment` service
(fields: `tracking_number`, `postal_code`, optional `name`, optional
`remove_after_days`) so a whole "add shipment" form can live directly on a
dashboard:

1. Create three `input_text` helpers (**Settings → Devices & Services →
   Helpers → Add helper → Text**): one each for tracking number, postal
   code, and name.
2. Create a script (**Settings → Automations & Scenes → Scripts**) that
   calls `bpost_tracker.add_shipment` with those helpers' values, then
   clears them:

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
   the script's row runs it.

If the tracking number/postal code combination is invalid, the service call
fails with a visible error instead of silently doing nothing, and no
shipment gets added.

## Viewing all your shipments on a dashboard

Rather than adding each new shipment's sensor to a dashboard by hand, use
the [auto-entities](https://github.com/thomasloven/lovelace-auto-entities)
custom card (available in HACS) to have a card populate itself:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: Bpost shipments
filter:
  include:
    - integration: bpost_tracker
      domain: sensor
sort:
  method: state
```

Add a second card the same way with `domain: camera` instead of `sensor` to
show delivery pictures automatically.

## Known limitations

- bpost's `activeStep` status codes are not officially documented, so the
  sensor state shows the raw code bpost returns. The `status_description`
  attribute contains the full, human-readable, localized text.
- This does **not** cover the "My bpost" app account features (automatic
  mail scans, parcels auto-linked to your account without a tracking
  number). That uses a different, authenticated mobile API that would need
  separate reverse-engineering.
