# Generated by Django 5.1.7 on 2025-03-16 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0009_delete_decision_delete_evalution_delete_recognition'),
    ]

    operations = [
        migrations.CreateModel(
            name='Decision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('judge', models.TextField(blank=True, null=True)),
                ('PhoneAction', models.TextField(blank=True, null=True)),
                ('EDIAction', models.TextField(blank=True, null=True)),
                ('RecordAction', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'decision',
            },
        ),
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('judge', models.TextField(blank=True, null=True)),
                ('alert', models.TextField(blank=True, null=True)),
                ('week', models.TextField(blank=True, null=True)),
                ('retail', models.TextField(blank=True, null=True)),
                ('wholesale', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'evaluation',
            },
        ),
        migrations.CreateModel(
            name='Recognition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert', models.TextField(blank=True, null=True)),
                ('week', models.TextField(blank=True, null=True)),
                ('retail', models.TextField(blank=True, null=True)),
                ('wholesale', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'recognition',
            },
        ),
    ]
