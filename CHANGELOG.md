# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/): a bug fix bumps the patch number,
a new feature the minor number, and every release gets a git tag.

## [0.4.0] - 2026-11-07

The first tagged release, and a security hardening release based on a review
of the integration. Nothing critical was found, but several weak spots are
closed.

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

### Documentation

- The README lists every sensor attribute, points to the `delivered`
  attribute for detecting delivery (the sensor state is bpost's raw step name,
  for example `delivered_kariboo_point`), states the minimum Home Assistant
  version (2024.12) and links this changelog.

### Upgrade notes

- Scripts or automations that call `bpost_tracker.add_shipment` **as a
  non-admin user** will now fail with a permission error. Automations running
  without a user, and administrators, are unaffected.
- Restart Home Assistant after updating.
- Until now Home Assistant and HACS identified the integration by commit hash
  (for example `10bba07`). From this release on they show the version
  (`v0.4.0`).

## Before 0.4.0

The project was built over a few days without releases or tags, so the
version numbers 0.1.0–0.3.1 that appear in older commits were never
published and cannot be installed separately. In short, that period added:

- Tracking any bpost shipment by tracking number and postal code through the
  public `track.bpost.cloud` API, with a status sensor and a safe-place
  delivery picture camera per shipment.
- Delivery detection from bpost's actual delivery time, because the status
  name differs per delivery method.
- The `bpost_tracker.add_shipment` service, so shipments can be added from a
  dashboard script.
- Automatic removal of shipments a configurable number of days after
  delivery (10 by default, 0 to disable), with an options flow. A shipment
  that was already past that limit when added used to be deleted before it
  ever appeared; it now stays visible until the next refresh.
- hassfest and HACS validation fixes, a local brand icon and a corrected
  minimum Home Assistant version.
