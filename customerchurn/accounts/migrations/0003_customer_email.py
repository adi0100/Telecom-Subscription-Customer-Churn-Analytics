from django.db import migrations, models


def add_email_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'customers'
    with connection.cursor() as cursor:
        if table_name not in connection.introspection.table_names(cursor):
            return
        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }

    if 'email' not in columns:
        customer_model = apps.get_model('accounts', 'Customers')
        email_type = customer_model._meta.get_field('email').db_type(connection)
        schema_editor.execute(
            f'ALTER TABLE {schema_editor.quote_name(table_name)} '
            f'ADD COLUMN {schema_editor.quote_name("email")} {email_type} NULL'
        )


def remove_email_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'customers'
    with connection.cursor() as cursor:
        if table_name not in connection.introspection.table_names(cursor):
            return
        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }

    if 'email' in columns:
        schema_editor.execute(
            f'ALTER TABLE {schema_editor.quote_name(table_name)} '
            f'DROP COLUMN {schema_editor.quote_name("email")}'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_churnprediction'),
    ]

    operations = [
        migrations.AddField(
            model_name='customers',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.RunPython(add_email_column, remove_email_column),
    ]
