from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.split_bills.models import (
    SplitBill,
    SplitBillCharge,
    SplitBillDebt,
    SplitBillItem,
    SplitBillParticipant,
    SplitBillParticipantItem,
    SplitBillSettlement,
)
from app.modules.split_bills.schemas import (
    SplitBillCalculateRequest,
    SplitBillCreate,
    SplitBillSettlementInput,
)
from app.modules.transactions.models import TransactionType
from app.modules.transactions.schemas import TransactionCreate
from app.modules.transactions.service import (
    create_transaction,
    get_transaction_by_id,
    soft_delete_transaction,
)

__all__ = [
    "create_bill",
    "get_bill_by_id",
    "get_bills_by_user",
    "get_bill_summaries_by_user",
    "get_bill_detail",
    "soft_delete_bill",
    "calculate_split",
    "create_settlement",
]


async def create_bill(db: AsyncSession, user_id: int, data: SplitBillCreate):
    subtotal = Decimal("0.00")
    items = []

    for item_data in data.items:
        item_subtotal = (item_data.price * item_data.quantity).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        subtotal += item_subtotal

        items.append(
            SplitBillItem(
                name=item_data.name,
                price=item_data.price,
                quantity=item_data.quantity,
                subtotal=item_subtotal,
            )
        )

    total_charges = Decimal("0.00")
    charges = []

    for charge_data in data.charges:
        total_charges += charge_data.amount
        charges.append(
            SplitBillCharge(
                type=charge_data.type,
                name=charge_data.name,
                amount=charge_data.amount,
            )
        )

    total_amount = subtotal + total_charges

    if total_amount <= Decimal("0.00"):
        raise ValueError("Bill total must be positive")

    bill = SplitBill(
        user_id=user_id,
        title=data.title,
        subtotal=subtotal,
        total_amount=total_amount,
        date=data.date,
        note=data.note,
        receipt_image_url=data.receipt_image_url,
    )

    db.add(bill)
    await db.flush()

    for item in items:
        item.bill_id = bill.id
        db.add(item)

    for charge in charges:
        charge.bill_id = bill.id
        db.add(charge)

    await db.commit()
    await db.refresh(bill)
    return bill


async def get_bill_by_id(db: AsyncSession, bill_id: int) -> SplitBill | None:
    result = await db.execute(
        select(SplitBill).where(
            SplitBill.id == bill_id,
            ~SplitBill.is_deleted,
        )
    )
    return result.scalar_one_or_none()


async def get_bills_by_user(db: AsyncSession, user_id: int) -> list[SplitBill]:
    result = await db.execute(
        select(SplitBill)
        .where(
            SplitBill.user_id == user_id,
            ~SplitBill.is_deleted,
        )
        .order_by(SplitBill.date.desc())
    )
    return list(result.scalars().all())


def _compute_bill_metrics(
    participants: list[SplitBillParticipant],
    debts: list[SplitBillDebt],
    settlements: list[SplitBillSettlement],
) -> dict:
    participant_count = len(participants)
    has_calculation = participant_count > 0

    if has_calculation:
        non_payers = [p for p in participants if not p.is_payer]
        total_non_payer_count = len(non_payers)

        outstanding_debtor_ids = {
            debt.debtor_participant_id
            for debt in debts
            if debt.remaining_amount > Decimal("0.00")
        }

        paid_participant_count = sum(
            1
            for participant in non_payers
            if participant.id not in outstanding_debtor_ids
        )
        is_fully_settled = all(debt.is_settled for debt in debts)
    else:
        total_non_payer_count = 0
        paid_participant_count = 0
        is_fully_settled = False

    total_debt_amount = sum(
        (debt.amount for debt in debts),
        Decimal("0.00"),
    )
    remaining_debt_amount = sum(
        (debt.remaining_amount for debt in debts),
        Decimal("0.00"),
    )

    settlement_summary = {
        "total_debt_amount": total_debt_amount,
        "remaining_debt_amount": remaining_debt_amount,
        "settled_debt_count": sum(1 for debt in debts if debt.is_settled),
        "total_debt_count": len(debts),
        "settlement_count": len(settlements),
        "settled_amount": total_debt_amount - remaining_debt_amount,
    }

    return {
        "participant_count": participant_count,
        "paid_participant_count": paid_participant_count,
        "total_non_payer_count": total_non_payer_count,
        "has_calculation": has_calculation,
        "is_fully_settled": is_fully_settled,
        "settlement_summary": settlement_summary,
    }


async def get_bill_summaries_by_user(
    db: AsyncSession,
    user_id: int,
) -> list[dict]:
    bills = await get_bills_by_user(db, user_id)
    if not bills:
        return []

    bill_ids = [bill.id for bill in bills]

    participants_result = await db.execute(
        select(SplitBillParticipant).where(
            SplitBillParticipant.bill_id.in_(bill_ids)
        )
    )
    participants_by_bill: dict[int, list[SplitBillParticipant]] = defaultdict(
        list
    )
    for participant in participants_result.scalars().all():
        participants_by_bill[participant.bill_id].append(participant)

    debts_result = await db.execute(
        select(SplitBillDebt).where(SplitBillDebt.bill_id.in_(bill_ids))
    )
    debts_by_bill: dict[int, list[SplitBillDebt]] = defaultdict(list)
    for debt in debts_result.scalars().all():
        debts_by_bill[debt.bill_id].append(debt)

    settlements_result = await db.execute(
        select(SplitBillSettlement).where(
            SplitBillSettlement.bill_id.in_(bill_ids)
        )
    )
    settlements_by_bill: dict[int, list[SplitBillSettlement]] = defaultdict(
        list
    )
    for settlement in settlements_result.scalars().all():
        settlements_by_bill[settlement.bill_id].append(settlement)

    summaries: list[dict] = []
    for bill in bills:
        participants = participants_by_bill.get(bill.id, [])
        debts = debts_by_bill.get(bill.id, [])
        settlements = settlements_by_bill.get(bill.id, [])
        metrics = _compute_bill_metrics(participants, debts, settlements)

        summaries.append(
            {
                "id": bill.id,
                "title": bill.title,
                "date": bill.date,
                "total_amount": bill.total_amount,
                "participant_count": metrics["participant_count"],
                "paid_participant_count": metrics["paid_participant_count"],
                "total_non_payer_count": metrics["total_non_payer_count"],
                "has_calculation": metrics["has_calculation"],
                "is_fully_settled": metrics["is_fully_settled"],
                "settlement_summary": metrics["settlement_summary"],
            }
        )

    return summaries


async def get_bill_detail(db: AsyncSession, bill: SplitBill) -> dict:
    # Load items
    items_result = await db.execute(
        select(SplitBillItem)
        .where(SplitBillItem.bill_id == bill.id)
        .order_by(SplitBillItem.id)
    )
    items = list(items_result.scalars().all())
    items_by_id = {item.id: item for item in items}

    # Load charges
    charges_result = await db.execute(
        select(SplitBillCharge)
        .where(SplitBillCharge.bill_id == bill.id)
        .order_by(SplitBillCharge.id)
    )
    charges = list(charges_result.scalars().all())

    # Load participants
    participants_result = await db.execute(
        select(SplitBillParticipant)
        .where(SplitBillParticipant.bill_id == bill.id)
        .order_by(SplitBillParticipant.id)
    )
    participants = list(participants_result.scalars().all())

    # Load debts
    debts_result = await db.execute(
        select(SplitBillDebt)
        .where(SplitBillDebt.bill_id == bill.id)
        .order_by(SplitBillDebt.id)
    )
    debts = list(debts_result.scalars().all())

    # Load settlements
    settlements_result = await db.execute(
        select(SplitBillSettlement)
        .where(SplitBillSettlement.bill_id == bill.id)
        .order_by(SplitBillSettlement.created_at)
    )
    settlements = list(settlements_result.scalars().all())

    participant_item_result = await db.execute(
        select(SplitBillParticipantItem)
        .where(SplitBillParticipantItem.bill_id == bill.id)
        .order_by(
            SplitBillParticipantItem.participant_id,
            SplitBillParticipantItem.item_id,
        )
    )
    participant_items = list(participant_item_result.scalars().all())

    participant_items_by_participant: dict[int, list[dict]] = defaultdict(list)
    for participant_item in participant_items:
        item = items_by_id.get(participant_item.item_id)
        if item is None:
            continue

        participant_items_by_participant[
            participant_item.participant_id
        ].append(
            {
                "item_id": item.id,
                "item_name": item.name,
                "portion": participant_item.portion,
                "allocated_subtotal": participant_item.allocated_subtotal,
            }
        )

    participant_details = []
    for participant in participants:
        participant_details.append(
            {
                "id": participant.id,
                "user_id": participant.user_id,
                "name": participant.name,
                "is_payer": participant.is_payer,
                "paid_amount": participant.paid_amount,
                "final_amount": participant.final_amount,
                "items": participant_items_by_participant.get(
                    participant.id, []
                ),
                "created_at": participant.created_at,
            }
        )

    metrics = _compute_bill_metrics(participants, debts, settlements)

    return {
        "id": bill.id,
        "title": bill.title,
        "subtotal": bill.subtotal,
        "total_amount": bill.total_amount,
        "date": bill.date,
        "note": bill.note,
        "receipt_image_url": bill.receipt_image_url,
        "transaction_id": bill.transaction_id,
        "items": items,
        "charges": charges,
        "participants": participant_details,
        "debts": debts,
        "settlements": settlements,
        "paid_participant_count": metrics["paid_participant_count"],
        "total_non_payer_count": metrics["total_non_payer_count"],
        "has_calculation": metrics["has_calculation"],
        "is_fully_settled": metrics["is_fully_settled"],
        "created_at": bill.created_at,
        "updated_at": bill.updated_at,
    }


async def soft_delete_bill(db: AsyncSession, bill: SplitBill):
    if bill.transaction_id is not None:
        transaction = await get_transaction_by_id(db, bill.transaction_id)
        if transaction is not None:
            await soft_delete_transaction(db, transaction)

    settlements_result = await db.execute(
        select(SplitBillSettlement).where(
            SplitBillSettlement.bill_id == bill.id,
            SplitBillSettlement.transaction_id.isnot(None),
        )
    )
    for settlement in settlements_result.scalars().all():
        txn = await get_transaction_by_id(db, settlement.transaction_id)
        if txn is not None:
            await soft_delete_transaction(db, txn)

    bill.is_deleted = True
    bill.deleted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(bill)
    return bill


async def calculate_split(
    db: AsyncSession,
    bill: SplitBill,
    data: SplitBillCalculateRequest,
):
    settlement_exists = await db.execute(
        select(SplitBillSettlement.id)
        .where(SplitBillSettlement.bill_id == bill.id)
        .limit(1)
    )

    if settlement_exists.scalar_one_or_none():
        raise ValueError(
            "Cannot recalculate a bill with existing settlements. "
            "Create a new bill instead."
        )

    payers = [p for p in data.participants if p.is_payer]
    if not payers:
        raise ValueError("At least one payer is required")

    total_paid = sum(p.paid_amount for p in data.participants)
    if total_paid != bill.total_amount:
        raise ValueError("Total paid must equal bill total")

    items_result = await db.execute(
        select(SplitBillItem).where(SplitBillItem.bill_id == bill.id)
    )
    bill_items = {item.id: item for item in items_result.scalars().all()}

    participant_count = len(data.participants)

    if bill.subtotal <= 0 or bill.total_amount <= 0:
        raise ValueError("Invalid bill values")

    raw_shares = [Decimal("0.00")] * participant_count
    participant_item_allocations: list[dict] = []

    if not data.shares:
        share = (bill.subtotal / participant_count).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        raw_shares = [share] * participant_count

        for item in bill_items.values():
            per_participant = (item.subtotal / participant_count).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            item_allocations = [
                {
                    "participant_index": p_index,
                    "item_id": item.id,
                    "portion": 1,
                    "allocated_subtotal": per_participant,
                }
                for p_index in range(participant_count)
            ]
            diff = item.subtotal - sum(
                a["allocated_subtotal"] for a in item_allocations
            )
            item_allocations[-1]["allocated_subtotal"] += diff
            participant_item_allocations.extend(item_allocations)

    else:
        for share in data.shares:
            if share.participant_index >= participant_count:
                raise ValueError(
                    f"Invalid participant index: {share.participant_index}"
                )

            if any(portion <= 0 for portion in share.share_portions.values()):
                raise ValueError("Share portions must be greater than 0")

        uses_custom_amount = any(
            s.custom_amount is not None for s in data.shares
        )
        uses_item_ids = any(s.item_ids for s in data.shares)

        if uses_custom_amount and uses_item_ids:
            raise ValueError(
                "Cannot mix custom amounts with item-based shares"
            )

        if uses_custom_amount:
            if len(data.shares) != participant_count:
                raise ValueError(
                    "Custom amounts must be provided for every participant"
                )

            if any(s.custom_amount is None for s in data.shares):
                raise ValueError(
                    "Custom amounts must be provided for every participant"
                )

            unique_indexes = {s.participant_index for s in data.shares}
            if len(unique_indexes) != participant_count:
                raise ValueError(
                    "Each participant must appear exactly once "
                    "in custom amounts"
                )

            for share in data.shares:
                raw_shares[share.participant_index] = share.custom_amount

            if sum(raw_shares) != bill.subtotal:
                raise ValueError("Custom amounts must match subtotal")

        elif not uses_item_ids:
            raise ValueError(
                "Invalid shares: provide custom amounts or item assignments"
            )

        item_sharing: dict[int, list[tuple[int, int]]] = {}

        if uses_item_ids:
            for share in data.shares:
                for item_id in share.item_ids:
                    if item_id not in bill_items:
                        raise ValueError(f"Invalid item {item_id}")

                    portions = share.share_portions.get(str(item_id), 1)

                    existing_sharers = item_sharing.setdefault(item_id, [])
                    if any(
                        idx == share.participant_index
                        for idx, _ in existing_sharers
                    ):
                        raise ValueError(
                            f"Duplicate share assignment for item {item_id} "
                            f"and participant index {share.participant_index}"
                        )

                    existing_sharers.append(
                        (share.participant_index, portions)
                    )

            if set(item_sharing.keys()) != set(bill_items.keys()):
                raise ValueError("All items must be assigned")

            for item_id, sharers in item_sharing.items():
                total_portions = sum(p for _, p in sharers)
                if total_portions <= 0:
                    raise ValueError(
                        f"Invalid share portions for item {item_id}"
                    )

                item = bill_items[item_id]
                rounded_allocations = []

                for p_index, portion in sharers:
                    allocated_subtotal = (
                        item.subtotal * portion / total_portions
                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    rounded_allocations.append(
                        {
                            "participant_index": p_index,
                            "item_id": item_id,
                            "portion": portion,
                            "allocated_subtotal": allocated_subtotal,
                        }
                    )

                if rounded_allocations:
                    allocation_diff = item.subtotal - sum(
                        (
                            allocation["allocated_subtotal"]
                            for allocation in rounded_allocations
                        ),
                        Decimal("0.00"),
                    )
                    rounded_allocations[-1]["allocated_subtotal"] += (
                        allocation_diff
                    )

                for allocation in rounded_allocations:
                    participant_item_allocations.append(allocation)
                    raw_shares[allocation["participant_index"]] += allocation[
                        "allocated_subtotal"
                    ]

    raw_total = sum(raw_shares)
    if raw_total == 0:
        raise ValueError("Invalid split")

    final_amounts = []

    for raw in raw_shares:
        proportion = raw / raw_total
        final = (bill.total_amount * proportion).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        final_amounts.append(final)

    diff = bill.total_amount - sum(final_amounts)
    final_amounts[-1] += diff

    for table in [
        SplitBillParticipantItem,
        SplitBillDebt,
        SplitBillParticipant,
    ]:
        result = await db.execute(
            select(table).where(table.bill_id == bill.id)
        )
        for row in result.scalars():
            await db.delete(row)

    await db.flush()

    db_participants = []

    for i, p_data in enumerate(data.participants):
        p = SplitBillParticipant(
            bill_id=bill.id,
            user_id=p_data.user_id,
            name=p_data.name,
            is_payer=p_data.is_payer,
            paid_amount=p_data.paid_amount,
            final_amount=final_amounts[i],
        )
        db.add(p)
        db_participants.append(p)

    await db.flush()

    if participant_item_allocations:
        participant_ids_by_index = {
            index: participant.id
            for index, participant in enumerate(db_participants)
        }

        for allocation in participant_item_allocations:
            db.add(
                SplitBillParticipantItem(
                    bill_id=bill.id,
                    participant_id=participant_ids_by_index[
                        allocation["participant_index"]
                    ],
                    item_id=allocation["item_id"],
                    portion=allocation["portion"],
                    allocated_subtotal=allocation["allocated_subtotal"],
                )
            )

        await db.flush()

    balances = [
        {"p": p, "net": p.paid_amount - p.final_amount}
        for p in db_participants
    ]

    creditors = sorted(
        [b for b in balances if b["net"] > 0],
        key=lambda x: x["net"],
        reverse=True,
    )
    debtors = sorted(
        [b for b in balances if b["net"] < 0],
        key=lambda x: x["net"],
    )

    db_debts = []
    ci = di = 0

    while ci < len(creditors) and di < len(debtors):
        c = creditors[ci]
        d = debtors[di]

        amount = min(c["net"], abs(d["net"])).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if amount > 0:
            debt = SplitBillDebt(
                bill_id=bill.id,
                debtor_participant_id=d["p"].id,
                creditor_participant_id=c["p"].id,
                amount=amount,
                remaining_amount=amount,
            )
            db.add(debt)
            db_debts.append(debt)

        c["net"] -= amount
        d["net"] += amount

        if c["net"] == 0:
            ci += 1
        if d["net"] == 0:
            di += 1

    await db.flush()

    participant_names = {p.id: p.name for p in db_participants}

    is_item_based = bool(data.shares and any(s.item_ids for s in data.shares))

    summary = []

    for debt in db_debts:
        debtor_items = []

        if is_item_based:
            debtor_index = next(
                i
                for i, p in enumerate(db_participants)
                if p.id == debt.debtor_participant_id
            )

            for share in data.shares:
                if share.participant_index == debtor_index:
                    for item_id in share.item_ids:
                        item = bill_items[item_id]
                        debtor_items.append(
                            {"name": item.name, "subtotal": item.subtotal}
                        )

        summary.append(
            {
                "debtor_name": participant_names[debt.debtor_participant_id],
                "creditor_name": participant_names[
                    debt.creditor_participant_id
                ],
                "amount": debt.amount,
                "items": debtor_items,
            }
        )

    text = generate_summary_text(
        bill.title,
        bill.total_amount,
        db_debts,
        participant_names,
        summary,
    )

    await db.commit()

    bill_changed = False

    if bill.transaction_id is not None:
        old_transaction = await get_transaction_by_id(db, bill.transaction_id)
        if old_transaction is not None:
            await soft_delete_transaction(db, old_transaction)
        bill.transaction_id = None
        bill_changed = True

    if data.account_id is not None:
        owner_participant = next(
            (p for p in db_participants if p.user_id == bill.user_id),
            None,
        )
        if owner_participant is not None:
            expense_amount = (
                owner_participant.paid_amount
                if owner_participant.is_payer
                else owner_participant.final_amount
            )
            new_transaction = await create_transaction(
                db,
                bill.user_id,
                TransactionCreate(
                    account_id=data.account_id,
                    type=TransactionType.expense,
                    amount=expense_amount,
                    date=bill.date,
                    note=f"Split Bill: {bill.title}",
                ),
            )
            bill.transaction_id = new_transaction.id
            bill_changed = True

    if bill_changed:
        await db.commit()

    return {
        "title": bill.title,
        "total_amount": bill.total_amount,
        "participants": db_participants,
        "debts": db_debts,
        "summary": summary,
        "text": text,
    }


def generate_summary_text(
    title,
    total,
    debts,
    names,
    summary=None,
):
    lines = [f"{title} (Rp{total:,.0f})", ""]

    for i, d in enumerate(debts):
        debtor = names[d.debtor_participant_id]
        creditor = names[d.creditor_participant_id]

        lines.append(f"{debtor} owes:")
        lines.append(f"{creditor}: Rp{d.amount:,.0f}")

        if summary:
            for item in summary[i]["items"]:
                lines.append(
                    f"{item['name']}: Rp{item['subtotal']:,.0f}"
                )

        lines.append("")

    return "\n".join(lines)


async def create_settlement(
    db: AsyncSession,
    bill: SplitBill,
    debt: SplitBillDebt,
    data: SplitBillSettlementInput,
):
    if debt.is_settled:
        raise ValueError("Debt already settled")

    if data.amount > debt.remaining_amount:
        raise ValueError("Overpayment not allowed")

    settlement = SplitBillSettlement(
        bill_id=bill.id,
        debt_id=debt.id,
        from_participant_id=debt.debtor_participant_id,
        to_participant_id=debt.creditor_participant_id,
        amount=data.amount,
    )

    db.add(settlement)
    debt.remaining_amount -= data.amount

    await db.commit()
    await db.refresh(settlement)
    await db.refresh(debt)

    if data.account_id is not None:
        owner_participant_result = await db.execute(
            select(SplitBillParticipant).where(
                SplitBillParticipant.bill_id == bill.id,
                SplitBillParticipant.user_id == bill.user_id,
            )
        )
        owner_participant = owner_participant_result.scalar_one_or_none()

        if owner_participant is not None:
            if owner_participant.id == debt.creditor_participant_id:
                txn_type = TransactionType.income
            elif owner_participant.id == debt.debtor_participant_id:
                txn_type = TransactionType.expense
            else:
                txn_type = None

            if txn_type is not None:
                new_transaction = await create_transaction(
                    db,
                    bill.user_id,
                    TransactionCreate(
                        account_id=data.account_id,
                        type=txn_type,
                        amount=data.amount,
                        date=datetime.now(timezone.utc).date(),
                        note=f"Split Bill Settlement: {bill.title}",
                    ),
                )
                settlement.transaction_id = new_transaction.id
                await db.commit()
                await db.refresh(settlement)

    return settlement