# Generated by Django 4.2.5 on 2024-05-12 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_remove_order_date_ordered_alter_order_transaction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='isHotSaled',
            field=models.BooleanField(default=False),
        ),
    ]