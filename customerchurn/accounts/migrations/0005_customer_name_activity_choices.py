from django.db import migrations, models


def add_name_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'customers'
    with connection.cursor() as cursor:
        if table_name not in connection.introspection.table_names(cursor):
            return
        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }

    if 'name' not in columns:
        customer_model = apps.get_model('accounts', 'Customers')
        name_type = customer_model._meta.get_field('name').db_type(connection)
        schema_editor.execute(
            f'ALTER TABLE {schema_editor.quote_name(table_name)} '
            f'ADD COLUMN {schema_editor.quote_name("name")} {name_type} NULL'
        )


def remove_name_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'customers'
    with connection.cursor() as cursor:
        if table_name not in connection.introspection.table_names(cursor):
            return
        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }

    if 'name' in columns:
        schema_editor.execute(
            f'ALTER TABLE {schema_editor.quote_name(table_name)} '
            f'DROP COLUMN {schema_editor.quote_name("name")}'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_customer_archive_agent_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='customers',
            name='name',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='agentactivity',
            name='action',
            field=models.CharField(
                choices=[
                    ('email_updated', 'Customer email updated'),
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
        migrations.RunPython(add_name_column, remove_name_column),
    ]
