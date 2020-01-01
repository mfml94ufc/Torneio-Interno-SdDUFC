# Generated by Django 2.0.8 on 2018-08-19 17:06

from django.db import migrations

from dynamic_preferences.serializers import BooleanSerializer, SerializationError


def convert_public_draw(apps, schema_editor):

    Tournament = apps.get_model('tournaments', 'Tournament')  # noqa: N806
    TournamentPreferenceModel = apps.get_model('options', 'TournamentPreferenceModel')  # noqa: N806

    for tournament in Tournament.objects.all():
        try:
            public_pref = TournamentPreferenceModel.objects.get(
                section='public_features', name='public_draw', instance_id=tournament.id)
            show_all_pref = TournamentPreferenceModel.objects.get(
                section='ui_options', name='show_all_draws', instance_id=tournament.id)
        except TournamentPreferenceModel.DoesNotExist:
            continue

        try:
            public_pref_value = BooleanSerializer.to_python(public_pref.raw_value)
        except SerializationError as e:
            print("Warning: public_features__public_draw is {}, leaving untouched".format(public_pref.raw_value))
            continue

        try:
            show_all_pref_value = BooleanSerializer.to_python(show_all_pref.raw_value)
        except SerializationError as e:
            print("Warning: ui_options__show_all_draws is {}, leaving untouched".format(show_all_pref.raw_value))
            continue

        if public_pref_value and show_all_pref_value:
            public_pref.raw_value = 'all-released'
        elif public_pref_value:
            public_pref.raw_value = 'current'
        else:
            public_pref.raw_value = 'off'
        public_pref.save()

        show_all_pref.delete()


def convert_public_draw_reverse(apps, schema_editor):

    Tournament = apps.get_model('tournaments', 'Tournament')  # noqa: N806
    TournamentPreferenceModel = apps.get_model('options', 'TournamentPreferenceModel')  # noqa: N806

    for tournament in Tournament.objects.all():
        try:
            public_pref = TournamentPreferenceModel.objects.get(
                section='public_features', name='public_draw', instance_id=tournament.id)
        except TournamentPreferenceModel.DoesNotExist:
            continue

        if public_pref.raw_value == 'off':
            public_pref_value = False
            show_all_pref_value = False
        elif public_pref.raw_value == 'current':
            public_pref_value = True
            show_all_pref_value = False
        elif public_pref.raw_value == 'all-released':
            public_pref_value = True
            show_all_pref_value = True
        else:
            print("Warning: public_features__public_draw is {}, leaving untouched".format(public_pref.raw_value))
            continue

        public_pref.raw_value = public_pref_value
        public_pref.save()

        show_all_pref, created = TournamentPreferenceModel.objects.get_or_create(
            section='ui_options', name='show_all_draws', instance_id=tournament.id,
            defaults={'raw_value': show_all_pref_value})


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0005_speaker_standings'),
    ]

    operations = [
        migrations.RunPython(convert_public_draw,
            convert_public_draw_reverse,
            elidable=True),
    ]
