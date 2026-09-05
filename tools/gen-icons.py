#!/usr/bin/env python3
# Blueshore skin for the Zimbra Classic web client
# Copyright (C) 2026 Gianluca Zamagni, Parvati Srl
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. See the LICENSE file for details.
"""Generate blueshore icons.css: CSS class overrides for Zimbra Classic sprite
icons, using inline SVG data URIs derived from Lucide (ISC license)."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
from skinprops import read_tokens  # noqa: E402

LUCIDE_DIR = TOOLS_DIR / "lucide"  # vendored subset, ISC (LICENSE-Lucide.txt inside)
if len(sys.argv) != 2:
    sys.exit("usage: gen-icons.py <skin-dir>  (reads skin.properties, writes icons.css + img/images.css.js)")
SKIN_DIR = Path(sys.argv[1]).resolve()
OUT = SKIN_DIR / "icons.css"
OUT_JS = SKIN_DIR / "img" / "images.css.js"

# Every colour comes from the skin's own design tokens: a colour variant is a
# different skin.properties, never a different script.
TOKENS = read_tokens(SKIN_DIR / "skin.properties")
HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

def T(name):
    """A colour token as #rrggbb. The value is embedded verbatim in SVG
    attributes and in the generated JavaScript, so only plain hex colours are
    accepted; #rgb is expanded because Zimbra's AjxColor, which tints the
    calendar with the Tag*C values, parses six digits only."""
    value = TOKENS.get(name)
    if value is None:
        sys.exit(f"{SKIN_DIR.name}/skin.properties: colour token {name} is missing")
    if not HEX_COLOR.match(value):
        sys.exit(f"{SKIN_DIR.name}/skin.properties: {name} must be a #rgb or #rrggbb "
                 f"colour, got {value!r}")
    if len(value) == 4:
        value = "#" + "".join(c * 2 for c in value[1:])
    return value

NEUTRAL = T("TextMidC")
ACCENT = T("AccentC")
ACCENT_TEXT = T("AccentTextC")  # accent as text/stroke on light surfaces
FAINT = T("TextFaintC")
ON_ACCENT = T("OnAccentC")
FLAG_ON = T("FlagC")
FLAG_OFF = T("FlagOffC")
READ_DOT = T("ReadDotC")
AVATAR_BG = T("AccentLightC")
PDF_C = T("PdfC")

TAG_COLORS = {name: T(f"Tag{name}C") for name in
              ("Blue", "Cyan", "Gray", "Green", "Orange", "Pink", "Purple", "Red", "Yellow")}

def lucide_inner(name):
    text = (LUCIDE_DIR / f"{name}.svg").read_text()
    m = re.search(r"<svg[^>]*>(.*)</svg>", text, re.S)
    if not m:
        sys.exit(f"cannot parse {name}.svg")
    return re.sub(r"\s+", " ", m.group(1)).strip()

def svg_lucide(name, color, w=16, h=16, sw=2, fill="none"):
    inner = lucide_inner(name)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 24 24" fill="{fill}" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round">{inner}</svg>')

def svg_dot(color, r, size=16):
    c = size / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
            f'<circle cx="{c}" cy="{c}" r="{r}" fill="{color}"/></svg>')

def svg_avatar(size):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="{AVATAR_BG}"/>'
            f'<g fill="none" stroke="{ACCENT_TEXT}" stroke-width="1.4" stroke-linecap="round" '
            f'stroke-linejoin="round"><circle cx="12" cy="9.5" r="3.6"/>'
            f'<path d="M5 20.2a8 8 0 0 1 14 0"/></g></svg>')

def guard_zero_pct(uri):
    # the server-side CSS minifier rewrites any "0%" to "0" — even inside data
    # URIs, corrupting the escapes. A harmless space keeps the tokens apart.
    return uri.replace("0%", "0 %")

def rule(selectors, svg):
    uri = quote(svg, safe="-_.!*() '=/:,")
    uri = guard_zero_pct(uri.replace("'", "%27"))
    return f'{selectors}{{background:url("data:image/svg+xml,{uri}") center no-repeat;}}\n'

rules = []
rules.append("/*\n * blueshore icon overrides for the Zimbra Classic sprite classes.\n"
             " * SPDX-License-Identifier: AGPL-3.0-or-later (Copyright (C) 2026 Gianluca Zamagni, Parvati Srl).\n"
             " * Icon artwork derived from Lucide (https://lucide.dev), ISC license —\n"
             " * see LICENSE-Lucide.txt in this directory. Generated file: edit\n"
             " * tools/gen-icons.py in the source repo, not this css.\n */\n\n")

# --- folder-tree icons: neutral + accent variant when the tree item is selected
FOLDERS = {
    "ImgInbox": "inbox",
    "ImgSentFolder": "send",
    "ImgDraftFolder": "square-pen",
    "ImgSpamFolder": "shield-x",
    "ImgJunkMail": "shield-x",
    "ImgTrash": "trash-2",
    "ImgFolder": "folder",
    "ImgSearchFolder": "folder-search",
    "ImgSharedMailFolder": "folder-symlink",
    "ImgContactsFolder": "book-user",
    "ImgEmailedContacts": "users",
    "ImgCalendarFolder": "calendar",
    "ImgTaskList": "list-todo",
    "ImgBriefcase": "briefcase",
    "ImgTag": "tag",
}
for cls, icon in FOLDERS.items():
    rules.append(rule(f".{cls}", svg_lucide(icon, NEUTRAL)))
    rules.append(rule(f".DwtTreeItem-selected .{cls}", svg_lucide(icon, ACCENT_TEXT)))

# --- tag color dots
for name, color in TAG_COLORS.items():
    rules.append(rule(f".ImgTag{name}", svg_dot(color, 4.5)))

# --- list state icons
rules.append(rule(".ImgMenuRadio", svg_dot(ACCENT, 3)))
rules.append(rule(".ImgMsgUnread", svg_dot(ACCENT, 4)))
rules.append(rule(".ImgMsgRead", svg_dot(READ_DOT, 3.5)))
rules.append(rule(".ImgAttachment", svg_lucide("paperclip", FAINT)))
rules.append(rule(".ImgFlagRed", svg_lucide("flag", FLAG_ON, fill=FLAG_ON)))
rules.append(rule(".ImgFlagDis", svg_lucide("flag", FLAG_OFF)))

# --- generic ui icons
rules.append(rule(".ImgSearch,.ImgSearch2", svg_lucide("search", FAINT)))
rules.append(rule(".ImgRefresh,.ImgRefreshAll", svg_lucide("refresh-cw", NEUTRAL)))
rules.append(rule(".ImgPrint", svg_lucide("printer", NEUTRAL)))
rules.append(rule(".ImgNodeCollapsed", svg_lucide("chevron-right", FAINT)))
rules.append(rule(".ImgNodeExpanded", svg_lucide("chevron-down", FAINT)))
rules.append(rule(".ImgContact,.ImgPerson", svg_lucide("user-round", FAINT)))

# --- dropdown arrows (odd canvases; svg sized to the sprite cell)
rules.append(rule(".ImgSelectPullDownArrow,.ImgSelectPullDownArrowHover,.ImgSelectPullDownArrowSel",
                  svg_lucide("chevron-down", NEUTRAL, w=12, h=16)))
rules.append(rule(".ZNewButton .ImgSelectPullDownArrow,.ZNewButton.ZHover .ImgSelectPullDownArrowHover,.ZNewButton.ZActive .ImgSelectPullDownArrow",
                  svg_lucide("chevron-down", ON_ACCENT, w=12, h=16)))
rules.append(rule(".ImgDownArrowSmall", svg_lucide("chevron-down", FAINT, w=7, h=4, sw=3)))

# --- mini calendar arrows
rules.append(rule(".ImgRevArrowSmall", svg_lucide("chevron-left", FAINT, w=6, h=9, sw=3)))
rules.append(rule(".ImgFwdArrowSmall", svg_lucide("chevron-right", FAINT, w=6, h=9, sw=3)))
rules.append(rule(".ImgFastRevArrowSmall", svg_lucide("chevrons-left", FAINT, w=10, h=9, sw=3)))
rules.append(rule(".ImgFastFwdArrowSmall", svg_lucide("chevrons-right", FAINT, w=10, h=9, sw=3)))

# --- menu / toolbar action icons
ACTIONS = {
    ".ImgMessage,.ImgMessageView": ("mail", NEUTRAL),
    ".ImgNewMessage": ("mail-plus", NEUTRAL),
    ".ImgReadMessage": ("mail-open", NEUTRAL),
    ".ImgUnreadMessage": ("mail", NEUTRAL),
    ".ImgContextMenu": ("settings", FAINT),
    ".ImgPreferences": ("settings", NEUTRAL),
    ".ImgMoveToFolder": ("folder-input", NEUTRAL),
    ".ImgArchiveFolder": ("archive", NEUTRAL),
    ".ImgConversationView": ("list", NEUTRAL),
    ".ImgConversation": ("messages-square", NEUTRAL),
    ".ImgReply": ("reply", NEUTRAL),
    ".ImgReplyAll": ("reply-all", NEUTRAL),
    ".ImgForward": ("forward", NEUTRAL),
    ".ImgDelete,.ImgDeleteMessage,.ImgDeleteConversation": ("trash-2", NEUTRAL),
    ".ImgEdit": ("pencil", NEUTRAL),
    ".ImgRedirect": ("corner-up-right", NEUTRAL),
    ".ImgNewAppointment": ("calendar-plus", NEUTRAL),
    ".ImgNewTask": ("circle-plus", NEUTRAL),
    ".ImgPlus": ("plus", NEUTRAL),
    ".ImgOpenInNewWindow": ("external-link", NEUTRAL),
    ".ImgCancel,.ImgClose,.ImgCloseGray": ("x", NEUTRAL),
    ".ImgLeftArrow": ("chevron-left", NEUTRAL),
    ".ImgRightArrow": ("chevron-right", NEUTRAL),
    ".ImgCalendar": ("calendar", NEUTRAL),
    ".ImgCheckboxUnchecked": ("square", FLAG_OFF),
    ".ImgCheckboxChecked": ("square-check-big", ACCENT_TEXT),
    # search-type menu and generic menu marks
    ".ImgGAL,.ImgGALContact": ("globe", NEUTRAL),
    ".ImgAppointment": ("calendar", NEUTRAL),
    ".ImgTasksApp": ("list-todo", NEUTRAL),
    ".ImgDoc": ("file-text", NEUTRAL),
    ".ImgGroup": ("users", NEUTRAL),
    ".ImgMenuCheck": ("check", ACCENT_TEXT),
}
for sel, (icon, color) in ACTIONS.items():
    rules.append(rule(sel, svg_lucide(icon, color)))

# --- preferences pages (tree items: neutral + accent when selected)
PREF_PAGES = {
    "ImgPreferences": "settings",
    "ImgAccounts": "user-round",
    "ImgMailApp": "mail",
    "ImgMailRule": "funnel",
    "ImgAddSignature": "signature",
    "ImgOutOfOffice": "plane",
    "ImgTrustedAddresses": "shield-check",
    "ImgContactsApp": "users",
    "ImgCalendarApp": "calendar",
    "ImgSharedContact": "share-2",
    "ImgApptReminder": "bell",
    "ImgSendReceive": "arrow-down-up",
    "ImgShortcut": "keyboard",
}
for cls, icon in PREF_PAGES.items():
    rules.append(rule(f".{cls}", svg_lucide(icon, NEUTRAL)))
    rules.append(rule(f".DwtTreeItem-selected .{cls}", svg_lucide(icon, ACCENT_TEXT)))

# --- avatar placeholders
rules.append(rule(".ImgPerson_32,.ImgGroupPerson_32,.ImgGroup_32", svg_avatar(32)))
rules.append(rule(".ImgSender_36", svg_avatar(36)))
rules.append(rule(".ImgPerson_48,.ImgPersonInline_48,.ImgGroupPerson_48,.ImgGroup_48", svg_avatar(48)))

# --- full sweep: everything visibly legacy with an obvious flat equivalent.
# Deliberately NOT mapped: legacy HTML-editor icons (the compose toolbar is
# already modern), IM/Voice apps (absent in this build), third-party brand
# icons, animated spinners/progress frames, spacers, country flags.

# semantic colours are aliases of the shared tag palette
INFO_C = ACCENT; WARN_C = TAG_COLORS["Yellow"]; CRIT_C = TAG_COLORS["Red"]; OK_C = TAG_COLORS["Green"]
MEDIA_C = TAG_COLORS["Purple"]; CODE_C = TAG_COLORS["Cyan"]; WORD_C = TAG_COLORS["Blue"]; PPT_C = TAG_COLORS["Orange"]

SWEEP = {
    # creation
    ".ImgNewFolder": ("folder-plus", NEUTRAL),
    ".ImgNewCalendarFolder": ("calendar-plus", NEUTRAL),
    ".ImgNewContactsFolder,.ImgNewContact": ("user-round-plus", NEUTRAL),
    ".ImgNewGroup": ("users", NEUTRAL),
    ".ImgNewDoc": ("file-plus", NEUTRAL),
    ".ImgNewTag": ("tag", NEUTRAL),
    ".ImgNewTaskList": ("list-todo", NEUTRAL),
    ".ImgCompose": ("square-pen", NEUTRAL),
    # common commands
    ".ImgSend,.ImgCalSend": ("send", NEUTRAL),
    ".ImgSendLater": ("clock", NEUTRAL),
    ".ImgSave": ("save", NEUTRAL),
    ".ImgUndo": ("undo-2", NEUTRAL),
    ".ImgRedo": ("redo-2", NEUTRAL),
    ".ImgCut": ("scissors", NEUTRAL),
    ".ImgCopy,.ImgCopyFolder": ("copy", NEUTRAL),
    ".ImgPaste": ("clipboard", NEUTRAL),
    ".ImgAdd,.ImgAddFilter": ("plus", NEUTRAL),
    ".ImgMinus,.ImgRemove": ("minus", NEUTRAL),
    ".ImgRoundPlus": ("circle-plus", NEUTRAL),
    ".ImgRoundMinus": ("circle-minus", NEUTRAL),
    ".ImgRename,.ImgFileRename,.ImgCalEdit": ("pencil", NEUTRAL),
    ".ImgProperties,.ImgOptions": ("settings", NEUTRAL),
    ".ImgEmptyFolder": ("folder-x", NEUTRAL),
    ".ImgUnDelete": ("undo-2", NEUTRAL),
    ".ImgNotJunk": ("shield-check", NEUTRAL),
    ".ImgDisable": ("ban", NEUTRAL),
    ".ImgHelp,.ImgHelpDocument,.ImgQuestionMark": ("circle-help", NEUTRAL),
    ".ImgFeedback,.ImgChatFolder": ("message-square", NEUTRAL),
    ".ImgGlobe,.ImgWebSearch": ("globe", NEUTRAL),
    ".ImgClearSearch": ("search-x", NEUTRAL),
    ".ImgSpellCheck": ("spell-check", NEUTRAL),
    ".ImgUpload,.ImgCheckin": ("upload", NEUTRAL),
    ".ImgCheckout": ("download", NEUTRAL),
    ".ImgDiscardCheckout": ("x", NEUTRAL),
    ".ImgVersionHistory,.ImgRestoreVersion": ("history", NEUTRAL),
    ".ImgFileOpen": ("folder-open", NEUTRAL),
    ".ImgFilePreview": ("eye", NEUTRAL),
    ".ImgPin": ("pin", NEUTRAL),
    ".ImgUnpin": ("pin-off", NEUTRAL),
    ".ImgPadlock,.ImgSmallPadlock,.ImgReadOnly": ("lock", FAINT),
    ".ImgTelephone": ("phone", NEUTRAL),
    ".ImgMobile": ("smartphone", NEUTRAL),
    ".ImgTime,.ImgNewTime,.ImgProposeTime": ("clock", NEUTRAL),
    ".ImgDate": ("calendar", NEUTRAL),
    ".ImgURL,.ImgInsertWeblink": ("link", NEUTRAL),
    ".ImgLocation": ("map-pin", NEUTRAL),
    ".ImgMailTo,.ImgEnvelope": ("mail", NEUTRAL),
    ".ImgEnvelopeGray": ("mail", FAINT),
    ".ImgEnvelopeOpen": ("mail-open", NEUTRAL),
    ".ImgDraftMsg": ("square-pen", NEUTRAL),
    ".ImgOutbox": ("send", NEUTRAL),
    ".ImgLocalFolders": ("hard-drive", NEUTRAL),
    ".ImgMailFolder": ("folder", NEUTRAL),
    ".ImgGlobalSearchFolder": ("folder-search", NEUTRAL),
    ".ImgSharedCalendarFolder": ("calendar", NEUTRAL),
    ".ImgSharedTaskList": ("list-todo", NEUTRAL),
    ".ImgTask": ("circle-check-big", NEUTRAL),
    ".ImgLogoff,.ImgDisconnect": ("log-out", NEUTRAL),
    ".ImgMute": ("volume-x", NEUTRAL),
    ".ImgVolume": ("volume-2", NEUTRAL),
    ".ImgPlay,.ImgRunSlides": ("play", NEUTRAL),
    ".ImgPause": ("pause", NEUTRAL),
    ".ImgRSS": ("rss", NEUTRAL),
    ".ImgZimlet": ("puzzle", NEUTRAL),
    ".ImgOpenInNewTab": ("external-link", NEUTRAL),
    ".ImgCheck,.ImgCheckModern": ("check", NEUTRAL),
    ".ImgTagStack": ("tags", NEUTRAL),
    ".ImgTagShared": ("tags", FAINT),
    ".ImgCascade": ("app-window", NEUTRAL),
    # calendar / invitations
    ".ImgApptRecur,.ImgApptRecurIndicator": ("repeat", FAINT),
    ".ImgApptMeeting,.ImgApptMeetingIndicator,.ImgAttendeesRequired": ("users", FAINT),
    ".ImgAttendeesOptional": ("user-round", FAINT),
    ".ImgMeetingRequest": ("calendar", NEUTRAL),
    # states and priorities
    ".ImgSuccess,.ImgCompleted,.ImgTaskViewCompleted": ("circle-check-big", OK_C),
    ".ImgTaskViewInProgress": ("clock", WARN_C),
    ".ImgTaskViewNotStarted": ("circle", FAINT),
    ".ImgTaskViewDeferred": ("pause", FAINT),
    ".ImgTaskViewWaiting": ("clock", FAINT),
    ".ImgTaskViewTodoList": ("list-todo", NEUTRAL),
    ".ImgTaskHigh,.ImgPriorityHigh,.ImgPriorityHigh_list,.ImgPriority": ("chevrons-up", CRIT_C),
    ".ImgPriorityDis": ("chevrons-up", FLAG_OFF),
    ".ImgTaskLow,.ImgPriorityLow,.ImgPriorityLow_list": ("chevron-down", FAINT),
    ".ImgTaskNormal,.ImgPriorityNormal,.ImgPriorityNormal_list": ("minus", FAINT),
    ".ImgCalInviteAccepted": ("check", OK_C),
    ".ImgCalInviteDeclined": ("x", CRIT_C),
    ".ImgCalInviteTentative,.ImgNeedsAction": ("circle-help", WARN_C),
    ".ImgApptException,.ImgApptExceptionIndicator": ("triangle-alert", WARN_C),
    ".ImgInformation,.ImgInformation_xtra_small": ("info", INFO_C),
    ".ImgWarning,.ImgWarning_12": ("triangle-alert", WARN_C),
    ".ImgCritical,.ImgCritical_12": ("octagon-alert", CRIT_C),
    # views
    ".ImgListView,.ImgCalListView,.ImgTasksListView": ("list", NEUTRAL),
    ".ImgIconView,.ImgCardsView": ("layout-grid", NEUTRAL),
    ".ImgColumnView": ("columns-2", NEUTRAL),
    ".ImgSinglePane": ("square", NEUTRAL),
    ".ImgSplitPane,.ImgSplitPaneOff,.ImgSplitPaneVertical,.ImgTasksSplitView,.ImgTasksDisplayView": ("columns-2", NEUTRAL),
    ".ImgDayView": ("calendar", NEUTRAL),
    ".ImgWeekView,.ImgWorkWeekView": ("calendar-range", NEUTRAL),
    ".ImgMonthView": ("calendar-days", NEUTRAL),
    # arrows and paging
    ".ImgUpArrow": ("chevron-up", NEUTRAL),
    ".ImgDownArrow,.ImgDropDown": ("chevron-down", NEUTRAL),
    ".ImgLeftDoubleArrow,.ImgFirstPage": ("chevrons-left", NEUTRAL),
    ".ImgRightDoubleArrow,.ImgLastPage": ("chevrons-right", NEUTRAL),
    ".ImgPreviousPage": ("chevron-left", NEUTRAL),
    ".ImgNextPage": ("chevron-right", NEUTRAL),
    ".ImgNodePlus": ("circle-plus", FAINT),
    ".ImgNodeMinus": ("circle-minus", FAINT),
    # message status (conversation headers / windows)
    ".ImgMsgStatusReply": ("reply", FAINT),
    ".ImgMsgStatusForward": ("forward", FAINT),
    ".ImgMsgStatusSent": ("send", FAINT),
    ".ImgMsgStatusDraft": ("square-pen", FAINT),
    ".ImgMsgStatusRead": ("mail-open", FAINT),
    ".ImgMsgStatusUnread,.ImgMsgStatus": ("mail", FAINT),
    ".ImgMsgStatusTrash": ("trash-2", FAINT),
    ".ImgMsgStatusRedirect": ("corner-up-right", FAINT),
    ".ImgMsgStatusAppointment": ("calendar", FAINT),
}
for sel, (icon, color) in SWEEP.items():
    rules.append(rule(sel, svg_lucide(icon, color)))

# special canvas sizes
rules.append(rule(".ImgUpArrowSmall", svg_lucide("chevron-up", FAINT, w=7, h=4, sw=3)))
rules.append(rule(".ImgColumnUpArrow", svg_lucide("chevron-up", FAINT, w=8, h=7, sw=3)))
rules.append(rule(".ImgColumnDownArrow", svg_lucide("chevron-down", FAINT, w=8, h=7, sw=3)))
rules.append(rule(".ImgConvExpand", svg_lucide("chevron-down", FAINT, w=12, h=12, sw=2.5)))
rules.append(rule(".ImgConvCollapse", svg_lucide("chevron-up", FAINT, w=12, h=12, sw=2.5)))
rules.append(rule(".ImgAccordionOpened,.ImgHeaderExpanded", svg_lucide("chevron-down", FAINT)))
rules.append(rule(".ImgAccordionClosed,.ImgHeaderCollapsed", svg_lucide("chevron-right", FAINT)))
rules.append(rule(".ImgBriefcase_32", svg_lucide("briefcase", NEUTRAL, w=32, h=32, sw=1.6)))
rules.append(rule(".ImgBriefcase_48", svg_lucide("briefcase", NEUTRAL, w=48, h=48, sw=1.5)))
rules.append(rule(".ImgInformation_32", svg_lucide("info", INFO_C, w=32, h=32, sw=1.6)))
rules.append(rule(".ImgWarning_32", svg_lucide("triangle-alert", WARN_C, w=32, h=32, sw=1.6)))
rules.append(rule(".ImgCritical_32", svg_lucide("octagon-alert", CRIT_C, w=32, h=32, sw=1.6)))

# free/busy and attendee dots
for sel, color in {
    ".ImgFreeBusyDotBusy": CRIT_C, ".ImgFreeBusyDotFree": OK_C,
    ".ImgFreeBusyDotOOO": MEDIA_C, ".ImgFreeBusyDotTentative": WARN_C,
    ".ImgAttendeeGreen": OK_C, ".ImgAttendeeOrange": WARN_C, ".ImgAttendeeRed": CRIT_C,
}.items():
    rules.append(rule(sel, svg_dot(color, 3.5)))

# document/attachment types (16px and 48px)
DOCS = {
    "ImgPDFDoc": ("file-text", PDF_C),
    "ImgMSWordDoc": ("file-text", WORD_C),
    "ImgMSExcelDoc": ("file-spreadsheet", OK_C),
    "ImgMSPowerpointDoc": ("file-text", PPT_C),
    "ImgPresentation": ("file-text", PPT_C),
    "ImgImageDoc": ("file-image", MEDIA_C),
    "ImgAudioDoc": ("file-audio", MEDIA_C),
    "ImgVideoDoc": ("file-video", MEDIA_C),
    "ImgZipDoc": ("file-archive", FAINT),
    "ImgHtmlDoc": ("file-code", CODE_C),
    "ImgExeDoc": ("file", NEUTRAL),
    "ImgGenericDoc": ("file", FAINT),
    "ImgUnknownDoc": ("file", FAINT),
    "ImgMSProjectDoc": ("file", FAINT),
    "ImgMSVisioDoc": ("file", FAINT),
    "ImgMessageDoc": ("mail", FAINT),
}
for cls, (icon, color) in DOCS.items():
    rules.append(rule(f".{cls}", svg_lucide(icon, color)))
    rules.append(rule(f".{cls}_48", svg_lucide(icon, color, w=48, h=48, sw=1.5)))
rules.append(rule(".ImgSpreadSheet,.ImgZSpreadSheet", svg_lucide("file-spreadsheet", OK_C)))
rules.append(rule(".ImgZSpreadsheet_48", svg_lucide("file-spreadsheet", OK_C, w=48, h=48, sw=1.5)))

# --- visible leftovers from the audit of class references in the client JS
TAIL = {
    ".ImgSharedContactsFolder,.ImgContactsPicker": ("book-user", NEUTRAL),
    ".ImgGroupSchedule": ("calendar-range", NEUTRAL),
    ".ImgSwitchFormat": ("repeat", NEUTRAL),
    ".ImgPOPAccount,.ImgAccountPOP,.ImgAccountIMAP,.ImgAccountGmail,.ImgAccountYahoo,.ImgAccountExchange": ("mail", NEUTRAL),
    ".ImgAccountZimbra": ("user-round", NEUTRAL),
    ".ImgAccountAll": ("users", NEUTRAL),
    ".ImgOffline": ("wifi-off", WARN_C),
    ".ImgMobileWipe": ("smartphone", CRIT_C),
    ".ImgMobileWipeCancel": ("smartphone", NEUTRAL),
    ".ImgNewMailAlert": ("mail", ACCENT_TEXT),
    ".ImgFlagNone": ("flag", FLAG_OFF),
    ".ImgDeleteTag": ("trash-2", NEUTRAL),
    ".ImgConnect": ("refresh-cw", NEUTRAL),
    ".ImgResource": ("projector", NEUTRAL),
    ".ImgQuickCommand": ("zap", NEUTRAL),
    ".ImgEditBadge": ("pencil", FAINT),
}
for sel, (icon, color) in TAIL.items():
    rules.append(rule(sel, svg_lucide(icon, color)))
rules.append(rule(".ImgDoc_48", svg_lucide("file-text", NEUTRAL, w=48, h=48, sw=1.5)))
rules.append(rule(".ImgDndMultiYes_48", svg_lucide("circle-check-big", OK_C, w=48, h=48, sw=1.5)))
rules.append(rule(".ImgDndMultiNo_48", svg_lucide("ban", CRIT_C, w=48, h=48, sw=1.5)))
rules.append(rule(".ImgBubbleDelete", svg_lucide("x", FAINT, w=12, h=12, sw=2.5)))
rules.append(rule(".ImgBubbleExpand", svg_lucide("chevron-down", FAINT, w=12, h=12, sw=2.5)))
for sel, color in {
    ".ImgImAvailable,.Img_ImSmallAvailable": OK_C,
    ".ImgImAway,.Img_ImSmallAway": WARN_C,
    ".ImgImDnd,.Img_ImSmallDnD": CRIT_C,
    ".ImgImUnavailable,.Img_ImSmallUnavailable": FAINT,
}.items():
    rules.append(rule(sel, svg_dot(color, 3.5)))

# the core has more specific hover/focus rules that bring these glyphs back to
# the legacy sprite: cover them again, with an accent variant on interactive ones
for cls, icon in {"ImgAdd": "plus", "ImgRemove": "minus", "ImgContextMenu": "settings",
                  "ImgPin": "pin", "ImgUnpin": "pin-off", "ImgEditBadge": "pencil"}.items():
    rules.append(rule(f".ZHover .{cls},.ZFocused .{cls},.ZActive .{cls}",
                      svg_lucide(icon, ACCENT_TEXT)))

OUT.write_text("".join(rules))
print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(rules)-1} rules)")

# ---------------------------------------------------------------------------
# images.css.js: neutralize the legacy canvas-composited colored icons, then
# re-add Mask/Overlay entries built from OUR flat shapes, so colored folders
# and tags composite into color-tinted flat icons.
#
# Hard-won constraints (see loadImgData.jsp): the file is inlined in a JSP
# <script> block that document.write()s each entry's f into src='...' with
# SINGLE quotes, and appends ?v=<vers> to it. Therefore: no single quotes in
# the data URIs (%27), no raw # inside them (%23), and each URI must END with
# a literal '#' so the appended query lands in the fragment. If a mask image
# fails to load, canvas drawImage throws and the overview layout dies with an
# empty sidebar and no console error.
# ---------------------------------------------------------------------------

def encode_uri(svg):
    uri = quote(svg, safe="-_.!*() =/:,")
    return "data:image/svg+xml," + guard_zero_pct(uri.replace("'", "%27")) + "#"

def svg_mask_stroke(name):
    """White sheet with the lucide stroke punched out: the composite fills
    the stroke with the organizer color."""
    inner = lucide_inner(name)
    return encode_uri(
        "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24'>"
        "<defs><mask id='m'><rect width='24' height='24' fill='white'/>"
        f"<g fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{inner}</g>"
        "</mask></defs>"
        "<rect width='24' height='24' fill='white' mask='url(#m)'/></svg>")

MASK_CIRCLE = encode_uri(
    "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16'>"
    "<path fill='white' fill-rule='evenodd' d='M0 0h16v16H0z M12.5 8a4.5 4.5 0 1 1-9 0a4.5 4.5 0 1 1 9 0Z'/></svg>")
CLEAR = encode_uri("<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16'></svg>")

COLORIZABLE = {
    "ImgFolder": "folder",
    "ImgSharedMailFolder": "folder-symlink",
    "ImgSearchFolder": "folder-search",
    "ImgInbox": "inbox",
    "ImgCalendarFolder": "calendar",
    "ImgTaskList": "list-todo",
    "ImgContactsFolder": "book-user",
    "ImgEmailedContacts": "users",
    "ImgBriefcase": "briefcase",
}

js = []
js.append('/*\n * SPDX-License-Identifier: AGPL-3.0-or-later (Copyright (C) 2026 Gianluca Zamagni, Parvati Srl)\n'
          ' * blueshore: replace the legacy colored-icon composites (generated file,\n'
          ' * edit tools/gen-icons.py). Deletes every core AjxImgData Overlay/Mask\n'
          ' * entry (client falls back to the flat class icons in icons.css), then\n'
          ' * re-adds masks built from the same flat shapes: colored organizers\n'
          ' * render as color-tinted flat icons, tags as plain colored dots.\n */\n')
js.append("if (!window.AjxImgData) AjxImgData = {};\n")
js.append("(function() {\n")
js.append("\tfor (var k in AjxImgData) {\n")
js.append("\t\tif (/(Overlay|Mask)$/.test(k)) { delete AjxImgData[k]; }\n")
js.append("\t}\n")
js.append(f'\tvar CLEAR = "{CLEAR}";\n')
js.append(f'\tvar DOT = "{MASK_CIRCLE}";\n')
js.append('\tAjxImgData.ImgTagMask = {t:0, l:0, w:16, h:16, f:DOT};\n')
js.append('\tAjxImgData.ImgTagOverlay = {t:0, l:0, w:16, h:16, f:CLEAR};\n')
js.append('\tAjxImgData.ImgTagStackMask = {t:0, l:0, w:16, h:16, f:DOT};\n')
js.append('\tAjxImgData.ImgTagStackOverlay = {t:0, l:0, w:16, h:16, f:CLEAR};\n')
for cls, icon in COLORIZABLE.items():
    js.append(f'\tAjxImgData.{cls}Mask = {{t:0, l:0, w:16, h:16, f:"{svg_mask_stroke(icon)}"}};\n')
    js.append(f'\tAjxImgData.{cls}Overlay = {{t:0, l:0, w:16, h:16, f:CLEAR}};\n')
js.append("})();\n")
# some avatars arrive as <img src="/img/large/..."> with no class:
# blueshore.js rewrites their src using this map
js.append("window.BlueshoreImgSwap = {\n")
js.append(f'\t"/img/large/ImgPerson_48.png": "{encode_uri(svg_avatar(48))}",\n')
js.append(f'\t"/img/large/ImgPerson_32.png": "{encode_uri(svg_avatar(32))}"\n')
js.append("};\n")
# standard folder/tag/calendar colours: the client tints them with the RGB values
# of ZmMsg.color* (ZmOrganizer.COLOR_VALUES table), not with the skin; blueshore.js
# replaces them with the token palette (per variant)
js.append("window.BlueshoreColorValues = ")
js.append(json.dumps({name.lower(): color for name, color in TAG_COLORS.items()}, indent="\t"))
js.append(";\n")
OUT_JS.write_text("".join(js))
print(f"wrote {OUT_JS} ({OUT_JS.stat().st_size} bytes)")
