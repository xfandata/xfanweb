# xFPL Quadrants

Every FPL player's ownership at the gameweek deadline against the points they scored that gameweek.
Fans search their players, hover dots for details and switch between gameweeks. By [@xfandata](https://www.instagram.com/xfandata/).

| Path | What it is |
|---|---|
| `public/` | The website (Cloudflare Pages serves this folder) |
| `public/data/gw<N>.json` | One file per gameweek; `gameweeks.json` lists them for the dropdown |
| `public/badges/` | Team crests, downloaded once by `update.py` |
| `public/og.png` | The preview card shown when the link is shared |
| `update.py` | Pulls the FPL API and writes the data files |
| `.github/workflows/update.yml` | Runs `update.py` at 07:00 and 22:00 UTC and commits any new numbers |

## Going live (one time, about 30 minutes)

### 1. Put it on GitHub
1. Create a free account at github.com.
2. Click **New repository**, name it `xfpl`, set it to **Public**, and don't add a README.
3. In Terminal:
   ```
   cd ~/Desktop/FootData/fpl-quadrants
   git remote add origin https://github.com/<your-username>/xfpl.git
   git push -u origin main
   ```
4. In the repo go to **Settings → Actions → General → Workflow permissions**, pick **Read and write permissions**, and save.
   Then **Actions → Update FPL data → Run workflow** to test it once.

### 2. Host it on Cloudflare Pages
1. Create a free account at dash.cloudflare.com.
2. **Workers & Pages → Create → Pages → Connect to Git**, and pick the `xfpl` repo.
3. Build settings: Framework preset **None**, build command **empty**, build output directory **`public`**.
4. Click **Save and Deploy**. The site goes live at `https://xfpl.pages.dev`
   (if that name is taken Cloudflare picks another, so change the two `xfpl.pages.dev` links at the top of `public/index.html`).

### 3. Visitor numbers: Cloudflare Web Analytics
In the Pages project open **Metrics → Web Analytics → Enable**. No code needed: it shows visitors, page views,
countries, devices and where people came from (Instagram shows up as `l.instagram.com`).

### 4. Which players people look up: GoatCounter
1. Sign up free at goatcounter.com and choose the code `xfpl` (if it's taken, use another and change
   `xfpl.goatcounter.com` near the top of `public/index.html`).
2. Every player someone opens is logged as an event like `player/Haaland`, so the dashboard ranks the most looked-up players.

### 5. Instagram
Put `https://xfpl.pages.dev/?utm_source=instagram` in your bio or story link stickers, so those visits are labelled.

## Every week
Nothing to do: the GitHub Action refreshes the data twice a day and Cloudflare redeploys within a minute.

If the FPL API blocks GitHub's servers (the Action fails with a 403), update from your laptop instead:
```
cd ~/Desktop/FootData/fpl-quadrants
python3 update.py
git add public && git commit -m "Update FPL data" && git push
```

## Changing the rules
`OWN_CUT` and `PTS_CUT` at the top of `update.py` set the lines (10% ownership; 3+ points = returned, 2 or fewer = blank).
They're saved into each gameweek's file, so a change applies from the next update.
