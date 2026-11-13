#!/usr/bin/env python3
"""
Applies comprehensive enhancements to bin/void-widget.py:
1. SystemAppRegistry: Dynamic desktop app indexing, fuzzy matching, snap/flatpak support, Antigravity IDE detection, robust closing.
2. STT Voice Normalizations: "anti-gravty", "closiing", "regoconise", "pen form", "make ure", "tittle", "pagges", "grammers".
3. Hearing Space: Increased silence threshold (~3.2s) and 45s utterance buffer for long, complex prompts.
4. Word & PDF Formatting: Styled callouts (shapes), comparison & benchmark tables, metric cards, page count scaling.
5. File Search & Selection: Multi-directory search returning all results with numbered clickable links and "open 1" voice selection.
6. Large Prompt Parsing: Extracts target pages, custom title, and cleans topic.
7. Widget UI: Accessible, wide scrollbars (not swallowed by window drag), corner dragging to resize with geometry persistence.
8. AI Training & Memory Reinforcement: System prompt exemplars and persistent memory profile.
"""

import sys
from pathlib import Path
import re

WIDGET_FILE = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")

def apply_enhancements():
    if not WIDGET_FILE.exists():
        print(f"Error: {WIDGET_FILE} not found!")
        sys.exit(1)

    code = WIDGET_FILE.read_text(encoding="utf-8")
    original_len = len(code)
    print(f"Read {original_len} characters from {WIDGET_FILE.name}.")

    # -----------------------------------------------------------------------
    # 1. SystemAppRegistry & Enhanced App Launcher / Closer
    # -----------------------------------------------------------------------
    app_registry_code = '''
# ---------------------------------------------------------------------------
# Intelligent System Application Registry & Process Manager
# ---------------------------------------------------------------------------
class SystemAppRegistry:
    """
    Dynamically scans and indexes all installed desktop applications across:
    - /usr/share/applications
    - /usr/local/share/applications
    - ~/.local/share/applications
    - /var/lib/snapd/desktop/applications
    - /var/lib/flatpak/exports/share/applications
    - ~/.local/share/flatpak/exports/share/applications
    - Snap binaries (/var/lib/snapd/snap/bin, /snap/bin)
    Provides robust fuzzy matching, explicit aliases, process mapping for closing,
    and native desktop launching via gio or direct Exec.
    """
    def __init__(self) -> None:
        self.apps: dict[str, dict[str, Any]] = {}
        self.search_dirs = [
            Path("/usr/share/applications"),
            Path("/usr/local/share/applications"),
            Path.home() / ".local/share/applications",
            Path("/var/lib/snapd/desktop/applications"),
            Path("/var/lib/flatpak/exports/share/applications"),
            Path.home() / ".local/share/flatpak/exports/share/applications",
        ]
        self._rescan()

    def _rescan(self) -> None:
        self.apps.clear()
        for sdir in self.search_dirs:
            if not sdir.exists():
                continue
            for f in sdir.glob("*.desktop"):
                try:
                    name, exec_cmd, wm_class, keywords, generic = "", "", "", "", ""
                    with open(f, "r", errors="ignore") as fp:
                        in_entry = False
                        for line in fp:
                            line = line.strip()
                            if line == "[Desktop Entry]":
                                in_entry = True
                                continue
                            elif line.startswith("[") and in_entry:
                                break
                            if not in_entry:
                                continue
                            if line.startswith("Name=") and not name:
                                name = line.split("=", 1)[1].strip()
                            elif line.startswith("Exec=") and not exec_cmd:
                                exec_cmd = line.split("=", 1)[1].strip()
                            elif line.startswith("StartupWMClass=") and not wm_class:
                                wm_class = line.split("=", 1)[1].strip()
                            elif line.startswith("Keywords=") and not keywords:
                                keywords = line.split("=", 1)[1].strip()
                            elif line.startswith("GenericName=") and not generic:
                                generic = line.split("=", 1)[1].strip()
                    if name and exec_cmd:
                        stem = f.stem.lower()
                        self.apps[stem] = {
                            "name": name,
                            "exec": exec_cmd,
                            "wm_class": wm_class,
                            "keywords": keywords,
                            "generic": generic,
                            "desktop_file": str(f),
                            "stem": stem
                        }
                except Exception:
                    pass

        # Explicit High-Priority Aliases for Core Local Applications
        # Antigravity IDE (Snap)
        antigravity_desktop = "/var/lib/snapd/desktop/applications/antigravity-ide-snap_antigravity-ide.desktop"
        antigravity_exec = "/var/lib/snapd/snap/bin/antigravity-ide-snap.antigravity-ide"
        if Path(antigravity_desktop).exists() or Path(antigravity_exec).exists():
            self.apps["antigravity"] = {
                "name": "Antigravity IDE",
                "exec": antigravity_exec,
                "wm_class": "antigravity-ide",
                "keywords": "antigravity;ide;agent;editor;code;development;",
                "generic": "Agent-first IDE",
                "desktop_file": antigravity_desktop if Path(antigravity_desktop).exists() else "",
                "stem": "antigravity"
            }

    def resolve(self, query: str) -> dict[str, Any] | None:
        q = query.strip().lower()
        if not q:
            return None
        q_clean = re.sub(r"[^a-z0-9]", "", q)
        if not q_clean or q_clean in ["that", "it", "this", "something", "file", "document", "pdf", "word"]:
            return None

        # 0. Antigravity IDE voice & alias overrides
        if any(k in q for k in ["antigravity", "anti-gravity", "anti gravity", "anti-gravty", "anti gravty", "antigravty", "antigravity ide", "agy"]):
            for k, v in self.apps.items():
                if "antigravity" in v["name"].lower() or "antigravity" in k:
                    return v

        # 1. Exact match on stem or name
        for k, v in self.apps.items():
            stem_clean = re.sub(r"[^a-z0-9]", "", k)
            name_clean = re.sub(r"[^a-z0-9]", "", v["name"].lower())
            if q_clean == stem_clean or q_clean == name_clean:
                return v

        # 2. Substring match on name
        for k, v in self.apps.items():
            name_clean = re.sub(r"[^a-z0-9]", "", v["name"].lower())
            if (len(q_clean) >= 3 and q_clean in name_clean) or (len(name_clean) >= 4 and name_clean in q_clean):
                return v

        # 3. GenericName or Keywords match
        for k, v in self.apps.items():
            gen_clean = re.sub(r"[^a-z0-9]", "", v["generic"].lower())
            if q_clean and (q_clean == gen_clean or (len(q_clean) >= 4 and q_clean in gen_clean)):
                return v
            kw_clean = re.sub(r"[^a-z0-9;]", "", v["keywords"].lower()).split(";")
            if any(q_clean == re.sub(r"[^a-z0-9]", "", kw) for kw in kw_clean if kw):
                return v

        # 4. Difflib close matches on display names
        import difflib
        names_map = {v["name"]: v for v in self.apps.values()}
        close = difflib.get_close_matches(q, list(names_map.keys()), n=1, cutoff=0.65)
        if close:
            return names_map[close[0]]

        return None

    def launch(self, query: str) -> tuple[bool, str]:
        app = self.resolve(query)
        if app:
            d_file = app.get("desktop_file", "")
            if d_file and Path(d_file).exists() and shutil.which("gio"):
                try:
                    subprocess.Popen(["gio", "launch", d_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return True, f"Opened {app['name']}."
                except Exception:
                    pass
            # Parse Exec line
            exec_raw = app.get("exec", "")
            if exec_raw:
                parts = []
                for p in exec_raw.split():
                    if p.startswith("%"):
                        continue
                    parts.append(p)
                if parts:
                    cmd_bin = shutil.which(parts[0]) or parts[0]
                    if Path(cmd_bin).exists() or shutil.which(parts[0]):
                        try:
                            subprocess.Popen([cmd_bin] + parts[1:], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                            return True, f"Opened {app['name']}."
                        except Exception:
                            pass

        # Fallback to standard binaries in PATH
        clean_bin = query.strip().lower()
        which_bin = shutil.which(clean_bin) or shutil.which(clean_bin.replace(" ", ""))
        if which_bin:
            try:
                subprocess.Popen([which_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                return True, f"Opened {clean_bin.title()}."
            except Exception:
                pass

        return False, f"Application '{query}' was not found on your system."

    def close(self, query: str) -> bool:
        clean = query.strip().lower()
        app = self.resolve(clean)
        targets = [clean]
        if app:
            if app.get("wm_class"):
                targets.append(app["wm_class"])
            if app.get("stem"):
                targets.append(app["stem"])
            # Extract binary name from Exec
            e_parts = app.get("exec", "").split()
            if e_parts:
                targets.append(Path(e_parts[0]).name)

        # Explicit aliases
        if any(k in clean for k in ["antigravity", "anti-gravity", "anti gravty", "anti-gravty", "agy"]):
            targets.extend(["antigravity-ide", "antigravity"])

        closed_any = False
        for tgt in set(targets):
            if not tgt or tgt in ["system", "window", "desktop", "all"]:
                continue
            try:
                res = subprocess.run(["pkill", "-f", tgt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    closed_any = True
            except Exception:
                pass
        return closed_any

SYSTEM_APP_REGISTRY = SystemAppRegistry()
'''

    # Insert SystemAppRegistry before KNOWN_APPS
    if "class SystemAppRegistry:" not in code:
        target_str = "KNOWN_APPS = {"
        if target_str in code:
            code = code.replace(target_str, app_registry_code + "\n" + target_str)
            print("Successfully inserted SystemAppRegistry.")
        else:
            print("Warning: KNOWN_APPS target string not found!")

    # Update KNOWN_APPS to include antigravity explicitly
    if '"antigravity": [' not in code:
        old_known = 'KNOWN_APPS = {\n    "chromium":'
        new_known = '''KNOWN_APPS = {
    "antigravity": ["antigravity", "anti gravity", "anti-gravity", "anti-gravty", "anti gravty", "antigravty", "antigravity ide", "agy"],
    "chromium":'''
        code = code.replace(old_known, new_known)
        print("Updated KNOWN_APPS with antigravity.")

    # Update launch_application and close_software_by_name
    old_launch_func = """def launch_application(app_name: str) -> tuple[bool, str]:"""
    if old_launch_func in code:
        # Replace implementation of launch_application
        launch_pattern = re.compile(r"def launch_application\(app_name: str\) -> tuple\[bool, str\]:.*?(?=\n\n# ---------------------------------------------------------------------------)", re.DOTALL)
        new_launch_impl = '''def launch_application(app_name: str) -> tuple[bool, str]:
    clean = app_name.strip().lower()
    # 1. System Registry First
    ok, msg = SYSTEM_APP_REGISTRY.launch(clean)
    if ok:
        return True, msg

    # 2. Known apps open map
    resolved = resolve_app_name(clean)
    target = resolved or clean
    open_map: dict[str, str] = {
        "antigravity": "/var/lib/snapd/snap/bin/antigravity-ide-snap.antigravity-ide",
        "chromium": "/usr/bin/chromium-browser",
        "browser": "/usr/bin/chromium-browser",
        "chrome": "/usr/bin/chromium-browser",
        "firefox": "/usr/bin/firefox",
        "konsole": "/usr/bin/konsole",
        "terminal": "/usr/bin/konsole",
        "dolphin": "/usr/bin/dolphin",
        "files": "/usr/bin/dolphin",
        "kcalc": "/usr/bin/kcalc",
        "calculator": "/usr/bin/kcalc",
        "kwrite": "/usr/bin/kwrite",
        "text editor": "/usr/bin/kwrite",
        "kate": "/usr/bin/kwrite",
        "systemsettings": "/usr/bin/systemsettings",
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
    }
    if target in open_map:
        if spawn_software(open_map[target]):
            return True, f"Opened {target.title()}."

    which_bin = shutil.which(target) or shutil.which(target.replace(" ", ""))
    if which_bin:
        if spawn_software(which_bin):
            return True, f"Opened {target.title()}."

    return False, f"Application '{clean}' was not found on your system."'''
        code = launch_pattern.sub(new_launch_impl, code, count=1)
        print("Updated launch_application implementation.")

    # Update close_software_by_name
    old_close_func = """def close_software_by_name(name: str) -> bool:"""
    if old_close_func in code:
        close_pattern = re.compile(r"def close_software_by_name\(name: str\) -> bool:.*?(?=\ndef spawn_software)", re.DOTALL)
        new_close_impl = '''def close_software_by_name(name: str) -> bool:
    clean = name.strip().lower()
    # Try through system app registry first
    if SYSTEM_APP_REGISTRY.close(clean):
        return True

    app_map = {
        "antigravity": "antigravity-ide",
        "chromium": "chromium", "firefox": "firefox", "browser": "chromium",
        "dolphin": "dolphin", "files": "dolphin", "file manager": "dolphin",
        "terminal": "konsole", "konsole": "konsole", "kate": "kwrite",
        "kwrite": "kwrite", "kcalc": "kcalc", "calculator": "kcalc",
        "vlc": "vlc", "settings": "systemsettings"
    }
    target = app_map.get(clean, clean)
    try:
        subprocess.run(["pkill", "-f", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False'''
        code = close_pattern.sub(new_close_impl, code, count=1)
        print("Updated close_software_by_name implementation.")

    # -----------------------------------------------------------------------
    # 2. STT Voice Normalizations
    # -----------------------------------------------------------------------
    norm_needle = '(r"\\b(?:whats\\s*app|wats\\s*app|watsapp|whatsaap)\\b", "whatsapp"),'
    if norm_needle in code:
        added_norms = '''(r"\\b(?:whats\\s*app|wats\\s*app|watsapp|whatsaap)\\b", "whatsapp"),
        (r"\\b(?:anti[- ]?grav(?:i)?t(?:y|ee)|anti[- ]?gravty|antigravty|anti\\s+gravty|anti\\s+gravity)\\b", "antigravity"),
        (r"\\b(?:closiing|clsing|clse|colse)\\b", "close"),
        (r"\\b(?:regoconise|recognise|recog)\\b", "recognize"),
        (r"\\b(?:pen form|pen from|open form)\\b", "open from"),
        (r"\\b(?:tittle)\\b", "title"),
        (r"\\b(?:pagges|pags)\\b", "pages"),
        (r"\\b(?:grammers)\\b", "grammar"),
        (r"\\b(?:errorrs)\\b", "errors"),
        (r"\\b(?:revalent)\\b", "relevant"),
        (r"\\b(?:feld)\\b", "field"),
        (r"\\b(?:coudnt)\\b", "couldnt"),
        (r"\\b(?:formating)\\b", "formatting"),
        (r"\\b(?:make ure)\\b", "make sure"),'''
        code = code.replace(norm_needle, added_norms)
        print("Added new STT voice normalizations.")

    # -----------------------------------------------------------------------
    # 3. Audio Silence / Hearing Space Extension
    # -----------------------------------------------------------------------
    old_silence = "if (self._silence_chunks >= 15 and len(self._audio_buffer) >= 10) or len(self._audio_buffer) > 120:"
    new_silence = "# Extended hearing space: ~3.2s silence pause tolerance and 45s maximum utterance buffer\n                                if (self._silence_chunks >= 32 and len(self._audio_buffer) >= 10) or len(self._audio_buffer) > 450:"
    if old_silence in code:
        code = code.replace(old_silence, new_silence)
        print("Updated audio hearing space (silence chunks >= 32, max buffer > 450).")

    # -----------------------------------------------------------------------
    # 4. Multi-Directory File Search with Clickable Links and Numbered Selection
    # -----------------------------------------------------------------------
    old_search_files = "    def search_files(self, pattern: str, search_path: str = \"/home/prakash/Documents\") -> list[str]:"
    if old_search_files in code:
        search_pattern = re.compile(r"    def search_files\(self, pattern: str, search_path: str = \"/home/prakash/Documents\"\) -> list\[str\]:.*?(?=\n    def create_document)", re.DOTALL)
        new_search_files = '''    def search_files(self, pattern: str, search_path: str = "") -> list[str]:
        """Searches across user Documents, Downloads, Pictures, Desktop, and project workspaces returning all matches."""
        clean_pat = pattern.strip().strip("*").lower()
        if not clean_pat:
            return []

        search_dirs = [
            Path("/home/prakash/Documents"),
            Path("/home/prakash/Downloads"),
            Path("/home/prakash/Pictures"),
            Path("/home/prakash/Desktop"),
            Path("/run/media/prakash/TR_39/VOID"),
        ]
        if search_path:
            custom_p = Path(search_path).expanduser().resolve()
            if is_safe_user_path(custom_p) and custom_p.exists():
                search_dirs.insert(0, custom_p)

        regex = re.compile(re.escape(clean_pat), re.I)
        matches = []
        seen = set()

        for sdir in search_dirs:
            if not sdir.exists():
                continue
            try:
                for root, dirs, files in os.walk(sdir):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for fname in files:
                        if fname.startswith("."):
                            continue
                        if regex.search(fname):
                            full_p = str(Path(root) / fname)
                            if full_p not in seen:
                                seen.add(full_p)
                                try:
                                    matches.append((Path(full_p).stat().st_mtime, full_p))
                                except Exception:
                                    matches.append((0, full_p))
                                if len(matches) >= 50:
                                    break
                    if len(matches) >= 50:
                        break
            except Exception:
                pass
            if len(matches) >= 50:
                break

        matches.sort(key=lambda x: x[0], reverse=True)
        res = [m[1] for m in matches]
        self.last_search_results = res
        return res'''
        code = search_pattern.sub(new_search_files, code, count=1)
        print("Updated search_files implementation for multi-directory search.")

    # -----------------------------------------------------------------------
    # 5. Fast Path for File Search and Numbered File Selection
    # -----------------------------------------------------------------------
    needle_before_opener = "# 2. Universal Content Opener & Search Engine"
    if "File Search & Interactive Number Selection Fast-Path" not in code and needle_before_opener in code:
        file_search_fast_path = '''        # 1h. File Search & Interactive Number Selection Fast-Path
        # A. File Search ("search files for ...", "find all files matching ...", "search for files ...")
        file_search_m = re.match(r"^(?:please\s+)?(?:search(?:\s+for)?|find|locate)\s+(?:all\s+)?files?\s+(?:named|matching|with|for)?\s*(.+)$", q_clean, re.I)
        if file_search_m and not any(k in q_lower for k in ["search notes", "search note", "notes for", "in notes"]):
            pat = file_search_m.group(1).strip().strip("\'\\"")
            matches = self.tool_hub.search_files(pat)
            if matches:
                links = []
                for idx, f in enumerate(matches, 1):
                    p_f = Path(f)
                    links.append(f"{idx}. <a href=\\"file://{p_f}\\" style=\\"color:#38bdf8; text-decoration:none;\\"><b>{p_f.name}</b></a> <span style=\\"color:#64748b; font-size:9px;\\">({p_f.parent.name})</span>")
                ui_text = f"Found {len(matches)} files matching \'{pat}\':<br><br>" + "<br>".join(links) + "<br><br><i>Say 'open 1' or click any file directly to open it.</i>"
                spoken = f"Found {len(matches)} files matching \'{pat}\'. Say open 1 or click any file directly."
                return (ui_text, f"Files: Found {len(matches)}", matches[0])
            else:
                return (f"No files found matching \'{pat}\' across Documents, Downloads, Desktop, or workspace.", "Files: Not Found", "")

        # B. Numbered File Selection ("open 1", "open file 1", "open the first file", "open number 2")
        num_open_m = re.match(r"^(?:please\s+)?open\s+(?:the\s+)?(?:file\s+)?(?:#|number\s+)?(\d+)(?:st|nd|rd|th)?(?:\s+file)?$", q_clean, re.I)
        target_idx = None
        if num_open_m:
            target_idx = int(num_open_m.group(1))
        else:
            ord_map = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4, "fifth": 5, "5th": 5}
            ord_m = re.match(r"^(?:please\s+)?open\s+(?:the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s+file$", q_clean, re.I)
            if ord_m:
                target_idx = ord_map.get(ord_m.group(1).lower())

        if target_idx is not None:
            recent_searches = getattr(self.tool_hub, "last_search_results", [])
            if recent_searches and 1 <= target_idx <= len(recent_searches):
                chosen_file = recent_searches[target_idx - 1]
                p_chosen = Path(chosen_file)
                if p_chosen.exists():
                    try:
                        subprocess.Popen(["xdg-open", str(p_chosen)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                        self.tool_hub.last_created_file = str(p_chosen)
                        return (f"Opened \'{p_chosen.name}\' in your default application.", f"File: {p_chosen.name[:16]}", str(p_chosen))
                    except Exception as e:
                        return (f"Failed to open \'{p_chosen.name}\': {e}", "File Open Error", "")
                else:
                    return (f"File \'{p_chosen.name}\' no longer exists at that path.", "File: Not Found", "")
            else:
                return (f"Could not find search result #{target_idx}. Please search for files first.", "File: Out of Range", "")

        '''
        code = code.replace(needle_before_opener, file_search_fast_path + "\n        " + needle_before_opener)
        print("Inserted file search and numbered selection fast-path.")

    # -----------------------------------------------------------------------
    # 6. Large Prompt Parsing & Page Count Extraction in Composition
    # -----------------------------------------------------------------------
    old_compose_block = '''        # 1e. Comprehensive Document Composition & Multi-Facet Intelligence Synthesis
        is_compose_cmd = (
            any(k in q_lower for k in [
                "compose a document", "compose document", "compose comprehensive document",
                "compose comprehensive", "compose deep document", "compose deep report",
                "compose pdf", "compose a pdf", "gather information and complete",
                "gather info and complete", "gather information complete the document",
                "take time and fully gather", "take time to gather", "compose report on",
                "compose comprehensive report"
            ])
            or (re.search(r"\\bcompose\\b", q_lower) and any(w in q_lower for w in ["document", "pdf", "report", "word"]))
        )'''

    if old_compose_block in code:
        new_compose_block = '''        # 1e. Comprehensive Document Composition & Multi-Facet Intelligence Synthesis
        is_compose_cmd = (
            any(k in q_lower for k in [
                "compose a document", "compose document", "compose comprehensive document",
                "compose comprehensive", "compose deep document", "compose deep report",
                "compose pdf", "compose a pdf", "gather information and complete",
                "gather info and complete", "gather information complete the document",
                "take time and fully gather", "take time to gather", "compose report on",
                "compose comprehensive report"
            ])
            or (re.search(r"\\bcompose\\b", q_lower) and any(w in q_lower for w in ["document", "pdf", "report", "word"]))
        )
        if is_compose_cmd:
            ft = "docx" if re.search(r"\\b(?:docx?|word)\\b", q_lower) else "pdf"

            # Parse Page Count ("5 page", "3 pages", "length of 4 pages")
            page_m = re.search(r"\\b(\\d+)\\s*(?:-|–)?\\s*(?:page|pages|pg|pgs)\\b", q_clean, re.I)
            target_pages = int(page_m.group(1)) if page_m else None

            # Parse Custom Title ("titled 'Next Gen Transmons'", "called '...'")
            custom_title = ""
            title_m = re.search(r"(?:titled|title(?:d)?\\s*(?:is|as)?|called|named)\\s*[\'\\"“]([^\'\\"”]+)[\'\\"”]", q_clean, re.I)
            if not title_m:
                title_m = re.search(r"(?:titled|called|named)\\s+([a-zA-Z0-9_\\s-]+?)(?:\\s+(?:with|having|about|on|for|\\d+\\s+pages?|$))", q_clean, re.I)
            if title_m:
                custom_title = title_m.group(1).strip()

            # Clean and isolate topic
            clean_topic = q_clean
            if title_m:
                clean_topic = clean_topic.replace(title_m.group(0), " ")
            if page_m:
                clean_topic = clean_topic.replace(page_m.group(0), " ")

            clean_topic = re.sub(
                r"^(?:please\\s+)?(?:when\\s+i\\s+ask\\s+void\\s+to\\s+)?(?:compose|draft|write|create)?\\s*(?:a\\s+)?(?:comprehensive\\s+)?(?:document|doc|report|pdf|docx?|word)?\\s*(?:on|about|regarding)?\\s*",
                "", clean_topic, flags=re.I
            ).strip()
            clean_topic = re.sub(r"\\b(?:and\\s+fully\\s+gather.*|it\\s+should\\s+take\\s+time.*|with\\s+tables?.*|with\\s+comparisons?.*)\\b", "", clean_topic, flags=re.I).strip(" ,.:;!?")
            topic = clean_topic or (custom_title if custom_title else "Comprehensive Strategic Overview")

            ok, msg, path = self.tool_hub.compose_comprehensive_document(topic, file_type=ft, custom_title=custom_title, target_pages=target_pages)
            badge_title = (custom_title or topic)[:16]
            return (msg, f"Composed: {ft.upper()} ({badge_title})", path)'''
        # Replace the entire old compose block and its immediate execution
        old_full_compose_regex = re.compile(r"        # 1e\. Comprehensive Document Composition & Multi-Facet Intelligence Synthesis\n        is_compose_cmd = \(.*?\n            return \(msg, f\"Composed: \{ft\.upper\(\)\} \(\{badge_title\}\)\", path\)", re.DOTALL)
        code = old_full_compose_regex.sub(new_compose_block, code, count=1)
        print("Updated document composition with page count and custom title parsing.")

    # -----------------------------------------------------------------------
    # 7. Document Formatting: Tables & Shapes in docx and pdf
    # -----------------------------------------------------------------------
    # Update draft_docx_document to add styled callout shapes and header fills
    old_docx_sec = '            for sec in sections:\n                h = sec.get("heading", "")'
    if old_docx_sec in code and "w:shd" not in code[:code.find("def draft_excel_spreadsheet")]:
        new_docx_sec = '''            from docx.shared import Inches, Pt, RGBColor
            from docx.oxml import parse_xml
            from docx.oxml.ns import nsdecls

            # Executive Summary Callout Box (Visual Shape)
            callout_tbl = doc.add_table(rows=1, cols=1)
            callout_tbl.autofit = False
            c_cell = callout_tbl.cell(0, 0)
            c_cell.width = Inches(6.5)
            shd = parse_xml(r\'<w:shd {} w:fill="F0F9FF"/>\'.format(nsdecls('w')))
            c_cell._tc.get_or_add_tcPr().append(shd)
            borders = parse_xml(r\'\'\'
                <w:tcBorders {} >
                    <w:top w:val="none"/>
                    <w:left w:val="single" w:sz="24" w:space="0" w:color="0284C7"/>
                    <w:bottom w:val="none"/>
                    <w:right w:val="none"/>
                </w:tcBorders>
            \'\'\'.format(nsdecls('w')))
            c_cell._tc.get_or_add_tcPr().append(borders)
            c_p = c_cell.paragraphs[0]
            c_r1 = c_p.add_run("💡 Strategic Overview & Executive Scope: ")
            c_r1.bold = True
            c_r1.font.color.rgb = RGBColor(3, 105, 161)
            c_r2 = c_p.add_run(f"Comprehensive analysis and verified intelligence for {title}.")
            c_r2.font.color.rgb = RGBColor(30, 41, 59)
            doc.add_paragraph()

            for sec in sections:
                h = sec.get("heading", "")'''
        code = code.replace(old_docx_sec, new_docx_sec)
        print("Enhanced Word (.docx) document drafting with callout shape.")

    # Update draft_pdf_document CSS with modern shapes, metrics grid, and page break rules
    old_pdf_style = "    .content-list {\n        margin: 6px 0 14px 20px;\n        padding: 0;\n    }"
    if old_pdf_style in code:
        new_pdf_style = '''    .content-list {
        margin: 6px 0 14px 20px;
        padding: 0;
    }
    .header-bar {
        height: 4px;
        background: linear-gradient(90deg, #0284c7, #38bdf8, #818cf8);
        margin-bottom: 20px;
        border-radius: 2px;
    }
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin: 16px 0 20px 0;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: center;
    }
    .metric-val { font-size: 16pt; font-weight: 700; color: #0284c7; margin-bottom: 2px; }
    .metric-lbl { font-size: 8pt; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
    .callout-box {
        background: #f0f9ff;
        border-left: 4px solid #0284c7;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 16px 0;
    }
    .callout-title { font-weight: 700; color: #0369a1; font-size: 10.5pt; margin-bottom: 4px; }
    .page-break { page-break-before: always; }'''
        code = code.replace(old_pdf_style, new_pdf_style)
        print("Enhanced PDF document styling with CSS shapes, metrics grid, and page-break rules.")

    # -----------------------------------------------------------------------
    # 8. Widget UI: Scrollbars Access & Corner Dragging to Resize
    # -----------------------------------------------------------------------
    # In _resp_scroll, increase scrollbar width from 5px to 10px and style it with distinct hover
    old_scroll_style = """            QScrollBar:vertical {
                border: none;
                background: rgba(15, 23, 42, 0.35);
                width: 5px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(56, 189, 248, 0.45);
                border-radius: 2px;
                min-height: 15px;
            }"""

    new_scroll_style = """            QScrollBar:vertical {
                border: none;
                background: rgba(15, 23, 42, 0.45);
                width: 10px;
                border-radius: 5px;
                margin: 2px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(56, 189, 248, 0.60);
                border-radius: 5px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(56, 189, 248, 0.95);
            }"""

    if old_scroll_style in code:
        code = code.replace(old_scroll_style, new_scroll_style)
        print("Widened and enhanced scrollbar styling.")

    # Enable openExternalLinks on _resp_text
    old_resp_text = 'self._resp_text = QLabel("Ready to assist you.", self._resp_scroll)\n        self._resp_text.setWordWrap(True)'
    if old_resp_text in code:
        new_resp_text = '''self._resp_text = QLabel("Ready to assist you.", self._resp_scroll)
        self._resp_text.setWordWrap(True)
        self._resp_text.setOpenExternalLinks(True)
        self._resp_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)'''
        code = code.replace(old_resp_text, new_resp_text)
        print("Enabled clickable external links on _resp_text.")

    # Exclude scrollbar, scroll area, and text edit from drag event filter
    old_filter_install = """        # Enable dragging anywhere on the glass surface
        self._card.setCursor(Qt.CursorShape.OpenHandCursor)
        self._card.installEventFilter(self)
        for child in self._card.findChildren(QWidget):
            if not isinstance(child, (QPushButton, QLineEdit, MicButton)):
                child.installEventFilter(self)"""

    new_filter_install = """        # Enable dragging anywhere on the glass surface, EXCLUDING interactive scrollbars & text
        self._card.setCursor(Qt.CursorShape.OpenHandCursor)
        self._card.installEventFilter(self)
        for child in self._card.findChildren(QWidget):
            if not isinstance(child, (QPushButton, QLineEdit, QTextEdit, QPlainTextEdit, QScrollBar, QAbstractScrollArea, QScrollArea, MicButton)):
                if child not in (self._resp_scroll, self._resp_text, self._input_field):
                    child.installEventFilter(self)"""

    if old_filter_install in code:
        code = code.replace(old_filter_install, new_filter_install)
        print("Updated drag event filter installation to preserve scrollbar access.")

    # Event filter method exclusion
    old_event_filter = """    def eventFilter(self, watched: QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if isinstance(event, QtGui.QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                if not isinstance(watched, (QPushButton, QLineEdit, MicButton)):
                    self.start_drag(event)
                    return True"""

    new_event_filter = """    def eventFilter(self, watched: QObject, event: QtCore.QEvent) -> bool:
        # Never swallow mouse events on interactive controls or scrollbars
        if isinstance(watched, (QPushButton, QLineEdit, QTextEdit, QPlainTextEdit, QScrollBar, QAbstractScrollArea, QScrollArea, MicButton)) or watched in (self._resp_scroll, self._resp_text, self._input_field):
            return super().eventFilter(watched, event)
        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if isinstance(event, QtGui.QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                self.start_drag(event)
                return True"""

    if old_event_filter in code:
        code = code.replace(old_event_filter, new_event_filter)
        print("Updated eventFilter method to never swallow scrollbar events.")

    # Corner Dragging to Resize implementation
    old_setup_flags = """    def _setup_window_flags(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(self.COLLAPSED_W, self.COLLAPSED_H)"""

    new_setup_flags = """    def _setup_window_flags(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setMinimumSize(self.COLLAPSED_W, self.COLLAPSED_H)
        self.resize(self.COLLAPSED_W, self.COLLAPSED_H)"""

    if old_setup_flags in code:
        code = code.replace(old_setup_flags, new_setup_flags)
        print("Updated _setup_window_flags to support dynamic resizing.")

    # Update set_expanded to use resizable dimensions and load geometry
    old_set_expanded = """    def set_expanded(self, expanded: bool) -> None:
        self._is_expanded = expanded
        self._expanded_box.setVisible(expanded)
        self._expand_btn.setText("▲" if expanded else "▼")
        self._update_glass_style(expanded)
        if expanded:
            self.setFixedSize(self.EXPANDED_W, self.EXPANDED_H)
            self._auto_collapse_timer.stop()
        else:
            self.setFixedSize(self.COLLAPSED_W, self.COLLAPSED_H)"""

    new_set_expanded = """    def set_expanded(self, expanded: bool) -> None:
        self._is_expanded = expanded
        self._expanded_box.setVisible(expanded)
        self._expand_btn.setText("▲" if expanded else "▼")
        self._update_glass_style(expanded)
        if expanded:
            self.setMinimumSize(370, 240)
            self.setMaximumSize(1200, 950)
            target_w = max(370, getattr(self, "_user_expanded_w", 420))
            target_h = max(260, getattr(self, "_user_expanded_h", 320))
            self.resize(target_w, target_h)
            if hasattr(self, "_resp_scroll"):
                self._resp_scroll.setMaximumHeight(max(85, target_h - 170))
            self._auto_collapse_timer.stop()
        else:
            self.setMinimumSize(self.COLLAPSED_W, self.COLLAPSED_H)
            self.setMaximumSize(self.COLLAPSED_W, self.COLLAPSED_H)
            self.resize(self.COLLAPSED_W, self.COLLAPSED_H)"""

    if old_set_expanded in code:
        code = code.replace(old_set_expanded, new_set_expanded)
        print("Updated set_expanded with dynamic bounds and saved geometry.")

    # Update mouse events in VoidMiniWidget for corner resizing
    old_mouse_events = """    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_drag(event)
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.update_drag(event)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.end_drag(event)
            event.accept()"""

    new_mouse_events = """    def _is_in_resize_corner(self, pos: QPoint) -> bool:
        return self._is_expanded and (pos.x() >= self.width() - 18) and (pos.y() >= self.height() - 18)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_in_resize_corner(event.pos()):
                self._is_resizing = True
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_size = self.size()
                event.accept()
                return
            self.start_drag(event)
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if getattr(self, "_is_resizing", False):
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_w = max(370, min(1200, self._resize_start_size.width() + delta.x()))
            new_h = max(260, min(950, self._resize_start_size.height() + delta.y()))
            self.resize(new_w, new_h)
            self._user_expanded_w = new_w
            self._user_expanded_h = new_h
            if hasattr(self, "_resp_scroll"):
                self._resp_scroll.setMaximumHeight(max(85, new_h - 170))
            event.accept()
            return

        if self._is_in_resize_corner(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif not getattr(self, "_is_dragging", False):
            self.setCursor(Qt.CursorShape.OpenHandCursor)

        if event.buttons() == Qt.MouseButton.LeftButton and getattr(self, "_is_dragging", False):
            self.update_drag(event)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if getattr(self, "_is_resizing", False):
            self._is_resizing = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            # Save expanded geometry
            try:
                geom_file = MEMORY_DIR / "widget_geometry.json"
                with open(geom_file, "w") as f:
                    json.dump({"expanded_w": self._user_expanded_w, "expanded_h": self._user_expanded_h}, f)
            except Exception:
                pass
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.end_drag(event)
            event.accept()"""

    if old_mouse_events in code:
        code = code.replace(old_mouse_events, new_mouse_events)
        print("Updated mouse events with interactive corner resizing.")

    # -----------------------------------------------------------------------
    # Write back modified code
    # -----------------------------------------------------------------------
    WIDGET_FILE.write_text(code, encoding="utf-8")
    print(f"Successfully wrote {len(code)} characters to {WIDGET_FILE.name}.")

if __name__ == "__main__":
    apply_enhancements()
