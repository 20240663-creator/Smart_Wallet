from django.shortcuts import render
from rest_framework import  generics
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db.models import Q, Sum
from Notifications.models import Notification
from . import models
from . import serializer
from . import permessions
# Create your views here.




class TransactionsViewSets(ModelViewSet):
    serializer_class = serializer.TransactionSerializer
    permission_classes = [IsAuthenticated,permessions.IsOwnerOfWallet]

    def perform_create(self, serializer):
        wallet = getattr(self.request.user, "wallet", None)
        if not wallet:
            raise ValidationError("User has no wallet")
        
        amount = serializer.validated_data['amount']
        type = serializer.validated_data['type']
        budget = serializer.validated_data.get('budget')
        goal = serializer.validated_data.get('saving_goals')
        reciever = serializer.validated_data.get('reciever')

        if type == 'income':
            wallet.total_balance += amount
            wallet.total_income += amount
            wallet.save()
            Notification.objects.create(
            user=wallet.user,
            type='GENERAL',
            message=f"Income added: +{amount}"
            )
        elif type == 'expense':
            if amount > wallet.total_balance:
                raise ValidationError("Not enough balance")
            
            if budget:
                budget.spended += amount
                budget.percentage = (budget.spended / budget.amount) * 100
                budget.save()
                if budget.spended >= budget.amount:
                    Notification.objects.create(
                        user=wallet.user,
                        type='BUDGET_EXCEEDED',
                        message=f"You exceeded budget for {budget.category.name}"
                    )
                else:
                    Notification.objects.create(
                        user=wallet.user,
                        type='BUDGET_ALERT',
                        message=f"Budget update: {budget.category.name} is now {budget.percentage:.1f}% used"
                    )

            if goal:
                if goal.current_amount + amount > goal.target_amount:
                    raise ValidationError("Exceed the limit of goal")

                goal.current_amount += amount

                if goal.current_amount >= goal.target_amount:
                    goal.status = 'complete'
                    Notification.objects.create(
                        user=wallet.user,
                        type='GOAL_COMPLETE',
                        message=f"🎉 Goal completed: {goal.name}"
                    )
                else:
                    Notification.objects.create(
                        user=wallet.user,
                        type='GOAL_PROGRESS',
                        message=f"Saving goal updated: {goal.name} ({goal.current_amount}/{goal.target_amount})"
                    )

                goal.save()
        elif type == 'send':
            fee = 0

            if amount > wallet.total_balance:
                raise ValidationError("Not enough balance")

            if wallet.send_limit > 0:
                wallet.send_limit -= 1
            else:
                fee = 2.0

            total_deduction = amount + fee

            if total_deduction > wallet.total_balance:
                raise ValidationError("Not enough balance after fee")

            reciever.total_balance += amount
            reciever.total_income += amount

            wallet.total_balance -= total_deduction
            wallet.total_expense += total_deduction

            reciever.save()
            wallet.save()
            Notification.objects.create(
            user=reciever.user,
            type='GENERAL',
            message=f"You received {amount} from {wallet.user}"
            )

            Notification.objects.create(
                user=wallet.user,
                type='GENERAL',
                message=f"You sent {amount} successfully"
            )
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        



    def get_queryset(self):
        queryset = models.Transaction.objects.all()
        type = self.request.query_params.get('type')

        if type is not None:
            queryset = queryset.filter(type=type)

        if self.request.user.is_staff:
            return queryset
        
        return queryset.filter(
        Q(wallet__user=self.request.user) |
        Q(reciever__user=self.request.user)
        )
    

class CategoryViewSets(ModelViewSet):
    serializer_class = serializer.CategorySerializer
    permission_classes = [IsAuthenticated,permessions.IsMyCategory]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Category.objects.all()
        return models.Category.objects.filter(
            wallet__user=self.request.user
        )
    
    def perform_create(self, serializer):
        wallet = self.request.user.wallet
        serializer.save(wallet=wallet)

    

class BudgetViewSets(ModelViewSet):
    serializer_class = serializer.BudgetSerializer
    permission_classes = [IsAuthenticated,permessions.IsMyBudget]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Budget.objects.all()
        return models.Budget.objects.filter(
            wallet__user=self.request.user
        )

    

    
class SavingGoalsViewSets(ModelViewSet):
    serializer_class = serializer.SavingGoalsSerializer
    permission_classes = [IsAuthenticated,permessions.IsMySaving]
    query = models.SavingGoals.objects.all()

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.query
        return self.query.filter(wallet=self.request.user.wallet)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        total_target = queryset.aggregate(
            total=Sum('target_amount')
        )['total'] or 0

        total_current = queryset.aggregate(
            current=Sum('current_amount')
        )['current'] or 0

        complete_percentage = (
            round((total_current / total_target) * 100, 2)
            if total_target else 0
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data.update({
                'summary': {
                    'total_target': total_target,
                    'total_current': total_current,
                    'complete_percentage': complete_percentage,
                }
            })
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'summary': {
                'total_target': total_target,
                'total_current': total_current,
                'complete_percentage': complete_percentage,
            },
            'saving_goals': serializer.data,
        })

