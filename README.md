# RIP AND DIP // STUDIO_EDITION v2.1

A high-performance multimedia production suite designed for rapid batch audio extraction, Spotify library dumping, and AI-powered stem separation.

## ENGINE SPECS
- **[ RIP ]**: Full-throttle YouTube/URL downloader with hyphenated metadata parsing.
- **[ DUMPS ]**: Automated Spotify playlist extraction via `spotdl` with stealth cooldowns.
- **[ DIP ]**: Advanced stem separation utilizing `htdemucs_ft` models for clean isolation.

## SYSTEM DEPENDENCIES
- **Python 3.10+**
- **Node.js** (Required for YouTube JS handshake)
- **FFmpeg** (Global PATH access required)
- **PySide6** (UI Framework)
- **yt-dlp** (Core extraction engine)

## USAGE
1. **Batch Rip**: Drag a `.csv` or `.txt` into the UI. The parser will automatically format targets as `Artist - Song Name`.
2. **Spotify Dump**: Paste Spotify URLs into the DUMPS tab to clone playlists locally.
3. **Stem Dip**: Add local audio files to the DIP tab to separate vocals, drums, bass, and other elements.

## INSTALLATION
```powershell
pip install yt-dlp spotdl audio-separator[cpu] PySide6