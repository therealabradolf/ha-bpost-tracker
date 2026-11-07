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
- A status sensor per shipment. Its state is bpost's raw step name, such as
  `delivered_kariboo_point` — the exact value differs per delivery method, so
  don't compare the state to a fixed text to detect delivery. Use the
  `delivered` attribute for that. The sensor carries these attributes:

  | Attribute | Meaning |
  | --- | --- |
  | `delivered` | `true` once bpost has recorded an actual delivery |
  | `status_label` | Short readable status, e.g. "Picked Up" |
  | `status_description` | Description of the latest tracking event |
  | `status_time` | Date and time of that event, e.g. `2026-08-07 11:52` |
  | `sender` | Sender name, when bpost provides one |
  | `expected_delivery_from`, `expected_delivery_to` | Expected delivery window, when bpost provides one |
  | `stops_until_delivery` | Stops left on the delivery round, when available |
  | `tracking_number`, `postal_code` | What the shipment was added with |

  Labels and descriptions follow your Home Assistant language (Dutch, French
  or English — falls back to English).
- A camera entity showing the "safe place" delivery picture, when the
  courier left the parcel without a signature and bpost has a photo for it.
- Polling slows down automatically (every 6 hours instead of every 15
  minutes) once a shipment is marked as delivered.
- Shipments can be removed automatically a configurable number of days after
  delivery (10 days by default, 0 to disable) — set when adding a shipment,
  or changed later via the entry's **Configure** button under
  **Settings → Devices & Services**.

## Installation

Requires Home Assistant 2024.12 or newer.

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

Input is normalised and checked before anything is stored: the tracking
number must be 8–40 letters/digits (case and spaces are ignored), the postal
code 3–10 characters, and the name at most 100 characters.

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
dashboard. Like the UI flow, the service **requires an administrator**: a
script that a non-admin user triggers will fail with a permission error.

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

### Making a tile open the bpost tracking page directly

bpost's tracker supports a deep link that opens a specific shipment directly:

```
https://track.bpost.cloud/btr/web/#/search?lang=nl&itemCode=<tracking_number>&postalCode=<postal_code>
```

Since a card's `tap_action` can't contain a live template, build the tiles
with `auto-entities`' `template` filter instead of `include`, so the URL is
computed once per entity when the card renders:

```yaml
type: custom:auto-entities
card:
  type: grid
  columns: 2
  square: false
card_param: cards
filter:
  template: >
    [
    {% for entity_id in integration_entities('bpost_tracker') if entity_id.startswith('sensor.') %}
    {
      "entity": "{{ entity_id }}",
      "type": "tile",
      "tap_action": {
        "action": "url",
        "url_path": "https://track.bpost.cloud/btr/web/#/search?lang=nl&itemCode={{ state_attr(entity_id, 'tracking_number') | urlencode }}&postalCode={{ state_attr(entity_id, 'postal_code') | urlencode }}"
      },
      "hold_action": {"action": "more-info"}
    }{{ "," if not loop.last }}
    {% endfor %}
    ]
sort:
  method: state
```

Tapping a tile opens that shipment's bpost tracking page in a new tab;
long-pressing still shows the normal Home Assistant more-info dialog.

Keep the `| urlencode` filters: the template builds JSON by string
concatenation, so a value containing a backslash or quote would otherwise
break the whole card for every shipment.

## Known limitations

- bpost's `activeStep` status codes are not officially documented, so the
  sensor state shows the raw code bpost returns. Use the `delivered`
  attribute to detect delivery, and `status_label` / `status_description`
  for readable, localized text.
- This does **not** cover the "My bpost" app account features (automatic
  mail scans, parcels auto-linked to your account without a tracking
  number). That uses a different, authenticated mobile API that would need
  separate reverse-engineering.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for what changed in each version.
