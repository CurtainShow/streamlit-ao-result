import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime

# ─── Page Config ───
st.set_page_config(
    page_title="NM Materiel CJSLM - Vérification des Recommandations",
    page_icon="🔍",
    layout="wide",
)

# ─── Custom CSS ───
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; max-width: 1400px; }
    .header-bar {
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
        color: white; padding: 20px 28px; border-radius: 12px; margin-bottom: 20px;
    }
    .header-bar h1 { color: white; margin: 0; font-size: 1.6rem; }
    .header-bar p { color: rgba(255,255,255,0.85); margin: 4px 0 0; font-size: 0.95rem; }
    .input-card {
        background: #f0f4ff; border: 1px solid #c7d2fe;
        border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;
    }
    .input-card .label { font-size: 0.78rem; color: #6366f1; font-weight: 700; text-transform: uppercase; }
    .input-card .text { font-size: 1.05rem; font-weight: 600; color: #1e1b4b; margin-top: 4px; }
    .input-card .ptype { font-size: 0.82rem; color: #4338ca; margin-top: 2px; }
    .criteria-card {
        background: #fffbeb; border: 1px solid #fde68a;
        border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;
    }
    .criteria-card .label { font-size: 0.78rem; color: #d97706; font-weight: 700; text-transform: uppercase; }
    .criteria-card .text { font-size: 0.88rem; color: #78350f; margin-top: 4px; line-height: 1.6; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: 600; font-size: 0.82rem; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ───
def safe_str(val):
    if pd.isna(val) or val is None or str(val).strip().lower() in ('nan', 'none', ''):
        return ""
    return str(val).strip()


def match_color(ratio):
    try:
        r = float(ratio)
        if r >= 60: return "#dcfce7", "#166534"
        elif r >= 35: return "#fef9c3", "#854d0e"
    except: pass
    return "#fee2e2", "#991b1b"


def avail_color(avail_text):
    a = safe_str(avail_text).lower()
    if "stock" in a: return "#dcfce7", "#166534"
    if "fournisseur" in a: return "#dbeafe", "#1e40af"
    return "#fee2e2", "#991b1b"


def render_chips_html(text, bg, fg):
    """Render pipe-separated items as inline HTML chips."""
    if not text:
        return ""
    items = [x.strip() for x in text.split("|") if x.strip()]
    return " ".join(
        f'<span style="display:inline-block; background:{bg}; color:{fg}; '
        f'padding:2px 7px; border-radius:4px; font-size:0.73rem; margin:2px 2px; line-height:1.6;">{i}</span>'
        for i in items
    )


def render_product_tile(row, rank, idx):
    """Render a product tile using st.container + native components to avoid HTML rendering issues."""
    prefix = f"rank_{rank}_"
    name = safe_str(row.get(f"{prefix}name"))
    sku = safe_str(row.get(f"{prefix}sku"))
    price = safe_str(row.get(f"{prefix}price"))
    img_url = safe_str(row.get(f"{prefix}url_image"))
    url = safe_str(row.get(f"{prefix}url"))
    match_ratio = safe_str(row.get(f"{prefix}match_ratio"))
    rerank_score = safe_str(row.get(f"{prefix}rerank_score"))
    matched = safe_str(row.get(f"{prefix}matched"))
    partial = safe_str(row.get(f"{prefix}partial"))
    missing = safe_str(row.get(f"{prefix}missing"))
    availability = safe_str(row.get(f"{prefix}availability"))
    brand = safe_str(row.get(f"{prefix}brand"))
    attrs = safe_str(row.get(f"{prefix}attrs"))
    cost_price = safe_str(row.get(f"{prefix}cost_price"))
    sales_price = safe_str(row.get(f"{prefix}sales_price"))
    positioning = safe_str(row.get(f"{prefix}positioning"))

    is_relevant_raw = safe_str(row.get(f"{prefix}is_relevant"))
    is_relevant = is_relevant_raw.lower() == "true" if is_relevant_raw else None
    relevance_reason = safe_str(row.get(f"{prefix}relevance_reason"))

    if not name:
        with st.container(border=True):
            st.markdown(f"<p style='text-align:center; color:#999; padding:30px 0;'>Pas de proposition #{rank}</p>", unsafe_allow_html=True)
        return

    with st.container(border=True):
        # ── Relevance badge (top-right) ──
        if is_relevant is not None:
            if is_relevant:
                badge_html = '<div style="text-align:right; margin-bottom:4px;"><span title="Produit pertinent" style="background:#dcfce7; color:#166534; padding:3px 10px; border-radius:20px; font-size:0.85rem; font-weight:700;">✅ Pertinent</span></div>'
            else:
                title = relevance_reason if relevance_reason else "Produit non pertinent"
                badge_html = f'<div style="text-align:right; margin-bottom:4px;"><span title="{title}" style="background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:20px; font-size:0.85rem; font-weight:700;">❌ Non pertinent</span></div>'
            st.markdown(badge_html, unsafe_allow_html=True)

        # ── Image ──
        if img_url:
            st.markdown(
                f'<div style="background:#f8f9fa; border-radius:8px; padding:8px; text-align:center; '
                f'min-height:160px; display:flex; align-items:center; justify-content:center;">'
                f'<img src="{img_url}" style="max-height:150px; max-width:100%; object-fit:contain;" '
                f'onerror="this.style.display=\'none\'">'
                f'</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="background:#f8f9fa; border-radius:8px; padding:40px 8px; '
                'text-align:center; color:#bbb;">Pas d\'image</div>', unsafe_allow_html=True)

        # ── SKU + Match badge ──
        badges = f'<span style="display:inline-block; background:#eef2ff; color:#4338ca; padding:2px 8px; border-radius:6px; font-size:0.78rem; font-weight:600; margin-right:6px;">{sku}</span>'
        if match_ratio:
            bg, fg = match_color(match_ratio)
            badges += f'<span style="display:inline-block; background:{bg}; color:{fg}; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700;">Match: {match_ratio}%</span> '
        if positioning:
            badges += f'<span style="font-size:0.73rem; background:#e0e7ff; color:#3730a3; padding:2px 7px; border-radius:4px;">{positioning}</span>'
        st.markdown(badges, unsafe_allow_html=True)

        # ── Name ──
        st.markdown(f"**{name}**")

        # ── Availability + Brand ──
        info_badges = ""
        if availability:
            abg, afg = avail_color(availability)
            info_badges += f'<span style="display:inline-block; font-size:0.73rem; padding:2px 7px; border-radius:4px; background:{abg}; color:{afg}; margin-right:6px;">{availability}</span>'
        if brand:
            info_badges += f'<span style="display:inline-block; background:#fef3c7; color:#92400e; padding:2px 8px; border-radius:6px; font-size:0.78rem; font-weight:600;">🏷️ {brand}</span>'
        if info_badges:
            st.markdown(info_badges, unsafe_allow_html=True)

        # ── Prices — native st.columns + st.metric for guaranteed rendering ──
        has_cost = bool(cost_price)
        has_sales = bool(sales_price)
        if has_cost or has_sales:
            pc = st.columns(2)
            if has_cost:
                pc[0].metric("Prix d'achat", f"{cost_price} €")
            if has_sales:
                pc[1].metric("Prix de vente", f"{sales_price} €")
        elif price:
            st.metric("Prix", f"{price} €")

        # ── Criteria chips ──
        if matched:
            chips = render_chips_html(matched, "#dcfce7", "#166534")
            st.markdown(f'<div style="margin:6px 0;"><strong style="font-size:0.75rem; color:#16a34a;">✅ PRÉSENT</strong><br>{chips}</div>', unsafe_allow_html=True)
        if partial:
            chips = render_chips_html(partial, "#fef3c7", "#92400e")
            st.markdown(f'<div style="margin:6px 0;"><strong style="font-size:0.75rem; color:#d97706;">⚠️ PARTIEL</strong><br>{chips}</div>', unsafe_allow_html=True)
        if missing:
            chips = render_chips_html(missing, "#fee2e2", "#991b1b")
            st.markdown(f'<div style="margin:6px 0;"><strong style="font-size:0.75rem; color:#dc2626;">❌ MANQUANT</strong><br>{chips}</div>', unsafe_allow_html=True)

        # ── Link ──
        if url:
            st.markdown(f'<a href="{url}" target="_blank" style="font-size:0.75rem; color:#6366f1;">Voir le produit ↗</a>', unsafe_allow_html=True)

        # ── Scores & Attributs expander ──
        with st.expander("📊 Scores & Attributs", expanded=False):
            sc = st.columns(2)
            sc[0].metric("Match Ratio", f"{match_ratio}%" if match_ratio else "N/A")
            sc[1].metric("Rerank Score", rerank_score if rerank_score else "N/A")
            if attrs:
                st.markdown("**Attributs techniques :**")
                for attr in [a.strip() for a in attrs.split("|") if a.strip()]:
                    st.markdown(f"- {attr}")

        # ── Buttons ──
        key_base = f"row_{idx}_rank_{rank}"
        current = st.session_state.get("annotations", {}).get(str(idx), {})

        bc = st.columns(2)
        with bc[0]:
            is_exact = current.get("exact_match") == rank
            if st.button("✅ Exact Match" if is_exact else "Exact Match",
                         key=f"{key_base}_exact",
                         type="primary" if is_exact else "secondary",
                         use_container_width=True):
                set_annotation(idx, "exact_match", rank)
                st.rerun()
        with bc[1]:
            is_alt = current.get("alternative") == rank
            if st.button("🔄 Alternative" if is_alt else "Alternative",
                         key=f"{key_base}_alt",
                         type="primary" if is_alt else "secondary",
                         use_container_width=True):
                set_annotation(idx, "alternative", rank)
                st.rerun()


def set_annotation(idx, field, value):
    if "annotations" not in st.session_state:
        st.session_state.annotations = {}
    key = str(idx)
    if key not in st.session_state.annotations:
        st.session_state.annotations[key] = {}
    if st.session_state.annotations[key].get(field) == value:
        del st.session_state.annotations[key][field]
    else:
        st.session_state.annotations[key][field] = value


def export_annotations(df):
    records = []
    annotations = st.session_state.get("annotations", {})
    for idx_str, annot in annotations.items():
        idx = int(idx_str)
        if idx < len(df):
            row = df.iloc[idx]
            record = {
                "row_index": idx,
                "input_text": row.get("input_text", ""),
                "product_type": row.get("product_type", ""),
                "exact_match_rank": annot.get("exact_match"),
                "alternative_rank": annot.get("alternative"),
                "no_match": annot.get("no_match", False),
            }
            for field_name, rank_key in [("exact_match", "exact_match"), ("alternative", "alternative")]:
                rank = annot.get(rank_key)
                if rank:
                    prefix = f"rank_{rank}_"
                    record[f"{field_name}_sku"] = safe_str(row.get(f"{prefix}sku"))
                    record[f"{field_name}_name"] = safe_str(row.get(f"{prefix}name"))
                    record[f"{field_name}_match_ratio"] = safe_str(row.get(f"{prefix}match_ratio"))
            records.append(record)
    return pd.DataFrame(records) if records else pd.DataFrame()


def export_progress(df):
    return json.dumps({
        "annotations": st.session_state.get("annotations", {}),
        "current_index": st.session_state.get("current_index", 0),
        "timestamp": datetime.now().isoformat(),
        "total_rows": len(df),
    }, ensure_ascii=False, indent=2)


# ─── Session State Init ───
for k, v in [("annotations", {}), ("current_index", 0), ("df", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Header ───
st.markdown("""
<div class="header-bar">
    <h1>🔍 NM Materiel CJSLM - Vérification des Recommandations</h1>
    <p>Annotez les résultats de matching : sélectionnez un Exact Match, une Alternative, ou marquez comme non pertinent.</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ───
with st.sidebar:
    st.markdown("### 📂 Chargement des données")
    uploaded_file = st.file_uploader("Charger le fichier CSV", type=["csv"], key="csv_upload")
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
            st.session_state.df = df
            st.success(f"✅ {len(df)} lignes chargées")
        except Exception as e:
            st.error(f"Erreur : {e}")

    st.divider()
    st.markdown("### 💾 Reprendre une session")
    progress_file = st.file_uploader("Charger un fichier de progression (.json)", type=["json"], key="progress_upload")
    if progress_file is not None:
        try:
            progress = json.load(progress_file)
            st.session_state.annotations = progress.get("annotations", {})
            st.session_state.current_index = progress.get("current_index", 0)
            st.success(f"✅ Session restaurée — ligne {st.session_state.current_index + 1}")
        except Exception as e:
            st.error(f"Erreur : {e}")

    if st.session_state.df is not None:
        df = st.session_state.df
        total = len(df)
        annotated = len(st.session_state.annotations)

        st.divider()
        st.markdown("### 📊 Progression")
        st.progress(annotated / total if total > 0 else 0)
        st.markdown(f"**{annotated}** / **{total}** lignes annotées ({annotated * 100 // total if total > 0 else 0}%)")

        st.divider()
        st.markdown("### 📤 Exports")
        progress_json = export_progress(df)
        st.download_button(
            "⏸️ Sauvegarder la progression", data=progress_json,
            file_name=f"cern_progress_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json", use_container_width=True,
        )
        export_df = export_annotations(df)
        if not export_df.empty:
            buf = io.StringIO()
            export_df.to_csv(buf, index=False, sep=";")
            st.download_button(
                "📊 Exporter les annotations (CSV)", data=buf.getvalue(),
                file_name=f"cern_annotations_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True,
            )
        else:
            st.info("Aucune annotation à exporter.")

        st.divider()
        st.markdown("### 🔢 Navigation")
        new_idx = st.number_input("Aller à la ligne :", min_value=1, max_value=total,
                                  value=st.session_state.current_index + 1, step=1)
        if new_idx - 1 != st.session_state.current_index:
            st.session_state.current_index = new_idx - 1
            st.rerun()


# ─── Main ───
if st.session_state.df is None:
    st.markdown("""
    <div style="text-align:center; padding:60px 20px;">
        <p style="font-size:3rem; margin-bottom:10px;">📄</p>
        <h3 style="color:#4338ca;">Chargez un fichier CSV pour commencer</h3>
        <p style="color:#666;">Utilisez le panneau latéral pour charger votre fichier de résultats CERN.</p>
        <p style="color:#999; font-size:0.85rem;">Vous pouvez aussi reprendre une session précédente via un fichier JSON.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    df = st.session_state.df
    total = len(df)
    idx = st.session_state.current_index

    if idx >= total:
        st.balloons()
        st.success("🎉 Toutes les lignes ont été vérifiées ! Exportez vos résultats depuis le panneau latéral.")
    else:
        row = df.iloc[idx]

        # ── Nav ──
        nav = st.columns([1, 3, 1])
        with nav[0]:
            if st.button("⬅️ Précédent", disabled=(idx == 0), use_container_width=True):
                st.session_state.current_index = max(0, idx - 1)
                st.rerun()
        with nav[1]:
            st.markdown(f"<div style='text-align:center; font-size:1.1rem; font-weight:700; padding:8px;'>Ligne {idx + 1} / {total}</div>", unsafe_allow_html=True)
        with nav[2]:
            if st.button("Suivant ➡️", disabled=(idx >= total - 1), use_container_width=True):
                st.session_state.current_index = min(total - 1, idx + 1)
                st.rerun()

        # ── Input + Criteria ──
        tc = st.columns([2, 3])
        with tc[0]:
            st.markdown(f"""
            <div class="input-card">
                <div class="label">Produit recherché</div>
                <div class="text">{safe_str(row.get('input_text'))}</div>
                <div class="ptype">Type : {safe_str(row.get('product_type'))}</div>
            </div>""", unsafe_allow_html=True)
        with tc[1]:
            st.markdown(f"""
            <div class="criteria-card">
                <div class="label">Critères de sélection</div>
                <div class="text">{safe_str(row.get('criteres'))}</div>
            </div>""", unsafe_allow_html=True)

        # ── Relevance warning ──
        has_good_match = safe_str(row.get("relevance_has_good_match")).lower()
        if has_good_match == "false":
            relevance_msg = safe_str(row.get("relevance_message"))
            msg = relevance_msg if relevance_msg else "Aucun produit suffisamment pertinent trouvé dans l'offre actuelle."
            st.markdown(
                f'<div style="background:#fee2e2; border:1px solid #fca5a5; border-radius:10px; '
                f'padding:14px 18px; margin:12px 0; color:#991b1b; font-weight:600; font-size:0.9rem;">'
                f'⚠️ Les produits proposés ne sont pas forcément pertinents pour cette recherche — '
                f'{msg}</div>',
                unsafe_allow_html=True,
            )

        # ── Annotation status ──
        current_annot = st.session_state.annotations.get(str(idx), {})
        if current_annot:
            parts = []
            if current_annot.get("exact_match"):
                parts.append(f"✅ Exact Match : Rang {current_annot['exact_match']}")
            if current_annot.get("alternative"):
                parts.append(f"🔄 Alternative : Rang {current_annot['alternative']}")
            if current_annot.get("no_match"):
                parts.append("🚫 Aucune recommandation pertinente")
            st.info(" — ".join(parts))

        # ── 4 tiles ──
        cols = st.columns(4, gap="medium")
        for rank in range(1, 5):
            with cols[rank - 1]:
                st.markdown(f"<div style='text-align:center; font-weight:700; color:#6366f1; margin-bottom:8px;'>Rang #{rank}</div>", unsafe_allow_html=True)
                render_product_tile(row, rank, idx)

        # ── No match ──
        st.markdown("")
        nc = st.columns([1, 2, 1])
        with nc[1]:
            is_no = current_annot.get("no_match", False)
            if st.button("🚫 Aucune recommandation pertinente" + (" ✓" if is_no else ""),
                         key=f"no_match_{idx}",
                         type="primary" if is_no else "secondary",
                         use_container_width=True):
                key = str(idx)
                if key not in st.session_state.annotations:
                    st.session_state.annotations[key] = {}
                if st.session_state.annotations[key].get("no_match"):
                    del st.session_state.annotations[key]["no_match"]
                else:
                    st.session_state.annotations[key] = {"no_match": True}
                st.rerun()

        # ── Validate + advance ──
        st.markdown("")
        ac = st.columns([1, 2, 1])
        with ac[1]:
            if current_annot and st.button("Valider et passer au suivant ➡️", type="primary", use_container_width=True):
                if idx < total - 1:
                    st.session_state.current_index = idx + 1
                    st.rerun()
                else:
                    st.balloons()
                    st.success("🎉 Dernière ligne atteinte !")