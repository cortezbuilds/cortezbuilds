# Cortez Builds identity

**Version 1 · prepared 23 September 2026 · provisional location**

This page is one discovery point for the **Cortez Builds** project identity. The proposed stable record label is `urn:uuid:1bd866d8-46eb-4203-9be1-64e471de91ba`. The label is random: it is not a secret, a signature, or proof of who controls this identity. It becomes meaningful only when the first reviewed record and its change authority are pinned through a trusted introduction.

This GitHub location is provisional. A privately registered HTTPS domain, a Tor onion service, or another endpoint can later serve the *same signed record* without becoming the cryptographic root. Each endpoint has its own custody and availability risks. The identity claim here is about the Cortez Builds public presence, not a verified legal identity.

The [versioned public record](record.json) contains the same key roster in an **experimental Cortez Builds JSON format** that software can read. It is not a general identity standard. It lists **public** credentials and their purposes. It does not contain private keys, recovery material, device serial numbers, account tokens, or a list of services I use.

Version 1 can be endorsed with the existing OpenPGP mail signing key as a bridge from the already published Cortez Builds fingerprint. Check the [detached signature](record.json.asc) and the full fingerprint before relying on that endorsement; if the signature file is absent, this record is unendorsed. This key is a **bootstrap witness**, not the permanent authority for all future roles.

## Current contact credential

| Purpose | Current credential | Status |
| --- | --- | --- |
| Encrypted mail to `cortezbuilds@proton.me` | OpenPGP fingerprint `96D2 1E92 9922 899D 6C86 AA37 FAF3 EE10 99BB 76CF` · [Proton-compatible public certificate](../keys/cortezbuilds-email.asc) | Primary mail key in Proton on 23 September 2026. Classical Curve25519 encryption. |

Compare the full fingerprint through another trusted channel before relying on it for sensitive mail. The [full local certificate](../keys/cortezbuilds-openpgp.asc) has the **same primary fingerprint** and an additional GnuPG LibrePGP hybrid encryption subkey. That subkey is for explicitly tested local GnuPG use; Proton does not currently publish it as the address's mail encryption route. The older Proton Curve25519 key, fingerprint `F8DD7C302C27CE9C172621B6DF080D21B5B17BF8`, is retained for older mail.

**Post-quantum mail:** no Proton PQ key is active for this address as of this version. When Proton offers its v6 PQ option, a new address key will have a new fingerprint. This page will name that key as current only after Proton and local export, restore, message, and public-discovery tests pass. The older keys will remain in the history for decryption and verification.

## How new capabilities join this identity

The public record will name a credential's **role, scope, fingerprint or public identifier, status, and replacement date**. A credential can be authorized for one purpose without becoming a universal login key. Examples include a mail key, a device enrollment key, or a software-signing key. WebAuthn passkeys are created separately for each site's domain; a site's permission is required before any device credential can log in there.

The identity page is a locator. A future portable device may prove possession of one approved credential and consent to a particular request. The computer or service still decides what access to grant. Keys and sessions will be scoped and replaceable so losing one device does not require changing this address.

Publishing this record at multiple locations deliberately links those locations to the same public identity. An onion endpoint could protect its network location, but cross-linking it here would not make this already-public persona anonymous.

**Device status today:** the ESP32-S3/Pico OpenPGP board is experimental and holds no live Cortez Builds identity key. Its standard USB smart-card path has not passed the required test. No claim of Bluetooth, Wi-Fi, NFC, or general computer sign-in is attached to it. A production device will be listed only after its firmware, interface, user-presence, recovery, and replacement tests pass.

## Change and recovery policy

1. Keep each published version and its exact bytes. A new version names the previous version's SHA-256 digest and states which credentials were added, rotated, or retired.
2. Sign a version with the designated change authority and, during a rotation, have both the outgoing and incoming authorities sign the transition. Publish the complete fingerprints and verify the signatures independently. The first production change authority and its recovery ceremony are still to be selected; the existing mail key is **not** silently promoted to that role.
3. Anchor important changes through an independently operated second channel with a verifiable publication time. A date typed into a page or an old RSA signature alone cannot establish a post-quantum-safe history.
4. Keep private recovery inventories and backup locations offline. Rehearse restoring and replacing a device or key before relying on it. Preserve older mail decryption keys while older encrypted mail is needed.
5. If a discovery location changes, add the new endpoint through a signed record update. Leave a signed forwarding statement at the old address when possible, and verify the new one independently. Preserve the record label, history, and latest trusted authority across location changes.

**Current trust limit:** version 1 has no dedicated offline change authority or post-quantum identity signature. Its public URL will establish a discoverable place for the identity; it will not by itself prove real-world identity, make every account accept a portable card, or make today's mail post-quantum secure.
