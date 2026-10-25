# money-decoded-agent

Fully automatic bot for the YouTube channel **Money Decoded** (@MoneyDecodedAnimated).

Every day on GitHub Actions: pick a topic (owner's topics first, then our own versions of viral money videos) → research →
timeline script → storyboard → AI voice → code-drawn motion graphics (Remotion) → music + sound → ChatGPT thumbnail → upload.
The long video is scheduled for **20:00 UTC (23:00 Istanbul)** and one Short for **20:30 UTC (23:30 Istanbul)**.

- Rules: `config/rules.md` · settings: `config/channel.json` · topic bank: `data/topics.json`
- Run manually: Actions → *Make episode* → Run workflow (`dry_run` = build only, no upload)
- Secrets (Settings → Secrets and variables → Actions): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `YT_TOKEN_JSON`
- The bot refuses to upload unless `YT_TOKEN_JSON` belongs to the Money Decoded channel.
- Educational content only — not financial advice.
