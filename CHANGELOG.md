# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.4.0] - 2026-11-07

Security hardening release, based on a review of the integration. Nothing
critical was found, but several weak spots are closed.

### Security

- **`bpost_tracker.add_shipment` now requires an administrator.** Previously
  any logged-in Home Assistant user could call it, creating persistent config
  entries and querying bpost through your instance, which is more than the
  UI flow (admin only) allows.
- **Tracking numbers and postal codes are normalised and validated** before
  they are stored: tracking numbers must be 8–40 letters/digits (case and
  whitespace are ignored), postal codes 3–10 characters, names at most 100
  characters. bpost itself accepts almost any junk around a barcode (`&`, `#`,
  `\`, spaces, lowercase) and did not appear to check the postal code, so a
  successful lookup was no proof of clean input. This also stops duplicate
  entries that differed only in case or whitespace.
- **Dashboard recipe is injection-safe**: the `auto-entities` template now
  uses `| urlencode`. Without it, one tracking number ending in a backslash
  produced invalid JSON and blanked the whole shipments card.
- **Hardened the bpost client**
  - 15 second request timeout (aiohttp's default is five minutes), also
    handled in the config flow and coordinator as "cannot connect" instead of
    an unexpected error.
  - The optional "stops until delivery" lookup is best effort and can no
    longer fail a shipment update.
  - Delivery pictures are decoded strictly and must be a real JPEG/PNG of at
    most 5 MB. bpost answers HTTP 200 with a JSON error body for unknown
    pictures, which the old lenient decoding would have served as an image.
  - The picture is fetched once per image and cached, instead of contacting
    bpost on every frontend request.
- **CI**: workflow token limited to `contents: read`, third-party actions
  pinned to commit SHAs, and Dependabot added to keep them current.

### Changed

- Validation errors for the tracking number and postal code are shown next to
  the field (new `invalid_tracking_number` / `invalid_postal_code` messages,
  English and Dutch). The `add_shipment` service reports all of them.

### Upgrade notes

- Scripts or automations that call `bpost_tracker.add_shipment` **as a
  non-admin user** will now fail with a permission error. Automations running
  without a user, and administrators, are unaffected.
- Restart Home Assistant after updating.

## [0.3.1] - 2026-08-09

### Fixed

- A shipment added after it was already past its "remove after" threshold
  (for example delivered weeks ago) was deleted before its entities were even
  created, so it never appeared. It now stays visible until the next refresh.

### Added

- Local brand icon (`brand/icon.png`), so HACS brand validation passes.

### Changed

- Minimum Home Assistant version corrected to 2024.12.

## [0.3.0] - 2026-08-09

### Added

- Shipments can be removed automatically a set number of days after delivery
  (10 by default, 0 to disable), configurable when adding a shipment and later
  through the entry's **Configure** button.

## [0.2.1] - 2026-08-09

### Fixed

- hassfest validation: sorted manifest keys and added a `CONFIG_SCHEMA`.

## [0.2.0] - 2026-08-09

### Added

- `bpost_tracker.add_shipment` service, so shipments can be added from a
  dashboard script instead of the integrations UI.

## [0.1.0] - 2026-08-09

### Added

- Initial release: track any bpost shipment by tracking number and postal
  code through the public `track.bpost.cloud` API. A status sensor and a
  safe-place delivery picture camera per shipment, with polling that slows
  down once a parcel is delivered.
- Delivery is detected from bpost's actual delivery time rather than the
  status name, which differs per delivery method.
