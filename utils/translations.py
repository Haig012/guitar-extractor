"""
Localization strings for English and Hebrew
"""

TRANSLATIONS = {
    "en": {
        # Header
        "made_by": "Made by Hai Guriel",
        "app_title": "Guitar Extractor",
        "app_subtitle": "Export the Demucs \"other\" stem and a full mix without it",

        # Card titles
        "card_performance": "⚙️  Performance",
        "card_recent": "🕘  Recent Files",
        "card_debug": "🛠  Debugging & Status",

        # Card 1 - Performance
        "export_folder": "Export Folder",
        "export_folder_placeholder": "Select output folder...",
        "browse": "Browse",
        "input_source": "Input Source",
        "youtube_link": "YouTube Link",
        "upload_pc": "Upload from PC",
        "url_placeholder": "Paste YouTube URL here...",
        "upload_placeholder": "Click to select audio file...",
        "output_format": "Output Format",
        "time_range_label": "Time range (optional)",
        "time_range_placeholder": "e.g. 2:00 - 4:56   or   start - 6:47   or   4:56 - end",
        "time_range_invalid_title": "Invalid time range",
        "remove_crowd_noise": "Remove Crowd Noise",
        "remove_reverb": "Remove Reverb",
        "crowd_handling_mode": "Crowd Handling Mode",
        "crowd_mode_remove": "Remove Completely",
        "crowd_mode_separate": "Keep as Separate File",
        "crowd_mode_mix_light": "Mix Back Lightly",
        "show_details": "Show details",
        "hide_details": "Hide details",
        "open_folder": "Open Folder",
        "go_button": "🎸  GO",
        "go_button_processing": "Processing...",
        "repeat_last": "🔁  Repeat Last Job",
        "check_deps": "🔍  Check Dependencies",

        # Card 2 - Recent Files
        "recent_empty": "No recent files yet.",
        "recent_open": "Click a file to open it",
        "clear_recent": "Clear History",

        # Card 3 - Debug
        "progress": "Progress",
        "eta": "ETA",
        "status": "Status",
        "eta_calculating": "Calculating...",
        "eta_unknown": "Unknown",
        "save_log": "💾  Save Log",
        "clear_log": "🗑  Clear Log",
        "open_output": "📂  Open Output Folder",

        # Pipeline steps
        "step_check": "Checking dependencies...",
        "step_download": "Downloading audio from YouTube...",
        "step_convert": "Converting format...",
        "step_demucs1": "Separating stems (Pass 1)...",
        "step_demucs2": "Second stem pass (unused)...",
        "step_filter": "Cleaning noise with DeepFilterNet...",
        "step_export": "Exporting final file...",
        "step_cleanup": "Cleaning up temp files...",
        "step_done": "✅  Done! Stems exported.",
        "export_done_title": "Done! 🎸",
        "export_done_body": "Saved in:\n{folder}\n\n• {other}\n• {mix}",

        # Errors
        "error_invalid_url": "Invalid YouTube URL. Please check the link.",
        "error_no_input": "Please provide a YouTube URL or upload a file.",
        "error_no_folder": "Please select an export folder.",
        "error_ytdlp": "yt-dlp failed. Check your internet connection or URL.",
        "error_demucs": "Demucs stem separation failed.",
        "error_deepfilter": "DeepFilterNet noise cleaning failed.",
        "error_ffmpeg": "ffmpeg not found. Please install ffmpeg and add it to PATH.",
        "error_file_not_found": "Input file not found.",
        "error_missing_dep": "Missing dependency: {dep}",

        # Dependency check
        "dep_check_title": "Dependency Check",
        "dep_found": "✅  {dep} — found",
        "dep_missing": "❌  {dep} — NOT found",
        "dep_install_hint": "Install with: {cmd}",
        "dep_all_ok": "All dependencies are installed!",
        "dep_auto_install": "Auto-Install Missing",

        # Misc
        "gpu_detected": "🚀  GPU detected — using CUDA acceleration",
        "gpu_not_detected": "💻  No GPU — using CPU (slower)",
        "file_label": "{name} — {date}",
        "confirm_clear": "Clear all recent file history?",
        "yes": "Yes",
        "no": "No",
        "settings": "⚙  Settings",
        "language": "Language",
    },

    "he": {
        # Header
        "made_by": "נוצר על ידי חי גוריאל",
        "app_title": "חילוץ גיטרה",
        "app_subtitle": "ייצוא גזע \"other\" של Demucs ומיקס מלא בלעדיו",

        # Card titles
        "card_performance": "⚙️  ביצועים",
        "card_recent": "🕘  קבצים אחרונים",
        "card_debug": "🛠  ניפוי שגיאות וסטטוס",

        # Card 1 - Performance
        "export_folder": "תיקיית יצוא",
        "export_folder_placeholder": "בחר תיקיית פלט...",
        "browse": "עיון",
        "input_source": "מקור קלט",
        "youtube_link": "קישור YouTube",
        "upload_pc": "העלה מהמחשב",
        "url_placeholder": "הדבק קישור YouTube כאן...",
        "upload_placeholder": "לחץ לבחירת קובץ שמע...",
        "output_format": "פורמט פלט",
        "time_range_label": "טווח זמן (אופציונלי)",
        "time_range_placeholder": "למשל 2:00 - 4:56   או   start - 6:47   או   4:56 - end",
        "time_range_invalid_title": "טווח זמן לא תקין",
        "remove_crowd_noise": "הסר רעש קהל",
        "remove_reverb": "הסר ריוורב",
        "crowd_handling_mode": "אופן טיפול בקהל",
        "crowd_mode_remove": "הסר לגמרי",
        "crowd_mode_separate": "שמור כקובץ נפרד",
        "crowd_mode_mix_light": "ערבב חזרה בעדינות",
        "show_details": "הצג פרטים",
        "hide_details": "הסתר פרטים",
        "open_folder": "פתח תיקייה",
        "go_button": "🎸  הפעל",
        "go_button_processing": "מעבד...",
        "repeat_last": "🔁  חזור על המשימה הקודמת",
        "check_deps": "🔍  בדוק תלויות",

        # Card 2 - Recent Files
        "recent_empty": "אין קבצים אחרונים עדיין.",
        "recent_open": "לחץ על קובץ לפתיחה",
        "clear_recent": "נקה היסטוריה",

        # Card 3 - Debug
        "progress": "התקדמות",
        "eta": "זמן משוער",
        "status": "סטטוס",
        "eta_calculating": "מחשב...",
        "eta_unknown": "לא ידוע",
        "save_log": "💾  שמור לוג",
        "clear_log": "🗑  נקה לוג",
        "open_output": "📂  פתח תיקיית פלט",

        # Pipeline steps
        "step_check": "בודק תלויות...",
        "step_download": "מוריד שמע מ-YouTube...",
        "step_convert": "ממיר פורמט...",
        "step_demucs1": "מפריד גזעים (סבב 1)...",
        "step_demucs2": "סבב גזעים שני (לא בשימוש)...",
        "step_filter": "מנקה רעש עם DeepFilterNet...",
        "step_export": "מייצא קובץ סופי...",
        "step_cleanup": "מנקה קבצים זמניים...",
        "step_done": "✅  סיום! הגזעים יוצאו.",
        "export_done_title": "סיום! 🎸",
        "export_done_body": "נשמר ב:\n{folder}\n\n• {other}\n• {mix}",

        # Errors
        "error_invalid_url": "קישור YouTube לא תקין. בדוק את הקישור.",
        "error_no_input": "נא לספק קישור YouTube או להעלות קובץ.",
        "error_no_folder": "נא לבחור תיקיית יצוא.",
        "error_ytdlp": "yt-dlp נכשל. בדוק את החיבור לאינטרנט או את הקישור.",
        "error_demucs": "הפרדת הגזעים של Demucs נכשלה.",
        "error_deepfilter": "ניקוי הרעש של DeepFilterNet נכשל.",
        "error_ffmpeg": "ffmpeg לא נמצא. נא להתקין ffmpeg ולהוסיפו ל-PATH.",
        "error_file_not_found": "קובץ קלט לא נמצא.",
        "error_missing_dep": "תלות חסרה: {dep}",

        # Dependency check
        "dep_check_title": "בדיקת תלויות",
        "dep_found": "✅  {dep} — נמצא",
        "dep_missing": "❌  {dep} — לא נמצא",
        "dep_install_hint": "התקן עם: {cmd}",
        "dep_all_ok": "כל התלויות מותקנות!",
        "dep_auto_install": "התקן אוטומטית חסרים",

        # Misc
        "gpu_detected": "🚀  GPU זוהה — משתמש בהאצת CUDA",
        "gpu_not_detected": "💻  אין GPU — משתמש במעבד (איטי יותר)",
        "file_label": "{name} — {date}",
        "confirm_clear": "לנקות את כל היסטוריית הקבצים האחרונים?",
        "yes": "כן",
        "no": "לא",
        "settings": "⚙  הגדרות",
        "language": "שפה",
    }
}

INSTALL_COMMANDS = {
    "yt-dlp": "pip install yt-dlp",
    "demucs": "pip install demucs",
    "deepfilternet": "pip install deepfilternet",
    "soundfile": "pip install soundfile",
    "ffmpeg": "winget install ffmpeg  (or download from ffmpeg.org)",
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """Get translated text for a given key."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
