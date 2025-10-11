# --- Deposit Submission Views ---
from .models import Deposit
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os


@login_required
@require_POST
def submit_usdt_deposit(request):
    """Handle USDT deposit form submission (AJAX, file upload)."""
    amount = request.POST.get("amount")
    tx_hash = request.POST.get("txHash")
    usdt_address = request.POST.get("usdtAddress")
    file = request.FILES.get("file")
    if not (amount and tx_hash and file):
        return JsonResponse({"success": False, "error": "All fields are required."})
    deposit = Deposit(
        user=request.user,
        method="usdt",
        amount=amount,
        tx_hash=tx_hash,
        usdt_address=usdt_address,
        status="pending",
    )
    if file:
        deposit.card_proof = file
    deposit.save()
    return JsonResponse(
        {
            "success": True,
            "message": "USDT deposit submitted. Pending admin verification.",
        }
    )


@login_required
@require_POST
def submit_giftcard_deposit(request):
    """Handle Gift Card deposit form submission (AJAX, file upload)."""
    amount = request.POST.get("amount")
    card_type = request.POST.get("type")
    card_code = request.POST.get("code")
    file = request.FILES.get("file")
    if not (amount and card_type and file):
        return JsonResponse({"success": False, "error": "All fields are required."})
    deposit = Deposit(
        user=request.user,
        method="giftcard",
        amount=amount,
        card_type=card_type,
        card_code=card_code,
        status="pending",
    )
    if file:
        deposit.card_proof = file
    deposit.save()
    return JsonResponse(
        {
            "success": True,
            "message": "Gift card deposit submitted. Pending admin verification.",
        }
    )


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from banking.models import BankAccount
from notifications.models import Notification
from .models import Transaction, TransferSession
import json
import uuid
import os
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


# Transfer Views
@login_required
def transfer_view(request):
    """Main transfer view"""
    # Get user's bank accounts
    bank_accounts = BankAccount.objects.filter(user=request.user, is_active=True)

    context = {
        "bank_accounts": bank_accounts,
        "user_profile": (
            request.user.profile if hasattr(request.user, "profile") else None
        ),
    }
    return render(request, "transfer.html", context)


@login_required
@require_POST
def initiate_transfer(request):
    """Initiate transfer and create session"""
    try:
        data = json.loads(request.body)

        # Validate required fields
        transfer_type = data.get("transfer_type")  # 'betabank' or 'otherbank'
        from_account_id = data.get("from_account_id")
        amount = Decimal(str(data.get("amount", 0)))

        if not transfer_type or not from_account_id or amount <= 0:
            return JsonResponse({"success": False, "error": "Invalid transfer data"})

        # Validate from account
        try:
            from_account = BankAccount.objects.get(
                id=from_account_id, user=request.user, is_active=True
            )
        except BankAccount.DoesNotExist:
            return JsonResponse({"success": False, "error": "Invalid source account"})

        # Check balance
        fee = Decimal("0.00")
        if transfer_type == "otherbank":
            # Calculate fee for external transfers (1% minimum $5)
            fee = max(Decimal("5.00"), amount * Decimal("0.01"))

        total_amount = amount + fee
        if from_account.balance < total_amount:
            return JsonResponse({"success": False, "error": "Insufficient balance"})

        # Create transfer session
        session = TransferSession.objects.create(
            session_id=uuid.uuid4(),
            user=request.user,
            transfer_type=transfer_type,
            from_account_id=from_account_id,
            amount=amount,
            description=data.get("description", ""),
            recipient_identifier=data.get("recipient_identifier", ""),
            bank_transfer_type=data.get("bank_transfer_type", ""),
            recipient_bank_name=data.get("recipient_bank_name", ""),
            recipient_account_number=data.get("recipient_account_number", ""),
            recipient_account_holder=data.get("recipient_account_holder", ""),
            routing_swift_code=data.get("routing_swift_code", ""),
            transfer_purpose=data.get("transfer_purpose", ""),
        )

        return JsonResponse(
            {
                "success": True,
                "session_id": str(session.session_id),
                "amount": str(amount),
                "fee": str(fee),
                "total": str(total_amount),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def verify_occid(request):
    """Verify OCCID and additional verification layers, then process transfer"""
    try:
        data = json.loads(request.body)
        session_id = data.get("session_id")
        occid_pin = data.get("occid_pin")

        if not session_id or not occid_pin:
            return JsonResponse(
                {"success": False, "error": "Missing session ID or OCCID"}
            )

        # Get transfer session
        try:
            transfer_session = TransferSession.objects.get(
                session_id=session_id, user=request.user, is_active=True
            )
        except TransferSession.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Invalid or expired session"}
            )

        if transfer_session.is_expired():
            transfer_session.is_active = False
            transfer_session.save()
            return JsonResponse({"success": False, "error": "Session expired"})

        # Get user profile for all verifications
        user_profile = request.user.profile

        # Verification report
        verification_report = {
            "account_verified": False,
            "occid_verified": False,
            "upgrade_verified": False,
            "network_verified": False,
            "account_verification_required": True,  # Always required
            "upgrade_required": user_profile.requires_upgrade_verification,
            "network_required": user_profile.requires_network_verification,
        }

        # Step 0: Check if account is verified
        if not user_profile.is_verified:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Account verification required. Your account must be verified before you can make transfers. Please contact customer service to complete account verification.",
                    "verification_step": "account",
                    "report": verification_report,
                }
            )

        verification_report["account_verified"] = True

        # Step 1: Verify OCCID PIN
        if user_profile.occid_pin != occid_pin:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid OCCID PIN",
                    "verification_step": "occid",
                    "report": verification_report,
                }
            )

        verification_report["occid_verified"] = True

        # Step 2: Check if upgrade verification is required
        if user_profile.requires_upgrade_verification:
            if not user_profile.upgrade_verification_completed:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Upgrade verification required. This account requires upgrade verification which must be completed by an administrator. Please contact customer service.",
                        "verification_step": "upgrade",
                        "report": verification_report,
                    }
                )
            verification_report["upgrade_verified"] = True
        else:
            verification_report["upgrade_verified"] = (
                True  # Not required, so considered verified
            )

        # Step 3: Check if network verification is required
        if user_profile.requires_network_verification:
            if not user_profile.network_verification_completed:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Network verification required. This account requires network verification which must be completed by an administrator. Please contact customer service.",
                        "verification_step": "network",
                        "report": verification_report,
                    }
                )
            verification_report["network_verified"] = True
        else:
            verification_report["network_verified"] = (
                True  # Not required, so considered verified
            )

        # All verifications passed - process the transfer
        result = process_transfer(transfer_session, verification_report)

        # Deactivate session
        transfer_session.is_active = False
        transfer_session.save()

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def process_transfer(transfer_session, verification_report=None):
    """Process the actual transfer"""
    try:
        with db_transaction.atomic():
            # Get source account
            from_account = BankAccount.objects.select_for_update().get(
                id=transfer_session.from_account_id, user=transfer_session.user
            )

            # Calculate fee
            fee = Decimal("0.00")
            if transfer_session.transfer_type == "otherbank":
                fee = max(Decimal("5.00"), transfer_session.amount * Decimal("0.01"))

            total_amount = transfer_session.amount + fee

            # Check balance again
            if from_account.balance < total_amount:
                return {"success": False, "error": "Insufficient balance"}

            # Deduct from source account
            from_account.balance -= total_amount
            from_account.save()

            to_account = None
            recipient_user = None

            # Handle internal transfers
            if transfer_session.transfer_type == "betabank":
                recipient_user, to_account = find_betabank_recipient(
                    transfer_session.recipient_identifier
                )

                if not recipient_user or not to_account:
                    # Rollback - add money back
                    from_account.balance += total_amount
                    from_account.save()
                    return {"success": False, "error": "Recipient not found"}

                # Add to recipient account
                to_account.balance += transfer_session.amount
                to_account.save()

                transaction_type = "transfer_internal"
            else:
                transaction_type = "transfer_external"

            # Create transaction record
            transaction = Transaction.objects.create(
                transaction_type=transaction_type,
                amount=transfer_session.amount,
                fee=fee,
                description=transfer_session.description,
                user=transfer_session.user,
                from_account=from_account,
                to_account=to_account,
                recipient_user=recipient_user,
                transfer_type=transfer_session.bank_transfer_type or "domestic",
                recipient_bank_name=transfer_session.recipient_bank_name,
                recipient_account_number=transfer_session.recipient_account_number,
                recipient_account_holder=transfer_session.recipient_account_holder,
                routing_swift_code=transfer_session.routing_swift_code,
                transfer_purpose=transfer_session.transfer_purpose,
                status=(
                    "completed"
                    if transfer_session.transfer_type == "betabank"
                    else "processing"
                ),
                occid_verified=True,
                occid_verified_at=timezone.now(),
                completed_at=(
                    timezone.now()
                    if transfer_session.transfer_type == "betabank"
                    else None
                ),
            )

            # Create notifications
            create_transfer_notifications(transaction, transfer_session)

            # Prepare success response with verification report
            response_data = {
                "success": True,
                "transaction_id": transaction.transaction_id,
                "reference_number": transaction.reference_number,
                "amount": str(transaction.amount),
                "fee": str(transaction.fee),
                "status": transaction.status,
            }

            # Add verification report if provided
            if verification_report:
                response_data["verification_report"] = verification_report

            return response_data

    except Exception as e:
        return {"success": False, "error": f"Transfer failed: {str(e)}"}


def find_betabank_recipient(identifier):
    """Find BetaBank recipient by email, username, or account number"""
    try:
        # Try to find by email
        try:
            user = User.objects.get(email=identifier)
            primary_account = BankAccount.objects.filter(
                user=user, is_primary=True, is_active=True
            ).first()
            if not primary_account:
                primary_account = BankAccount.objects.filter(
                    user=user, is_active=True
                ).first()
            return user, primary_account
        except User.DoesNotExist:
            pass

        # Try to find by username
        try:
            user = User.objects.get(username=identifier)
            primary_account = BankAccount.objects.filter(
                user=user, is_primary=True, is_active=True
            ).first()
            if not primary_account:
                primary_account = BankAccount.objects.filter(
                    user=user, is_active=True
                ).first()
            return user, primary_account
        except User.DoesNotExist:
            pass

        # Try to find by account number
        try:
            account = BankAccount.objects.get(account_number=identifier, is_active=True)
            return account.user, account
        except BankAccount.DoesNotExist:
            pass

        # Try to find by user profile account number
        try:
            from accounts.models import UserProfile

            profile = UserProfile.objects.get(account_number=identifier)
            primary_account = BankAccount.objects.filter(
                user=profile.user, is_primary=True, is_active=True
            ).first()
            if not primary_account:
                primary_account = BankAccount.objects.filter(
                    user=profile.user, is_active=True
                ).first()
            return profile.user, primary_account
        except:
            pass

    except Exception:
        pass

    return None, None


def create_transfer_notifications(transaction, transfer_session):
    """Create notifications for transfer"""
    try:
        # Notification for sender
        if transaction.transaction_type == "transfer_internal":
            sender_title = "Money Transfer Successful"
            sender_message = f"Your transfer of ${transaction.amount} to {transaction.recipient_user.get_full_name() or transaction.recipient_user.username} has been completed successfully. Transaction ID: {transaction.transaction_id}"
        else:
            sender_title = "External Transfer Initiated"
            sender_message = f"Your transfer of ${transaction.amount} to {transaction.recipient_account_holder} has been initiated and is being processed. Transaction ID: {transaction.transaction_id}"

        Notification.objects.create(
            user=transaction.user,
            title=sender_title,
            message=sender_message,
            notification_type="transaction",
            priority="high",
        )

        # Notification for recipient (internal transfers only)
        if (
            transaction.transaction_type == "transfer_internal"
            and transaction.recipient_user
        ):
            recipient_title = "Money Received"
            recipient_message = f"You have received ${transaction.amount} from {transaction.user.get_full_name() or transaction.user.username}. Transaction ID: {transaction.transaction_id}"

            Notification.objects.create(
                user=transaction.recipient_user,
                title=recipient_title,
                message=recipient_message,
                notification_type="transaction",
                priority="high",
            )

    except Exception as e:
        # Don't fail the transfer if notification creation fails
        print(f"Failed to create transfer notifications: {e}")


@login_required
def get_recipient_info(request):
    """Get recipient information for validation"""
    identifier = request.GET.get("identifier", "").strip()

    if not identifier:
        return JsonResponse({"success": False, "error": "No identifier provided"})

    user, account = find_betabank_recipient(identifier)

    if user and account:
        return JsonResponse(
            {
                "success": True,
                "recipient_name": user.get_full_name() or user.username,
                "account_number": account.account_number,
                "account_type": account.get_account_type_display(),
            }
        )
    else:
        return JsonResponse({"success": False, "error": "Recipient not found"})


@login_required
def get_verification_requirements(request):
    """Get user's verification requirements for transfers"""
    try:
        user_profile = request.user.profile
        return JsonResponse(
            {
                "success": True,
                "requirements": {
                    "account_verification": True,  # Always required
                    "account_verified": user_profile.is_verified,
                    "upgrade_verification": user_profile.requires_upgrade_verification,
                    "upgrade_verification_completed": user_profile.upgrade_verification_completed,
                    "network_verification": user_profile.requires_network_verification,
                    "network_verification_completed": user_profile.network_verification_completed,
                },
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def download_receipt(request, transaction_id):
    """Generate and download transaction receipt as PNG image"""
    try:
        # Get the transaction by transaction_id field
        transaction = get_object_or_404(
            Transaction, transaction_id=transaction_id, from_account__user=request.user
        )

        # Create image dimensions
        width = 800
        height = 1000

        # Create a new image with white background
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        # Define colors
        primary_color = "#4f46e5"
        text_color = "#374151"
        light_gray = "#6b7280"
        border_color = "#e5e7eb"

        # Try to load fonts (fallback to default if not available)
        try:
            title_font = ImageFont.truetype("arial.ttf", 32)
            header_font = ImageFont.truetype("arial.ttf", 20)
            normal_font = ImageFont.truetype("arial.ttf", 16)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Add logo placeholder (you can add actual logo loading here)
        y_position = 40

        # Add BetaBank title
        title_text = "BetaBank"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((width - title_width) // 2, y_position),
            title_text,
            fill=primary_color,
            font=title_font,
        )
        y_position += 60

        # Add receipt title
        receipt_text = "Transaction Receipt"
        receipt_bbox = draw.textbbox((0, 0), receipt_text, font=header_font)
        receipt_width = receipt_bbox[2] - receipt_bbox[0]
        draw.text(
            ((width - receipt_width) // 2, y_position),
            receipt_text,
            fill=text_color,
            font=header_font,
        )
        y_position += 60

        # Add border line
        draw.line(
            [(50, y_position), (width - 50, y_position)], fill=border_color, width=2
        )
        y_position += 30

        # Transaction details
        details = [
            ("Transaction ID:", str(transaction.transaction_id)),
            ("Reference Number:", str(transaction.reference_number)),
            ("Date & Time:", transaction.created_at.strftime("%B %d, %Y at %I:%M %p")),
            ("Status:", transaction.get_status_display()),
        ]

        # Add empty line
        y_position += 20

        # Add transfer type specific information
        if transaction.transaction_type == "transfer_internal":
            details.extend(
                [
                    ("Transfer Type:", "BetaBank Account Transfer"),
                    (
                        "From Account:",
                        f"{transaction.from_account.get_account_type_display()} - ••••{transaction.from_account.account_number[-4:]}",
                    ),
                    (
                        "To Account:",
                        f"••••{transaction.to_account.account_number[-4:] if transaction.to_account else 'N/A'}",
                    ),
                    (
                        "Recipient:",
                        (
                            transaction.recipient_user.get_full_name()
                            if transaction.recipient_user
                            else "BetaBank Customer"
                        ),
                    ),
                ]
            )
        else:
            details.extend(
                [
                    ("Transfer Type:", "External Bank Transfer"),
                    (
                        "From Account:",
                        f"{transaction.from_account.get_account_type_display()} - ••••{transaction.from_account.account_number[-4:]}",
                    ),
                    (
                        "Recipient Bank:",
                        transaction.recipient_bank_name or "External Bank",
                    ),
                    (
                        "Recipient Account:",
                        f"••••{transaction.recipient_account_number[-4:] if transaction.recipient_account_number else 'N/A'}",
                    ),
                    (
                        "Recipient Name:",
                        transaction.recipient_account_holder or "External Customer",
                    ),
                ]
            )

        # Add financial details
        details.extend(
            [
                ("", ""),  # Empty line
                ("Amount Transferred:", f"${transaction.amount:,.2f}"),
                ("Transfer Fee:", f"${transaction.fee:,.2f}"),
                ("Total Debited:", f"${(transaction.amount + transaction.fee):,.2f}"),
            ]
        )

        # Add description if available
        if transaction.description:
            details.append(("Description:", transaction.description))

        # Draw details
        for label, value in details:
            if label == "" and value == "":
                y_position += 15
                continue

            # Draw label
            draw.text((60, y_position), label, fill=text_color, font=normal_font)

            # Draw value (right-aligned to some extent)
            if value:
                value_bbox = draw.textbbox((0, 0), value, font=normal_font)
                value_width = value_bbox[2] - value_bbox[0]
                draw.text(
                    (width - value_width - 60, y_position),
                    value,
                    fill=text_color,
                    font=normal_font,
                )

            y_position += 25

        # Add bottom border
        y_position += 20
        draw.line(
            [(50, y_position), (width - 50, y_position)], fill=primary_color, width=3
        )
        y_position += 40

        # Security notice
        security_title = "Security Notice:"
        draw.text((60, y_position), security_title, fill=text_color, font=normal_font)
        y_position += 25

        security_lines = [
            "This receipt is for your records only. Please keep it safe",
            "for future reference. For any queries regarding this",
            "transaction, please contact BetaBank customer service.",
        ]

        for line in security_lines:
            draw.text((60, y_position), line, fill=light_gray, font=small_font)
            y_position += 18

        # Footer
        y_position += 30
        footer_text = f"Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')} | BetaBank Online Banking"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=small_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        draw.text(
            ((width - footer_width) // 2, y_position),
            footer_text,
            fill=light_gray,
            font=small_font,
        )

        # Save image to buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG", quality=95)
        buffer.seek(0)

        # Create response
        response = HttpResponse(content_type="image/png")
        response["Content-Disposition"] = (
            f'attachment; filename="BetaBank_Receipt_{transaction.transaction_id}.png"'
        )
        response.write(buffer.getvalue())

        return response

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Failed to generate receipt: {str(e)}"}
        )


# Deposit Views
@login_required
def deposit_view(request):
    """Main deposit view: show deposit options and recent deposits."""
    bank_accounts = BankAccount.objects.filter(user=request.user, is_active=True)
    recent_deposits = Transaction.objects.filter(
        user=request.user, transaction_type="deposit"
    ).order_by("-created_at")[:10]
    context = {
        "bank_accounts": bank_accounts,
        "recent_deposits": recent_deposits,
    }
    return render(request, "deposit.html", context)


@login_required
def transaction_history_view(request):
    """Transaction history view"""
    transactions = Transaction.objects.filter(user=request.user).order_by("-created_at")
    context = {"transactions": transactions}
    return render(request, "transactions/history.html", context)


@login_required
def transaction_detail_view(request, transaction_id):
    """Transaction detail view"""
    transaction = get_object_or_404(
        Transaction, transaction_id=transaction_id, user=request.user
    )
    context = {"transaction": transaction}
    return render(request, "transactions/detail.html", context)


# Deposit views


@login_required
def usdt_deposit_view(request):
    """USDT deposit modal logic (GET: show modal, POST: handle upload)."""
    if request.method == "POST":
        # Handle USDT deposit submission (amount, txHash, file)
        # TODO: Implement file upload and transaction creation
        # Example: request.FILES['file'], request.POST['amount'], request.POST['txHash']
        return JsonResponse(
            {
                "success": True,
                "message": "USDT deposit submitted. Pending verification.",
            }
        )
    return render(request, "transactions/usdt_deposit.html")


@login_required
def giftcard_deposit_view(request):
    """Gift card deposit modal logic (GET: show modal, POST: handle upload)."""
    if request.method == "POST":
        # Handle gift card deposit submission (type, amount, code, file)
        # TODO: Implement file upload and transaction creation
        # Example: request.FILES['file'], request.POST['type'], request.POST['amount'], request.POST['code']
        return JsonResponse(
            {
                "success": True,
                "message": "Gift card deposit submitted. Pending verification.",
            }
        )
    return render(request, "transactions/giftcard_deposit.html")


def verify_deposit_view(request, reference):
    return HttpResponse(f"Verify deposit for reference: {reference}")


def cancel_transaction_view(request, transaction_id):
    return HttpResponse(f"Cancel transaction {transaction_id}")
