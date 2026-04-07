```
  ____                      _   _ ________          
 / ___|  ___ ___ _ __   ___| \ | |__  / __ )___     
 \___ \ / __/ _ \ '_ \ / _ \  \| | / /|  _ / __|    
  ___) | (_|  __/ | | |  __/ |\  |/ /_| |_) \__ \   
 |____/ \___\___|_| |_|\___|_| \_/____|____/|___/   
          _   _ ____  _     ___    _    ____  _____ ____  
         | | | |  _ \| |   / _ \  / \  |  _ \| ____|  _ \ 
         | | | | |_) | |  | | | |/ _ \ | | | |  _| | |_) |
         | |_| |  __/| |__| |_| / ___ \| |_| | |___|  _ < 
          \___/|_|   |_____\___/_/   \_\____/|_____|_| \_\
```

# SceneNZBs Uploader

A fast Python CLI to upload NZBs to [SceneNZBs](https://scenenzbs.com).

[SceneNZBs](https://scenenzbs.com/) is a private Usenet indexer focused on scene releases. This script automates uploading `.nzb` files to the site via its API, so you don't have to do it manually through the web interface. It handles single files, batch folder uploads, companion file detection (MediaInfo XML and NFO), duplicate skipping, and logs every upload result.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key
edit config.yaml

# Upload
python upload.py -path "release.nzb"
```

## Usage

```
python upload.py -path <file_or_folder> [-mediainfo <file>] [-nfo <file>]
```

| Flag          | Description                                      |
|---------------|--------------------------------------------------|
| `-path`       | Path to an `.nzb` file or a folder of `.nzb` files (required) |
| `-mediainfo`  | Path to a MediaInfo XML file (optional, single-file mode)     |
| `-nfo`        | Path to an NFO file (optional, single-file mode)              |

### Single File

```bash
python upload.py -path "Movie.2025.1080p.BluRay.nzb"
```

### Single File with Attachments

```bash
python upload.py -path "Movie.2025.nzb" -mediainfo "Movie.2025.xml" -nfo "Movie.2025.nfo"
```

### Batch Upload (Folder)

```bash
python upload.py -path "/path/to/nzbs/"
```

Uploads every `.nzb` in the folder, sorted alphabetically.

## Auto-Detection

When uploading, the script automatically looks for companion files next to each `.nzb`:

```
Movie.2025.1080p.BluRay.nzb
Movie.2025.1080p.BluRay.xml    <-- picked up as MediaInfo
Movie.2025.1080p.BluRay.nfo    <-- picked up as NFO
```

If they exist, they're attached. If not, the upload proceeds without them. No flags needed.

## Configuration

Edit `config.yaml`:

```yaml
api_key: "your-api-key-here"
category: -1              # -1 = auto-detect
base_url: "https://scenenzbs.com"
api_path: "/api/v1"
```

| Key         | Description                                         |
|-------------|-----------------------------------------------------|
| `api_key`   | Your SceneNZBs API key                              |
| `category`  | Category ID for uploads (`-1` for auto-detect)      |
| `base_url`  | Site base URL                                       |
| `api_path`  | API path prefix                                     |

## Upload Log

Every upload is logged to `upload_log.json` with:

- Filename and full path
- Timestamp (UTC)
- Status (`ok`, `skipped`, `error`)
- Release GUID and URL (on success)
- Error details (on failure)

The log is saved after each file, so nothing is lost if the process is interrupted.

## Terminal Output

```
Found 3 file(s) to upload

  + MediaInfo: Movie.2025.xml
  + NFO: Movie.2025.nfo
Uploading: Movie.2025.1080p.BluRay.nzb ... OK
  Link: https://scenenzbs.com/releases/abc123def456
Uploading: Show.S01E01.720p.nzb ... OK
  Link: https://scenenzbs.com/releases/bbb222ccc333
Skipping: Old.Movie.2020.nzb
  Detail: NZB has already been uploaded

Done: 2 uploaded, 1 skipped, 0 failed
Log: /path/to/upload_log.json
```

## Requirements

- Python 3.8+
- `requests`
- `pyyaml`

```bash
pip install -r requirements.txt
```

## Author

Made by [@ManOfInfinity](https://github.com/ManOfInfinity)

## License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html). You are free to use, modify, and distribute this software, provided that:

- Any modified versions are also open source under GPLv3
- Credit is given to the original author
