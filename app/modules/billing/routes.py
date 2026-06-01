from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.modules.billing import billing_bp
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.article import Article
from app.models.transaction import Transaction
from app.core.extensions import db
from app.core.decorators import tenant_owner_required
from datetime import datetime, timedelta
from types import SimpleNamespace
import hashlib
import hmac
import requests

def _app_currency():
    configured = (current_app.config.get('RAZORPAY_CURRENCY') or 'INR').strip().upper()
    # Billing is standardized to INR across the product.
    return 'INR' if configured != 'INR' else configured

def get_or_create_subscription(tenant_id):
    app_currency = _app_currency()
    sub = Subscription.query.filter_by(tenant_id=tenant_id).first()
    needs_commit = False
    if not sub:
        sub = Subscription(
            tenant_id = tenant_id,
            plan      = 'free',
            status    = 'active',
            amount    = 0.0,
            currency  = app_currency,
        )
        db.session.add(sub)
        needs_commit = True
    elif (sub.currency or '').upper() != app_currency:
        sub.currency = app_currency
        needs_commit = True

    normalized_txns = Transaction.query.filter_by(tenant_id=tenant_id).filter(
        Transaction.currency != app_currency
    ).update({Transaction.currency: app_currency}, synchronize_session=False)
    if normalized_txns:
        needs_commit = True

    if needs_commit:
        db.session.commit()
    return sub

def _get_razorpay_credentials():
    key_id = (current_app.config.get('RAZORPAY_KEY_ID') or '').strip()
    key_secret = (current_app.config.get('RAZORPAY_KEY_SECRET') or '').strip()
    if not key_id or not key_secret:
        raise ValueError('Razorpay keys are not configured.')
    return key_id, key_secret

def _create_razorpay_order(*, amount_paise, currency, receipt, notes):
    key_id, key_secret = _get_razorpay_credentials()
    payload = {
        'amount': int(amount_paise),
        'currency': currency,
        'receipt': receipt,
        'payment_capture': 1,
        'notes': notes or {},
    }
    session = requests.Session()
    session.trust_env = False

    try:
        response = session.post(
            'https://api.razorpay.com/v1/orders',
            json=payload,
            auth=(key_id, key_secret),
            timeout=25,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f'Unable to reach Razorpay ({exc}). Please check proxy/network settings.') from exc

    try:
        order = response.json()
    except ValueError:
        order = {}

    if response.status_code >= 400:
        message = (
            order.get('error', {}).get('description')
            if isinstance(order, dict) else None
        ) or 'Razorpay order creation failed.'
        raise RuntimeError(message)

    if not isinstance(order, dict) or not order.get('id'):
        raise RuntimeError('Invalid order response from Razorpay.')

    return {'key_id': key_id, 'order': order}

def _verify_razorpay_signature(order_id, payment_id, signature):
    _, key_secret = _get_razorpay_credentials()
    expected_signature = hmac.new(
        key_secret.encode('utf-8'),
        f'{order_id}|{payment_id}'.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def _resolve_plan_amount(plan, billing_cycle='monthly'):
    plan_data = Subscription.PLAN_LIMITS.get(plan)
    if not plan_data:
        return None

    base_price = float(plan_data.get('price', 0) or 0)
    if base_price <= 0:
        return None

    if billing_cycle == 'annual':
        # Annual discount (~17%)
        return round((base_price * 12) * 0.83, 2)
    return round(base_price, 2)

def _managed_tenant_for_current_user():
    tenant = Tenant.query.filter_by(owner_id=current_user.id).first()
    if tenant:
        return tenant
    if current_user.tenant_id:
        return Tenant.query.get(current_user.tenant_id)
    return None

# -- BILLING DASHBOARD ----------------------------------------
@billing_bp.route('/')
@login_required
def dashboard():
    if not (current_user.can_manage_tenant() or current_user.is_admin()):
        flash('Billing access required.', 'danger')
        return redirect(url_for('main.index'))

    tenant = _managed_tenant_for_current_user()
    if not tenant:
        if current_user.is_admin():
            return redirect(url_for('billing.pending_requests'))
        onboarding_tenant = SimpleNamespace(name='No Journal Yet', member_count=0)
        onboarding_sub = Subscription(
            plan='free',
            status='inactive',
            amount=0.0,
            billing_cycle='monthly',
            currency=_app_currency(),
            started_at=datetime.utcnow(),
        )
        return render_template(
            'billing/dashboard.html',
            user=current_user, tenant=onboarding_tenant, sub=onboarding_sub, limits=onboarding_sub.limits,
            article_count=0, member_count=0,
            art_pct=0, mem_pct=0, plans=Subscription.PLAN_LIMITS,
            razorpay_key_id=(current_app.config.get('RAZORPAY_KEY_ID') or '').strip(),
            razorpay_currency=_app_currency(),
            billing_locked=True,
        )
    sub = get_or_create_subscription(tenant.id)
    article_count = Article.query.filter_by(tenant_id=tenant.id).count()
    member_count  = tenant.member_count
    limits        = sub.limits
    art_limit = limits['articles']
    art_pct   = 0 if art_limit == -1 else min(100, int(article_count / art_limit * 100))
    mem_limit = limits['members']
    mem_pct   = 0 if mem_limit == -1 else min(100, int(member_count / mem_limit * 100))
    return render_template(
        'billing/dashboard.html',
        user=current_user, tenant=tenant, sub=sub, limits=limits,
        article_count=article_count, member_count=member_count,
        art_pct=art_pct, mem_pct=mem_pct, plans=Subscription.PLAN_LIMITS,
        razorpay_key_id=(current_app.config.get('RAZORPAY_KEY_ID') or '').strip(),
        razorpay_currency=_app_currency(),
        billing_locked=False,
    )

# -- UPGRADE --------------------------------------------------
@billing_bp.route('/upgrade/<plan>', methods=['POST'])
@login_required
@tenant_owner_required
def upgrade(plan):
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('No journal found.', 'danger')
        return redirect(url_for('billing.dashboard'))
    allowed_plans = ['free', 'pro', 'enterprise']
    if plan not in allowed_plans:
        flash('Invalid plan.', 'danger')
        return redirect(url_for('billing.dashboard'))
    sub = get_or_create_subscription(tenant.id)
    if sub.plan == plan:
        flash(f'You are already on the {plan.title()} plan.', 'info')
        return redirect(url_for('billing.dashboard'))
    if plan != 'free':
        flash('Complete payment via Razorpay checkout to upgrade this plan.', 'warning')
        return redirect(url_for('billing.dashboard'))
    old_plan   = sub.plan
    sub.plan   = plan
    sub.status = 'active'
    sub.amount = Subscription.PLAN_LIMITS[plan]['price']
    if plan != 'free':
        sub.expires_at    = datetime.utcnow() + timedelta(days=30)
        sub.trial_ends_at = datetime.utcnow() + timedelta(days=14)
    tenant.plan = plan
    db.session.commit()
    flash(
        f'Successfully upgraded from {old_plan.title()} to {plan.title()}! '
        f'{"14-day free trial activated." if plan != "free" else ""}',
        'success'
    )
    return redirect(url_for('billing.dashboard'))

# -- RAZORPAY CREATE ORDER ------------------------------------
@billing_bp.route('/create-order', methods=['POST'])
@login_required
@tenant_owner_required
def create_order():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        return jsonify({'ok': False, 'message': 'No journal found for this account.'}), 400

    payload = request.get_json(silent=True) or {}
    plan = (payload.get('plan') or '').strip().lower()
    billing_cycle = (payload.get('billing_cycle') or 'monthly').strip().lower()
    if billing_cycle not in ['monthly', 'annual']:
        billing_cycle = 'monthly'

    if plan not in ['pro']:
        return jsonify({'ok': False, 'message': 'This plan cannot be purchased online.'}), 400

    amount = _resolve_plan_amount(plan, billing_cycle)
    if amount is None or amount <= 0:
        return jsonify({'ok': False, 'message': 'Invalid plan pricing.'}), 400

    try:
        currency = _app_currency()
        receipt = f'sub_{tenant.id}_{int(datetime.utcnow().timestamp())}'
        order_data = _create_razorpay_order(
            amount_paise=int(amount * 100),
            currency=currency,
            receipt=receipt,
            notes={
                'tenant_id': str(tenant.id),
                'user_id': str(current_user.id),
                'plan': plan,
                'billing_cycle': billing_cycle,
            },
        )
        key_id = order_data['key_id']
        order = order_data['order']
    except Exception as exc:
        return jsonify({'ok': False, 'message': f'Could not create payment order: {exc}'}), 500

    return jsonify({
        'ok': True,
        'key_id': key_id,
        'order_id': order.get('id'),
        'amount': int(amount * 100),
        'currency': currency,
        'plan': plan,
        'billing_cycle': billing_cycle,
        'tenant_name': tenant.name,
        'user_name': current_user.full_name,
        'user_email': current_user.email,
    })

# -- RAZORPAY VERIFY PAYMENT ----------------------------------
@billing_bp.route('/verify-payment', methods=['POST'])
@login_required
@tenant_owner_required
def verify_payment():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        return jsonify({'ok': False, 'message': 'No journal found for this account.'}), 400

    payload = request.get_json(silent=True) or {}
    plan = (payload.get('plan') or '').strip().lower()
    billing_cycle = (payload.get('billing_cycle') or 'monthly').strip().lower()
    if billing_cycle not in ['monthly', 'annual']:
        billing_cycle = 'monthly'

    payment_id = (payload.get('razorpay_payment_id') or '').strip()
    order_id = (payload.get('razorpay_order_id') or '').strip()
    signature = (payload.get('razorpay_signature') or '').strip()
    if not plan or not payment_id or not order_id or not signature:
        return jsonify({'ok': False, 'message': 'Missing payment verification fields.'}), 400

    amount = _resolve_plan_amount(plan, billing_cycle)
    if amount is None or amount <= 0:
        return jsonify({'ok': False, 'message': 'Invalid plan or pricing.'}), 400

    if not _verify_razorpay_signature(order_id, payment_id, signature):
        return jsonify({'ok': False, 'message': 'Payment signature verification failed.'}), 400

    sub = get_or_create_subscription(tenant.id)
    now = datetime.utcnow()
    sub.plan = plan
    sub.status = 'active'
    sub.amount = amount
    sub.currency = _app_currency()
    sub.billing_cycle = billing_cycle
    sub.started_at = now
    sub.cancelled_at = None
    sub.trial_ends_at = None
    sub.expires_at = now + (timedelta(days=365) if billing_cycle == 'annual' else timedelta(days=30))
    tenant.plan = plan

    txn = Transaction(
        tenant_id=tenant.id,
        subscription_id=sub.id,
        amount=amount,
        currency=sub.currency,
        status='completed',
        payment_method='razorpay',
        plan=plan,
        reference_id=payment_id,
        notes=f'order_id={order_id};signature={signature};cycle={billing_cycle}',
        approved_by_id=current_user.id,
        approved_at=now,
    )
    db.session.add(txn)
    db.session.commit()

    flash('Payment successful. Subscription activated.', 'success')
    return jsonify({'ok': True, 'redirect_url': url_for('billing.dashboard')})

# -- RAZORPAY FAILURE LOG -------------------------------------
@billing_bp.route('/payment-failed', methods=['POST'])
@login_required
@tenant_owner_required
def payment_failed():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        return jsonify({'ok': False, 'message': 'No journal found for this account.'}), 400

    payload = request.get_json(silent=True) or {}
    plan = (payload.get('plan') or '').strip().lower() or None
    cycle = (payload.get('billing_cycle') or 'monthly').strip().lower()
    if cycle not in ['monthly', 'annual']:
        cycle = 'monthly'
    order_id = (payload.get('razorpay_order_id') or '').strip()
    payment_id = (payload.get('razorpay_payment_id') or '').strip()
    error_message = (
        (payload.get('error', {}).get('description') if isinstance(payload.get('error'), dict) else None)
        or (payload.get('error') or '')
    )

    sub = get_or_create_subscription(tenant.id)
    txn = Transaction(
        tenant_id=tenant.id,
        subscription_id=sub.id,
        amount=_resolve_plan_amount(plan, cycle) or 0,
        currency=_app_currency(),
        status='failed',
        payment_method='razorpay',
        plan=plan,
        reference_id=payment_id or order_id or None,
        notes=f'order_id={order_id};error={error_message}',
    )
    db.session.add(txn)
    db.session.commit()
    return jsonify({'ok': True})

# -- CANCEL ---------------------------------------------------
@billing_bp.route('/cancel', methods=['POST'])
@login_required
@tenant_owner_required
def cancel():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        return redirect(url_for('billing.dashboard'))
    sub = get_or_create_subscription(tenant.id)
    if sub.plan == 'free':
        flash('You are already on the free plan.', 'info')
        return redirect(url_for('billing.dashboard'))
    sub.status       = 'cancelled'
    sub.cancelled_at = datetime.utcnow()
    sub.plan         = 'free'
    sub.amount       = 0.0
    tenant.plan      = 'free'
    db.session.commit()
    flash('Subscription cancelled. You have been moved to the Free plan.', 'info')
    return redirect(url_for('billing.dashboard'))

# -- PLANS (public) -------------------------------------------
@billing_bp.route('/plans')
def plans():
    return render_template('billing/plans.html', plans=Subscription.PLAN_LIMITS)

# -- SEND RENEWAL EMAIL ---------------------------------------
@billing_bp.route('/send-renewal-email', methods=['POST'])
@login_required
def send_renewal_email():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('No journal found.', 'error')
        return redirect(url_for('billing.dashboard'))
    subscription = get_or_create_subscription(tenant.id)
    from app.utils.email import send_subscription_renewal
    success, error = send_subscription_renewal(current_user, subscription)
    if success:
        flash('\u2705 Renewal reminder sent!', 'success')
    else:
        flash(f'\u274c Failed: {error}', 'error')
    return redirect(url_for('billing.dashboard'))

# -- TEST EMAILS ----------------------------------------------
@billing_bp.route('/test-email/<email_type>')
@login_required
def test_email(email_type):
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        return "No journal found.", 400
    subscription = get_or_create_subscription(tenant.id)
    from app.utils.email import send_subscription_renewal, send_subscription_expired, send_expiring_soon
    if email_type == 'renewal':
        success, error = send_subscription_renewal(current_user, subscription)
    elif email_type == 'expired':
        success, error = send_subscription_expired(current_user, subscription)
    elif email_type == 'expiring7':
        success, error = send_expiring_soon(current_user, subscription, days_left=7)
    elif email_type == 'expiring3':
        success, error = send_expiring_soon(current_user, subscription, days_left=3)
    elif email_type == 'expiring1':
        success, error = send_expiring_soon(current_user, subscription, days_left=1)
    else:
        return "Unknown email type.", 400
    return f"\u2705 Sent to {current_user.email}!" if success else f"\u274c Failed: {error}", 500

# -- TRANSACTIONS ---------------------------------------------
@billing_bp.route('/transactions')
@login_required
@tenant_owner_required
def transactions():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    sub = get_or_create_subscription(tenant.id)
    status_filter = request.args.get('status', '')
    method_filter = request.args.get('method', '')
    query = Transaction.query.filter_by(tenant_id=tenant.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if method_filter:
        query = query.filter_by(payment_method=method_filter)
    all_txns      = query.order_by(Transaction.created_at.desc()).all()
    completed_txns = Transaction.query.filter_by(tenant_id=tenant.id, status='completed').all()
    total_paid    = sum(t.amount for t in completed_txns)
    pending_count = Transaction.query.filter_by(tenant_id=tenant.id, status='pending').count()
    failed_count  = Transaction.query.filter_by(tenant_id=tenant.id, status='failed').count()
    return render_template(
        'billing/transactions.html',
        user=current_user, tenant=tenant, sub=sub,
        transactions=all_txns, total_paid=total_paid,
        pending_count=pending_count, failed_count=failed_count,
        total_count=len(all_txns),
        status_filter=status_filter, method_filter=method_filter,
    )

# -- SETTINGS -------------------------------------------------
@billing_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@tenant_owner_required
def settings():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    sub = get_or_create_subscription(tenant.id)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_billing_cycle':
            new_cycle = request.form.get('billing_cycle')
            if new_cycle in ['monthly', 'annual']:
                sub.billing_cycle = new_cycle
                db.session.commit()
                flash('Billing cycle updated.', 'success')
        elif action == 'update_currency':
            sub.currency = _app_currency()
            db.session.commit()
            flash('Currency updated to INR.', 'success')
        return redirect(url_for('billing.settings'))
    return render_template(
        'billing/settings.html',
        user=current_user, tenant=tenant, sub=sub, limits=sub.limits,
    )

# -- OFFLINE PAYMENTS -----------------------------------------
@billing_bp.route('/offline-payments', methods=['GET', 'POST'])
@login_required
@tenant_owner_required
def offline_payments():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    sub = get_or_create_subscription(tenant.id)
    if request.method == 'POST':
        try:
            txn = Transaction(
                tenant_id      = tenant.id,
                subscription_id= sub.id,
                amount         = float(request.form.get('amount', 0)),
                currency       = sub.currency,
                status         = 'pending',
                payment_method = request.form.get('payment_method', 'cash'),
                plan           = request.form.get('plan', sub.plan),
                reference_id   = request.form.get('reference_id', ''),
                notes          = request.form.get('notes', ''),
            )
            db.session.add(txn)
            db.session.commit()
            flash('Payment submitted. Awaiting admin approval.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('billing.offline_payments'))
    offline_txns = Transaction.query.filter_by(tenant_id=tenant.id).filter(
        Transaction.payment_method.in_(['cash', 'bank_transfer', 'cheque', 'upi'])
    ).order_by(Transaction.created_at.desc()).all()
    return render_template(
        'billing/offline_payments.html',
        user=current_user, tenant=tenant, sub=sub,
        transactions=offline_txns, plans=Subscription.PLAN_LIMITS,
    )

# -- CUSTOM DOMAIN --------------------------------------------
@billing_bp.route('/custom-domain', methods=['GET', 'POST'])
@login_required
@tenant_owner_required
def custom_domain():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    sub = get_or_create_subscription(tenant.id)
    if not sub.limits.get('custom_domain'):
        flash('Custom domain requires a Pro or Enterprise plan.', 'warning')
        return redirect(url_for('billing.dashboard'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'set_domain':
            domain = request.form.get('domain', '').strip().lower()
            if domain and '.' in domain and len(domain) > 4:
                tenant.custom_domain = domain
                db.session.commit()
                flash(f'Custom domain set to {domain}.', 'success')
            else:
                flash('Invalid domain. Use something like journal.yoursite.com', 'danger')
        elif action == 'remove_domain':
            tenant.custom_domain = None
            db.session.commit()
            flash('Custom domain removed.', 'info')
        return redirect(url_for('billing.custom_domain'))
    return render_template(
        'billing/custom_domain.html',
        user=current_user, tenant=tenant, sub=sub,
    )

# PAYMENT REQUESTS
# FIX: Super admin now sees ALL transactions (Razorpay online
# + offline cash/UPI/etc). Tenant owners still see only their
# own offline (manual) payment transactions.

@billing_bp.route('/pending-requests')
@login_required
def pending_requests():
    if not (current_user.is_admin() or current_user.is_tenant_owner()):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    OFFLINE_METHODS = ['cash', 'bank_transfer', 'cheque', 'upi']
    search        = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'pending').strip()
    # 'online' | 'offline' | '' (all) — only meaningful for super admins
    method_filter = request.args.get('method', '').strip().lower()

    is_super_admin = current_user.is_admin()

    if is_super_admin:
        # Super admin sees every transaction on the platform (all payment methods)
        base_q = Transaction.query
    else:
        # Tenant owner sees only their own offline (manual) payment transactions
        tenant = _managed_tenant_for_current_user()
        if not tenant:
            flash('Create a journal first.', 'warning')
            return redirect(url_for('tenants.create_journal'))
        base_q = Transaction.query.filter(
            Transaction.tenant_id == tenant.id,
            Transaction.payment_method.in_(OFFLINE_METHODS)
        )

    # Stats counters (computed on the full scoped base before extra list filters)
    total_pending  = base_q.filter(Transaction.status == 'pending').count()
    total_approved = base_q.filter(Transaction.status == 'completed').count()
    total_rejected = base_q.filter(Transaction.status == 'failed').count()

    # Apply status, optional method, and search filters for the displayed list
    query = base_q
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    if is_super_admin and method_filter == 'offline':
        query = query.filter(Transaction.payment_method.in_(OFFLINE_METHODS))
    elif is_super_admin and method_filter == 'online':
        query = query.filter(~Transaction.payment_method.in_(OFFLINE_METHODS))
    if search:
        query = query.filter(
            Transaction.reference_id.ilike(f'%{search}%') |
            Transaction.notes.ilike(f'%{search}%')
        )

    pending_txns = query.order_by(Transaction.created_at.desc()).all()

    return render_template(
        'billing/pending_requests.html',
        user=current_user, transactions=pending_txns,
        total_pending=total_pending, total_approved=total_approved,
        total_rejected=total_rejected,
        status_filter=status_filter, search=search,
        method_filter=method_filter,
        is_super_admin=is_super_admin,
    )

@billing_bp.route('/approve-payment/<int:txn_id>', methods=['POST'])
@login_required
def approve_payment(txn_id):
    if not (current_user.is_admin() or current_user.is_tenant_owner()):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    txn = Transaction.query.get_or_404(txn_id)
    txn.status         = 'completed'
    txn.approved_by_id = current_user.id
    txn.approved_at    = datetime.utcnow()
    sub = get_or_create_subscription(txn.tenant_id)
    if txn.plan and txn.plan in Subscription.PLAN_LIMITS:
        sub.plan       = txn.plan
        sub.status     = 'active'
        sub.amount     = txn.amount
        sub.expires_at = datetime.utcnow() + timedelta(days=30)
        t = Tenant.query.get(txn.tenant_id)
        if t:
            t.plan = txn.plan
    db.session.commit()
    flash('Payment approved and subscription activated.', 'success')
    return redirect(url_for('billing.pending_requests'))

@billing_bp.route('/reject-payment/<int:txn_id>', methods=['POST'])
@login_required
def reject_payment(txn_id):
    if not (current_user.is_admin() or current_user.is_tenant_owner()):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    txn        = Transaction.query.get_or_404(txn_id)
    txn.status = 'failed'
    db.session.commit()
    flash('Payment rejected.', 'info')
    return redirect(url_for('billing.pending_requests'))
