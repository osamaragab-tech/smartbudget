# transactions/views.py
from email.utils import parsedate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Transaction, Category
from django.shortcuts import get_object_or_404
from datetime import datetime





@login_required
def dashboard(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user).select_related('category')

     # ======================
    # Filtering logic
    # ======================
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    category_id = request.GET.get('category')
    type_filter = request.GET.get('type')

    if from_date:
        try:
            from_date_parsed = datetime.strptime(from_date, "%Y-%m-%d").date()
            transactions = transactions.filter(date__date__gte=from_date_parsed)
        except ValueError:
            pass  # تجاهل التاريخ لو فيه مشكلة في الفورمات

    if to_date:
        try:
            to_date_parsed = datetime.strptime(to_date, "%Y-%m-%d").date()
            transactions = transactions.filter(date__date__lte=to_date_parsed)
        except ValueError:
            pass

    if category_id and category_id != "":
        transactions = transactions.filter(category__id=category_id)
    if type_filter in ['income', 'expense']:
        if type_filter == 'income':
            transactions = transactions.filter(amount__gt=0)
        else:
            transactions = transactions.filter(amount__lt=0)

    # ======================
    # Stats
    # ======================
    # الحسابات الخاصة بالفلترة الحالية فقط
    income = transactions.filter(amount__gt=0).aggregate(total=Sum('amount'))['total'] or 0
    expenses = abs(transactions.filter(amount__lt=0).aggregate(total=Sum('amount'))['total'] or 0)
    balance = income - expenses

    # إجمالي جميع العمليات بعد الفلترة
    total_filtered = transactions.aggregate(total=Sum('amount'))['total'] or 0

    categories = Category.objects.filter(user=user)

    return render(request, 'transactions/dashboard.html', {
        'transactions': transactions.order_by('-date'),
        'income': income,
        'expenses': expenses,
        'balance': balance,
        'total_filtered': total_filtered,
        'categories': categories,
        'filters': {
            'from_date': from_date or '',
            'to_date': to_date or '',
            'category': category_id or '',
            'type': type_filter or '',
        }
    })
@login_required
def add_transaction(request):
    # احصل على فئات المستخدم لعرضها في الـ form
    user_categories = Category.objects.filter(user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        amount = float(request.POST.get('amount', '0') or 0)
        type_ = request.POST.get('type', 'income')  # 'income' or 'expense'
        # category can be an id (from select) or a new category name (from text input)
        category_input = request.POST.get('category_select') or request.POST.get('category_new')

        # normalise amount: expenses stored as negative
        if type_ == 'expense':
            amount = -abs(amount)
        else:
            amount = abs(amount)

        # Resolve category to a Category instance
        category_obj = None
        if category_input:
            # try interpret as id
            try:
                # if user sent an id value
                category_obj = Category.objects.get(id=int(category_input), user=request.user)
            except (ValueError, Category.DoesNotExist):
                # treat as name: get or create for this user and type
                category_name = category_input.strip()
                if category_name:
                    category_obj, created = Category.objects.get_or_create(
                        user=request.user,
                        name=category_name,
                        defaults={'type': type_}
                    )
                    # if existed but has different type, optionally update or keep existing type
                    if not created and category_obj.type != type_:
                        # keep existing type (or you could update it). We'll keep as-is.
                        pass

        # If still no category, fallback to a default category (optional)
        if category_obj is None:
            category_obj, _ = Category.objects.get_or_create(
                user=request.user,
                name='Uncategorized',
                defaults={'type': type_}
            )

        Transaction.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            category=category_obj
        )
        return redirect('dashboard')

    return render(request, 'transactions/add_transaction.html', {
        'categories': user_categories,
    })

    

@login_required
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    user_categories = Category.objects.filter(user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        amount = float(request.POST.get('amount', '0') or 0)
        type_ = request.POST.get('type', 'income')
        category_input = request.POST.get('category_select') or request.POST.get('category_new')

        if type_ == 'expense':
            amount = -abs(amount)
        else:
            amount = abs(amount)

        # resolve category similar to add
        category_obj = None
        if category_input:
            try:
                category_obj = Category.objects.get(id=int(category_input), user=request.user)
            except (ValueError, Category.DoesNotExist):
                category_name = category_input.strip()
                if category_name:
                    category_obj, created = Category.objects.get_or_create(
                        user=request.user,
                        name=category_name,
                        defaults={'type': type_}
                    )
                    if not created and category_obj.type != type_:
                        pass

        if category_obj is None:
            category_obj, _ = Category.objects.get_or_create(
                user=request.user,
                name='Uncategorized',
                defaults={'type': type_}
            )

        # save changes
        transaction.title = title
        transaction.amount = amount
        transaction.category = category_obj
        transaction.save()

        return redirect('dashboard')

    type_ = 'income' if transaction.amount > 0 else 'expense'
    return render(request, 'transactions/edit_transaction.html', {
        'transaction': transaction,
        'type': type_,
        'categories': user_categories,
    })


@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    transaction.delete()
    return redirect('dashboard')