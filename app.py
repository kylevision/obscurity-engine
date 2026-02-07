"""OBSCURITY ENGINE v7.1 — QUOTA GUARD EDITION"""
import os, sys, json, random, logging, re, time
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import Counter
import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add module path
sys.path.insert(0, str(Path(__file__).parent))

# Import Custom Modules
from modules.secrets_manager import *
from modules.youtube_engine import *
from modules.archive_engine import *
from modules.vault import *
from modules.geo_hunter import *
from modules.scraper_engine import scraper_search_full, scraper_get_details, scraper_parse_results
from modules.persistence import *
from modules.crawler import *
from modules.analyzer import *
from modules.brute_force import *
from modules.export_tools import *
from modules.media_analyzer import *

# ═══════════════════════════════════════════════════════════════════════
# CONFIG & STYLING
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="O.E. v7.1", page_icon="⌬", layout="wide", initial_sidebar_state="expanded")

css = Path(__file__).parent / "static" / "style.css"
if css.exists():
    st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)

st.markdown("""<style>
.H{text-align:center;padding:0.5rem 0;border:1px solid #1a8c1a;background:#050505}
.T{font-family:'VT323',monospace;font-size:2.2rem;color:#66ff66;text-shadow:0 0 20px rgba(51,255,51,0.3);letter-spacing:6px;margin:0}
.S{font-family:'VT323',monospace;font-size:0.9rem;color:#1a8c1a;letter-spacing:4px;text-transform:uppercase}
.rt{font-family:'VT323',monospace;color:#33ffff;font-size:1rem}.rm{font-family:'VT323',monospace;color:#1a8c1a;font-size:.85rem;line-height:1.6}
.rm .g{color:#33ff33}.rm .a{color:#ffb000}.rm .r{color:#ff3333}
.b{display:inline-block;padding:1px 5px;font-size:.75rem;font-family:'VT323',monospace;letter-spacing:1px;margin-right:3px;border:1px solid}
.b0{color:#33ff33;border-color:#33ff33}.bv{color:#ffb000;border-color:#ffb000}.bw{color:#ff3333;border-color:#ff3333}
.bd{color:#cc66ff;border-color:#cc66ff}.bg{color:#33ffff;border-color:#33ffff}.bh{color:#555;border-color:#555}
.bo{color:#b8860b;border-color:#b8860b}.bf{color:#ff69b4;border-color:#ff69b4}.bs{color:#666;border-color:#666}
.bb{color:#ffff33;border-color:#ffff33}.bx{color:#ff6666;border-color:#ff6666}.ba{color:#888;border-color:#888}.bm{color:#66ffcc;border-color:#66ffcc}
.wb{height:4px;background:#111;overflow:hidden;margin-top:3px}.wf{height:100%}
.sd{display:inline-block;width:8px;height:8px;margin-right:6px;border:1px solid}
.so{border-color:#33ff33;background:#33ff33;box-shadow:0 0 6px rgba(51,255,51,.5)}.sf{border-color:#ff3333;background:#ff3333}
.tb{border:1px solid #1a8c1a;background:#050505;padding:8px;margin:4px 0;font-family:'VT323',monospace;font-size:.85rem;color:#33ff33}
.boot{font-family:'VT323',monospace;color:#33ff33;font-size:1rem;line-height:1.8;white-space:pre}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# STATE & BOOT
# ═══════════════════════════════════════════════════════════════════════
for k, v in {"yt_results": pd.DataFrame(), "ia_results": pd.DataFrame(), "search_count": 0, "last_queries": [],
             "batch_selected": set(), "roulette_queue": [], "roulette_idx": 0, "rabbit_hole_queries": [], "booted": False}.items():
    if k not in st.session_state: st.session_state[k] = v

load_env(); ensure_vault(); ensure_data_dir()
if st.session_state.yt_results.empty:
    c = load_last_results()
    if not c.empty: st.session_state.yt_results = c

if not st.session_state.booted:
    st.session_state.booted = True
    boot_placeholder = st.empty()
    boot_placeholder.markdown(f"""<div class="boot">
OBSCURITY ENGINE v7.1 — QUOTA GUARD
{'=' * 50}
[OK] Loading modules............... 12 loaded
[OK] CRT terminal mode............ active
[OK] Quota Guard.................. active (Multi-Key Rotation)
[OK] API keys..................... {get_credential_status().get('api_key_count', 0)} configured
[OK] Scraper engine (yt-dlp)...... ready
[OK] Vault........................ {get_vault_stats()['total_items']} items
[OK] Leaderboard.................. {len(load_leaderboard())} entries
[OK] Favorites.................... {len(load_favorites())} saved
[OK] Search history............... {len(load_search_history())} sessions
[OK] Brute force scanner.......... armed
[OK] Media analyzer (ffprobe)..... loaded
[OK] Geo-hunter ({len(LOCATION_PRESETS)} locations)... ready
{'=' * 50}
SYSTEM READY. SELECT MODULE FROM SIDEBAR.
> _</div>""", unsafe_allow_html=True)
    time.sleep(1.5)
    boot_placeholder.empty()

def _e(t):
    if not t: return ""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="H"><div class="T">⌬ O.E. v7.1</div><div class="S">Quota Guard</div></div>', unsafe_allow_html=True)
        s = get_credential_status(); d = lambda o: f'<span class="sd {"so" if o else "sf"}"></span>'
        st.markdown(f'{d(s["api_key_set"])} API[{s.get("api_key_count", 0)}] {d(True)} SCRAPE {d(True)} SYS', unsafe_allow_html=True)
        st.markdown("---")
        v = get_vault_stats(); ss = get_session_stats()
        c1, c2 = st.columns(2); c1.metric("VAULT", v["total_items"]); c2.metric("FAVS", ss["favorites_count"])
        c3, c4 = st.columns(2); c3.metric("BOARD", ss["leaderboard_entries"]); c4.metric("RUNS", ss["total_sessions"])
        st.markdown("---")
        page = st.radio("SYS>", ["🔍 SEARCH", "🗺️ GEO", "🐇 RABBIT", "🕵️ CHANNEL", "🕸️ CRAWL", "🎲 CHAOS",
                                 "📺 ROULETTE", "💀 BRUTE", "⏳ CAPSULE", "🔬 ANALYZE", "🔊 MEDIA", "🏆 BOARD", "⭐ FAVS",
                                 "📊 STATS", "📤 EXPORT", "📦 VAULT", "⚙️ SETUP"], label_visibility="collapsed")
        return page

# ═══════════════════════════════════════════════════════════════════════
# CORE LOGIC & QUOTA GUARD
# ═══════════════════════════════════════════════════════════════════════
def render_yt_card(row, idx, prefix="sr", show_batch=True):
    views = int(row.get("views", 0)); vid = row.get("video_id", ""); title = row.get("title", "?")
    ch = row.get("channel", "?"); pub = str(row.get("published", ""))[:10]; dur = row.get("duration_fmt", "?")
    url = row.get("url", ""); thumb = row.get("thumbnail", ""); w = float(row.get("weirdness_score", 0))
    iv = is_in_vault(vid); ifav = is_favorite(vid); iw = is_watched(vid); age = int(row.get("age_days", 0)); vpd = float(row.get("views_per_day", 0))
    anom = detect_metadata_anomalies(row.to_dict() if hasattr(row, "to_dict") else dict(row))
    b = ""
    if views == 0: b += '<span class="b b0">[0V]</span>'
    elif views <= 5: b += '<span class="b b0">[≤5]</span>'
    if ifav: b += '<span class="b bf">[★]</span>'
    if iw: b += '<span class="b bs">[SEEN]</span>'
    if iv: b += '<span class="b bv">[VAULT]</span>'
    if w >= 50: b += f'<span class="b bw">[W{w:.0f}]</span>'
    if row.get("is_default_filename"): b += '<span class="b bd">[DEF]</span>'
    if row.get("has_geo"): b += '<span class="b bg">[GEO]</span>'
    if int(row.get("likes", 0)) == 0 and int(row.get("comments", 0)) == 0 and views <= 10: b += '<span class="b bh">[GHOST]</span>'
    if age > 3650: b += '<span class="b bo">[OLD]</span>'
    if row.get("auto_thumbnail"): b += '<span class="b ba">[AUTOTHUMB]</span>'
    for a in anom: b += f'<span class="b bm">[{a.split(":")[0]}]</span>'
    wc = "#ff3333" if w >= 60 else "#ffb000" if w >= 40 else "#33ff33" if w >= 20 else "#333"
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if thumb: st.image(thumb, use_container_width=True)
    with c2:
        st.markdown(f'<div class="rt">{_e(title)}</div>{b}<div class="rm"><span class="g">V:{views:,}</span> D:{dur} {pub} AGE:{age:,}d VPD:{vpd:.3f}<br>CH:{_e(ch)} L:{int(row.get("likes", 0)):,} C:{int(row.get("comments", 0)):,} <a href="{url}">[OPEN]</a></div><div class="wb"><div class="wf" style="width:{min(w, 100)}%;background:{wc}"></div></div>', unsafe_allow_html=True)
        if vid and st.checkbox("▶", key=f"{prefix}_p_{vid}_{idx}", value=False):
            add_to_watch_history(vid, str(title), str(url)); st.markdown(f'<iframe width="100%" height="250" src="https://www.youtube.com/embed/{vid}" frameborder="0" allowfullscreen></iframe>', unsafe_allow_html=True)
    with c3:
        bc1, bc2 = st.columns(2)
        with bc1:
            if not ifav:
                if st.button("★", key=f"{prefix}_f_{vid}_{idx}"): add_favorite(row.to_dict() if hasattr(row, "to_dict") else dict(row)); st.rerun()
            else:
                if st.button("☆", key=f"{prefix}_u_{vid}_{idx}"): remove_favorite(vid); st.rerun()
        with bc2:
            if not iv:
                st.caption("DL")
            else: st.caption("✓")
        if show_batch:
            if st.checkbox("SEL", key=f"{prefix}_s_{vid}_{idx}", value=vid in st.session_state.batch_selected): st.session_state.batch_selected.add(vid)
            elif vid in st.session_state.batch_selected: st.session_state.batch_selected.discard(vid)

def _dl(vid, url, title, row):
    with st.spinner(f"DL {str(title)[:30]}..."):
        m = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        for k, v in list(m.items()):
            if isinstance(v, (pd.Timestamp, datetime)): m[k] = str(v)
            elif isinstance(v, float) and pd.isna(v): m[k] = None
        r = download_youtube_video(url=url, video_id=vid, title=str(title), quality="best", metadata=m)
        if r["success"]: st.success("OK"); st.rerun()
        else: st.error(r["error"])

def _xv(items): return [it.get("id", {}).get("videoId", "") if isinstance(it.get("id"), dict) else str(it.get("id", "")) for it in items]

def _yt(svc, qs, mpq, pa, pb, so, da, rg, la, ca, ss, vd, et=""):
    """
    Search wrapper with Automatic Quota Rotation.
    If a key hits 403, it swaps to the next available key.
    """
    ai = []; p = st.progress(0)
    
    # Load all available keys from secrets manager
    keys = get_all_api_keys()
    if not keys:
        # Fallback to single key if that's all we have
        keys = [os.environ.get("YOUTUBE_API_KEY")] if os.environ.get("YOUTUBE_API_KEY") else []
    
    current_key_idx = 0
    
    def get_service_for_key(idx):
        if idx >= len(keys): return None
        return build('youtube', 'v3', developerKey=keys[idx])

    # Ensure we start with a valid service if passed one isn't working
    active_svc = svc

    for i, q in enumerate(qs):
        p.progress((i + 1) / len(qs), f"SYS> '{q}' [{i + 1}/{len(qs)}]")
        
        fetched_count = 0
        next_page_token = None
        
        while fetched_count < mpq:
            batch_size = min(50, mpq - fetched_count)
            
            # Retry Loop for Quota Hitting
            max_retries = len(keys) + 1
            retry = 0
            
            while retry < max_retries:
                try:
                    r = search_youtube(
                        service=active_svc,
                        query=q,
                        max_results=batch_size,
                        published_after=pa,
                        published_before=pb,
                        order=so,
                        video_duration=da,
                        region_code=REGION_CODES.get(rg, ""),
                        relevance_language=RELEVANCE_LANGUAGES.get(la, ""),
                        video_category_id=VIDEO_CATEGORIES.get(ca, ""),
                        video_definition=vd,
                        safe_search=ss,
                        event_type=et,
                        page_token=next_page_token
                    )
                    
                    # Manual Error Check (if module returns dict error instead of raising)
                    if isinstance(r, dict) and "error" in r:
                        raise HttpError(type('MockResp', (object,), {'status': 403, 'reason': 'Quota'}), b'Quota')

                    # If successful, break retry loop
                    items = r.get("items", [])
                    if items:
                        ai.extend(items)
                        fetched_count += len(items)
                        st.session_state.search_count += len(items)
                        next_page_token = r.get("nextPageToken")
                    
                    if not items or not next_page_token:
                        # Force outer loop break if no more pages
                        fetched_count = mpq + 1 
                    
                    break # Break retry loop

                except (HttpError, Exception) as e:
                    is_quota = False
                    if hasattr(e, 'resp') and e.resp.status in [403, 429]: is_quota = True
                    if "quota" in str(e).lower(): is_quota = True

                    if is_quota:
                        st.warning(f"⚠️ KEY #{current_key_idx+1} EXHAUSTED. SWAPPING...")
                        current_key_idx += 1
                        if current_key_idx < len(keys):
                            active_svc = get_service_for_key(current_key_idx)
                            retry += 1
                        else:
                            st.error("💀 ALL KEYS DEAD. WAIT 24H.")
                            fetched_count = mpq + 1 # Stop searching
                            break
                    else:
                        # Non-quota error
                        st.warning(f"Error on query '{q}': {e}")
                        fetched_count = mpq + 1
                        break

    seen = set(); u = []
    for it in ai:
        vid = it.get("id", {}); vi = vid.get("videoId", "") if isinstance(vid, dict) else str(vid)
        if vi and vi not in seen: seen.add(vi); u.append(it)
    
    if u:
        all_details = {}
        u_chunks = [u[i:i + 50] for i in range(0, len(u), 50)]
        for idx, chunk in enumerate(u_chunks):
            p.progress(0.85 + (0.15 * (idx / len(u_chunks))), f"DETAILS {idx + 1}/{len(u_chunks)}...")
            vs = [v for v in _xv(chunk) if v]
            
            # Simple retry for details too
            try:
                det = get_video_details(active_svc, vs)
            except:
                if current_key_idx + 1 < len(keys):
                    current_key_idx += 1
                    active_svc = get_service_for_key(current_key_idx)
                    det = get_video_details(active_svc, vs)
                else:
                    det = []

            if det: all_details.update({d['id']: d for d in det})
            
        det_list = list(all_details.values())
        df = parse_video_data(u, det_list)
        df = analyze_thumbnails(df)
        p.progress(1.0, f"{len(df)} FOUND")
        return df
        
    p.progress(1.0, "NONE"); return pd.DataFrame()

def _pf(df, mv, **kw):
    if df.empty: return df
    df = filter_by_views(df, mv)
    if kw.get("mnv", 0) > 0: df = filter_by_min_views(df, kw["mnv"])
    if kw.get("mnd", 0) > 0 or kw.get("mxd", 999999) < 999999: df = filter_by_duration(df, kw.get("mnd", 0), kw.get("mxd", 999999))
    if kw.get("od"): df = filter_default_filenames_only(df)
    if kw.get("mw", 0) > 0: df = filter_by_weirdness(df, kw["mw"])
    if kw.get("gh"): df = filter_no_engagement(df)
    if kw.get("go"): df = filter_has_geolocation(df)
    if kw.get("tc"): df = filter_title_contains(df, kw["tc"])
    if kw.get("tr"): df = filter_title_regex(df, kw["tr"])
    if kw.get("st"): df = filter_short_title(df)
    if kw.get("ac"): df = filter_all_caps(df)
    if kw.get("nd"): df = filter_no_description(df)
    if kw.get("nt"): df = filter_no_tags(df)
    if kw.get("nl"): df = filter_no_links(df)
    if kw.get("sd"): df = filter_sd_only(df)
    if kw.get("ul"): df = filter_exclude_licensed(df)
    if kw.get("mvp", 1000) < 1000: df = filter_by_views_per_day(df, kw["mvp"])
    if kw.get("mna", 0) > 0 or kw.get("mxa", 99999) < 99999: df = filter_by_age(df, kw.get("mna", 0), kw.get("mxa", 99999))
    hr = kw.get("hr", (0, 23))
    if hr != (0, 23): df = filter_by_upload_hour(df, hr[0], hr[1])
    if kw.get("dc"): df = filter_description_contains(df, kw["dc"])
    if kw.get("cf"): df = filter_channel_contains(df, kw["cf"])
    return df

def _show():
    yt = st.session_state.yt_results; ia = st.session_state.ia_results
    if yt.empty and ia.empty: return
    st.markdown("---")
    if not yt.empty:
        s1, s2, s3, s4 = st.columns(4); s1.metric("N", len(yt)); s2.metric("0V", len(yt[yt["views"] == 0]) if "views" in yt.columns else 0)
        s3.metric("W", f"{yt['weirdness_score'].mean():.1f}" if "weirdness_score" in yt.columns else "—"); s4.metric("DEF", len(yt[yt["is_default_filename"] == True]) if "is_default_filename" in yt.columns else 0)
    tabs = [];
    if not yt.empty: tabs.append(f"YT[{len(yt)}]")
    if not ia.empty: tabs.append(f"IA[{len(ia)}]")
    tabs.append("DATA"); to = st.tabs(tabs); ti = 0
    if not yt.empty:
        with to[ti]:
            for idx, row in yt.iterrows(): render_yt_card(row, idx); st.markdown("---")
        ti += 1
    if not ia.empty:
        with to[ti]:
            for _, row in ia.iterrows():
                st.markdown(f'<div class="tb">{_e(row.get("title", "?"))} | {row.get("date", "")} | DL:{int(row.get("downloads", 0)):,} <a href="{row.get("url", "")}">[OPEN]</a></div>', unsafe_allow_html=True)
        ti += 1
    with to[ti]:
        if not yt.empty: st.dataframe(yt[[c for c in ["title", "channel", "views", "weirdness_score", "views_per_day", "url"] if c in yt.columns]], use_container_width=True, height=400); st.download_button("CSV", yt.to_csv(index=False), "oe.csv", "text/csv")

# ═══ SEARCH ═══
def render_search():
    st.markdown('<div class="H"><div class="T">SEARCH</div><div class="S">All engines active</div></div>', unsafe_allow_html=True)
    qc, bc = st.columns([5, 2])
    with qc: query = st.text_input("SYS>", placeholder="QUERY...", label_visibility="collapsed")
    with bc: b1, b2, b3 = st.columns(3); go = b1.button("EXEC", use_container_width=True); rnd = b2.button("RAND", use_container_width=True); chao = b3.button("CHAOS", use_container_width=True)
    st.markdown("---")
    s1, s2, s3, mv, lv, d1, d2, d3 = st.columns([.7, .7, .7, 1, .7, 1.1, 1.1, 1.1])
    with s1: syt = st.toggle("API", value=True)
    with s2: ssc = st.toggle("SCRAPE", value=False)
    with s3: sia = st.toggle("ARCH", value=False)
    with mv: tmv = st.number_input("MAX_V", 0, 10000000, 10, step=1, key="tv")
    with lv: slv = st.toggle("LIVE", value=False)
    with d1: tp = st.selectbox("ERA", list(TEMPORAL_PRESETS.keys()), index=0, label_visibility="collapsed")
    pd_ = TEMPORAL_PRESETS[tp]
    with d2:
        if pd_[0] is None: df_ = st.date_input("FROM", value=date(2005, 4, 23), min_value=date(1900, 1, 1), max_value=date.today(), key="df")
        else: df_ = pd_[0].date(); st.date_input("FROM", value=df_, disabled=True, key="dfl")
    with d3:
        if pd_[0] is None: dt_ = st.date_input("TO", value=date.today(), min_value=date(1900, 1, 1), max_value=date.today(), key="dt")
        else: dt_ = pd_[1].date(); st.date_input("TO", value=dt_, disabled=True, key="dtl")
    bs = st.session_state.batch_selected
    if bs:
        bc1, bc2 = st.columns([2, 1]); bc1.info(f"SEL:{len(bs)}")
        with bc2:
            st.caption("Batch DL Disabled")
    with st.expander("CONTROL PANEL", expanded=False):
        tp2, tf, tr, tpr, ta = st.tabs(["PAT", "FILT", "REG", "PRE", "ADV"])
        with tp2:
            sp = []; cols = st.columns(len(PATTERN_CATEGORIES))
            for i, (cn, cp) in enumerate(PATTERN_CATEGORIES.items()):
                with cols[i]:
                    st.caption(cn)
                    for p in cp:
                        if st.checkbox(p, key=f"p_{p}"): sp.append(p)
            cpat = st.text_input("CUSTOM", key="cpat")
        with tf:
            f1, f2, f3, f4 = st.columns(4)
            with f1: mnv = st.number_input("MIN_V", 0, 10000000, 0); oz = st.checkbox("ZERO")
            with f2: das = st.selectbox("DUR", ["any", "short", "medium", "long"]); mnd = st.number_input("MIN_S", 0, 999999, 0, step=5); mxd = st.number_input("MAX_S", 0, 999999, 999999, step=60)
            with f3: so = st.selectbox("SORT", ["date", "viewCount", "relevance", "rating"]); mpq = st.number_input("PER_Q", 10, 500, 50, step=10); od = st.checkbox("DEF")
            with f4: mw = st.slider("MIN_W", 0, 80, 0, step=5); gh = st.checkbox("GHOST"); geo = st.checkbox("GEO"); vdf = st.selectbox("DEF", ["any", "high", "standard"], key="vdf")
        with tr:
            r1, r2, r3 = st.columns(3)
            with r1: rg = st.selectbox("REG", list(REGION_CODES.keys()))
            with r2: la = st.selectbox("LANG", list(RELEVANCE_LANGUAGES.keys()))
            with r3: ca = st.selectbox("CAT", list(VIDEO_CATEGORIES.keys())); ss = st.selectbox("SAFE", ["none", "moderate", "strict"])
        with tpr:
            pcols = st.columns(4); cpq = []
            for i, (pn, pqs) in enumerate(RANDOM_DEEP_QUERIES.items()):
                with pcols[i % 4]:
                    if st.button(pn, key=f"pr_{i}", use_container_width=True): cpq = random.sample(pqs, min(3, len(pqs)))
            wkw = st.multiselect("KW", WEIRDNESS_BOOSTERS, default=[], max_selections=5)
        with ta:
            a1, a2, a3 = st.columns(3)
            with a1: ptc = st.text_input("TIT_HAS", key="ptc"); ptr = st.text_input("TIT_RE", key="ptr"); psh = st.checkbox("SHORT"); pac = st.checkbox("CAPS")
            with a2: pnd = st.checkbox("NO_DESC"); pnt = st.checkbox("NO_TAGS"); pnl = st.checkbox("NO_LINKS"); psd = st.checkbox("SD"); pul = st.checkbox("UNLIC"); pvp = st.number_input("MAX_VPD", 0.0, 1000.0, 1000.0, step=0.1)
            with a3: pma = st.number_input("MIN_AGE", 0, 99999, 0, step=30); pmx = st.number_input("MAX_AGE", 0, 99999, 99999, step=365); phr = st.slider("HOUR", 0, 23, (0, 23), key="phr"); pdc = st.text_input("DESC_HAS", key="pdc"); pch = st.text_input("CH_HAS", key="pch")
    fkw = dict(mnv=mnv, mnd=mnd, mxd=mxd if mxd > 0 else 999999, od=od, mw=mw, gh=gh, go=geo, tc=ptc, tr=ptr, st=psh, ac=pac, nd=pnd, nt=pnt, nl=pnl, sd=psd, ul=pul, mvp=pvp, mna=pma, mxa=pmx, hr=phr, dc=pdc, cf=pch)
    if rnd: q2, s2, e2 = generate_time_travel_query(); query = q2; df_ = s2.date(); dt_ = e2.date(); go = True
    if chao: cpq = generate_chaos_queries(5); go = True
    should = go and (query or sp or cpq)
    if cpq and not go: should = True
    if should:
        aq = cpq if cpq else build_search_queries(query, sp or None, cpat, wkw or None)
        st.session_state.last_queries = aq; pa = datetime.combine(df_, datetime.min.time()); pb = datetime.combine(dt_, datetime.max.time())
        if syt:
            svc = get_youtube_service()
            if svc:
                df = _yt(svc, aq, mpq, pa, pb, so, das, rg, la, ca, ss, vdf, et="" if not slv else "completed")
                emv = 0 if oz else tmv; pre = len(df); df = _pf(df, emv, **fkw)
                if df.empty and pre > 0: st.warning(f"{pre} FOUND, ALL FILTERED")
                if not df.empty: df = df.sort_values("weirdness_score", ascending=False).reset_index(drop=True)
                st.session_state.yt_results = df
            else: st.warning("NO KEY"); st.session_state.yt_results = pd.DataFrame()
        elif not ssc: st.session_state.yt_results = pd.DataFrame()
        if ssc:
            sp2 = st.progress(0); sdfs = []
            for i, q in enumerate(aq):
                sp2.progress((i + 1) / len(aq), f"SCRAPE '{q}'")
                sdf = scraper_search_full(q, mpq)
                if not sdf.empty: sdf = analyze_thumbnails(sdf); sdfs.append(sdf)
            if sdfs:
                sdf = pd.concat(sdfs, ignore_index=True).drop_duplicates(subset=["video_id"]).reset_index(drop=True); emv = 0 if oz else tmv; sdf = _pf(sdf, emv, **fkw)
                if not sdf.empty: sdf = sdf.sort_values("weirdness_score", ascending=False).reset_index(drop=True)
                ex = st.session_state.yt_results; st.session_state.yt_results = pd.concat([ex, sdf], ignore_index=True).drop_duplicates(subset=["video_id"]).reset_index(drop=True) if not ex.empty else sdf
        if sia:
            aia = [];
            for q in aq: r = search_archive(query=q, media_type="movies", max_results=mpq, date_start=df_.isoformat(), date_end=dt_.isoformat()); aia.extend(r.get("items", []))
            seen = set(); st.session_state.ia_results = parse_archive_results([it for it in aia if it.get("identifier") not in seen and not seen.add(it.get("identifier"))])
        else: st.session_state.ia_results = pd.DataFrame()
        save_search_session(aq, len(st.session_state.yt_results) + len(st.session_state.ia_results))
        if not st.session_state.yt_results.empty: update_leaderboard(st.session_state.yt_results); save_last_results(st.session_state.yt_results)
    _show()

# ═══ GEO ═══
def render_geo():
    st.markdown('<div class="H"><div class="T">GEO-HUNT</div><div class="S">Click map or pick a city</div></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        gq = st.text_input("KEYWORDS", key="gq")
        presets = get_location_presets()
        preset_names = [k for k in presets.keys()]
        sel = st.selectbox("📍 PICK A LOCATION", preset_names, index=0, key="gps")
        coords = presets.get(sel)
        if coords:
            lat, lng = coords
            st.success(f"LAT:{lat:.4f} LNG:{lng:.4f}")
        else:
            lat = st.number_input("LAT", value=40.7128, format="%.4f", step=0.01)
            lng = st.number_input("LNG", value=-74.006, format="%.4f", step=0.01)
        st.markdown("*Or click the map to set coordinates*")
        rad = st.select_slider("RADIUS", ["1km", "5km", "10km", "25km", "50km", "100km", "500km"], value="10km")
        g1, g2 = st.columns(2)
        with g1: gf = st.date_input("FROM", value=date(2005, 1, 1), min_value=date(1900, 1, 1), key="gdf")
        with g2: gt = st.date_input("TO", value=date.today(), key="gdt")
        gmv = st.number_input("MAX VIEWS", 0, 100000, 100, key="gmv")
        if st.button("🎯 SCAN LOCATION", use_container_width=True):
            svc = get_youtube_service()
            if svc:
                with st.spinner(f"SCANNING {lat:.4f},{lng:.4f}..."):
                    r = search_youtube(service=svc, query=gq or "", max_results=50, published_after=datetime.combine(gf, datetime.min.time()), published_before=datetime.combine(gt, datetime.max.time()), location=(lat, lng), location_radius=rad, order="date")
                    if r["items"]:
                        vs = [v for v in _xv(r["items"]) if v]; det = get_video_details(svc, vs); df = parse_video_data(r["items"], det); df = filter_by_views(df, gmv); df = analyze_thumbnails(df)
                        st.session_state.yt_results = df; update_leaderboard(df)
                        st.success(f"{len(df)} TARGETS")
                    else: st.info("NOTHING FOUND AT THIS LOCATION")
            else: st.error("GEO NEEDS API KEY")
    with c2:
        m = create_clickable_map(center=(lat, lng), zoom=6 if coords else 4)
        m = add_search_radius(m, (lat, lng), float(rad.replace("km", "")))
        yt = st.session_state.yt_results
        if not yt.empty: m = add_video_markers(m, yt)
        try:
            from streamlit_folium import st_folium
            map_data = st_folium(m, width=None, height=500, returned_objects=["last_clicked"])
            if map_data and map_data.get("last_clicked"):
                cl = map_data["last_clicked"]
                st.markdown(f'<div class="tb">CLICKED: LAT:{cl["lat"]:.6f} LNG:{cl["lng"]:.6f} — Copy these into the lat/lng fields</div>', unsafe_allow_html=True)
        except: st.components.v1.html(m._repr_html_(), height=500)
    if not st.session_state.yt_results.empty:
        st.markdown("---")
        for idx, row in st.session_state.yt_results.iterrows(): render_yt_card(row, idx, prefix="geo"); st.markdown("---")

# ═══ RABBIT, CHANNEL, CRAWL, CHAOS ═══
def render_rabbit():
    st.markdown('<div class="H"><div class="T">RABBIT HOLE</div></div>', unsafe_allow_html=True)
    rh = st.session_state.rabbit_hole_queries
    if rh:
        for i, q in enumerate(rh): rh[i] = st.text_input(f"Q{i + 1}", value=q, key=f"rh_{i}")
        if st.button("EXEC ALL"):
            for q in rh: _exec_q(q)
    ti = st.text_input("TAGS", key="mt")
    if ti and st.button("GEN"): st.session_state.rabbit_hole_queries = generate_rabbit_hole_queries([t.strip() for t in ti.split(",")]); st.rerun()
    _show()

def _exec_q(q):
    svc = get_youtube_service()
    if svc:
        r = search_youtube(service=svc, query=q, max_results=25, order="date")
        if r["items"]: vs = [v for v in _xv(r["items"]) if v]; det = get_video_details(svc, vs); df = parse_video_data(r["items"], det); df = filter_by_views(df, 10000); ex = st.session_state.yt_results; st.session_state.yt_results = pd.concat([ex, df], ignore_index=True).drop_duplicates(subset=["video_id"]).reset_index(drop=True) if not ex.empty else df
    else:
        df = scraper_search_full(q, 15);
        if not df.empty: ex = st.session_state.yt_results; st.session_state.yt_results = pd.concat([ex, df], ignore_index=True).drop_duplicates(subset=["video_id"]).reset_index(drop=True) if not ex.empty else df

def render_channel():
    st.markdown('<div class="H"><div class="T">CHANNEL AUTOPSY</div><div class="S">Score + Burst + Dead + Bot fingerprint</div></div>', unsafe_allow_html=True)
    ch = st.text_input("CHANNEL ID", placeholder="UCxxxxxxx")
    usc = st.checkbox("SCRAPER", value=True)
    if ch and st.button("AUTOPSY", use_container_width=True):
        with st.spinner("SCANNING..."):
            if usc: df = channel_autopsy_full(ch, 50)
            else:
                svc = get_youtube_service()
                if not svc: st.error("KEY"); return
                items = search_channel_videos(svc, ch, 50); vs = [v for v in _xv(items) if v]; det = get_video_details(svc, vs); df = parse_video_data(items, det) if items else pd.DataFrame()
            if not df.empty:
                df = analyze_thumbnails(df); df = df.sort_values("weirdness_score", ascending=False).reset_index(drop=True); st.session_state.yt_results = df; update_leaderboard(df)
                score = compute_channel_obscurity_score(df); sc = score["total_score"]; scol = "#ff3333" if sc >= 60 else "#ffb000" if sc >= 40 else "#33ff33"
                st.markdown(f'<div class="tb" style="text-align:center;font-size:1.5rem">OBSCURITY: <span style="color:{scol};font-size:2rem">{sc}/100</span></div>', unsafe_allow_html=True)
                fp = fingerprint_upload_pattern(df)
                fpc = "#ff3333" if fp["score"] >= 60 else "#ffb000" if fp["score"] >= 30 else "#33ff33"
                st.markdown(f'<div class="tb">PATTERN: <span style="color:{fpc}">{fp["pattern"]}</span> ({fp["score"]}/100)</div>', unsafe_allow_html=True)
                for f in fp["flags"]: st.markdown(f'<div class="tb"><span class="b bb">[{f}]</span></div>', unsafe_allow_html=True)
                bursts = detect_upload_bursts(df, 3)
                if not bursts.empty:
                    for _, br in bursts.iterrows(): st.markdown(f'<div class="tb"><span class="b bb">[BURST]</span> {br["date"]} {br["upload_count"]}x {br["burst_type"]}</div>', unsafe_allow_html=True)
                for idx, row in df.iterrows(): render_yt_card(row, idx, prefix="ch"); st.markdown("---")

def render_crawl():
    st.markdown('<div class="H"><div class="T">CRAWL</div></div>', unsafe_allow_html=True)
    seed = st.text_input("SEED", value=st.session_state.get("_crawl_seed", ""))
    if "youtube.com" in seed or "youtu.be" in seed:
        if "v=" in seed: seed = seed.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in seed: seed = seed.split("youtu.be/")[-1].split("?")[0]
    c1, c2, c3 = st.columns(3)
    with c1: dep = st.slider("DEPTH", 1, 5, 2)
    with c2: per = st.slider("PER_HOP", 2, 10, 5)
    with c3: crv = st.number_input("MAX_V", 0, 100000, 100, key="crv")
    if seed and st.button("CRAWL"):
        p = st.progress(0); items = crawl_related_chain(seed, dep, per, lambda d, v: p.progress(min(.95, (d + 1) / (dep + 1))))
        if items:
            vs = [it.get("id", it.get("url", "")) for it in items]; vs = [v.split("v=")[-1].split("&")[0].split("/")[-1] if "http" in str(v) else str(v) for v in vs if v][:100]
            det = scraper_get_details(vs)
            if det: df = scraper_parse_results(det); df = filter_by_views(df, crv); df = analyze_thumbnails(df); df = df.sort_values("weirdness_score", ascending=False).reset_index(drop=True); st.session_state.yt_results = df; update_leaderboard(df)
        _show()

def render_chaos():
    st.markdown('<div class="H"><div class="T">CHAOS</div></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: nq = st.slider("N", 1, 20, 5)
    with c2: cmv = st.number_input("MAX_V", 0, 10000, 50, key="cmv")
    if st.button("UNLEASH"):
        qs = generate_chaos_queries(nq); st.session_state.last_queries = qs; [st.code(q) for q in qs]
        svc = get_youtube_service()
        if svc: df = _yt(svc, qs, 25, datetime(2005, 1, 1), datetime.now(), "date", "any", "🌍 Any Region", "Any Language", "Any Category", "none", "any")
        else: sdfs = [scraper_search_full(q, 10) for q in qs]; sdfs = [s for s in sdfs if not s.empty]; df = pd.concat(sdfs, ignore_index=True).drop_duplicates(subset=["video_id"]).reset_index(drop=True) if sdfs else pd.DataFrame()
        if not df.empty: df = filter_by_views(df, cmv); df = analyze_thumbnails(df); df = df.sort_values("weirdness_score", ascending=False).reset_index(drop=True); update_leaderboard(df)
        st.session_state.yt_results = df; _show()

# ═══ ROULETTE, BRUTE, CAPSULE, MEDIA ═══
def render_roulette():
    st.markdown('<div class="H"><div class="T">ROULETTE</div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("NEXT", use_container_width=True, type="primary"):
            with st.spinner("..."): vid = deep_roulette_pick()
            if vid: st.session_state["rc"] = vid
    with c2:
        if st.button("QUEUE 10"):
            with st.spinner("..."): b = deep_roulette_batch(10); st.session_state.roulette_queue = b; st.session_state.roulette_idx = 0
            if b: st.session_state["rc"] = b[0]
    with c3:
        q = st.session_state.roulette_queue
        if q and st.button(f"SKIP[{st.session_state.roulette_idx + 1}/{len(q)}]"): st.session_state.roulette_idx = min(st.session_state.roulette_idx + 1, len(q) - 1); st.session_state["rc"] = q[st.session_state.roulette_idx]
    vid = st.session_state.get("rc", "")
    if vid:
        st.markdown(f'<iframe width="100%" height="450" src="https://www.youtube.com/embed/{vid}?autoplay=1" frameborder="0" allow="autoplay" allowfullscreen></iframe>', unsafe_allow_html=True)
        add_to_watch_history(vid, "", f"https://www.youtube.com/watch?v={vid}")
        det = scraper_get_details([vid])
        if det:
            df = scraper_parse_results(det)
            if not df.empty: r = df.iloc[0]; update_leaderboard(df); st.markdown(f'<div class="tb">{_e(str(r.get("title", "?")))}<br>V:{int(r.get("views", 0)):,} W{r.get("weirdness_score", 0):.0f}</div>', unsafe_allow_html=True)
            if st.button("★FAV"): add_favorite(df.iloc[0].to_dict())

def render_brute():
    st.markdown('<div class="H"><div class="T">BRUTE FORCE</div><div class="S">Random ID scanner + Wayback</div></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["RANDOM", "NEAR", "WAYBACK"])
    with t1:
        bs = st.slider("BATCH", 5, 100, 20)
        if st.button("SCAN"):
            p = st.progress(0); found = brute_force_scan(bs, lambda i, n, v: p.progress((i + 1) / n, f"{v}"))
            if found: df = scraper_parse_results(found); df = analyze_thumbnails(df); st.session_state.yt_results = df; update_leaderboard(df); st.success(f"{len(found)} FOUND"); _show()
            else: st.info(f"0/{bs}. ~1/1000 hit rate.")
    with t2:
        seed = st.text_input("SEED ID"); nc = st.slider("COUNT", 5, 50, 20)
        if seed and st.button("SCAN NEAR"):
            near = generate_near_ids(seed, nc); p = st.progress(0); found = []
            for i, n in enumerate(near):
                p.progress((i + 1) / len(near))
                r = check_video_exists(n)
                if r: found.append(r)
            if found: df = scraper_parse_results(found); st.session_state.yt_results = df; _show()
    with t3:
        df = st.session_state.yt_results
        if df.empty: st.info("SEARCH FIRST"); return
        mx = st.slider("MAX CHECK", 1, 50, 10)
        if st.button("CHECK"):
            vids = df["video_id"].head(mx).tolist(); p = st.progress(0)
            results = check_wayback_batch(vids, lambda i, n, v: p.progress((i + 1) / n))
            if results:
                for vid, snap in results.items(): st.markdown(f'<div class="tb"><span class="b bm">[ARCHIVED]</span> {vid} <a href="{snap["url"]}">[WAYBACK]</a></div>', unsafe_allow_html=True)

def render_capsule():
    st.markdown('<div class="H"><div class="T">TIME CAPSULE</div><div class="S">Everything from one day</div></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: td = st.date_input("DATE", value=date(2010, 6, 15), min_value=date(2005, 4, 23)); tmv2 = st.number_input("MAX_V", 0, 10000, 10, key="tcm")
    with c2:
        if st.button("RANDOM DATE"): td = random_time_capsule_date().date()
    if st.button("OPEN CAPSULE"):
        qs = generate_time_capsule_queries(datetime.combine(td, datetime.min.time())); st.session_state.last_queries = qs
        svc = get_youtube_service()
        if svc: df = _yt(svc, qs[:5], 25, datetime.combine(td, datetime.min.time()), datetime.combine(td, datetime.max.time()), "date", "any", "🌍 Any Region", "Any Language", "Any Category", "none", "any")
        else: sdfs = [scraper_search_full(q, 10) for q in qs[:5]]; sdfs = [s for s in sdfs if not s.empty]; df = pd.concat(sdfs, ignore_index=True).drop_duplicates(subset=["video_id"]).reset_index(drop=True) if sdfs else pd.DataFrame()
        if not df.empty: df = filter_by_views(df, tmv2); df = analyze_thumbnails(df); df = df.sort_values("weirdness_score", ascending=False).reset_index(drop=True); st.session_state.yt_results = df; update_leaderboard(df)
        _show()
    df = st.session_state.yt_results
    if not df.empty and "video_id" in df.columns:
        st.markdown("### COMPARE")
        sel = st.multiselect("SELECT 2-4", df["video_id"].head(20).tolist(), max_selections=4)
        if len(sel) >= 2:
            cols = st.columns(len(sel))
            for i, v in enumerate(sel):
                with cols[i]: st.markdown(f'<iframe width="100%" height="200" src="https://www.youtube.com/embed/{v}" frameborder="0" allowfullscreen></iframe>', unsafe_allow_html=True)

def render_media():
    st.markdown('<div class="H"><div class="T">MEDIA ANALYZER</div><div class="S">Audio // Subtitles // Fingerprint</div></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["AUDIO SCAN", "SUBTITLE MINE", "PATTERN ID"])
    df = st.session_state.yt_results
    with t1:
        st.markdown("Check if videos have audio, are silent, or have unusual audio properties.")
        if df.empty: st.info("SEARCH FIRST"); return
        mx = st.slider("MAX TO SCAN", 1, 20, 5, key="ams")
        if st.button("SCAN AUDIO"):
            vids = df["video_id"].head(mx).tolist(); p = st.progress(0)
            results = batch_audio_check(vids, lambda i, n, v: p.progress((i + 1) / n, f"PROBING {v}"))
            for vid, info in results.items():
                if info.get("is_silent"): st.markdown(f'<div class="tb"><span class="b bw">[SILENT]</span> {vid} — NO AUDIO STREAM</div>', unsafe_allow_html=True)
                elif info.get("is_low_bitrate"): st.markdown(f'<div class="tb"><span class="b bb">[LOW_AUDIO]</span> {vid} — {info.get("audio_bitrate", 0)}kbps</div>', unsafe_allow_html=True)
                elif info.get("has_audio"): st.markdown(f'<div class="tb"><span class="b b0">[OK]</span> {vid} — {info.get("audio_codec", "?")} {info.get("audio_bitrate", 0)}kbps</div>', unsafe_allow_html=True)
    with t2:
        st.markdown("Download auto-generated captions and search within them.")
        term = st.text_input("SEARCH TERM", placeholder="weird phrase to find...")
        if df.empty: st.info("SEARCH FIRST"); return
        mx2 = st.slider("MAX VIDEOS", 1, 20, 5, key="sms")
        if term and st.button("MINE SUBTITLES"):
            vids = df["video_id"].head(mx2).tolist(); p = st.progress(0)
            matches = search_subtitles(vids, term, lambda i, n, v: p.progress((i + 1) / n, f"MINING {v}"))
            if matches:
                st.success(f"{len(matches)} MATCHES")
                for m in matches: st.markdown(f'<div class="tb"><a href="{m["url"]}">{m["video_id"]}</a><br>{_e(m["context"])}</div>', unsafe_allow_html=True)
            else: st.info("NO MATCHES IN CAPTIONS")
    with t3:
        st.markdown("Analyze upload patterns of channels in current results to identify bots vs humans.")
        if df.empty: st.info("SEARCH FIRST"); return
        if "channel" in df.columns:
            channels = df["channel"].unique().tolist()[:10]
            for ch in channels:
                ch_df = df[df["channel"] == ch]
                if len(ch_df) >= 3:
                    fp = fingerprint_upload_pattern(ch_df)
                    fpc = "#ff3333" if fp["score"] >= 60 else "#ffb000" if fp["score"] >= 30 else "#33ff33"
                    st.markdown(f'<div class="tb">{_e(ch)} — <span style="color:{fpc}">{fp["pattern"]}</span> ({fp["score"]}/100)</div>', unsafe_allow_html=True)
                    for f in fp["flags"]: st.caption(f"  └ {f}")

# ═══ ANALYZE, BOARD, FAVS, STATS, EXPORT, VAULT, SETUP ═══
def render_analyze():
    st.markdown('<div class="H"><div class="T">DEEP ANALYSIS</div></div>', unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["BURST/DEAD", "DUPE/LANG/ANOMALY", "ARCHAEOLOGY", "PLAYLISTS", "WATCH LOG"])
    df = st.session_state.yt_results
    with t1:
        if df.empty: st.info("SEARCH FIRST"); return
        bursts = detect_upload_bursts(df, st.slider("BURST_N", 2, 20, 3))
        if not bursts.empty:
            for _, br in bursts.iterrows(): st.markdown(f'<div class="tb"><span class="b bb">[BURST]</span> {_e(str(br.get("channel", "")))} {br["date"]} {br["upload_count"]}x {br["burst_type"]}</div>', unsafe_allow_html=True)
        dead = find_dead_channels(df, st.slider("DEAD_N", 1, 10, 3), st.slider("DEAD_D", 30, 3650, 365))
        if not dead.empty:
            for _, dc in dead.iterrows(): st.markdown(f'<div class="tb"><span class="b bx">[DEAD]</span> {_e(dc["channel"])} {dc["video_count"]}v {dc["oldest_video_days"]}d</div>', unsafe_allow_html=True)
    with t2:
        if df.empty: return
        dupes = find_duplicate_titles(df)
        if not dupes.empty: st.markdown(f"**{len(dupes)} DUPES**"); st.dataframe(dupes[["title", "channel", "views", "url"]].head(30), use_container_width=True)
        lang = find_language_mismatches(df); mixed = lang[lang["is_mixed_script"] == True] if "is_mixed_script" in lang.columns else pd.DataFrame()
        if not mixed.empty:
            st.markdown(f"**{len(mixed)} MIXED SCRIPT**")
            for _, r in mixed.head(15).iterrows(): st.markdown(f'<div class="tb">{_e(str(r.get("title", "")))}</div>', unsafe_allow_html=True)
        all_a = []; [all_a.extend(detect_metadata_anomalies(r.to_dict() if hasattr(r, "to_dict") else dict(r))) for _, r in df.iterrows()]
        if all_a:
            st.markdown("### ANOMALIES")
            for a, n in Counter(all_a).most_common(20): st.markdown(f'<div class="tb"><span class="b bm">[{a}]</span> x{n}</div>', unsafe_allow_html=True)
    with t3:
        phrases = st.multiselect("PHRASES", ARCHAEOLOGY_PHRASES, default=ARCHAEOLOGY_PHRASES[:5])
        if st.button("DIG"):
            items = archaeology_search(phrases, 3)
            if items:
                vs = [it.get("id", it.get("url", "")) for it in items]; vs = [v.split("/")[-1] if "http" in str(v) else str(v) for v in vs if v][:50]
                det = scraper_get_details(vs)
                if det: df2 = scraper_parse_results(det); df2 = analyze_thumbnails(df2); st.session_state.yt_results = df2; update_leaderboard(df2)
            _show()
    with t4:
        purl = st.text_input("PLAYLIST URL")
        if purl and st.button("SPELUNK"):
            items = spelunk_playlist(purl, 50)
            if items:
                vs = [it.get("id", it.get("url", "")) for it in items]; vs = [v.split("/")[-1] if "http" in str(v) else str(v) for v in vs if v][:50]
                det = scraper_get_details(vs)
                if det: df2 = scraper_parse_results(det); st.session_state.yt_results = df2; update_leaderboard(df2)
            _show()
    with t5:
        wh = load_watch_history()
        if wh:
            st.markdown(f"**{len(wh)} WATCHED**")
            for h in reversed(wh[-50:]): st.markdown(f'<div class="tb">{h.get("watched_at", "")[:16]} {_e(h.get("title", "?"))} <a href="{h.get("url", "#")}">[OPEN]</a></div>', unsafe_allow_html=True)

def render_board():
    st.markdown('<div class="H"><div class="T">LEADERBOARD</div></div>', unsafe_allow_html=True)
    board = load_leaderboard()
    if not board: st.info("EMPTY"); return
    if st.button("CLEAR"): clear_leaderboard(); st.rerun()
    for i, e in enumerate(board):
        w = e.get("weirdness_score", 0); wc = "#ff3333" if w >= 60 else "#ffb000" if w >= 40 else "#33ff33"
        st.markdown(f'<div class="tb"><span style="color:{wc}">[#{i + 1}] W{w:.0f}</span> {_e(e.get("title", "?"))}<br><span style="color:#1a8c1a">V:{e.get("views", 0):,} CH:{_e(e.get("channel", "?"))}</span> <a href="{e.get("url", "#")}">[OPEN]</a></div>', unsafe_allow_html=True)

def render_favs():
    st.markdown('<div class="H"><div class="T">FAVORITES</div></div>', unsafe_allow_html=True)
    favs = load_favorites()
    if not favs: st.info("EMPTY"); return
    sb = st.selectbox("SORT", ["RECENT", "WEIRD", "LOW_V"])
    if sb == "WEIRD": favs.sort(key=lambda x: x.get("weirdness_score", 0), reverse=True)
    elif sb == "LOW_V": favs.sort(key=lambda x: x.get("views", 0))
    else: favs.reverse()
    for i, f in enumerate(favs):
        w = f.get("weirdness_score", 0); wc = "#ff3333" if w >= 60 else "#ffb000" if w >= 40 else "#33ff33"
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f'<div class="tb"><span style="color:{wc}">W{w:.0f}</span> {_e(f.get("title", "?"))}<br><span style="color:#1a8c1a">V:{f.get("views", 0):,} CH:{_e(f.get("channel", "?"))}</span> <a href="{f.get("url", "#")}">[OPEN]</a></div>', unsafe_allow_html=True)
            st.text_input("NOTE", key=f"n_{i}", label_visibility="collapsed", placeholder="...")
        with c2:
            if st.button("DEL", key=f"rf_{i}"): remove_favorite(f.get("video_id", "")); st.rerun()
    st.download_button("JSON", json.dumps(favs, indent=2), "favs.json")

def render_stats():
    st.markdown('<div class="H"><div class="T">STATS</div></div>', unsafe_allow_html=True)
    ss = get_session_stats(); s1, s2, s3, s4 = st.columns(4); s1.metric("RUNS", ss["total_sessions"]); s2.metric("Q", ss["total_queries"]); s3.metric("FOUND", ss["total_results_found"]); s4.metric("TOP", f"{ss['top_weirdness']:.0f}")
    df = st.session_state.yt_results
    if df.empty: return
    if "views" in df.columns: st.bar_chart(pd.Series({"0": len(df[df["views"] == 0]), "1-5": len(df[(df["views"] >= 1) & (df["views"] <= 5)]), "6-50": len(df[(df["views"] >= 6) & (df["views"] <= 50)]), "50+": len(df[df["views"] > 50])}))
    if "weirdness_score" in df.columns: st.bar_chart(df["weirdness_score"].value_counts(bins=5).sort_index())

def render_export():
    st.markdown('<div class="H"><div class="T">EXPORT</div><div class="S">HTML // Obsidian // RSS // Notion</div></div>', unsafe_allow_html=True)
    df = st.session_state.yt_results; board = load_leaderboard(); favs = load_favorites()
    t1, t2, t3, t4 = st.tabs(["HTML", "OBSIDIAN", "RSS", "NOTION"])
    with t1:
        src = st.selectbox("SRC", ["Results", "Board", "Favs"])
        if st.button("GEN HTML"):
            d = df if src == "Results" else pd.DataFrame(board) if src == "Board" else pd.DataFrame(favs)
            if not d.empty: st.download_button("DL", generate_html_report(d), "report.html", "text/html")
    with t2:
        if not df.empty: md = export_to_obsidian(df); st.download_button("DL .MD", md, "oe.md", "text/markdown")
    with t3:
        items = board if st.selectbox("SRC", ["Board", "Favs"], key="rs") == "Board" else favs
        if items: st.download_button("DL .XML", generate_rss_feed(items), "oe.xml", "application/xml")
    with t4:
        if not df.empty: st.download_button("DL CSV", export_to_notion_csv(df), "notion.csv", "text/csv")

def render_vault():
    st.markdown('<div class="H"><div class="T">VAULT</div></div>', unsafe_allow_html=True)
    s = get_vault_stats(); c1, c2, c3, c4 = st.columns(4); c1.metric("N", s["total_items"]); c2.metric("YT", s["youtube_items"]); c3.metric("IA", s["archive_items"]); c4.metric("SIZE", s["total_size_human"])
    for item in reversed(get_vault_index().get("items", [])):
        with st.expander(item.get("title", "?")[:50]): st.code(f"ID:{item.get('id')}\nURL:{item.get('url')}\nPATH:{item.get('filepath')}")
    st.info("Manual download disabled for GitHub release.")

def render_setup():
    st.markdown('<div class="H"><div class="T">SETUP</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="tb">SCRAPE MODE = NO API KEYS</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["KEYS", "OAUTH", "IA"])
    with t1:
        ak = get_all_api_keys()
        if ak: st.success(f"{len(ak)} KEYS LOADED. ROTATION ACTIVE."); [st.code(f"K{i + 1}:{k[:8]}...{k[-4:]}") for i, k in enumerate(ak)]
        nk = st.text_input("ADD", type="password")
        if nk and st.button(f"SAVE K{len(ak) + 1}"):
            if len(ak) == 0: save_api_key(nk)
            else: save_additional_api_key(nk, len(ak) + 1)
            st.rerun()
    with t2:
        if has_client_secrets(): st.success("OK")
        up = st.file_uploader("JSON", type=["json"])
        if up:
            try: save_client_secrets(up.read().decode()); st.rerun()
            except: st.error("BAD")
    with t3:
        ia = get_archive_credentials()
        if ia: st.success(ia["email"])
        em = st.text_input("EMAIL"); pw = st.text_input("PASS", type="password")
        if st.button("SAVE", disabled=not(em and pw)): save_archive_credentials(em, pw); st.rerun()

def main():
    p = render_sidebar()
    pages = {"🔍 SEARCH": render_search, "🗺️ GEO": render_geo, "🐇 RABBIT": render_rabbit, "🕵️ CHANNEL": render_channel,
             "🕸️ CRAWL": render_crawl, "🎲 CHAOS": render_chaos, "📺 ROULETTE": render_roulette, "💀 BRUTE": render_brute,
             "⏳ CAPSULE": render_capsule, "🔬 ANALYZE": render_analyze, "🔊 MEDIA": render_media, "🏆 BOARD": render_board,
             "⭐ FAVS": render_favs, "📊 STATS": render_stats, "📤 EXPORT": render_export, "📦 VAULT": render_vault, "⚙️ SETUP": render_setup}
    fn = pages.get(p, render_search)
    try:
        fn()
    except Exception as ex:
        st.error(f"PAGE ERROR: {type(ex).__name__}: {ex}")
        st.markdown(f'<div class="tb">SYS> Error in {p}. Try another module or refresh.\nDetails: {_e(str(ex)[:200])}</div>', unsafe_allow_html=True)
        import traceback
        with st.expander("TRACEBACK"):
            st.code(traceback.format_exc())

if __name__ == "__main__": main()
