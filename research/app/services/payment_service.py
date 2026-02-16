"""
Payment service abstraction
"""
import stripe
from flask import current_app
from datetime import datetime
from app.extensions import db
from app.models.subscription import Payment


class PaymentService:
    """Payment gateway service"""
    
    def __init__(self):
        self.stripe_key = current_app.config.get('STRIPE_SECRET_KEY')
        stripe.api_key = self.stripe_key
    
    def create_customer(self, email, name=None, metadata=None):
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error: {str(e)}")
            return None
    
    def create_subscription(self, customer_id, price_id, trial_days=None):
        """Create a subscription"""
        try:
            params = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent']
            }
            
            if trial_days:
                params['trial_period_days'] = trial_days
            
            subscription = stripe.Subscription.create(**params)
            return subscription
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error: {str(e)}")
            return None
    
    def cancel_subscription(self, subscription_id):
        """Cancel a subscription"""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error: {str(e)}")
            return None
    
    def create_payment_intent(self, amount, currency='usd', customer_id=None, metadata=None):
        """Create a payment intent"""
        try:
            params = {
                'amount': int(amount * 100),  # Convert to cents
                'currency': currency,
                'metadata': metadata or {}
            }
            
            if customer_id:
                params['customer'] = customer_id
            
            intent = stripe.PaymentIntent.create(**params)
            return intent
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error: {str(e)}")
            return None
    
    def handle_webhook(self, payload, sig_header):
        """Handle Stripe webhook"""
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            current_app.logger.error(f"Invalid payload: {str(e)}")
            return False
        except stripe.error.SignatureVerificationError as e:
            current_app.logger.error(f"Invalid signature: {str(e)}")
            return False
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            self._handle_payment_failed(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            self._handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            self._handle_subscription_deleted(event['data']['object'])
        
        return True
    
    def _handle_payment_succeeded(self, payment_intent):
        """Handle successful payment"""
        # Create payment record
        payment = Payment(
            stripe_payment_intent_id=payment_intent['id'],
            amount=payment_intent['amount'] / 100,
            currency=payment_intent['currency'],
            status='succeeded',
            paid_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()
    
    def _handle_payment_failed(self, payment_intent):
        """Handle failed payment"""
        current_app.logger.warning(f"Payment failed: {payment_intent['id']}")
    
    def _handle_subscription_updated(self, subscription):
        """Handle subscription update"""
        current_app.logger.info(f"Subscription updated: {subscription['id']}")
    
    def _handle_subscription_deleted(self, subscription):
        """Handle subscription deletion"""
        current_app.logger.info(f"Subscription canceled: {subscription['id']}")