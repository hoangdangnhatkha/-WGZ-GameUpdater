Drop the portable rustdesk.exe in this folder.

Download URL:
  https://github.com/rustdesk/rustdesk/releases/latest

Pick `rustdesk-x.x.x-x86_64.exe` (Windows portable). Rename to `rustdesk.exe`
and place it here. PyInstaller already bundles this directory via
`wgz_updater\resources` in GameUpdater.spec — no spec changes needed.

At runtime the bundled binary is accessed as RUSTDESK_EXE
(see wgz_updater/core/paths.py).

Discord webhook URL goes in the remote config JSON under:
  {
    "support": {
      "discord_webhook": "https://discord.com/api/webhooks/...",
      "mention": "<@&ROLE_ID>"        // optional
    }
  }
