# Publish a Turbo8 cartridge

## Submit to the official source

1. Open your game and choose PUBLISH → ONLINE (SUBMIT FOR REVIEW) → CONTINUE TO ONLINE. You can also open PUBLISH from the game’s library menu (…). Continuing saves your current edits. A built-in game becomes a Player copy.

2. Sign in with your GitHub account and enter a title and version such as 1.0.0. If the cover is missing, open the game’s menu under PLAYER and choose EDIT COVER. Confirm that you have permission to share the code, artwork and audio, then select SUBMIT FOR REVIEW.

3. In ONLINE, select the Official source and open MY SUBMISSIONS. Open the review link if changes are requested. After a maintainer merges the submission, wait for Published, then refresh the official source to download it.

4. To update the same work, reopen PUBLISH from the original Player cartridge and submit a higher version. Copying the game creates a new submission identity.

## Publish to your own GitHub source

1. Select SAVE SOURCE TEMPLATE in this guide and unzip it. Create an empty public GitHub repository and put the extracted files at its root. Include the hidden .github directory. Check that .github/workflows/publish.yml appears on the default branch.

2. For each game, choose PUBLISH → CARTRIDGE ZIP, enable INCLUDE COVER IMAGE and select EXPORT CARTRIDGE. Put the ZIP in cartridges/ and give each game a distinct filename. Each ZIP can be up to 32 MiB. Its cover must be a 256 × 144 PNG of up to 128 KiB.

3. Commit and push the template and ZIPs to the default branch. On GitHub, open Actions → Publish Turbo8 cartridges → Run workflow and select that branch. When the run succeeds, open the Latest release and check for catalog-v2.json. Run the workflow whenever you want to publish changes.

4. Share the repository URL, such as https://github.com/owner/games. Players paste it into ONLINE → SOURCE and select ADD AND OPEN. Click a cover’s download button, then the cover to play. Players can browse and install without signing in to GitHub.

5. Replace a ZIP under the same filename and run the workflow to release an update. Changed games advance one patch version. Unchanged games keep their versions. To unlist a game, remove its ZIP and publish again. Keep old releases because other games may still use their assets.

If adding the source fails, check that the repository is public, the workflow succeeded and the Latest release contains the catalog. You publish directly to your own source. Submit a game separately for review to include it in the default official source.
