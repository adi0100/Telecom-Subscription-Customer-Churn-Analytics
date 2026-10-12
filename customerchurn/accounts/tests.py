from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from .views import AGENT_GROUP_NAME


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
