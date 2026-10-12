from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.db import connection
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from .views import AGENT_GROUP_NAME
from .models import AgentActivity, BillingAccounts, ChurnPrediction, ChurnRecords, Customers, Services, SystemUsers


User = get_user_model()


class AgentManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin-password',
        )
        self.agent_group = Group.objects.create(name=AGENT_GROUP_NAME)

    def test_superuser_can_view_agent_manager(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('agent_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add an agent')
        self.assertContains(response, 'No agents have been added yet.')

    def test_superuser_can_add_agent(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse('agent_list'), {
            'username': 'agent1',
            'full_name': 'Alex Agent',
            'email': 'agent@example.com',
            'password1': 'StrongAgentPassword123!',
            'password2': 'StrongAgentPassword123!',
        })

        self.assertRedirects(response, reverse('agent_list'))
        agent = User.objects.get(username='agent1')
        self.assertTrue(agent.check_password('StrongAgentPassword123!'))
        self.assertEqual(agent.get_full_name(), 'Alex Agent')
        self.assertIn(self.agent_group, agent.groups.all())
        self.assertFalse(agent.is_staff)
        self.assertFalse(agent.is_superuser)

    def test_superuser_can_remove_agent(self):
        agent = User.objects.create_user(
            username='agent1',
            password='StrongAgentPassword123!',
        )
        agent.groups.add(self.agent_group)
        self.client.force_login(self.admin)

        response = self.client.post(reverse('agent_remove', args=[agent.pk]))

        self.assertRedirects(response, reverse('agent_list'))
        self.assertFalse(User.objects.filter(pk=agent.pk).exists())

    def test_non_superuser_cannot_manage_agents(self):
        regular_user = User.objects.create_user(
            username='regular',
            password='regular-password',
        )
        self.client.force_login(regular_user)

        response = self.client.get(reverse('agent_list'))

        self.assertEqual(response.status_code, 403)

    def test_agent_removal_requires_post(self):
        agent = User.objects.create_user(
            username='agent1',
            password='StrongAgentPassword123!',
        )
        agent.groups.add(self.agent_group)
        self.client.force_login(self.admin)

        response = self.client.get(reverse('agent_remove', args=[agent.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(pk=agent.pk).exists())

    def test_non_agent_accounts_cannot_be_removed_from_agent_page(self):
        regular_user = User.objects.create_user(
            username='regular',
            password='regular-password',
        )
        self.client.force_login(self.admin)

        response = self.client.post(reverse('agent_remove', args=[regular_user.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(User.objects.filter(pk=regular_user.pk).exists())


class DashboardDataTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            for model in (SystemUsers, Customers, Services, BillingAccounts, ChurnRecords):
                schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            for model in (ChurnRecords, BillingAccounts, Services, Customers, SystemUsers):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='dashboard-admin',
            email='dashboard-admin@example.com',
            password='admin-password',
        )
        self.client.force_login(self.admin)
        Customers.objects.all().delete()
        self._create_customer('A-001', 'Month-to-month', 'Yes', 0.91, 'High')
        self._create_customer('A-002', 'Month-to-month', 'Yes', 0.82, 'High')
        self._create_customer('A-003', 'Month-to-month', 'No', 0.42, 'Medium')
        self._create_customer('A-004', 'One year', 'Yes', 0.76, 'High')
        self._create_customer('A-005', 'One year', 'No', 0.12, 'Low')

    def _create_customer(self, customer_id, contract, churn_status, probability, risk_level):
        customer = Customers.objects.create(customer_id=customer_id)
        BillingAccounts.objects.create(customer=customer, contract=contract, tenure=2)
        ChurnRecords.objects.create(customer=customer, churn_status=churn_status)
        ChurnPrediction.objects.create(
            customer=customer,
            churn_probability=probability,
            risk_level=risk_level,
        )

    def test_dashboard_metrics_and_charts_use_current_database_data(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['customer_count'], 5)
        self.assertEqual(response.context['churned_count'], 3)
        self.assertEqual(response.context['retained_count'], 2)
        self.assertEqual(response.context['churn_rate'], 60.0)
        self.assertEqual(response.context['high_risk_contract'], {
            'label': 'Month-to-month',
            'churn_rate': 66.7,
        })
        self.assertEqual(response.context['status_chart_data'], [2, 3])
        self.assertEqual(
            [item['label'] for item in response.context['contract_chart_data']],
            ['Month-to-month', 'One year'],
        )
        self.assertContains(response, 'A-001')
        self.assertContains(response, '66.7%')

    def test_dashboard_handles_missing_churn_and_prediction_data(self):
        Customers.objects.all().delete()

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.context['customer_count'], 0)
        self.assertIsNone(response.context['churn_rate'])
        self.assertIsNone(response.context['high_risk_contract'])
        self.assertEqual(response.context['risk_customers'].count(), 0)
        self.assertContains(response, 'No churn predictions are available yet.')

    def test_customer_list_shows_saved_risk_levels_and_missing_prediction(self):
        customer_without_prediction = Customers.objects.create(customer_id='A-006')
        BillingAccounts.objects.create(
            customer=customer_without_prediction,
            contract='Two year',
            tenure=12,
        )
        ChurnRecords.objects.create(customer=customer_without_prediction, churn_status='No')

        response = self.client.get(reverse('customer_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Risk level')
        self.assertContains(response, 'High')
        self.assertContains(response, 'Medium')
        self.assertContains(response, 'Low')
        self.assertContains(response, 'Not predicted')

    def test_agent_can_add_customer_email_and_return_to_filtered_page(self):
        customer = Customers.objects.get(customer_id='A-001')

        response = self.client.post(
            reverse('customer_email_update', args=[customer.customer_id]),
            {
                'email': 'customer@example.com',
                'customer_id': customer.customer_id,
                'risk_level': 'High',
                'customer_state': 'active',
                'page': '2',
            },
        )

        self.assertRedirects(
            response,
            f'{reverse("customer_list")}?customer_id=A-001&risk_level=High&customer_state=active&page=2',
        )
        customer.refresh_from_db()
        self.assertEqual(customer.email, 'customer@example.com')
        self.assertEqual(
            AgentActivity.objects.filter(
                actor=self.admin,
                action='email_updated',
                customer_id=customer.customer_id,
            ).count(),
            1,
        )
        customer_list = self.client.get(reverse('customer_list'), {'customer_id': customer.customer_id})
        self.assertContains(customer_list, 'mailto:customer@example.com')
        self.assertContains(customer_list, 'customer@example.com')

    def test_invalid_customer_email_is_not_saved(self):
        customer = Customers.objects.get(customer_id='A-001')

        response = self.client.post(
            reverse('customer_email_update', args=[customer.customer_id]),
            {'email': 'not-an-email'},
        )

        self.assertRedirects(response, reverse('customer_list'))
        customer.refresh_from_db()
        self.assertIsNone(customer.email)

    def test_customer_list_filters_by_risk_and_hides_churn_status(self):
        response = self.client.get(reverse('customer_list'), {'risk_level': 'High'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.count, 3)
        self.assertContains(response, 'A-001')
        self.assertNotContains(response, 'A-003')
        self.assertNotContains(response, 'Churn status')

    def test_agent_can_add_customer_with_name_billing_and_services(self):
        agent = User.objects.create_user(
            username='customer-agent',
            password='agent-password',
        )
        self.client.force_login(agent)

        response = self.client.post(reverse('customer_create'), {
            'name': 'Taylor Customer',
            'email': 'taylor@example.com',
            'gender': 'Female',
            'contract': 'Month-to-month',
            'monthly_charges': '79.95',
            'churn_status': 'No',
            'phone_service': 'Yes',
            'multiple_lines': 'Yes',
            'internet_service': 'Fiber optic',
            'online_security': 'Yes',
            'online_backup': 'No',
            'device_protection': 'Yes',
            'tech_support': 'No',
            'streaming_tv': 'Yes',
            'streaming_movies': 'No',
        })

        self.assertRedirects(response, reverse('customer_list'))
        customer = Customers.objects.get(name='Taylor Customer')
        self.assertRegex(customer.pk, r'^CUST-[0-9A-F]{32}$')
        self.assertEqual(customer.name, 'Taylor Customer')
        self.assertEqual(customer.email, 'taylor@example.com')
        self.assertEqual(customer.billingaccounts.monthly_charges, Decimal('79.95'))
        self.assertEqual(customer.billingaccounts.contract, 'Month-to-month')
        self.assertEqual(customer.services.internet_service, 'Fiber optic')
        self.assertEqual(customer.services.online_security, 'Yes')
        self.assertEqual(customer.churnrecords.churn_status, 'No')
        self.assertTrue(AgentActivity.objects.filter(
            actor=agent,
            action='customer_created',
            customer_id=customer.pk,
        ).exists())
        form_page = self.client.get(reverse('customer_create'))
        self.assertNotContains(form_page, 'Customer ID')

    def test_new_customer_name_is_required(self):
        customer_count = Customers.objects.count()
        response = self.client.post(reverse('customer_create'), {
            'contract': 'One year',
            'monthly_charges': '45.00',
            'churn_status': 'No',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customers.objects.count(), customer_count)
        self.assertIn('name', response.context['form'].errors)

    def test_existing_customer_name_can_remain_empty(self):
        customer = Customers.objects.get(pk='A-001')
        self.assertIsNone(customer.name)

        response = self.client.get(reverse('customer_edit', args=[customer.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].fields['name'].required)

    def test_edit_updates_contract_monthly_charges_and_all_services(self):
        customer = Customers.objects.get(pk='A-001')
        response = self.client.post(reverse('customer_edit', args=[customer.pk]), {
            'name': 'Updated Customer Name',
            'email': '',
            'contract': 'Two year',
            'monthly_charges': '120.50',
            'total_charges': '500.00',
            'churn_status': 'Yes',
            'phone_service': 'Yes',
            'multiple_lines': 'No',
            'internet_service': 'DSL',
            'online_security': 'Yes',
            'online_backup': 'Yes',
            'device_protection': 'No',
            'tech_support': 'Yes',
            'streaming_tv': 'No',
            'streaming_movies': 'Yes',
        })

        self.assertRedirects(response, reverse('customer_list'))
        customer.refresh_from_db()
        self.assertEqual(customer.name, 'Updated Customer Name')
        self.assertEqual(customer.billingaccounts.contract, 'Two year')
        self.assertEqual(customer.billingaccounts.monthly_charges, Decimal('120.50'))
        self.assertEqual(customer.services.internet_service, 'DSL')
        self.assertEqual(customer.services.streaming_movies, 'Yes')
        self.assertTrue(AgentActivity.objects.filter(
            actor=self.admin,
            action='customer_updated',
            customer_id=customer.pk,
        ).exists())

    def test_contract_chart_reflects_billing_and_churn_changes(self):
        customer = Customers.objects.get(pk='A-005')
        self.client.post(reverse('customer_edit', args=[customer.pk]), {
            'contract': 'Month-to-month',
            'monthly_charges': '45.00',
            'churn_status': 'Yes',
        })

        response = self.client.get(reverse('dashboard'))
        rates = {item['label']: item['churn_rate'] for item in response.context['contract_chart_data']}

        self.assertEqual(rates['Month-to-month'], 75.0)
        self.assertEqual(rates['One year'], 100.0)

    def test_agent_can_archive_and_restore_churned_customer_without_deleting_history(self):
        customer = Customers.objects.get(customer_id='A-001')
        archive_response = self.client.post(
            reverse('customer_archive', args=[customer.customer_id]),
            {'risk_level': 'High', 'customer_state': 'active'},
        )

        self.assertRedirects(
            archive_response,
            f'{reverse("customer_list")}?risk_level=High&customer_state=active',
        )
        customer.refresh_from_db()
        self.assertTrue(customer.is_archived)
        self.assertTrue(BillingAccounts.objects.filter(customer=customer).exists())
        self.assertTrue(ChurnRecords.objects.filter(customer=customer).exists())
        self.assertTrue(ChurnPrediction.objects.filter(customer=customer).exists())
        self.assertNotContains(self.client.get(reverse('customer_list')), 'A-001')

        archived_response = self.client.get(
            reverse('customer_list'),
            {'customer_state': 'archived'},
        )
        self.assertContains(archived_response, 'A-001')
        restore_response = self.client.post(
            reverse('customer_restore', args=[customer.customer_id]),
            {'customer_state': 'active'},
        )
        self.assertRedirects(
            restore_response,
            f'{reverse("customer_list")}?customer_state=active',
        )
        customer.refresh_from_db()
        self.assertFalse(customer.is_archived)
        self.assertEqual(
            AgentActivity.objects.filter(
                customer_id=customer.customer_id,
                action__in=('customer_archived', 'customer_restored'),
            ).count(),
            2,
        )

    def test_only_churned_customers_can_be_archived(self):
        customer = Customers.objects.get(customer_id='A-005')

        response = self.client.post(reverse('customer_archive', args=[customer.customer_id]))

        self.assertRedirects(response, reverse('customer_list'))
        customer.refresh_from_db()
        self.assertFalse(customer.is_archived)
        self.assertFalse(
            AgentActivity.objects.filter(
                customer_id=customer.customer_id,
                action='customer_archived',
            ).exists()
        )

    def test_agent_activity_page_only_shows_current_agents_own_activity(self):
        agent = User.objects.create_user(
            username='current-agent',
            password='agent-password',
        )
        other_agent = User.objects.create_user(
            username='other-agent',
            password='other-password',
        )
        AgentActivity.objects.create(
            actor=agent,
            actor_username=agent.username,
            action='email_updated',
            details='Updated my customer.',
        )
        AgentActivity.objects.create(
            actor=other_agent,
            actor_username=other_agent.username,
            action='email_updated',
            details='Updated another customer.',
        )
        self.client.force_login(agent)

        response = self.client.get(reverse('agent_activity'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Updated my customer.')
        self.assertNotContains(response, 'Updated another customer.')
