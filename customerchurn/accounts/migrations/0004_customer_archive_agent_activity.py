import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def add_archive_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'customers'
    with connection.cursor() as cursor:
        if table_name not in connection.introspection.table_names(cursor):
            return
        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }

    if 'is_archived' not in columns:
        customer_model = apps.get_model('accounts', 'Customers')
        archive_type = customer_model._meta.get_field('is_archived').db_type(connection)
        default_value = 'FALSE' if connection.vendor == 'postgresql' else '0'
        schema_editor.execute(
            f'ALTER TABLE {schema_editor.quote_name(table_name)} '
            f'ADD COLUMN {schema_editor.quote_name("is_archived")} '
            f'{archive_type} NOT NULL DEFAULT {default_value}'
        )


def remove_archive_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'customers'
    with connection.cursor() as cursor:
        if table_name not in connection.introspection.table_names(cursor):
            return
        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }

    if 'is_archived' in columns:
        schema_editor.execute(
            f'ALTER TABLE {schema_editor.quote_name(table_name)} '
            f'DROP COLUMN {schema_editor.quote_name("is_archived")}'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_customer_email'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='customers',
            name='is_archived',
            field=models.BooleanField(db_default=False, default=False),
        ),
        migrations.CreateModel(
            name='AgentActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actor_username', models.CharField(max_length=150)),
                ('action', models.CharField(
                    choices=[
                        ('email_updated', 'Customer email updated'),
                        ('customer_archived', 'Churned customer archived'),
                        ('customer_restored', 'Customer restored'),
                        ('agent_added', 'Agent added'),
                        ('agent_removed', 'Agent removed'),
                    ],
                    max_length=32,
                )),
                ('customer_id', models.CharField(blank=True, max_length=50)),
                ('details', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='agent_activities',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'agent_activities',
                'ordering': ('-created_at', '-pk'),
            },
        ),
        migrations.RunPython(add_archive_column, remove_archive_column),
    ]
