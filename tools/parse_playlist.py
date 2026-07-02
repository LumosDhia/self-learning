#!/usr/bin/env python3
import sys
import re
import json
import urllib.request
import argparse
from pathlib import Path

def fetch_playlist_html(url_or_id):
    playlist_id = url_or_id
    if "list=" in url_or_id:
        m = re.search(r'list=([a-zA-Z0-9_-]+)', url_or_id)
        if m:
            playlist_id = m.group(1)
    
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    print(f"Fetching playlist: {url} ...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def parse_videos(html_content):
    videos = []
    
    # Method 1: parse lockupViewModel structures (newer desktop layout)
    matches = list(re.finditer(r'\{"lockupViewModel"', html_content))
    for match in matches:
        start_idx = match.start()
        brace_count = 1
        curr_idx = match.end()
        while brace_count > 0 and curr_idx < len(html_content):
            char = html_content[curr_idx]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            curr_idx += 1
        
        obj_str = html_content[start_idx:curr_idx]
        try:
            obj = json.loads(obj_str)
            lvm = obj.get("lockupViewModel", {})
            title = lvm.get("metadata", {}).get("lockupMetadataViewModel", {}).get("title", {}).get("content", "")
            video_id = lvm.get("contentId", "")
            if title and video_id:
                videos.append((video_id, title))
        except:
            continue
            
    # Method 2: Fallback to playlistVideoRenderer (classic layout)
    if not videos:
        matches = list(re.finditer(r'"playlistVideoRenderer"\s*:\s*\{', html_content))
        for match in matches:
            start_idx = match.start()
            brace_count = 1
            curr_idx = match.end()
            while brace_count > 0 and curr_idx < len(html_content):
                char = html_content[curr_idx]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                curr_idx += 1
            
            obj_str = html_content[start_idx + len('"playlistVideoRenderer":'):curr_idx]
            try:
                video_id_match = re.search(r'"videoId"\s*:\s*"([^"]+)"', obj_str)
                title_match = re.search(r'"title"\s*:\s*\{\s*"runs"\s*:\s*\[\s*\{\s*"text"\s*:\s*"([^"]+)"', obj_str)
                if video_id_match and title_match:
                    v_id = video_id_match.group(1)
                    title = title_match.group(1).encode().decode('unicode-escape')
                    videos.append((v_id, title))
            except:
                continue
                
    return videos

def format_markdown(videos, title="Course Videos"):
    lines = [f"### 📚 {title}"]
    for idx, (v_id, t) in enumerate(videos):
        # Clean title slightly if needed
        clean_title = t.replace("[", "\\[").replace("]", "\\]")
        lines.append(f"- [ ] [{clean_title}](https://youtube.com/watch?v={v_id})")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Fetch and parse a YouTube playlist into a Markdown checklist.")
    parser.add_argument("playlist", help="YouTube playlist URL or playlist ID")
    parser.add_argument("-o", "--output", help="Output file path (e.g. 30-days-with/devops/README.md)")
    parser.add_argument("-t", "--title", default="Course Videos", help="Heading title for the checklist section")
    
    args = parser.parse_args()
    
    try:
        html = fetch_playlist_html(args.playlist)
        videos = parse_videos(html)
        
        if not videos:
            print("Error: Could not find any videos in the playlist. Please verify the URL or ID.")
            sys.exit(1)
            
        print(f"Successfully parsed {len(videos)} videos.")
        md_checklist = format_markdown(videos, args.title)
        
        if args.output:
            out_path = Path(args.output).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            if out_path.exists():
                content = out_path.read_text(encoding='utf-8')
                # Try to replace existing list under the heading if possible
                header_pat = rf"(### 📚 {re.escape(args.title)}\n)(.*?)(\n\n---|\n#|\Z)"
                if re.search(header_pat, content, re.DOTALL):
                    # Extract checklist lines (excluding the first header line)
                    new_list_content = md_checklist.split('\n', 1)[1]
                    new_content = re.sub(header_pat, rf"\1{new_list_content}\3", content, flags=re.DOTALL)
                    out_path.write_text(new_content, encoding='utf-8')
                    print(f"Updated existing checklist section in: {out_path}")
                else:
                    # Append it
                    new_content = content.rstrip() + "\n\n" + md_checklist + "\n"
                    out_path.write_text(new_content, encoding='utf-8')
                    print(f"Appended checklist to: {out_path}")
            else:
                # Create a simple new file
                new_content = f"# Playlist: {args.title}\n\n{md_checklist}\n"
                out_path.write_text(new_content, encoding='utf-8')
                print(f"Created new file with checklist: {out_path}")
        else:
            print("\nGenerated Markdown:\n")
            print(md_checklist)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
