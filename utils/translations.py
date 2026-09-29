"""
English + Hebrew localisation.
"""
from __future__ import annotations


TRANSLATIONS = {
    "en": {
        # Header
        "app_title": "Guitar Extractor",
        "app_subtitle": "Isolate the guitar. Jam over the rest.",
        "made_by": "Made by Hai Guriel",

        # Section labels
        "section_input": "Source",
        "section_output": "Output",
        "section_time": "Time range (optional)",
        "section_solo": "Solo time",
        "section_cleanup": "Cleanup (optional, slow)",
        "section_player": "Listen",
        "section_progress": "Progress",

        # Input
        "youtube_link": "YouTube link",
        "upload_pc": "Local file",
        "url_placeholder": "Paste a YouTube URL…",
        "upload_placeholder": "Drop an audio file here or click Browse",
        "browse": "Browse",
        "export_folder": "Export folder",

        # Output
        "output_format": "Download format",

        # Tracks to export
        "section_tracks": "Tracks to export",
        "tracks_hint": "Pick which stems to save. htdemucs_6s splits the song into these; guitar & piano are weaker than drums/bass/vocals.",
        "track_guitar": "Guitar",
        "track_drums": "Drums",
        "track_bass": "Bass",
        "track_vocals": "Vocals",
        "track_piano": "Piano",
        "track_other": "Other",
        "track_backing": "Backing (no guitar)",
        "error_no_tracks": "Select at least one track to export.",

        "export_video": "Also export play-along video (guitar removed)",
        "export_video_hint": "Needs a video source (YouTube link or local video file). Turn on 'Detect chords' too to run the chords on screen.",
        "detect_chords": "Detect chords (from the guitar stem)",
        "detect_chords_hint": "Writes a timed chord sheet (.txt/.lrc/.srt). With the video option on, the chords are burned onto the play-along video. Best on clean triads; names only, no 7ths/inversions.",
        "time_range_hint": "e.g. 1:00 - 2:30   •   blank = full track",
        "time_start": "Start",
        "time_end": "End",

        # Solo time
        "remove_reverb": "Extract reverb / echo as its own track (UVR DeEcho-DeReverb)",
        "remove_crowd": "Extract crowd noise as its own track (UVR MDX-Net Crowd)",
        "uvr_hint_ok": "UVR ready — reverb / crowd are pulled from the full mix into their own tracks.",
        "uvr_pkg_missing": "audio-separator not installed (pip install audio-separator[gpu])",
        "uvr_dereverb_missing": "UVR-DeEcho-DeReverb.pth missing in resources/",
        "uvr_crowd_missing": "UVR-MDX-NET_Crowd_HQ_1.onnx missing in resources/",

        "enable_solo_time": "Enable Solo Time (guitar only during these windows)",
        "solo_title": "Solo segments",
        "add_segment": "+ Add segment",
        "remove_segment": "Remove",

        # Go
        "go_button": "EXTRACT",
        "go_button_processing": "PROCESSING…",
        "repeat_last": "Repeat last job",
        "status_ready": "Ready",
        "cancel": "Cancel",

        # Player
        "player_guitar": "Guitar only",
        "player_backing": "No-guitar backing",
        "player_solo": "Solo mix",
        "player_drums": "Drums",
        "player_bass": "Bass",
        "player_vocals": "Vocals",
        "player_piano": "Piano",
        "player_other": "Other",
        "player_crowd": "Crowd",
        "player_reverb": "Reverb / Echo",
        "player_dry": "No-reverb mix",
        "player_clean": "No-crowd mix",
        "chord_now": "Chord",
        "tempo": "Tempo",
        "volume": "Volume",
        "open_folder": "Open folder",

        # Debug
        "log_title": "Pipeline log",
        "save_log": "Save log",
        "clear_log": "Clear",
        "show_log": "Show log",
        "hide_log": "Hide log",
        "eta": "ETA",
        "status": "Status",

        # Dialogs
        "export_done_title": "Done",
        "export_done_body": "Saved to:\n{folder}",
        "error_no_folder": "Please choose an export folder.",
        "error_invalid_time": "Invalid time: {msg}",
        "error_no_previous": "No previous job to repeat yet.",
        "confirm_cancel_exit": "A job is currently running. Cancel and exit?",
    },
    "he": {
        "app_title": "חילוץ גיטרה",
        "app_subtitle": "מבודד את הגיטרה. ג'אם מעל השאר.",
        "made_by": "נוצר על ידי חי גוריאל",

        "section_input": "מקור",
        "section_output": "פלט",
        "section_time": "טווח זמן (אופציונלי)",
        "section_solo": "זמן סולו",
        "section_cleanup": "ניקוי (אופציונלי, איטי)",
        "section_player": "האזנה",
        "section_progress": "התקדמות",

        "youtube_link": "קישור יוטיוב",
        "upload_pc": "קובץ מקומי",
        "url_placeholder": "הדבק קישור יוטיוב…",
        "upload_placeholder": "גרור קובץ אודיו או לחץ עיון",
        "browse": "עיון",
        "export_folder": "תיקיית יצוא",

        "output_format": "פורמט הורדה",

        "section_tracks": "טראקים לייצוא",
        "tracks_hint": "בחר אילו טראקים לשמור. htdemucs_6s מפצל את השיר לטראקים האלה; גיטרה ופסנתר חלשים יותר מתופים/בס/שירה.",
        "track_guitar": "גיטרה",
        "track_drums": "תופים",
        "track_bass": "בס",
        "track_vocals": "שירה",
        "track_piano": "פסנתר",
        "track_other": "אחר",
        "track_backing": "רקע (ללא גיטרה)",
        "error_no_tracks": "בחר לפחות טראק אחד לייצוא.",

        "export_video": "ייצא גם וידאו לנגינה (גיטרה הוסרה)",
        "export_video_hint": "דורש מקור וידאו (קישור יוטיוב או קובץ וידאו מקומי). הפעל גם 'זהה אקורדים' כדי שהאקורדים ירוצו על המסך.",
        "detect_chords": "זהה אקורדים (מתוך הגיטרה המבודדת)",
        "detect_chords_hint": "יוצר דף אקורדים מתוזמן (txt./lrc./srt.). כשאפשרות הווידאו פעילה, האקורדים נצרבים על הווידאו לנגינה. מדויק באקורדים פשוטים; שמות בלבד, ללא היפוכים/אקורדי 7.",
        "time_range_hint": "למשל 1:00 - 2:30   •   ריק = כל השיר",
        "time_start": "התחלה",
        "time_end": "סיום",

        "remove_reverb": "חלץ ריוורב/הדים לטראק נפרד (UVR DeEcho-DeReverb)",
        "remove_crowd": "חלץ רעש קהל לטראק נפרד (UVR MDX-Net Crowd)",
        "uvr_hint_ok": "UVR מוכן — ריוורב/קהל מופקים מהמיקס המלא לטראקים נפרדים.",
        "uvr_pkg_missing": "audio-separator לא מותקן (pip install audio-separator[gpu])",
        "uvr_dereverb_missing": "חסר UVR-DeEcho-DeReverb.pth בתיקיית resources/",
        "uvr_crowd_missing": "חסר UVR-MDX-NET_Crowd_HQ_1.onnx בתיקיית resources/",

        "enable_solo_time": "הפעל זמן סולו (גיטרה רק בחלונות שייבחרו)",
        "solo_title": "קטעי סולו",
        "add_segment": "+ הוסף קטע",
        "remove_segment": "הסר",

        "go_button": "הפעל",
        "go_button_processing": "מעבד…",
        "repeat_last": "חזור על המשימה הקודמת",
        "status_ready": "מוכן",
        "cancel": "ביטול",

        "player_guitar": "גיטרה בלבד",
        "player_backing": "רקע ללא גיטרה",
        "player_solo": "מיקס סולו",
        "player_drums": "תופים",
        "player_bass": "בס",
        "player_vocals": "שירה",
        "player_piano": "פסנתר",
        "player_other": "אחר",
        "player_crowd": "קהל",
        "player_reverb": "ריוורב / הדים",
        "player_dry": "מיקס ללא ריוורב",
        "player_clean": "מיקס ללא קהל",
        "chord_now": "אקורד",
        "tempo": "מהירות",
        "volume": "עוצמה",
        "open_folder": "פתח תיקייה",

        "log_title": "יומן פעולה",
        "save_log": "שמור לוג",
        "clear_log": "נקה",
        "show_log": "הצג לוג",
        "hide_log": "הסתר לוג",
        "eta": "זמן משוער",
        "status": "סטטוס",

        "export_done_title": "סיום",
        "export_done_body": "נשמר ב:\n{folder}",
        "error_no_folder": "אנא בחר תיקיית יצוא.",
        "error_invalid_time": "טווח זמן לא תקין: {msg}",
        "error_no_previous": "אין משימה קודמת לחזור עליה.",
        "confirm_cancel_exit": "משימה רצה כעת. לבטל ולצאת?",
    },
}


def get_text(lang: str, key: str, **kwargs) -> str:
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
