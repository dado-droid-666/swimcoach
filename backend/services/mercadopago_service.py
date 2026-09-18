import mercadopago
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models import User, SubscriptionStatus, SubscriptionTier

settings = get_settings()

# Initialize MercadoPago SDK
mp_client = mercadopago.SDK(settings.mp_access_token)

# Preapproval plan ID - create this in MercadoPago dashboard and add to env
# For development, we'll create preapprovals directly without a plan
MP_PREAPPROVAL_PLAN_ID = getattr(settings, 'mp_preapproval_plan_id', None)


def get_or_create_preapproval_plan() -> Optional[str]:
    """Get preapproval plan ID from settings or environment.
    
    In production, create a plan in MercadoPago dashboard and set MP_PREAPPROVAL_PLAN_ID.
    For development, we create preapprovals directly without a plan.
    """
    return MP_PREAPPROVAL_PLAN_ID


def create_preapproval(user: User, plan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create a preapproval for a user."""
    try:
        preapproval_data = {
            "payer_email": user.email,
            "external_reference": f"user_{user.id}",
            "back_url": f"{settings.frontend_url}/#/upgrade?status=success",
            "auto_recurring": {
                "frequency": 1,
                "frequency_type": "months",
                "repetitions": 12,
                "billing_day": 1,
                "billing_day_proportional": True,
                "free_trial": {
                    "frequency": 1,
                    "frequency_type": "months"
                },
                "transaction_amount": 100.0,  # $100 MXN/month
                "currency_id": "MXN"
            },
            "status": "pending"
        }
        
        # Add plan_id if provided
        if plan_id:
            preapproval_data["preapproval_plan_id"] = plan_id
        
        result = mp_client.preapproval().create(preapproval_data)
        if result["status"] == 201:
            return result["response"]
        
        return None
    except Exception as e:
        print(f"Error creating preapproval: {e}")
        return None


def get_preapproval(preapproval_id: str) -> Optional[Dict[str, Any]]:
    """Get preapproval details."""
    try:
        result = mp_client.preapproval().get(preapproval_id)
        if result["status"] == 200:
            return result["response"]
        return None
    except Exception as e:
        print(f"Error getting preapproval: {e}")
        return None


def cancel_preapproval(preapproval_id: str) -> bool:
    """Cancel a preapproval."""
    try:
        result = mp_client.preapproval().cancel(preapproval_id)
        return result["status"] == 200
    except Exception as e:
        print(f"Error canceling preapproval: {e}")
        return False


def create_checkout_preference(user: User, plan_id: str) -> Optional[Dict[str, Any]]:
    """Create a checkout preference for MercadoPago."""
    try:
        # For development without valid MP credentials, return mock checkout
        if settings.environment == "development" and (
            settings.mp_access_token.startswith("TEST-") or 
            settings.mp_access_token == "TEST-1234567890"
        ):
            # Return mock checkout for development
            mock_preapproval_id = f"preapproval_dev_{user.id}_{int(datetime.utcnow().timestamp())}"
            mock_init_point = f"{settings.frontend_url}/#/upgrade?mock_checkout=1&preapproval_id=mock_{user.id}"
            return {
                "init_point": mock_init_point,
                "preapproval_id": mock_preapproval_id,
                "sandbox_init_point": mock_init_point
            }
        
        # First ensure preapproval plan exists
        if not plan_id:
            plan_id = get_or_create_preapproval_plan()
        
        if not plan_id:
            raise HTTPException(status_code=500, detail="Could not create subscription plan")
        
        # Create preapproval for user
        preapproval = create_preapproval(user, plan_id)
        if not preapproval:
            raise HTTPException(status_code=500, detail="Could not create subscription")
        
        # Return init_point for redirect
        return {
            "init_point": preapproval.get("init_point"),
            "preapproval_id": preapproval.get("id"),
            "sandbox_init_point": preapproval.get("sandbox_init_point")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout")


def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    """Verify MercadoPago webhook signature."""
    if not settings.mp_webhook_secret:
        return True  # Skip verification if no secret configured
    
    try:
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            settings.mp_webhook_secret.encode(),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False


def process_webhook(webhook_data: Dict[str, Any], db: Session) -> bool:
    """Process MercadoPago webhook notification."""
    try:
        action = webhook_data.get("action")
        data = webhook_data.get("data", {})
        resource_id = data.get("id")
        
        if action == "preapproval.authorized_payment" or action == "payment.created":
            # Payment successful - check if it's a subscription payment
            preapproval_id = webhook_data.get("data", {}).get("preapproval_id")
            
            if preapproval_id:
                preapproval = get_preapproval(preapproval_id)
                if preapproval:
                    external_ref = preapproval.get("external_reference", "")
                    if external_ref.startswith("user_"):
                        user_id = int(external_ref.split("_")[1])
                        user = db.query(User).filter(User.id == user_id).first()
                        
                        if user:
                            # Update user subscription
                            user.subscription_tier = SubscriptionTier.PRO
                            user.subscription_status = SubscriptionStatus.ACTIVE
                            user.mp_preapproval_id = preapproval_id
                            user.mp_subscription_id = preapproval.get("id")
                            
                            # Set period end (1 month from now)
                            user.current_period_end = datetime.utcnow() + timedelta(days=30)
                            
                            db.commit()
                            return True
        
        elif action == "preapproval.cancelled":
            preapproval_id = data.get("id")
            preapproval = get_preapproval(preapproval_id)
            if preapproval:
                external_ref = preapproval.get("external_reference", "")
                if external_ref.startswith("user_"):
                    user_id = int(external_ref.split("_")[1])
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user.subscription_status = SubscriptionStatus.CANCELLED
                        # Keep PRO until period ends
                        db.commit()
                        return True
        
        elif action == "preapproval.pending":
            # Initial creation - store preapproval_id
            preapproval_id = data.get("id")
            preapproval = get_preapproval(preapproval_id)
            if preapproval:
                external_ref = preapproval.get("external_reference", "")
                if external_ref.startswith("user_"):
                    user_id = int(external_ref.split("_")[1])
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user.mp_preapproval_id = preapproval_id
                        user.subscription_status = SubscriptionStatus.PENDING
                        db.commit()
                        return True
        
        return True  # Acknowledge webhook even if not handled
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return False


def get_billing_portal_url(user: User) -> Optional[str]:
    """Get MercadoPago billing portal URL for user."""
    try:
        if not user.mp_preapproval_id:
            return None
        
        preapproval = get_preapproval(user.mp_preapproval_id)
        if preapproval and "payer" in preapproval:
            # MercadoPago doesn't have a direct billing portal URL for preapprovals
            # User manages subscriptions in their MP account
            return "https://www.mercadopago.com.ar/subscriptions"  # Or appropriate country URL
        
        return None
    except Exception as e:
        print(f"Error getting billing portal: {e}")
        return None