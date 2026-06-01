from flask import request, g

def detect_tenant():
    g.tenant = None
    try:
        from app.models.tenant import Tenant
        host = request.host
        tenant_param = request.args.get('tenant')
        if tenant_param:
            t = Tenant.query.filter_by(subdomain=tenant_param, is_active=True).first()
            if t:
                g.tenant = t
                return
        parts = host.split(':')[0].split('.')
        if len(parts) > 1 and parts[0] not in ('www', ''):
            t = Tenant.query.filter_by(subdomain=parts[0], is_active=True).first()
            if t:
                g.tenant = t
    except Exception:
        pass
