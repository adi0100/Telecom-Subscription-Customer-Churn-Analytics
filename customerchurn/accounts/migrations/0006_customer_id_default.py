import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_customer_name_activity_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customers',
            name='customer_id',
            field=models.CharField(
                default=accounts.models.generate_customer_id,
                max_length=50,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
