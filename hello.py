import os
import json
import requests
import argparse
from datetime import datetime
import html2text
import time

def authenticate_with_credentials(email, password):
    """Authenticate with BazQux using email and password."""
    url = "https://bazqux.com/accounts/ClientLogin"
    data = {
        "Email": email,
        "Passwd": password
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    
    # Parse the response which typically looks like Key=Value lines
    response_text = response.text
    for line in response_text.split('\n'):
        if line.startswith('Auth='):
            return line[5:]  # Return just the token part
    
    raise ValueError("No authentication token found in the response")

def get_auth_token():
    """Get auth token from environment or user input"""
    token = os.environ.get("BAZQUX_TOKEN")
    if token:
        return token
    
    print("Please provide your BazQux credentials.")
    email = input("Email: ")
    password = input("Password: ")
    return authenticate_with_credentials(email, password)

def get_tags(token):
    url = "https://bazqux.com/reader/api/0/tag/list?output=json"
    headers = {"Authorization": f"GoogleLogin auth={token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tags_data = response.json()
    
    tags = []
    if "tags" in tags_data:
        for tag in tags_data["tags"]:
            # Extract tag name from "user/-/label/TagName" format
            if "/label/" in tag["id"]:
                tag_name = tag["id"].split("/label/")[-1]
                tags.append(tag_name)
    return tags

def get_items_for_tag(token, tag, continuation=None):
    encoded_tag = requests.utils.quote(tag)
    url = f"https://bazqux.com/reader/api/0/stream/contents?output=json&n=1000&s=user/-/label/{encoded_tag}"
    if continuation:
        url += f"&c={continuation}"
    
    headers = {"Authorization": f"GoogleLogin auth={token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def convert_to_markdown(item):
    h = html2text.HTML2Text()
    h.ignore_links = False
    
    title = item.get("title", "Untitled")
    content = item.get("summary", {}).get("content", "")
    author = item.get("author", "Unknown Author")
    published = datetime.fromtimestamp(item.get("published", 0))
    url = item.get("alternate", [{}])[0].get("href", "")
    
    markdown = f"# {title}\n\n"
    markdown += f"**Author:** {author}  \n"
    markdown += f"**Published:** {published.strftime('%Y-%m-%d %H:%M:%S')}  \n"
    markdown += f"**URL:** {url}  \n\n"
    markdown += "---\n\n"
    
    # Convert HTML content to markdown
    markdown_content = h.handle(content)
    
    # Special handling for Hacker News posts
    if "news.ycombinator.com" in markdown_content:
        # Replace "# Comments: N" with "Comments: N"
        markdown_content = markdown_content.replace("\n# Comments:", "\nComments:")
    
    markdown += markdown_content
    
    return markdown

def sanitize_filename(name):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name

def save_tag_markdown(tag_content, tag):
    """Save all posts from a tag to a single markdown file."""
    os.makedirs("backups", exist_ok=True)
    
    filename = f"{sanitize_filename(tag)}.md"
    filepath = os.path.join("backups", filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(tag_content)
    
    return filepath

def backup_tag(token, tag):
    print(f"Backing up tag: {tag}")
    continuation = None
    total_items = 0
    all_content = f"# Tag: {tag}\n\n"
    
    while True:
        try:
            data = get_items_for_tag(token, tag, continuation)
            items = data.get("items", [])
            total_items += len(items)
            
            for item in items:
                markdown_content = convert_to_markdown(item)
                all_content += markdown_content
                all_content += "\n\n---\n\n"  # Separator between posts
            
            if "continuation" in data and data["continuation"]:
                continuation = data["continuation"]
                print(f"  Fetched {len(items)} items, continuing...")
                time.sleep(1)  # Be nice to the API server
            else:
                break
        except Exception as e:
            print(f"Error fetching items for tag {tag}: {e}")
            break
    
    if total_items > 0:
        filepath = save_tag_markdown(all_content, tag)
        print(f"Saved {total_items} items for tag '{tag}' to {filepath}")
    else:
        print(f"No items found for tag '{tag}'")
    
    print(f"Completed backup of {total_items} items for tag: {tag}")

def main():
    parser = argparse.ArgumentParser(description="Backup BazQux Reader items to Markdown files")
    parser.add_argument("--token", help="BazQux API token (optional)")
    parser.add_argument("--email", help="BazQux account email")
    parser.add_argument("--password", help="BazQux account password")
    parser.add_argument("--tag", help="Specific tag to backup (default: backup all tags)")
    parser.add_argument("--starred", action="store_true", help="Backup starred items")
    args = parser.parse_args()
    
    # Get authentication token
    token = None
    if args.email and args.password:
        print(f"Authenticating with email: {args.email}")
        token = authenticate_with_credentials(args.email, args.password)
    elif args.token:
        token = args.token
    else:
        token = get_auth_token()
    
    os.makedirs("backups", exist_ok=True)
    
    if args.starred:
        print("Backing up starred items...")
        url = "https://bazqux.com/reader/api/0/stream/contents?output=json&n=1000&s=user/-/state/com.google/starred"
        headers = {"Authorization": f"GoogleLogin auth={token}"}
        
        continuation = None
        total_items = 0
        all_starred_content = "# Starred Items\n\n"
        
        while True:
            current_url = url
            if continuation:
                current_url += f"&c={continuation}"
                
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            total_items += len(items)
            
            for item in items:
                markdown_content = convert_to_markdown(item)
                all_starred_content += markdown_content
                all_starred_content += "\n\n---\n\n"  # Separator between posts
            
            if "continuation" in data and data["continuation"]:
                continuation = data["continuation"]
                print(f"  Fetched {len(items)} starred items, continuing...")
                time.sleep(1)
            else:
                break
        
        if total_items > 0:
            filepath = save_tag_markdown(all_starred_content, "starred")
            print(f"Saved {total_items} starred items to {filepath}")
        else:
            print("No starred items found")
                
        print(f"Completed backup of {total_items} starred items")
    
    if args.tag:
        backup_tag(token, args.tag)
    elif not args.starred:
        tags = get_tags(token)
        print(f"Found {len(tags)} tags: {', '.join(tags)}")
        
        for tag in tags:
            backup_tag(token, tag)
    
    print("Backup completed successfully!")

if __name__ == "__main__":
    main()
