#!/usr/bin/env python3
"""
Splice Universal Open & Search Engine into VOID Desktop Assistant (/run/media/prakash/TR_39/VOID/bin/void-widget.py)
Supports:
  - __filename: documents, spreadsheets, text files, code, notes (.docx, .xlsx, .pdf, .txt, .md, .py, etc.)
  - _vedioname: local video files (.mp4, .mkv, .webm, etc.) or online YouTube direct streaming
  - _photoname: local images/screenshots (.png, .jpg, etc.) or Google Images search
  - _appname: desktop applications via KWin, desktop files, or system binaries
  - _browser: Chromium browser, URLs, web services
  - etc: universal fallback search in Chromium
"""

import sys
import re
from pathlib import Path

WIDGET_FILE = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")

def apply_enhancements():
    if not WIDGET_FILE.exists():
        print(f"[ERROR] Widget file not found: {WIDGET_FILE}")
        sys.exit(1)

    content = WIDGET_FILE.read_text(encoding="utf-8")

    # 1. Expand KNOWN_APPS and resolve_app_name to reject files with extensions
    old_known_apps = '''KNOWN_APPS = {
    "chromium": ["chrome", "chromium", "google chrome", "google", "browser", "web browser", "web", "internet", "crome", "chrom", "chromum"],
    "firefox": ["firefox", "fire fox", "mozila", "mozilla"],
    "konsole": ["konsole", "terminal", "termianl", "console", "consol", "shell", "bash"],
    "dolphin": ["dolphin", "files", "file manager", "filemanager", "explorer", "folders", "directory"],
    "kwrite": ["kwrite", "text editor", "notepad", "notes", "editor", "kate"],
    "kcalc": ["kcalc", "calculator", "calcultor", "calc"],
    "systemsettings": ["settings", "system settings", "control panel", "config", "systemsettings"],
    "plasma-systemmonitor": ["system monitor", "task manager", "activity monitor", "resources"]
}'''

    new_known_apps = '''KNOWN_APPS = {
    "chromium": ["chrome", "chromium", "google chrome", "google", "browser", "web browser", "web", "internet", "crome", "chrom", "chromum"],
    "firefox": ["firefox", "fire fox", "mozila", "mozilla"],
    "konsole": ["konsole", "terminal", "termianl", "console", "consol", "shell", "bash"],
    "dolphin": ["dolphin", "files", "file manager", "filemanager", "explorer", "folders", "directory"],
    "kwrite": ["kwrite", "text editor", "notepad", "notes", "editor", "kate"],
    "kcalc": ["kcalc", "calculator", "calcultor", "calc"],
    "systemsettings": ["settings", "system settings", "control panel", "config", "systemsettings"],
    "plasma-systemmonitor": ["system monitor", "task manager", "activity monitor", "resources"],
    "vlc": ["vlc", "vlc media player", "video player"],
    "gwenview": ["gwenview", "image viewer", "photo viewer"],
    "gimp": ["gimp", "photo editor", "image editor"],
    "code": ["vs code", "vscode", "code", "visual studio code"],
    "spotify": ["spotify"],
    "steam": ["steam"],
    "obs": ["obs", "obs studio"],
    "thunderbird": ["thunderbird", "mail client"],
    "libreoffice": ["libreoffice", "office", "word processor"]
}'''

    if old_known_apps in content:
        content = content.replace(old_known_apps, new_known_apps, 1)
        print("[APPLIED] Expanded KNOWN_APPS with multimedia and productivity apps.")

    # In resolve_app_name, make sure files with extensions are never treated as apps
    old_resolve_guard = '''    # Never resolve generic pronouns, articles, or stop words as application names
    if raw_lower in ["that", "it", "this", "something", "the summary", "summary", "document", "file", "all"]:
        return None'''

    new_resolve_guard = '''    # Never resolve generic pronouns, articles, stop words, or filenames with extensions as app names
    if raw_lower in ["that", "it", "this", "something", "the summary", "summary", "document", "file", "all"]:
        return None
    if "." in raw_lower and any(raw_lower.endswith(ext) for ext in [
        ".docx", ".doc", ".xlsx", ".xls", ".pdf", ".txt", ".md", ".csv",
        ".json", ".py", ".sh", ".odt", ".ods", ".png", ".jpg", ".jpeg",
        ".webp", ".gif", ".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv",
        ".mp3", ".wav", ".svg", ".bmp"
    ]):
        return None'''

    if old_resolve_guard in content:
        content = content.replace(old_resolve_guard, new_resolve_guard, 1)
        print("[APPLIED] Added filename extension guard to resolve_app_name.")

    # Expand open_map in launch_application
    old_open_map = '''        "systemsettings": "/usr/bin/systemsettings",
        "settings": "/usr/bin/systemsettings",
        "plasma-systemmonitor": "/usr/bin/plasma-systemmonitor",
    }'''

    new_open_map = '''        "systemsettings": "/usr/bin/systemsettings",
        "settings": "/usr/bin/systemsettings",
        "plasma-systemmonitor": "/usr/bin/plasma-systemmonitor",
        "vlc": "/usr/bin/vlc",
        "gwenview": "/usr/bin/gwenview",
        "gimp": "/usr/bin/gimp",
        "code": "/usr/bin/code",
        "spotify": "/usr/bin/spotify",
        "steam": "/usr/bin/steam",
        "obs": "/usr/bin/obs",
        "thunderbird": "/usr/bin/thunderbird",
        "libreoffice": "/usr/bin/libreoffice",
    }'''

    if old_open_map in content:
        content = content.replace(old_open_map, new_open_map, 1)
        print("[APPLIED] Expanded open_map in launch_application.")

    # 2. Add find_user_content and detect_content_type helper functions
    file_helpers_code = '''
# ---------------------------------------------------------------------------
# Universal File, Media, and Content Search Subsystem
# ---------------------------------------------------------------------------
DOC_EXTENSIONS = {
    ".docx", ".doc", ".xlsx", ".xls", ".pdf", ".txt", ".md", ".csv",
    ".json", ".py", ".sh", ".odt", ".ods", ".odp", ".pptx", ".ppt",
    ".html", ".xml", ".log", ".yaml", ".yml", ".zip", ".tar.gz", ".ini", ".conf"
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv", ".m4v",
    ".mpg", ".mpeg", ".3gp", ".ts"
}

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg", ".ico",
    ".tiff", ".tif", ".heic"
}

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".opus"
}

def detect_content_type(file_or_name: str | Path) -> str:
    path = Path(file_or_name)
    ext = path.suffix.lower()
    if ext in DOC_EXTENSIONS:
        return "document"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    return "file"

def find_user_content(target: str, expected_type: str = "any") -> tuple[Path | None, str]:
    """
    Intelligently searches user directories for a matching file, document, photo, or video.
    Returns (matching_path, detected_type) or (None, '').
    """
    raw = target.strip().strip("'\\"").strip()
    if not raw:
        return (None, "")

    direct_p = Path(raw).expanduser().resolve()
    if direct_p.exists() and direct_p.is_file():
        return (direct_p, detect_content_type(direct_p))

    clean_target = re.sub(
        r"^(?:file|document|doc|report|note|video|movie|photo|image|picture|screenshot|song|track)\s+",
        "", raw, flags=re.I
    ).strip()
    if not clean_target:
        clean_target = raw

    t_lower = clean_target.lower()
    t_path = Path(clean_target)
    t_stem = t_path.stem.lower()
    t_suffix = t_path.suffix.lower()

    home = Path.home()
    ssd_root = Path("/run/media/prakash/TR_39/VOID")

    doc_dirs = [
        home / "Documents/Reports",
        home / "Documents/Notes",
        home / "Documents/Drafts",
        home / "Documents",
        home / "Downloads",
        home / "Desktop",
        ssd_root,
        home,
    ]
    img_dirs = [
        home / "Pictures/Screenshots",
        home / "Pictures",
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
        ssd_root,
        home,
    ]
    vid_dirs = [
        home / "Videos",
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
        ssd_root,
        home,
    ]
    audio_dirs = [
        home / "Music",
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
        home,
    ]

    if expected_type in ["image", "photo", "picture"]:
        search_dirs = img_dirs + doc_dirs
    elif expected_type in ["video", "movie"]:
        search_dirs = vid_dirs + doc_dirs
    elif expected_type in ["document", "doc", "file"]:
        search_dirs = doc_dirs + img_dirs + vid_dirs
    elif expected_type in ["audio", "song", "music"]:
        search_dirs = audio_dirs + vid_dirs + doc_dirs
    else:
        if t_suffix in IMAGE_EXTENSIONS:
            search_dirs = img_dirs + doc_dirs
        elif t_suffix in VIDEO_EXTENSIONS:
            search_dirs = vid_dirs + doc_dirs
        elif t_suffix in DOC_EXTENSIONS:
            search_dirs = doc_dirs + img_dirs + vid_dirs
        else:
            search_dirs = doc_dirs + img_dirs + vid_dirs + audio_dirs

    seen = set()
    unique_dirs = []
    for d in search_dirs:
        if str(d) not in seen and d.exists() and d.is_dir():
            seen.add(str(d))
            unique_dirs.append(d)

    # Pass 1: Direct child exact filename match
    for sdir in unique_dirs:
        try:
            for child in sdir.iterdir():
                if child.is_file() and not child.name.startswith("."):
                    if child.name.lower() == t_lower:
                        return (child, detect_content_type(child))
                    if t_suffix and child.stem.lower() == t_stem and child.suffix.lower() == t_suffix:
                        return (child, detect_content_type(child))
        except Exception:
            pass

    # Pass 2: Exact stem match without extension (e.g. "Mothers_Importance" -> "Mothers_Importance.docx")
    for sdir in unique_dirs:
        try:
            for child in sdir.iterdir():
                if child.is_file() and not child.name.startswith("."):
                    c_stem = child.stem.lower()
                    if c_stem == t_stem or c_stem == t_lower or c_stem.replace("_", " ") == t_lower or c_stem == t_lower.replace(" ", "_"):
                        return (child, detect_content_type(child))
        except Exception:
            pass

    # Pass 3: Fuzzy / Substring match in primary document/media folders (depth <= 2)
    matches = []
    for sdir in unique_dirs[:5]:
        try:
            for root, dirs, files in os.walk(sdir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", ".venv", "node_modules", ".git"]]
                rel_parts = Path(root).relative_to(sdir).parts
                if len(rel_parts) > 2:
                    dirs.clear()
                    continue
                for fname in files:
                    if fname.startswith("."):
                        continue
                    f_lower = fname.lower()
                    f_path = Path(root) / fname
                    if t_lower in f_lower or t_stem in f_lower or t_lower.replace(" ", "_") in f_lower:
                        matches.append((f_path.stat().st_mtime, f_path))
        except Exception:
            pass

    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        best = matches[0][1]
        return (best, detect_content_type(best))

    return (None, "")
'''

    if "def find_user_content" not in content:
        target_marker = "def normalize_voice_intent(text: str) -> str:"
        content = content.replace(target_marker, file_helpers_code + "\n" + target_marker, 1)
        print("[APPLIED] Added find_user_content and detect_content_type helpers.")

    # 3. Add phonetic typo corrections to normalize_voice_intent
    old_typos = '''        (r"\\b(?:snag|sng)\\b", "song"),'''
    new_typos = '''        (r"\\b(?:snag|sng)\\b", "song"),
        (r"\\b(?:vedio|vido|vdeo|vedeo)\\b", "video"),
        (r"\\b(?:fotot|foto|photot|pictr|piture|piktur)\\b", "photo"),
        (r"\\b(?:filname|fiel|fle)\\b", "file"),
        (r"\\b(?:documnt|docment|dcoument)\\b", "document"),'''

    if old_typos in content and "vedio" not in content:
        content = content.replace(old_typos, new_typos, 1)
        print("[APPLIED] Added video/photo/file phonetic typo replacements.")

    # 4. Add open_or_search_content method to DodaiosToolHub
    toolhub_open_method = '''    def open_or_search_content(self, target: str, raw_query: str = "") -> tuple[bool, str, str, str]:
        """
        Universal Opener & Search Engine for:
        - __filename: documents, spreadsheets, text files, code, notes (.docx, .xlsx, .pdf, .txt, etc.)
        - _vedioname: local video files or YouTube direct streaming
        - _photoname: local photos/screenshots or Google Images search
        - _appname: desktop applications via KWin / desktop files / binaries
        - _browser: Chromium browser, URLs, web services
        - etc: universal fallback search in Chromium

        Returns (success: bool, reply_text: str, action_badge: str, media_path: str)
        """
        t_clean = target.strip().strip("'\\"").strip()
        t_lower = t_clean.lower()
        if not t_clean:
            return False, "Please specify what you would like me to open or search.", "Open: Missing Target", ""

        # 1. Direct Web Services, Browser, and URLs
        if t_lower in ["browser", "chromium", "chrome", "default browser"]:
            msg = self.open_browser(url="chrome://newtab", new_tab=True)
            return True, msg, "Browser: Chromium", ""

        if t_lower in ["firefox"]:
            spawn_software("/usr/bin/firefox")
            return True, "Opened Firefox browser.", "Browser: Firefox", ""

        web_services = {
            "whatsapp web": ("https://web.whatsapp.com", "WhatsApp Web"),
            "whatsapp": ("https://web.whatsapp.com", "WhatsApp Web"),
            "youtube": ("https://www.youtube.com", "YouTube"),
            "github": ("https://github.com", "GitHub"),
            "reddit": ("https://www.reddit.com", "Reddit"),
            "gmail": ("https://mail.google.com", "Gmail"),
            "wikipedia": ("https://www.wikipedia.org", "Wikipedia"),
        }
        for svc_name, (svc_url, svc_disp) in web_services.items():
            if t_lower == svc_name or t_lower == f"the {svc_name}":
                self.open_browser(url=svc_url, new_tab=True)
                return True, f"Opened {svc_disp} in Chromium.", f"Browser: {svc_disp}", ""

        if t_lower.startswith("http://") or t_lower.startswith("https://") or ('.' in t_clean and ' ' not in t_clean and any(t_clean.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".in", ".edu", ".gov", ".dev", ".ai"])):
            url_target = t_clean if t_clean.startswith("http") else f"https://{t_clean}"
            msg = self.open_browser(url=url_target, new_tab=True)
            return True, f"Opened {t_clean} in Chromium.", f"Browser: {t_clean[:18]}", ""

        # 2. Check if user is asking for a Video / Song (_vedioname)
        is_video_intent = (
            any(w in t_lower for w in ["video", "movie", "clip", "song", "track"]) or
            Path(t_clean).suffix.lower() in VIDEO_EXTENSIONS or
            "video" in raw_query.lower() or "song" in raw_query.lower() or "play" in raw_query.lower()
        )
        if is_video_intent:
            found_v, kind = find_user_content(t_clean, expected_type="video")
            if found_v and found_v.exists():
                try:
                    subprocess.Popen(["xdg-open", str(found_v)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return True, f"Opened video '{found_v.name}' in your media player.", f"Video: {found_v.name[:18]}", ""
                except Exception as e:
                    return False, f"Failed to open video file: {e}", "Video Error", ""
            else:
                clean_yt = re.sub(r"\\b(?:open|play|video|song|movie|track|clip|in\\s+chromium|on\\s+youtube)\\b", "", t_clean, flags=re.I).strip()
                if not clean_yt:
                    clean_yt = t_clean
                ok, msg = self.play_youtube_query(clean_yt)
                return True, msg, f"YouTube: Play ({clean_yt[:16]})", ""

        # 3. Check if user is asking for a Photo / Image (_photoname)
        is_photo_intent = (
            any(w in t_lower for w in ["photo", "image", "picture", "screenshot", "wallpaper", "pic"]) or
            Path(t_clean).suffix.lower() in IMAGE_EXTENSIONS or
            "photo" in raw_query.lower() or "image" in raw_query.lower() or "picture" in raw_query.lower()
        )
        if is_photo_intent:
            found_img, kind = find_user_content(t_clean, expected_type="image")
            if found_img and found_img.exists():
                try:
                    subprocess.Popen(["xdg-open", str(found_img)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return True, f"Opened photo '{found_img.name}' in default viewer.", f"Photo: {found_img.name[:18]}", str(found_img)
                except Exception as e:
                    return False, f"Failed to open image file: {e}", "Photo Error", ""
            else:
                clean_img = re.sub(r"\\b(?:open|show|display|find|photo\\s+of|image\\s+of|picture\\s+of|photo|image|picture|screenshot|snapshot)\\b", "", t_clean, flags=re.I).strip()
                if not clean_img:
                    clean_img = t_clean
                img_url = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(clean_img)}"
                self.open_browser(url=img_url, new_tab=True)
                return True, f"Opened Chromium searching photos for '{clean_img}'.", f"Photos: {clean_img[:16]}", ""

        # 4. Check if user is asking for a Document or File (__filename)
        is_file_intent = (
            any(w in t_lower for w in ["file", "document", "report", "doc", "notes", "spreadsheet", "excel", "pdf"]) or
            Path(t_clean).suffix.lower() in DOC_EXTENSIONS or
            "file" in raw_query.lower() or "document" in raw_query.lower()
        )
        if is_file_intent or Path(t_clean).suffix.lower() in DOC_EXTENSIONS:
            found_doc, kind = find_user_content(t_clean, expected_type="document")
            if found_doc and found_doc.exists():
                try:
                    subprocess.Popen(["xdg-open", str(found_doc)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    self.last_created_file = str(found_doc)
                    return True, f"Opened '{found_doc.name}' in your default application.", f"File: {found_doc.name[:18]}", ""
                except Exception as e:
                    return False, f"Failed to open document: {e}", "File Open Error", ""

        # 5. Check Desktop Applications (_appname)
        resolved_app = resolve_app_name(t_clean)
        if resolved_app or shutil.which(t_clean) or shutil.which(t_clean.replace(" ", "")) or find_desktop_app(t_clean):
            ok, msg = launch_application(t_clean)
            if ok:
                return True, msg, f"App: Open {t_clean.title()[:16]}", ""

        # 6. General Local Search for File (untyped exact or stem match)
        found_any, kind = find_user_content(t_clean, expected_type="any")
        if found_any and found_any.exists():
            try:
                subprocess.Popen(["xdg-open", str(found_any)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                media_out = str(found_any) if kind == "image" else ""
                return True, f"Opened {kind} '{found_any.name}' in your default application.", f"{kind.title()}: {found_any.name[:18]}", media_out
            except Exception as e:
                return False, f"Failed to open {kind}: {e}", "Open Error", ""

        # 7. Fallback: Search the Web in Chromium (_browser etc)
        if is_file_intent and ("file" in t_lower or "." in t_clean):
            return False, f"File '{t_clean}' was not found in Documents, Downloads, or Desktop.", "File: Not Found", ""
        if "app" in raw_query.lower() or "application" in raw_query.lower():
            return False, f"Application '{t_clean}' was not found on your system.", "App: Not Found", ""

        clean_search = re.sub(r"^(?:open|search(?:\\s+for)?|look\\s+up|google(?:\\s+for)?)\\s+", "", t_clean, flags=re.I).strip()
        if not clean_search:
            clean_search = t_clean
        msg = self.browser_search(clean_search)
        return True, f"I couldn't find a local file or application for '{t_clean}', so I searched for it in Chromium.", f"Search: {clean_search[:16]}", ""
'''

    if "def open_or_search_content" not in content:
        anchor = "    def play_youtube_query(self, query: str) -> tuple[bool, str]:"
        content = content.replace(anchor, toolhub_open_method + "\n" + anchor, 1)
        print("[APPLIED] Added open_or_search_content to DodaiosToolHub.")

    # 5. Route 'open <target>' and 'search <target>' in AudioVoiceEngine._execute_single_command
    old_app_open_block = '''        open_m = re.match(r"^(?:please\s+)?(?:open|launch|start|spawn)\s+(?:the\s+)?([a-zA-Z0-9_\-\s]+)$", q_lower)
        if open_m:
            app_raw = open_m.group(1).strip()
            if app_raw not in ["ollama", "brain", "ai"] and not any(k in app_raw for k in ["dictat", "doc", "excel", "spreadsheet", "report", "summary", "research", "mail", "whatsapp"]):
                ok, msg = launch_application(app_raw)
                if ok:
                    return (msg, f"App: Open {app_raw.title()}", "")
                else:
                    return (msg, "App: Not Found", "")'''

    new_app_open_block = '''        # 2. Universal Content Opener & Search Engine (Filename, Videoname, Photoname, Appname, Browser & Web Search)
        open_req_m = (
            re.match(r"^(?:please\s+)?(?:open|launch|start|spawn|view|show|play)\s+(?:the\s+)?(.+)$", q_clean, re.I) or
            re.match(r"^(?:please\s+)?(?:search(?:\s+for)?|look\s+up|find)\s+(?:the\s+)?(.+)$", q_clean, re.I)
        )
        if open_req_m:
            target_raw = open_req_m.group(1).strip().rstrip(" ,.;!?")
            target_lower = target_raw.lower()
            if target_lower not in ["ollama", "brain", "ai"] and not any(k in target_lower for k in ["dictat", "create doc", "draft doc", "create excel", "draft excel", "create file", "write a file"]):
                ok, reply, badge, media = self.tool_hub.open_or_search_content(target_raw, raw_query=q_clean)
                return (reply, badge, media)'''

    if old_app_open_block in content:
        content = content.replace(old_app_open_block, new_app_open_block, 1)
        print("[APPLIED] Replaced legacy app open with Universal Content Opener & Search Engine in _execute_single_command.")
    else:
        print("[WARNING] Could not find legacy app open block in void-widget.py. Checking if already replaced...")

    WIDGET_FILE.write_text(content, encoding="utf-8")
    print(f"[SUCCESS] VOID Desktop Assistant updated at: {WIDGET_FILE}")

if __name__ == "__main__":
    apply_enhancements()

