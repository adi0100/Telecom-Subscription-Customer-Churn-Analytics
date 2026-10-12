from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_customer_id_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentactivity',
            name='action',
            field=models.CharField(
                choices=[
                    ('email_updated', 'Customer email updated'),
                    ('predictions_run', 'Churn predictions run'),
                    ('customer_created', 'Customer record created'),
                    ('customer_updated', 'Customer record updated'),
                    ('customer_archived', 'Churned customer archived'),
                    ('customer_restored', 'Customer restored'),
                    ('agent_added', 'Agent added'),
                    ('agent_removed', 'Agent removed'),
                ],
                max_length=32,
            ),
        ),
    ]
