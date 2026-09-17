from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.common.decorators import company_member_required, manager_required

from .models import Subscription, SubscriptionPlan


@company_member_required
def plans_list_view(request):
    plans = SubscriptionPlan.objects.all()
    current_code = None
    if request.user.company_id:
        current_code = request.user.company.plan
    return render(
        request, "subscriptions/plans.html", {"plans": plans, "current_code": current_code}
    )


@company_member_required
def my_subscription_view(request):
    subscription = getattr(request.user, 'subscription', None)

    if not subscription or not subscription.is_active:
        messages.warning(request, "Sizda faol subscription mavjud emas.")
        return redirect('dashboard:dashboard')  

    return redirect('subscription_detail', pk=subscription.pk)

@manager_required
def upgrade_view(request, plan_code):
    company = request.user.company
    if company is None:
        messages.error(request, "You are not attached to a company.")
        return redirect("dashboard:dashboard")

    plan = get_object_or_404(SubscriptionPlan, code=plan_code)
    subscription, _ = Subscription.objects.get_or_create(
        company=company,
        defaults={"plan": SubscriptionPlan.objects.get(code="free")},
    )
    if request.method == "POST":
        subscription.plan = plan
        subscription.save(update_fields=["plan"])
        subscription.sync_company_plan()
        messages.success(request, f"Your company is now on the {plan.name} plan (mock billing — no real charge).")
        return redirect("subscriptions:mine")
    return render(request, "subscriptions/confirm_upgrade.html", {"plan": plan, "subscription": subscription})
