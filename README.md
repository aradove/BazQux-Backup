**Note:** This is NOT related to the offical BazQux in any way. 

# BazQux Backup
A Python application to backup all your BazQux Reader items to Markdown files.

Each tag will get their own markdown file, just like your read posts in BazQux. 

## Installation

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

or just run `uv init`

## Usage
Example to backup all **`tags`** and **`starred`** items (default behavior):
```bash
 uv run .\bazqux_backup.py --email "your@mail.com" --password "your_password"
```

Example to backup **`specific tag`**:
```bash
uv run .\bazqux_backup.py --email "your@mail.com" --password "your_password" --tag "TagName"
```

Example to backup **`starred items`**:
```bash
uv run .\bazqux_backup.py --email "your@mail.com" --password "your_password" --starred
```

Example to backup **`tagged items`**:
```bash
uv run .\bazqux_backup.py --email "your@mail.com" --password "your_password" --tags-only
```

Help print:
```bash
uv run .\bazqux_backup.py --help
usage: bazqux_backup.py [-h] [--token TOKEN] [--email EMAIL] [--password PASSWORD] [--tag TAG]
                        [--starred] [--tags-only]

Backup BazQux Reader items to Markdown files

options:
  -h, --help           show this help message and exit
  --token TOKEN        NOT WORKING! BazQux API token (optional)
  --email EMAIL        BazQux account email
  --password PASSWORD  BazQux account password
  --tag TAG            Specific tag to backup (default: backup all tags)
  --starred            Backup starred items only
  --tags-only          Backup all tags without starred items
```

## Output
The files will be stored in the following structure in the `backups` folder:
```
backups
|-- automation.md
|-- blogs.md
|-- coding.md
|-- DIY.md
|-- ...
```

### Authentication

The script supports authentication with email and password.
I never got Token to work, and the API seem to state it is unsupported as of now.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

