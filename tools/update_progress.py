import os
import re
from pathlib import Path

def generate_bar(pct, length=10):
    filled = int(round(length * pct / 100))
    return '█' * filled + '░' * (length - filled)

def parse_config(config_text):
    config = {}
    for line in config_text.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            config[key.strip().lower()] = val.strip()
    return config

def update_book_checkboxes(content, current, total):
    lines = content.split('\n')
    items = []
    
    # 1. Gather all checklist lines containing page comments
    for idx, line in enumerate(lines):
        cb_match = re.match(r'^(\s*-\s*\[)([ xX])(\]\s*(.*?)\s*<!--\s*page:\s*(\d+)\s*-->)', line)
        if cb_match:
            prefix = cb_match.group(1)
            status = cb_match.group(2)
            suffix = cb_match.group(3)
            page = int(cb_match.group(5))
            items.append({
                'idx': idx,
                'page': page,
                'prefix': prefix,
                'suffix': suffix,
                'line': line
            })
            
    if not items:
        return content
        
    # Sort items by page order to make sure we compare correctly
    items.sort(key=lambda x: x['page'])
    
    # 2. Check each item off based on page ranges
    for i, item in enumerate(items):
        if i + 1 < len(items):
            next_page = items[i + 1]['page']
        else:
            next_page = total # Last item is completed when we reach total (e.g. 349)
            
        # If current page is at or past the starting page of the next item,
        # it means the current item has been fully read.
        if current >= next_page:
            new_status = 'x'
        else:
            new_status = ' '
            
        line_idx = item['idx']
        lines[line_idx] = f"{item['prefix']}{new_status}{item['suffix']}"
        
    return '\n'.join(lines)

def main():
    # Since the script is in 'tools/', the root directory is the parent of 'tools/'
    root_dir = Path(__file__).parent.parent.resolve()
    progress_map = {}
    
    # First pass: update files with progress-config
    for md_file in root_dir.glob('**/*.md'):
        if '.git' in md_file.parts:
            continue
            
        try:
            content = md_file.read_text(encoding='utf-8')
            original_content = content
        except Exception as e:
            continue
        
        # Check for config
        config_match = re.search(r'<!--\s*progress-config\s*(.*?)\s*-->', content, re.DOTALL)
        if not config_match:
            continue
            
        config = parse_config(config_match.group(1))
        p_type = config.get('type')
        
        if not p_type:
            continue
            
        percentage = 0.0
        display_str = ""
        
        if p_type == 'book':
            try:
                current = float(config.get('current', 0))
                total = float(config.get('total', 1))
                
                # Automatically update checkboxes based on the page number
                content = update_book_checkboxes(content, current, total)
                
                if total > 0:
                    percentage = min(100.0, max(0.0, (current / total) * 100))
                bar = generate_bar(percentage)
                display_str = f"Progress: [{bar}] {int(percentage)}% ({int(current)}/{int(total)} pages)"
            except Exception as e:
                print(f"Error parsing book progress in {md_file}: {e}")
                continue
                
        elif p_type == 'checklist':
            # Count checklist items outside comments
            in_comment = False
            total_items = 0
            completed_items = 0
            
            lines = content.split('\n')
            for line in lines:
                cleaned = line.strip()
                if '<!--' in cleaned:
                    in_comment = True
                if '-->' in cleaned:
                    in_comment = False
                    continue
                if in_comment:
                    continue
                    
                match = re.match(r'^-\s*\[([ xX])\]', cleaned)
                if match:
                    total_items += 1
                    if match.group(1).lower() == 'x':
                        completed_items += 1
            
            if total_items > 0:
                percentage = min(100.0, max(0.0, (completed_items / total_items) * 100))
            bar = generate_bar(percentage)
            display_str = f"Progress: [{bar}] {int(percentage)}% ({completed_items}/{total_items} days completed)"
            
        # Update display in file
        display_pattern = r'(<!--\s*progress-display\s*-->)(.*?)(<!--\s*progress-display-end\s*-->)'
        if re.search(display_pattern, content, re.DOTALL):
            new_content = re.sub(
                display_pattern,
                f"\\1\n{display_str}\n\\3",
                content,
                flags=re.DOTALL
            )
            if new_content != original_content:
                md_file.write_text(new_content, encoding='utf-8')
                print(f"Updated {md_file.relative_to(root_dir)}: {int(percentage)}%")
                
        # Store for relative links
        rel_path = md_file.relative_to(root_dir).as_posix()
        bar_clean = generate_bar(percentage)
        progress_map[rel_path] = f"Progress: [{bar_clean}] {int(percentage)}%"

    # Second pass: update files with progress-link
    for md_file in root_dir.glob('**/*.md'):
        if '.git' in md_file.parts:
            continue
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            continue
        
        # Regex to find: <!-- progress-link: path --> ... <!-- progress-link-end -->
        link_pattern = r'(<!--\s*progress-link:\s*([^\s<>]+)\s*-->)(.*?)(<!--\s*progress-link-end\s*-->)'
        
        def replace_link(match):
            prefix = match.group(1)
            target_path = match.group(2)
            suffix = match.group(4)
            
            target_path_norm = Path(target_path).as_posix()
            
            if target_path_norm in progress_map:
                link_progress = progress_map[target_path_norm]
                return f"{prefix}\n    {link_progress}\n    {suffix}"
            return match.group(0)
            
        if re.search(link_pattern, content, re.DOTALL):
            new_content = re.sub(link_pattern, replace_link, content, flags=re.DOTALL)
            if new_content != content:
                md_file.write_text(new_content, encoding='utf-8')
                print(f"Updated link references in {md_file.relative_to(root_dir)}")

if __name__ == '__main__':
    main()
