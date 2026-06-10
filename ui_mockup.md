# 🖋️ UI Design Plan — Bengali PDF OCR App
### Aesthetic Standard: `UI_Skill_Claude_Grade.md`
### Aesthetic Direction: **Archival Scholar**

---

## Wireframe Reference

The approved wireframe (60/40 split, Settings button top-left):

- Left panel: 60% width — PDF viewer with cream paper texture
- Right panel: 40% width — Bengali text editor
- Settings button at top-left of left panel
- Select Area button at top-center of left panel

---

## Design Thinking

### Purpose
A scholarly tool for digitizing 1850s Bengali handwritten books. Users are historians, researchers, and cultural preservationists. The app must feel **serious, trustworthy, and culturally rooted** — not like a SaaS dashboard.

### Aesthetic Direction: "Archival Scholar"

> Think: the inside of a rare manuscript library. Dark, ink-stained shelves. Aged paper under warm amber lamp-light. Metal rulers and red wax seals. A tool that *respects* the text it handles.

This is **NOT** a generic dark-mode SaaS app with purple gradients. It is a **refined, editorial, historically-textured interface** — like a beautifully typeset academic journal printed on cream paper.

### The ONE Unforgettable Thing
> When the user opens a PDF, the page appears as if being **placed on a reading desk under a warm light** — the viewer panel has a subtle paper-cream inner glow, and the extracted text renders in a Bengali font that feels dignified.

### Tone
**Refined Maximalism** — rich texture and detail, but controlled and purposeful. Every element earns its place.

---

## Color Palette — "Lamp & Ink"

| Token | Value | Usage |
|---|---|---|
| `--bg-void` | `#0C0B0A` | Outermost app shell |
| `--bg-surface` | `#13110F` | Panel backgrounds |
| `--bg-raised` | `#1C1915` | Cards, viewer, editor boxes |
| `--bg-subtle` | `#211E1A` | Toolbar rows, hover states |
| `--bg-paper` | `#F5EDD8` | **THE KEY COLOR** — cream paper in PDF viewer |
| `--border-dim` | `#2D2924` | Quiet borders |
| `--border-warm` | `#4A3F30` | Active warm-toned borders |
| `--border-gold` | `#8B6914` | Accent borders |
| `--gold` | `#C9962A` | Primary accent — antique gold |
| `--gold-bright` | `#E8B240` | Hover gold |
| `--ink-red` | `#C0392B` | Error, Stop button |
| `--ink-green` | `#2D6A4F` | Success, connected state |
| `--ink-teal` | `#1A6B6B` | Process buttons |
| `--ink-teal-bright` | `#2A9090` | Process button hover |
| `--text-primary` | `#EDE0C8` | Warm cream — main text |
| `--text-secondary` | `#9A8B72` | Labels, hints |
| `--text-muted` | `#5C5146` | Disabled, placeholders |
| `--text-on-gold` | `#1A1208` | Dark text ON gold buttons |

Special effects:
- `--paper-glow`: `radial-gradient(ellipse at 50% 30%, #FFF8EC 0%, #F5EDD8 60%, #EDE0C0 100%)`
- `--lamp-shadow`: `0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,240,200,0.06)`

---

## Typography — "Two Worlds, One Voice"

| Font | Role | Why |
|---|---|---|
| `DM Mono` | All UI labels, buttons, page numbers | Page numbers like `02/10` look typeset, not digital |
| `Libre Baskerville` | Modal headers, settings titles | Classic editorial serif — scholarly authority |
| `Tiro Bangla` | All Bengali text in the editor | Designed for Bengali script dignity and readability |

**NEVER use:** Inter, Roboto, Arial, Space Grotesk, or any generic system font.

Google Fonts import:
```
DM Mono: wght 400, 500 + italic
Libre Baskerville: wght 400, 700 + italic
Tiro Bangla: regular + italic
```

---

## Layout Structure (60/40 Split)

```
┌──────────────────────────────────────────────────────────────┐
│  APP SHELL  bg-void, padding, rounded-2xl                    │
│                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────┐  │
│  │  LEFT PANEL  (60%)           │  │  RIGHT PANEL (40%)   │  │
│  │                              │  │                      │  │
│  │  [⚙ Settings] [🔍 Select]   │  │  [Word] [Append]     │  │
│  │  ───────────────────────     │  │  ─────────────────   │  │
│  │  ┌──────────────────────┐    │  │  ┌────────────────┐  │  │
│  │  │   PDF VIEWER         │    │  │  │  [font slider] │  │  │
│  │  │   cream paper bg     │    │  │  │                │  │  │
│  │  │   scrollable         │    │  │  │  TEXT EDITOR   │  │  │
│  │  │   crosshair cursor   │    │  │  │  Tiro Bangla   │  │  │
│  │  └──────────────────────┘    │  │  │  scrollable    │  │  │
│  │  [✏]  < 02/10 >  [+/-]      │  │  └────────────────┘  │  │
│  └──────────────────────────────┘  │  [Page] [Full PDF]   │  │
│                                     │  ══ progress bar ══  │  │
│                                     │  status text         │  │
│                                     └──────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### ⚙️ Settings Button (Top-Left, Left Panel)
- **Font:** DM Mono 12px
- **Style:** `bg-subtle`, `border-dim`, `rounded-lg`, `px-3 py-2`, `text-secondary`
- **Icon:** Lucide `Settings` size=14
- **Hover:** `bg-warm`, `text-primary`, `border-warm`
- **Click:** Opens Settings Modal

---

### 🔍 Select Area Button (Top-Center, Left Panel)
- **Font:** DM Mono 13px bold
- **Style:** `bg-gold/10`, `border-gold/40`, `rounded-lg`, `px-4 py-2`, `text-gold`, `flex-1`
- **Icon:** Lucide `Scan` size=14
- **Hover:** `bg-gold/20`, `border-gold`
- **Active state** (selection drawn): border glows, label changes to "Extract Selection ✓"
- **Disabled:** opacity-40, cursor-not-allowed (when no PDF loaded)

---

### 📄 PDF Viewer Box
- **Container:** `flex-1`, `min-h-0`, `overflow-auto`, `rounded-xl`
- **Background:** `var(--paper-glow)` with subtle SVG grain noise overlay
- **Border:** `1px solid var(--border-warm)`
- **Shadow:** `var(--lamp-shadow)`
- **Cursor:** `crosshair`

**PDF page image (`<img>`):**
- `src="/api/books/{id}/pages/{n}/image"`
- `max-width: 100%`, `display: block`, centered
- Animates with `page-place` keyframe on each load

**Selection overlay** (while dragging):
- `position: absolute`, `pointer-events: none`
- `border: 2px dashed var(--gold)`
- `background: rgba(201,150,42,0.08)`
- `border-radius: 4px`

**Empty state** (no PDF loaded):
- Lucide `BookOpen` icon, size=48, color `text-muted`
- "পিডিএফ বই লোড করুন" — Libre Baskerville italic, `text-muted`
- "নিচে পেন্সিল আইকনে ক্লিক করুন" — DM Mono 11px, `text-muted`

---

### 🧭 Bottom Navigation Bar (Left Panel)
Layout: `flex flex-row items-center justify-between px-2 py-1.5`

**Open/Pencil Button (left):**
- `w-10 h-10`, `bg-ink-red`, `rounded-lg`
- Icon: Lucide `FolderOpen` size=18, white
- Hover: `brightness-110`, `scale-105`
- Tooltip: "পিডিএফ ফাইল খুলুন"

**Page Navigation (center):**
- `< ChevronLeft | "02 / 10" | ChevronRight >`
- Arrows: `w-8 h-8`, `bg-subtle`, `rounded-md`, `text-secondary` | hover: `bg-warm text-primary` | disabled: `opacity-20`
- Counter: DM Mono 500, 15px, `text-primary`, `letter-spacing: 0.05em`, `w-20 text-center`

**Zoom Button (right):**
- `"+/−"` — DM Mono, `bg-subtle`, `rounded-md`, `px-3 py-2`
- Hover: `text-primary`, `bg-warm`
- Click: shows zoom slider popover (50%–200% range)

---

### 📂 Connect MS Word Button (Top-Left, Right Panel)
- **Font:** DM Mono 12px
- **Style:** `bg-subtle`, `border-dim`, `flex-1`, `py-2`, `rounded-lg`, `text-secondary`
- **Hover:** `bg-warm`, `text-primary`
- **Connected state:** `bg-ink-green/10`, `border-ink-green/30`, text: "✓ filename.docx" in `ink-green`

---

### 📝 Append / Save Button (Top-Right, Right Panel)
- **Font:** DM Mono 12px bold
- **Style:** `bg-gold/10`, `border-gold/40`, `flex-1`, `py-2`, `rounded-lg`, `text-gold`
- **Hover:** `bg-gold/20`
- **Shortcut badge:** small pill "⌃⇧A" — `bg-gold/10`, `text-gold/60`, 10px
- **Disabled** (no docx connected): opacity-40

---

### ✍️ Text Editor (Right Panel)
**Container:** `flex-1`, `min-h-0`, `bg-raised`, `rounded-xl`, `border border-warm`

**Font size row** (top of container):
- `px-4 py-2`, `border-bottom: border-dim`
- Label: "আকার" — DM Mono 10px uppercase, `text-muted`
- Custom slider — thumb color: `gold`
- Value badge: "18px" — DM Mono 11px

**`<textarea>`:**
- `w-full h-full`, `resize-none`, `p-6`, `bg-transparent`
- Font: **Tiro Bangla** 18px, `line-height: 2.0`
- `color: text-primary`, `caret-color: gold`
- Placeholder: "নিষ্কাশিত পাঠ্য এখানে দেখাবে..." italic, `text-muted`

---

### ⚡ Process This Page Button
- **Style:** `flex-1`, `py-3`, `rounded-xl`, `bg-ink-teal`, white text
- **Font:** DM Mono 13px bold
- **Shadow:** `0 4px 16px rgba(26,107,107,0.4)`
- **Hover:** `bg-ink-teal-bright`, `translateY(-1px)`, shadow grows
- **Loading:** spinner + "Processing..."

---

### 🚀 Process Full PDF Button
- **Style:** `flex-1`, `py-3`, `rounded-xl`, `bg-gold`, `text-on-gold`
- **Font:** DM Mono 13px bold
- **Shadow:** `0 4px 16px rgba(201,150,42,0.3)`
- **Hover:** `bg-gold-bright`, `translateY(-1px)`
- **Running state** → transforms to Stop Button:
  - `bg-ink-red`, white text, "■ বন্ধ করুন"
  - Animation: `pulse-border` 1.5s infinite

---

### 📊 Progress Bar & Status
**Bar:**
- Height: `2px` (thin, elegant like a loading line)
- Track: `border-dim`
- Fill: `linear-gradient(→, ink-teal, gold)`
- Transition: `width 400ms ease-out`

**Status text:**
- DM Mono 11px, `text-muted`, `mt-1.5`, `truncate`
- Example: "পৃষ্ঠা ৩ / ১০ সম্পন্ন — Tesseract-OCR"

---

### ⚙️ Settings Modal
**Backdrop:** `fixed inset-0`, `bg-black/70`, `backdrop-blur-sm`

**Modal box:**
- `bg-raised`, `rounded-2xl`
- `border: 1px solid border-warm`
- `w-[460px]`, `p-8`
- `box-shadow: 0 24px 80px rgba(0,0,0,0.7)`
- Enter animation: scale 95%→100% + fade, 250ms ease-out

**Header:**
- "কনফিগারেশন" — Libre Baskerville bold 20px
- `border-bottom: border-dim`, `pb-4 mb-6`

**Section 1 — Tesseract Path:**
- Label: DM Mono 11px uppercase tracking-wider, `text-muted`
- Input: `bg-subtle`, `border-dim`, `rounded-lg`, DM Mono 12px
- Focus: `border-gold`, `text-primary`
- Browse button: `text-gold`, hover underline

**Section 2 — DPI:**
- Segmented pills: `[150]` `[200]` `[300]`
- Active: `bg-gold text-on-gold` | Inactive: `bg-subtle text-secondary`

**Footer buttons (right-aligned):**
- [বাতিল] — ghost, `text-secondary`
- [সংরক্ষণ] — `bg-gold`, `text-on-gold`, `rounded-lg`, `px-6 py-2`

---

## Animations

### 1. App Load — Staggered Panel Entry
```css
@keyframes panelEnter {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.left-panel  { animation: panelEnter 500ms ease-out 0ms   both; }
.right-panel { animation: panelEnter 500ms ease-out 100ms both; }
```

### 2. PDF Page Load — "Placed on Desk"
```css
@keyframes pagePlace {
  from { opacity: 0; transform: scale(0.97) translateY(8px); filter: blur(2px); }
  to   { opacity: 1; transform: scale(1)    translateY(0);   filter: blur(0); }
}
.pdf-page-img { animation: pagePlace 350ms cubic-bezier(0.34, 1.56, 0.64, 1); }
```

### 3. OCR Text Reveal
```css
@keyframes textReveal {
  from { opacity: 0; filter: blur(4px); }
  to   { opacity: 1; filter: blur(0px); }
}
.text-editor.just-loaded { animation: textReveal 600ms ease-out; }
```

### 4. Button Microinteractions
```css
.btn-action {
  transition: transform 150ms ease, box-shadow 150ms ease, background 150ms ease;
}
.btn-action:hover:not(:disabled)  { transform: translateY(-1px); }
.btn-action:active:not(:disabled) { transform: translateY(0); }
.btn-action:disabled { opacity: 0.35; cursor: not-allowed; }
```

### 5. Stop Button Pulse
```css
@keyframes pulseBorder {
  0%, 100% { box-shadow: 0 0 0 0 rgba(192,57,43,0.4); }
  50%       { box-shadow: 0 0 0 4px rgba(192,57,43,0); }
}
```

---

## File Structure (React + Tailwind)

```
frontend/
├── index.html
├── package.json
├── vite.config.js         ← proxy: /api → localhost:8765
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.jsx
    ├── index.css              ← CSS variables, fonts, base
    ├── App.jsx                ← Root, global state
    ├── api/
    │   └── client.js          ← All fetch() calls centralized
    ├── hooks/
    │   ├── useBookState.js    ← book_id, page, totalPages
    │   ├── useOcrStream.js    ← EventSource SSE hook
    │   └── useSelection.js    ← Mouse drag state
    └── components/
        ├── left/
        │   ├── LeftToolbar.jsx
        │   ├── PDFViewer.jsx
        │   └── BottomNavBar.jsx
        ├── right/
        │   ├── RightToolbar.jsx
        │   ├── TextEditor.jsx
        │   ├── RightBottomBar.jsx
        │   └── StatusBar.jsx
        └── modals/
            └── SettingsModal.jsx
```

---

## API Endpoints (FastAPI Backend at localhost:8765)

| Method | Endpoint | Action |
|---|---|---|
| `POST` | `/api/books/open` | Upload PDF, returns `{book_id, total_pages}` |
| `GET` | `/api/books/{id}/pages/{n}/image` | Returns page as `image/png` |
| `GET` | `/api/books/{id}/pages/{n}` | Returns `{raw_text, edited_text, status}` |
| `POST` | `/api/books/{id}/pages/{n}/save` | Body: `{text}` — saves edited text |
| `POST` | `/api/books/{id}/ocr/page/{n}` | Run OCR on single page |
| `POST` | `/api/books/{id}/ocr/batch` | Start batch OCR |
| `POST` | `/api/books/{id}/ocr/stop` | Stop batch OCR |
| `GET` | `/api/books/{id}/ocr/stream` | **SSE stream** — live progress events |
| `POST` | `/api/books/{id}/ocr/selection` | Body: `{x1,y1,x2,y2}` — crop & OCR |
| `POST` | `/api/books/{id}/export/word` | Export `.docx` download |
| `GET` | `/api/config` | Load settings |
| `POST` | `/api/config` | Save settings |

### SSE Event Format
```json
{
  "page_num": 3,
  "status": "completed",
  "preview": "প্রথম লাইনের টেক্সট...",
  "processed": 3,
  "total": 10
}
```

---

## Visual Identity Summary

| Element | Choice | Why |
|---|---|---|
| Shell BG | `#0C0B0A` warm near-black | Disappears — focus on panels |
| Panel BG | `#13110F` | Depth without coldness |
| PDF Viewer | Cream paper `#F5EDD8` + warm glow | Mimics looking at a real manuscript |
| Primary Accent | Antique gold `#C9962A` | Scholarly authority, not generic |
| UI Font | `DM Mono` | Page numbers feel typeset, not digital |
| Bengali Font | `Tiro Bangla` | Respectful to the source material |
| Process Buttons | Deep teal + gold | Purposeful, not generic blue |
| **The Unforgettable** | Page "placed on desk" animation | Nobody forgets this moment |

---

*Design plan following `UI_Skill_Claude_Grade.md` — Archival Scholar aesthetic.*
*Version 1.0 — Bengali PDF OCR App, 2026.*
