import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from .models import JournalEntry, JournalEntryImage
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg
from django.db.models.functions import TruncHour, TruncDay, TruncMonth


@login_required
def journal_entry(request):
    if request.method == 'POST':
        print(request.POST)
        trade_date = request.POST.get('tradeDate')
        journal_text = request.POST.get('journalText')
        profit = request.POST.get('profit')
        symbol = request.POST.get('symbol')
        size = request.POST.get('size')
        # Create a new JournalEntry instance
        entry = JournalEntry(
            user=request.user,
            trade_date=trade_date,
            journal_text=journal_text,
            profit=Decimal(profit),
            symbol=symbol,
            size=Decimal(size),
        )
        entry.save()  # Save first to get an entry ID

        # Handle single image upload
        if 'imageUpload' in request.FILES:
            image = request.FILES['imageUpload']
            JournalEntryImage.objects.create(journal_entry=entry, image=image)

        # Handle additional image uploads (from dynamically added fields)
        if request.FILES.getlist('additionalImages'):
            for img in request.FILES.getlist('additionalImages'):
                JournalEntryImage.objects.create(journal_entry=entry, image=img)

        entry.save()
        return redirect('journal_list')  # Redirect to a list of journal entries

    return render(request, 'trades/journal_entry.html')


@login_required
def journal_detail(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    images = JournalEntryImage.objects.filter(journal_entry=entry)
    return render(request, 'trades/partials/journal_detail.html', {'entry': entry, 'images': images})


@login_required
def update_journal(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)

    if request.method == 'POST':
        trade_date = request.POST.get('trade_date')
        if trade_date:
            entry.trade_date = trade_date
        # Update journal entry text and other fields
        entry.journal_text = request.POST.get('journal_text')
        entry.profit = request.POST.get('profit')
        entry.symbol = request.POST.get('symbol')
        entry.size = request.POST.get('size')
        entry.save()

        # Handle image deletion
        if 'delete_images' in request.POST:
            for image_id in request.POST.getlist('delete_images'):
                image = JournalEntryImage.objects.get(id=image_id, journal_entry=entry)
                image.delete()  # This will trigger the custom delete method to remove the file

        # Handle new image uploads
        if request.FILES.getlist('additionalImages'):
            for img in request.FILES.getlist('additionalImages'):
                JournalEntryImage.objects.create(journal_entry=entry, image=img)

        # Return a JSON response to the AJAX call
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)


@login_required
def journal_list(request):
    if request.method == 'POST':
        # Handle creation, edit, or delete based on the form data
        if request.POST.get('create'):
            # Handle creation
            trade_date = request.POST.get('trade_date')
            journal_text = request.POST.get('journal_text')
            profit = request.POST.get('profit')
            symbol = request.POST.get('symbol')
            size = request.POST.get('size')

            # Create a new JournalEntry instance
            entry = JournalEntry(
                user=request.user,
                trade_date=trade_date,
                journal_text=journal_text,
                profit=Decimal(profit),
                symbol=symbol,
                size=Decimal(size),
            )
            entry.save()

            # Handle single image upload
            if 'imageUpload' in request.FILES:
                image = request.FILES['imageUpload']
                JournalEntryImage.objects.create(journal_entry=entry, image=image)

            # Handle additional image uploads (from dynamically added fields)
            if request.FILES.getlist('additionalImages'):
                for img in request.FILES.getlist('additionalImages'):
                    JournalEntryImage.objects.create(journal_entry=entry, image=img)

        elif request.POST.get('edit'):
            # Handle editing
            entry_id = request.POST.get('entry_id')
            entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)

            # Update the fields
            entry.trade_date = request.POST.get('trade_date')
            entry.journal_text = request.POST.get('journal_text')
            entry.profit = Decimal(request.POST.get('profit'))
            entry.symbol = request.POST.get('symbol')
            entry.size = Decimal(request.POST.get('size'))
            entry.save()

        elif request.POST.get('delete'):
            # Handle deleting
            entry_id = request.POST.get('entry_id')
            entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
            for image in entry.images.all():  # Assuming `related_name='images'` is set in the ForeignKey
                if image.image and os.path.isfile(image.image.path):
                    os.remove(image.image.path)
                image.delete()

            entry.delete()
            entries = JournalEntry.objects.filter(user=request.user).order_by('-trade_date')
            return render(request, 'trades/journal_list.html', {'entries': entries})
        # After processing creation, edit, or delete, return updated journal entries as HTML
        entries = JournalEntry.objects.filter(user=request.user).order_by('-trade_date')
        # Check if it's an AJAX request and return JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('trades/partials/journal_entries_list.html', {'entries': entries})
            return JsonResponse({'html': html})  # Ensure only JSON is returned
        else:
            # Redirect only for non-AJAX requests
            return redirect('journal_list')
    # Display all journal entries
    entries = JournalEntry.objects.filter(user=request.user).order_by('-trade_date')
    return render(request, 'trades/journal_list.html', {'entries': entries})


@login_required
def performance_analysis(request):
    user_entries = JournalEntry.objects.filter(user=request.user)

    # Profit performance
    profit_by_hour = user_entries.annotate(hour=TruncHour('trade_date')).values('hour').annotate(
        total_profit=Sum('profit')).order_by('hour')
    profit_by_day = user_entries.annotate(day=TruncDay('trade_date')).values('day').annotate(
        total_profit=Sum('profit')).order_by('day')
    profit_by_month = user_entries.annotate(month=TruncMonth('trade_date')).values('month').annotate(
        total_profit=Sum('profit')).order_by('month')

    # Lot size performance
    lot_size_by_hour = user_entries.annotate(hour=TruncHour('trade_date')).values('hour').annotate(
        avg_lot_size=Avg('size')).order_by('hour')
    lot_size_by_day = user_entries.annotate(day=TruncDay('trade_date')).values('day').annotate(
        avg_lot_size=Avg('size')).order_by('day')
    lot_size_by_month = user_entries.annotate(month=TruncMonth('trade_date')).values('month').annotate(
        avg_lot_size=Avg('size')).order_by('month')

    context = {
        'profit_by_hour': profit_by_hour,
        'profit_by_day': profit_by_day,
        'profit_by_month': profit_by_month,
        'lot_size_by_hour': lot_size_by_hour,
        'lot_size_by_day': lot_size_by_day,
        'lot_size_by_month': lot_size_by_month,
    }

    return render(request, 'trades/performance_analysis.html', context)
