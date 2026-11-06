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

        # Welcome page
        "idle_title": "Your tracks will appear here",
        "idle_step_1": "Paste a YouTube link or drop a file",
        "idle_step_2": "Choose the tracks you want",
        "idle_step_3": "Press Extract, then listen right here",
        "idle_keys": "Ctrl+Enter  extract   ·   Space  play / pause   ·   Esc  cancel",

        # Section labels
        "section_input": "SOURCE",
        "section_tracks": "TRACKS",
        "section_extras": "EXTRAS",
        "section_time": "TRIM",
        "section_player": "Listen",
        "output_format": "FORMAT",
        "export_folder": "SAVE TO",

        # Input
        "source_placeholder": "Paste a YouTube link or drop a file",
        "browse": "Browse",

        # Readiness line
        "hint_need_source": "Paste a link or drop a file to start",
        "hint_bad_source": "Not a YouTube link or a file on this PC",
        "hint_ready_youtube": "YouTube link ready",
        "error_no_tracks": "Select at least one track to export.",

        # Tracks to export
        "tracks_hint": "Pick which stems to save. htdemucs_6s splits the song into these; guitar & piano are weaker than drums/bass/vocals.",
        "tip_backing": "Everything except the guitar: your track to jam over.",
        "track_guitar": "Guitar",
        "track_drums": "Drums",
        "track_bass": "Bass",
        "track_vocals": "Vocals",
        "track_piano": "Piano",
        "track_other": "Other",
        "track_backing": "Backing",

        # Extras
        "chip_video": "Video",
        "chip_chords": "Chords",
        "chip_reverb": "Reverb",
        "chip_crowd": "Crowd",
        "chip_trim": "Trim",
        "chip_solo": "Solo",
        "export_video": "Also export play-along video (guitar removed)",
        "export_video_hint": "Needs a video source (YouTube link or local video file). Turn on 'Chords' too to run the chords on screen.",
        "detect_chords": "Detect chords (from the guitar stem)",
        "detect_chords_hint": "Writes a timed chord sheet (.txt/.lrc/.srt). With Video on, the chords are burned onto the play-along video. Best on clean triads; names only, no 7ths/inversions.",
        "time_range_hint": "Process only part of the song, e.g. 1:00 to 2:30. Leave a side blank to run from the start or to the end.",
        "time_start": "Start",
        "time_end": "End",

        # Cleanup (UVR)
        "remove_reverb": "Extract reverb / echo as its own track (slow)",
        "remove_crowd": "Extract crowd noise as its own track (slow)",
        "uvr_hint_ok": "UVR ready — reverb / crowd are pulled from the full mix into their own tracks.",
        "uvr_pkg_missing": "audio-separator not installed (pip install audio-separator[gpu])",
        "uvr_dereverb_missing": "UVR-DeEcho-DeReverb.pth missing in resources/",
        "uvr_crowd_missing": "UVR-MDX-NET_Crowd_HQ_1.onnx missing in resources/",

        # Solo time
        "enable_solo_time": "Solo Time: the guitar is heard only during the windows you set, and the band plays throughout.",
        "solo_title": "SOLO WINDOWS",
        "add_segment": "Add",

        # Go
        "go_button": "Extract",
        "go_button_processing": "Processing…",
        "status_ready": "Ready",
        "status_starting": "Starting…",
        "cancel": "Cancel",
        "cancelling": "Cancelling… finishing the current step first",

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
        "tempo": "TEMPO",
        "tempo_reset": "Back to normal speed",
        "loop_set_a": "Set the loop start at the current position",
        "loop_set_b": "Set the loop end at the current position",
        "loop_clear": "Clear the loop",
        "open_folder": "Open folder",
        "back_to_player": "Back to player",

        # Log
        "save_log": "Save log",
        "clear_log": "Clear",
        "show_log": "Log",
        "hide_log": "Hide log",

        # Errors and dialogs
        "error_no_folder": "Please choose an export folder.",
        "error_invalid_time": "Invalid time: {msg}",
        "confirm_cancel_exit": "A job is currently running. Cancel and exit?",
    },
    "he": {
        "app_title": "חילוץ גיטרה",
        "app_subtitle": "מבודד את הגיטרה. ג'אם מעל השאר.",
        "made_by": "נוצר על ידי חי גוריאל",

        "idle_title": "הטראקים שלך יופיעו כאן",
        "idle_step_1": "הדבק קישור יוטיוב או גרור קובץ",
        "idle_step_2": "בחר את הטראקים הרצויים",
        "idle_step_3": "לחץ הפעל, והאזן ישירות כאן",
        "idle_keys": "Ctrl+Enter  הפעלה   ·   Space  ניגון / השהיה   ·   Esc  ביטול",

        "section_input": "מקור",
        "section_tracks": "טראקים",
        "section_extras": "תוספות",
        "section_time": "חיתוך",
        "section_player": "האזנה",
        "output_format": "פורמט",
        "export_folder": "שמירה אל",

        "source_placeholder": "הדבק קישור יוטיוב או גרור קובץ",
        "browse": "עיון",

        "hint_need_source": "הדבק קישור או גרור קובץ כדי להתחיל",
        "hint_bad_source": "זה לא קישור יוטיוב או קובץ במחשב הזה",
        "hint_ready_youtube": "קישור יוטיוב מוכן",
        "error_no_tracks": "בחר לפחות טראק אחד לייצוא.",

        "tracks_hint": "בחר אילו טראקים לשמור. htdemucs_6s מפצל את השיר לטראקים האלה; גיטרה ופסנתר חלשים יותר מתופים/בס/שירה.",
        "tip_backing": "הכל חוץ מהגיטרה: הטראק שעליו מנגנים.",
        "track_guitar": "גיטרה",
        "track_drums": "תופים",
        "track_bass": "בס",
        "track_vocals": "שירה",
        "track_piano": "פסנתר",
        "track_other": "אחר",
        "track_backing": "רקע",

        "chip_video": "וידאו",
        "chip_chords": "אקורדים",
        "chip_reverb": "ריוורב",
        "chip_crowd": "קהל",
        "chip_trim": "חיתוך",
        "chip_solo": "סולו",
        "export_video": "ייצא גם וידאו לנגינה (גיטרה הוסרה)",
        "export_video_hint": "דורש מקור וידאו (קישור יוטיוב או קובץ וידאו מקומי). הפעל גם 'אקורדים' כדי שהאקורדים ירוצו על המסך.",
        "detect_chords": "זהה אקורדים (מתוך הגיטרה המבודדת)",
        "detect_chords_hint": "יוצר דף אקורדים מתוזמן (txt./lrc./srt.). כשוידאו פעיל, האקורדים נצרבים על הווידאו לנגינה. מדויק באקורדים פשוטים; שמות בלבד, ללא היפוכים/אקורדי 7.",
        "time_range_hint": "עבד רק חלק מהשיר, למשל 1:00 עד 2:30. שדה ריק = מתחילת השיר או עד סופו.",
        "time_start": "התחלה",
        "time_end": "סיום",

        "remove_reverb": "חלץ ריוורב/הדים לטראק נפרד (איטי)",
        "remove_crowd": "חלץ רעש קהל לטראק נפרד (איטי)",
        "uvr_hint_ok": "UVR מוכן — ריוורב/קהל מופקים מהמיקס המלא לטראקים נפרדים.",
        "uvr_pkg_missing": "audio-separator לא מותקן (pip install audio-separator[gpu])",
        "uvr_dereverb_missing": "חסר UVR-DeEcho-DeReverb.pth בתיקיית resources/",
        "uvr_crowd_missing": "חסר UVR-MDX-NET_Crowd_HQ_1.onnx בתיקיית resources/",

        "enable_solo_time": "זמן סולו: הגיטרה נשמעת רק בחלונות שתגדיר, והלהקה מנגנת לאורך כל השיר.",
        "solo_title": "חלונות סולו",
        "add_segment": "הוסף",

        "go_button": "הפעל",
        "go_button_processing": "מעבד…",
        "status_ready": "מוכן",
        "status_starting": "מתחיל…",
        "cancel": "ביטול",
        "cancelling": "מבטל… מסיים קודם את השלב הנוכחי",

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
        "tempo": "מהירות",
        "tempo_reset": "חזרה למהירות רגילה",
        "loop_set_a": "קבע את תחילת הלופ במיקום הנוכחי",
        "loop_set_b": "קבע את סוף הלופ במיקום הנוכחי",
        "loop_clear": "נקה לופ",
        "open_folder": "פתח תיקייה",
        "back_to_player": "חזרה לנגן",

        "save_log": "שמור לוג",
        "clear_log": "נקה",
        "show_log": "לוג",
        "hide_log": "הסתר לוג",

        "error_no_folder": "אנא בחר תיקיית יצוא.",
        "error_invalid_time": "טווח זמן לא תקין: {msg}",
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
