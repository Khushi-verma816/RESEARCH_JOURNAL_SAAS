from flask_mail import Message
from app.core.extensions import mail

def send_email(to, subject, body_html):
    try:
        msg = Message(subject=subject, recipients=[to], html=body_html)
        mail.send(msg)
        print(f'✅ Email sent successfully to {to}')
        return True
    except Exception as e:
        print(f'❌ Email error: {type(e).__name__}: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

# RENEWAL REMINDER  (called by check_subscriptions.py)

def send_renewal_reminder(user, tenant, sub, days_remaining):
    """Send plan renewal reminder email (7 / 3 / 1 days before expiry)."""
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px 24px">
      <div style="background:linear-gradient(135deg,#0272c6,#38adf8);padding:24px;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:#fff;font-size:1.4rem;margin:0">🔔 Your Plan Expires Soon</h1>
      </div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;padding:28px">
        <p style="color:#334155">Hi <strong>{user.first_name}</strong>,</p>
        <p style="color:#64748b">Your <strong style="color:#0272c6">{sub.plan.title()} Plan</strong> for
          <strong>{tenant.name}</strong> expires in
          <strong style="color:#e53e3e">{days_remaining} day{"s" if days_remaining != 1 else ""}</strong>.</p>
        <div style="background:#fef9c3;border:1px solid #fde047;border-radius:8px;padding:16px;margin:20px 0">
          <p style="color:#713f12;margin:0;font-size:.9rem">⚠️ Renew now to avoid losing access to your premium features.</p>
        </div>
        <table style="width:100%;border-collapse:collapse;margin:16px 0">
          <tr style="background:#f8fafc">
            <td style="padding:10px 14px;color:#64748b;font-size:.85rem;border:1px solid #e2e8f0">Current Plan</td>
            <td style="padding:10px 14px;color:#334155;font-weight:600;font-size:.85rem;border:1px solid #e2e8f0">{sub.plan.title()}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;color:#64748b;font-size:.85rem;border:1px solid #e2e8f0">Amount</td>
            <td style="padding:10px 14px;color:#334155;font-weight:600;font-size:.85rem;border:1px solid #e2e8f0">${sub.amount}/month</td>
          </tr>
          <tr style="background:#f8fafc">
            <td style="padding:10px 14px;color:#64748b;font-size:.85rem;border:1px solid #e2e8f0">Expires</td>
            <td style="padding:10px 14px;color:#e53e3e;font-weight:600;font-size:.85rem;border:1px solid #e2e8f0">{sub.expires_at.strftime('%d %b %Y')}</td>
          </tr>
        </table>
        <div style="text-align:center;margin:28px 0">
          <a href="http://localhost:5000/billing" style="background:#0272c6;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.95rem">Renew My Plan →</a>
        </div>
        <p style="color:#94a3b8;font-size:.8rem;text-align:center">Research Hub · Academic Publishing Platform</p>
      </div>
    </div>
    """
    return send_email(
        user.email,
        f'🔔 Your {sub.plan.title()} Plan expires in {days_remaining} days – Research Hub',
        body
    )

# PLAN EXPIRED  (called by check_subscriptions.py)

def send_plan_expired(user, tenant, plan):
    """Send plan expired notification — user downgraded to Free."""
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px 24px">
      <div style="background:linear-gradient(135deg,#dc2626,#ef4444);padding:24px;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:#fff;font-size:1.4rem;margin:0">❌ Your Plan Has Expired</h1>
      </div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;padding:28px">
        <p style="color:#334155">Hi <strong>{user.first_name}</strong>,</p>
        <p style="color:#64748b">Your <strong>{plan.title()} Plan</strong> for <strong>{tenant.name}</strong>
          has expired. You have been moved to the <strong>Free plan</strong>.</p>
        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px;margin:20px 0">
          <p style="color:#991b1b;margin:0;font-size:.9rem">Reactivate now to restore your premium features.</p>
        </div>
        <ul style="color:#64748b;line-height:2;font-size:.9rem">
          <li>❌ Unlimited articles (now limited to 10)</li>
          <li>❌ Unlimited team members (now limited to 3)</li>
          <li>❌ Custom domain</li>
          <li>❌ Analytics dashboard</li>
          <li>❌ Video conferencing</li>
          <li>❌ Full AI suite (now limited to 5 requests)</li>
        </ul>
        <div style="text-align:center;margin:28px 0">
          <a href="http://localhost:5000/billing" style="background:#0272c6;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.95rem">Reactivate Now →</a>
        </div>
        <p style="color:#94a3b8;font-size:.8rem;text-align:center">Research Hub · Academic Publishing Platform</p>
      </div>
    </div>
    """
    return send_email(
        user.email,
        f'❌ Your {plan.title()} Plan has expired – Research Hub',
        body
    )

# UPGRADE CONFIRMATION

def send_upgrade_confirmation(user, tenant, plan):
    """Send upgrade confirmation email after plan change."""
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px 24px">
      <div style="background:linear-gradient(135deg,#0272c6,#38adf8);padding:24px;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:#fff;font-size:1.4rem;margin:0">🎉 Welcome to {plan.title()} Plan!</h1>
      </div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;padding:28px">
        <p style="color:#334155">Hi <strong>{user.first_name}</strong>,</p>
        <p style="color:#64748b">Your journal <strong>{tenant.name}</strong> has been upgraded to the
          <strong style="color:#0272c6">{plan.title()} Plan</strong>. 🎉</p>
        <div style="background:#ecfdf5;border:1px solid #86efac;border-radius:8px;padding:16px;margin:20px 0">
          <p style="color:#166534;margin:0;font-size:.9rem">✅ Your new features are now active and ready to use.</p>
        </div>
        <div style="text-align:center;margin:28px 0">
          <a href="http://localhost:5000/admin/dashboard" style="background:#0272c6;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600">Go to Dashboard →</a>
        </div>
        <p style="color:#94a3b8;font-size:.8rem;text-align:center">Research Hub · Academic Publishing Platform</p>
      </div>
    </div>
    """
    return send_email(
        user.email,
        f'🎉 Upgraded to {plan.title()} Plan – Research Hub',
        body
    )

# SUBSCRIPTION CANCELLED

def send_subscription_cancelled(user, tenant):
    """Send cancellation confirmation email."""
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px 24px">
      <div style="background:linear-gradient(135deg,#0272c6,#38adf8);padding:24px;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:#fff;font-size:1.4rem;margin:0">Subscription Cancelled</h1>
      </div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;padding:28px">
        <p style="color:#334155">Hi <strong>{user.first_name}</strong>,</p>
        <p style="color:#64748b">Your subscription for <strong>{tenant.name}</strong> has been cancelled.
          You have been moved to the <strong>Free plan</strong>.</p>
        <p style="color:#64748b">You can upgrade again anytime from your billing dashboard.</p>
        <div style="text-align:center;margin:28px 0">
          <a href="http://localhost:5000/billing" style="background:#0272c6;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600">View Billing →</a>
        </div>
        <p style="color:#94a3b8;font-size:.8rem;text-align:center">Research Hub · Academic Publishing Platform</p>
      </div>
    </div>
    """
    return send_email(
        user.email,
        'Subscription Cancelled – Research Hub',
        body
    )

# TRIAL EXPIRY WARNING

def send_trial_expiry_warning(user, tenant, days_remaining):
    """Send trial expiry warning email."""
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px 24px">
      <div style="background:linear-gradient(135deg,#0272c6,#38adf8);padding:24px;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:#fff;font-size:1.4rem;margin:0">⏳ Your Trial is Ending Soon</h1>
      </div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;padding:28px">
        <p style="color:#334155">Hi <strong>{user.first_name}</strong>,</p>
        <p style="color:#64748b">Your free trial for <strong>{tenant.name}</strong> expires in
          <strong style="color:#e53e3e">{days_remaining} day{"s" if days_remaining != 1 else ""}</strong>.</p>
        <div style="background:#fef9c3;border:1px solid #fde047;border-radius:8px;padding:16px;margin:20px 0">
          <p style="color:#713f12;margin:0;font-size:.9rem">⚠️ After your trial ends you will be moved to the Free plan with limited features.</p>
        </div>
        <p style="color:#64748b">Upgrade now to keep access to:</p>
        <ul style="color:#64748b;line-height:2">
          <li>✅ Unlimited articles</li>
          <li>✅ Unlimited team members</li>
          <li>✅ Custom domain</li>
          <li>✅ Analytics dashboard</li>
          <li>✅ Video conferencing</li>
          <li>✅ Full AI suite</li>
        </ul>
        <div style="text-align:center;margin:28px 0">
          <a href="http://localhost:5000/billing" style="background:#0272c6;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.95rem">Upgrade My Plan →</a>
        </div>
        <p style="color:#94a3b8;font-size:.8rem;text-align:center">Research Hub · Academic Publishing Platform</p>
      </div>
    </div>
    """
    return send_email(
        user.email,
        f'⏳ Your trial expires in {days_remaining} days – Research Hub',
        body
    )

# SUBSCRIPTION RENEWAL (rich HTML template)

def send_subscription_renewal(user, subscription):
    """Send subscription renewal reminder email (rich HTML version)."""
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 600px; margin: 40px auto; }}
  .card {{ background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header {{ background: linear-gradient(135deg, #0ea5e9, #6366f1); padding: 32px; text-align: center; }}
  .header-icon {{ font-size: 2.5rem; margin-bottom: 10px; }}
  .header-title {{ color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0; }}
  .header-sub {{ color: rgba(255,255,255,0.85); font-size: 0.9rem; margin-top: 6px; }}
  .body {{ padding: 32px; }}
  .greeting {{ font-size: 1rem; color: #1e293b; margin-bottom: 16px; font-weight: 600; }}
  .message {{ font-size: 0.9rem; color: #475569; line-height: 1.7; margin-bottom: 24px; }}
  .plan-box {{ background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px; padding: 20px; margin-bottom: 24px; }}
  .plan-title {{ font-size: 1rem; font-weight: 700; color: #0369a1; margin-bottom: 14px; }}
  .plan-table {{ width: 100%; border-collapse: collapse; }}
  .plan-table td {{ padding: 6px 0; font-size: 0.84rem; }}
  .plan-label {{ color: #64748b; }}
  .plan-value {{ color: #1e293b; font-weight: 600; text-align: right; }}
  .expire-value {{ color: #dc2626; font-weight: 700; text-align: right; }}
  .btn-wrap {{ text-align: center; margin-bottom: 24px; }}
  .btn {{ display: inline-block; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: #ffffff !important; text-decoration: none; padding: 13px 32px; border-radius: 8px; font-weight: 700; font-size: 0.95rem; }}
  .divider {{ border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }}
  .footer {{ text-align: center; padding: 20px 32px; background: #f8fafc; }}
  .footer-text {{ font-size: 0.78rem; color: #94a3b8; line-height: 1.8; }}
  .footer-text a {{ color: #0ea5e9; text-decoration: none; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="card">
    <div class="header">
      <div class="header-icon">🔔</div>
      <div class="header-title">Subscription Renewal Reminder</div>
      <div class="header-sub">Research Hub · Academic Publishing Platform</div>
    </div>
    <div class="body">
      <div class="greeting">Hello {user.full_name},</div>
      <div class="message">
        Your <strong>{subscription.plan.title()} Plan</strong> subscription is expiring soon.
        Renew now to keep uninterrupted access to all your research tools,
        AI assistant, video rooms, and publishing features.
      </div>
      <div class="plan-box">
        <div class="plan-title">📋 Your Subscription Details</div>
        <table class="plan-table">
          <tr><td class="plan-label">Plan</td><td class="plan-value">{subscription.plan.title()} Plan</td></tr>
          <tr><td class="plan-label">Status</td><td class="plan-value">{subscription.status.title()}</td></tr>
          <tr>
            <td class="plan-label">Expires On</td>
            <td class="expire-value">{subscription.expires_at.strftime('%d %B %Y') if subscription.expires_at else 'N/A'}</td>
          </tr>
        </table>
      </div>
      <div class="btn-wrap">
        <a href="http://127.0.0.1:5000/billing" class="btn">🔄 Renew My Subscription</a>
      </div>
      <hr class="divider">
      <div class="message" style="font-size:0.83rem;margin-bottom:0">
        If you have any questions, reply to this email or visit your billing dashboard. We're happy to help!
      </div>
    </div>
    <div class="footer">
      <div class="footer-text">
        © 2026 Research Hub · Academic Publishing Platform<br>
        <a href="http://127.0.0.1:5000/billing">Manage Subscription</a>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""
    msg = Message(
        subject=f"⏰ Your Research Hub {subscription.plan.title()} Plan Expires Soon",
        recipients=[user.email],
        html=html_body
    )
    try:
        mail.send(msg)
        return True, None
    except Exception as e:
        return False, str(e)

# SUBSCRIPTION EXPIRED (rich HTML template)

def send_subscription_expired(user, subscription):
    """Send email when subscription has expired."""
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 600px; margin: 40px auto; }}
  .card {{ background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header {{ background: linear-gradient(135deg, #ef4444, #dc2626); padding: 32px; text-align: center; }}
  .header-title {{ color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0; }}
  .header-sub {{ color: rgba(255,255,255,0.85); font-size: 0.9rem; margin-top: 6px; }}
  .body {{ padding: 32px; }}
  .greeting {{ font-size: 1rem; color: #1e293b; margin-bottom: 16px; font-weight: 600; }}
  .message {{ font-size: 0.9rem; color: #475569; line-height: 1.7; margin-bottom: 24px; }}
  .alert-box {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px; padding: 20px; margin-bottom: 24px; }}
  .alert-title {{ font-size: 1rem; font-weight: 700; color: #dc2626; margin-bottom: 14px; }}
  .plan-table {{ width: 100%; border-collapse: collapse; }}
  .plan-table td {{ padding: 6px 0; font-size: 0.84rem; }}
  .plan-label {{ color: #64748b; }}
  .plan-value {{ color: #1e293b; font-weight: 600; text-align: right; }}
  .expired-value {{ color: #dc2626; font-weight: 700; text-align: right; }}
  .btn-wrap {{ text-align: center; margin-bottom: 24px; }}
  .btn {{ display: inline-block; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: #ffffff !important; text-decoration: none; padding: 13px 32px; border-radius: 8px; font-weight: 700; font-size: 0.95rem; }}
  .footer {{ text-align: center; padding: 20px 32px; background: #f8fafc; }}
  .footer-text {{ font-size: 0.78rem; color: #94a3b8; line-height: 1.8; }}
  .footer-text a {{ color: #0ea5e9; text-decoration: none; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="card">
    <div class="header">
      <div class="header-title">❌ Your Subscription Has Expired</div>
      <div class="header-sub">Research Hub · Academic Publishing Platform</div>
    </div>
    <div class="body">
      <div class="greeting">Hello {user.full_name},</div>
      <div class="message">
        Unfortunately, your <strong>{subscription.plan.title()} Plan</strong> subscription
        has expired. Renew now to restore full access instantly.
      </div>
      <div class="alert-box">
        <div class="alert-title">📋 Expired Subscription Details</div>
        <table class="plan-table">
          <tr><td class="plan-label">Plan</td><td class="plan-value">{subscription.plan.title()} Plan</td></tr>
          <tr><td class="plan-label">Status</td><td class="expired-value">❌ Expired</td></tr>
          <tr>
            <td class="plan-label">Expired On</td>
            <td class="expired-value">{subscription.expires_at.strftime('%d %B %Y') if subscription.expires_at else 'N/A'}</td>
          </tr>
        </table>
      </div>
      <div class="btn-wrap">
        <a href="http://127.0.0.1:5000/billing" class="btn">🔄 Renew Subscription Now</a>
      </div>
    </div>
    <div class="footer">
      <div class="footer-text">
        © 2026 Research Hub · Academic Publishing Platform<br>
        <a href="http://127.0.0.1:5000/billing">Renew Subscription</a>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""
    msg = Message(
        subject=f"❌ Your Research Hub {subscription.plan.title()} Plan Has Expired",
        recipients=[user.email],
        html=html_body
    )
    try:
        mail.send(msg)
        return True, None
    except Exception as e:
        return False, str(e)

# EXPIRING SOON (rich HTML template)

def send_expiring_soon(user, subscription, days_left):
    """Send email when subscription is expiring in X days."""
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 600px; margin: 40px auto; }}
  .card {{ background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header {{ background: linear-gradient(135deg, #f59e0b, #d97706); padding: 32px; text-align: center; }}
  .header-title {{ color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0; }}
  .header-sub {{ color: rgba(255,255,255,0.85); font-size: 0.9rem; margin-top: 6px; }}
  .body {{ padding: 32px; }}
  .greeting {{ font-size: 1rem; color: #1e293b; margin-bottom: 16px; font-weight: 600; }}
  .message {{ font-size: 0.9rem; color: #475569; line-height: 1.7; margin-bottom: 24px; }}
  .warning-box {{ background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px; padding: 20px; margin-bottom: 24px; }}
  .warning-title {{ font-size: 1rem; font-weight: 700; color: #d97706; margin-bottom: 14px; }}
  .days-badge {{ display: inline-block; background: #f59e0b; color: #fff; font-size: 1.8rem; font-weight: 800; padding: 10px 20px; border-radius: 10px; margin-bottom: 14px; }}
  .plan-table {{ width: 100%; border-collapse: collapse; }}
  .plan-table td {{ padding: 6px 0; font-size: 0.84rem; }}
  .plan-label {{ color: #64748b; }}
  .plan-value {{ color: #1e293b; font-weight: 600; text-align: right; }}
  .warn-value {{ color: #d97706; font-weight: 700; text-align: right; }}
  .btn-wrap {{ text-align: center; margin-bottom: 24px; }}
  .btn {{ display: inline-block; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: #ffffff !important; text-decoration: none; padding: 13px 32px; border-radius: 8px; font-weight: 700; font-size: 0.95rem; }}
  .footer {{ text-align: center; padding: 20px 32px; background: #f8fafc; }}
  .footer-text {{ font-size: 0.78rem; color: #94a3b8; line-height: 1.8; }}
  .footer-text a {{ color: #0ea5e9; text-decoration: none; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="card">
    <div class="header">
      <div class="header-title">⚠️ Subscription Expiring Soon</div>
      <div class="header-sub">Research Hub · Academic Publishing Platform</div>
    </div>
    <div class="body">
      <div class="greeting">Hello {user.full_name},</div>
      <div class="message">
        Your <strong>{subscription.plan.title()} Plan</strong> is expiring soon.
        Don't lose access to your research tools — renew before it's too late!
      </div>
      <div class="warning-box">
        <div class="warning-title">⏰ Time Remaining</div>
        <div class="days-badge">{days_left} days left</div>
        <table class="plan-table">
          <tr><td class="plan-label">Plan</td><td class="plan-value">{subscription.plan.title()} Plan</td></tr>
          <tr><td class="plan-label">Status</td><td class="warn-value">⚠️ Expiring Soon</td></tr>
          <tr>
            <td class="plan-label">Expires On</td>
            <td class="warn-value">{subscription.expires_at.strftime('%d %B %Y') if subscription.expires_at else 'N/A'}</td>
          </tr>
        </table>
      </div>
      <div class="btn-wrap">
        <a href="http://127.0.0.1:5000/billing" class="btn">🔄 Renew Now — Keep Access</a>
      </div>
    </div>
    <div class="footer">
      <div class="footer-text">
        © 2026 Research Hub · Academic Publishing Platform<br>
        <a href="http://127.0.0.1:5000/billing">Manage Subscription</a>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""
    msg = Message(
        subject=f"⚠️ Only {days_left} Days Left — Renew Your Research Hub Plan",
        recipients=[user.email],
        html=html_body
    )
    try:
        mail.send(msg)
        return True, None
    except Exception as e:
        return False, str(e)

# WELCOME EMAIL

def send_welcome_email(user):
    """Send welcome email on signup."""
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 600px; margin: 40px auto; }}
  .card {{ background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header {{ background: linear-gradient(135deg, #0ea5e9, #6366f1); padding: 32px; text-align: center; }}
  .header-title {{ color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0; }}
  .header-sub {{ color: rgba(255,255,255,0.85); font-size: 0.9rem; margin-top: 6px; }}
  .body {{ padding: 32px; }}
  .greeting {{ font-size: 1rem; color: #1e293b; margin-bottom: 16px; font-weight: 600; }}
  .message {{ font-size: 0.9rem; color: #475569; line-height: 1.7; margin-bottom: 24px; }}
  .btn-wrap {{ text-align: center; margin-bottom: 24px; }}
  .btn {{ display: inline-block; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: #ffffff !important; text-decoration: none; padding: 13px 32px; border-radius: 8px; font-weight: 700; font-size: 0.95rem; }}
  .footer {{ text-align: center; padding: 20px 32px; background: #f8fafc; }}
  .footer-text {{ font-size: 0.78rem; color: #94a3b8; line-height: 1.8; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="card">
    <div class="header">
      <div class="header-title">🎉 Welcome to Research Hub!</div>
      <div class="header-sub">Academic Publishing Platform</div>
    </div>
    <div class="body">
      <div class="greeting">Hello {user.full_name},</div>
      <div class="message">
        Welcome to Research Hub! Your account has been created successfully.<br><br>
        You can now submit articles, collaborate with your team, use AI tools,
        and manage your research journal — all in one place.
      </div>
      <div class="btn-wrap">
        <a href="http://127.0.0.1:5000/admin/dashboard" class="btn">🚀 Go to Dashboard</a>
      </div>
    </div>
    <div class="footer">
      <div class="footer-text">© 2026 Research Hub · Academic Publishing Platform</div>
    </div>
  </div>
</div>
</body>
</html>
"""
    msg = Message(
        subject="🎉 Welcome to Research Hub!",
        recipients=[user.email],
        html=html_body
    )
    try:
        mail.send(msg)
        return True, None
    except Exception as e:
        return False, str(e)