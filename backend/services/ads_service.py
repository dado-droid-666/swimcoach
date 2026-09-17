from typing import Optional
from backend.config import get_settings

settings = get_settings()


def get_adsense_client_id() -> str:
    """Get AdSense client ID."""
    return settings.adsense_client_id or "ca-pub-XXXXXXXXXXXX"


def get_adsense_slots() -> dict:
    """Get AdSense ad slot IDs."""
    return {
        "banner": settings.adsense_slot_banner or "1234567890",
        "interstitial": settings.adsense_slot_interstitial or "0987654321",
        "native": settings.adsense_slot_native or "",
        "in_article": settings.adsense_slot_in_article or "",
    }


def should_show_ads(user_tier: str) -> bool:
    """Determine if ads should be shown for a user tier."""
    return user_tier == "free"


def get_adsense_head_script() -> str:
    """Get AdSense head script for HTML."""
    client_id = get_adsense_client_id()
    if not client_id or client_id == "ca-pub-XXXXXXXXXXXX":
        return ""
    
    return f"""
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client_id}"
     crossorigin="anonymous"></script>
"""


def get_banner_ad_slot() -> str:
    """Get banner ad slot HTML."""
    if not should_show_ads("free"):
        return ""
    
    slots = get_adsense_slots()
    slot = slots.get("banner", "1234567890")
    
    return f"""
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{get_adsense_client_id()}"
     data-ad-slot="{slot}"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>
"""


def get_interstitial_ad_script() -> str:
    """Get interstitial ad script."""
    if not should_show_ads("free"):
        return ""
    
    slots = get_adsense_slots()
    slot = slots.get("interstitial", "0987654321")
    
    return f"""
<script>
    // Interstitial ad - show once per session
    if (!sessionStorage.getItem('interstitial_shown')) {{
        (adsbygoogle = window.adsbygoogle || []).push({{}});
        sessionStorage.setItem('interstitial_shown', 'true');
    }}
</script>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{get_adsense_client_id()}"
     data-ad-slot="{slot}"
     data-ad-format="interstitial"
     data-full-width-responsive="true"></ins>
"""


def get_native_ad_slot() -> str:
    """Get native ad slot HTML."""
    if not should_show_ads("free"):
        return ""
    
    slots = get_adsense_slots()
    slot = slots.get("native", "")
    
    if not slot:
        return ""
    
    return f"""
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{get_adsense_client_id()}"
     data-ad-slot="{slot}"
     data-matched-content-rows-num="2"
     data-matched-content-columns-num="2"
     data-matched-content-ui-type="image_stacked"
     data-ad-format="native"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>
"""


def get_ad_config_for_template(tier: str) -> dict:
    """Get ad configuration for frontend template."""
    if tier == "pro":
        return {
            "show_ads": False,
            "adsense_client": "",
            "banner_slot": "",
            "interstitial_slot": ""
        }
    
    slots = get_adsense_slots()
    return {
        "show_ads": True,
        "adsense_client": get_adsense_client_id(),
        "banner_slot": slots.get("banner", ""),
        "interstitial_slot": slots.get("interstitial", ""),
        "native_slot": slots.get("native", ""),
        "in_article_slot": slots.get("in_article", "")
    }