# -*- coding: utf-8 -*-
""" Drag and Drop v2 XBlock - Utils """
from collections import namedtuple


def _(text):
    """ Dummy `gettext` replacement to make string extraction tools scrape strings marked for translation """
    return text


def ngettext_fallback(text_singular, text_plural, number):
    """ Dummy `ngettext` replacement to make string extraction tools scrape strings marked for translation """
    if number == 1:
        return text_singular
    else:
        return text_plural


class DummyTranslationService(object):
    """
    Dummy drop-in replacement for i18n XBlock service
    """
    gettext = _
    ngettext = ngettext_fallback


class FeedbackMessages(object):
    """
    Feedback messages collection
    """
    class MessageClasses(object):
        """
        Namespace for message classes
        """
        CORRECT_SOLUTION = "correct"
        PARTIAL_SOLUTION = "partial"
        INCORRECT_SOLUTION = "incorrect"

        CORRECTLY_PLACED = CORRECT_SOLUTION
        MISPLACED = INCORRECT_SOLUTION
        NOT_PLACED = INCORRECT_SOLUTION

    FINAL_ATTEMPT_TPL = _('Final attempt was used, highest score is {score}')
    MISPLACED_ITEMS_RETURNED = _('Misplaced item(s) were returned to item bank.')

    @staticmethod
    def correctly_placed(number, ngettext=ngettext_fallback):
        """
        Formats "correctly placed items" message
        """
        return ngettext(
            'Correctly placed {correct_count} item.',
            'Correctly placed {correct_count} items.',
            number
        ).format(correct_count=number)

    @staticmethod
    def misplaced(number, ngettext=ngettext_fallback):
        """
        Formats "misplaced items" message
        """
        return ngettext(
            'Misplaced {misplaced_count} item. Misplaced item was returned to item bank.',
            'Misplaced {misplaced_count} items. Misplaced items were returned to item bank.',
            number
        ).format(misplaced_count=number)

    @staticmethod
    def not_placed(number, ngettext=ngettext_fallback):
        """
        Formats "did not place required items" message
        """
        return ngettext(
            'Did not place {missing_count} required item.',
            'Did not place {missing_count} required items.',
            number
        ).format(missing_count=number)


FeedbackMessage = namedtuple("FeedbackMessage", ["message", "message_class"])  # pylint: disable=invalid-name
ItemStats = namedtuple(  # pylint: disable=invalid-name
    'ItemStats',
    ["required", "placed", "correctly_placed", "decoy", "decoy_in_bank"]
)


class Constants(object):
    """
    Namespace class for various constants
    """
    ALLOWED_ZONE_ALIGNMENTS = ['left', 'right', 'center']
    DEFAULT_ZONE_ALIGNMENT = 'center'


class StateMigration(object):
    """
    Helper class to apply zone data and item state migrations
    """

    @classmethod
    def _apply_migration(cls, obj, migrations):
        """
        Applies migrations sequentially to a copy of an `obj`, to avoid updating actual data
        """
        tmp = obj.copy()
        for method in migrations:
            tmp = method(tmp)

        return tmp

    @classmethod
    def apply_zone_migrations(cls, zone):
        """
        Applies zone migrations
        """
        migrations = (cls._zone_v1_to_v2, cls._zone_v2_to_v2p1)

        return cls._apply_migration(zone, migrations)

    @classmethod
    def apply_item_state_migrations(cls, item_state):
        """
        Applies item_state migrations
        """
        migrations = (cls._item_state_v1_to_v1p5, cls._item_state_v1p5_to_v2, cls._item_state_v2_to_v2p1)

        return cls._apply_migration(item_state, migrations)

    @classmethod
    def _zone_v1_to_v2(cls, zone):
        """
        Migrates zone data from v1.0 format to v2.0 format.

        Changes:
        * v1 used zone "title" as UID, while v2 zone has dedicated "uid" property
        * "id" and "index" properties are no longer used

        In: {'id': 1, 'index': 2, 'title': "Zone", ...}
        Out: {'uid': "Zone", ...}
        """
        if "uid" not in zone:
            zone["uid"] = zone.get("title")
        zone.pop("id", None)
        zone.pop("index", None)

        return zone

    @classmethod
    def _zone_v2_to_v2p1(cls, zone):
        """
        Migrates zone data from v2.0 to v2.1

        Changes:
        * Removed "none" zone alignment; default align is "center"

        In: {
            'uid': "Zone", "align": "none",
            "x_percent": "10%", "y_percent": "10%", "width_percent": "10%", "height_percent": "10%"
        }
        Out: {
            'uid': "Zone", "align": "center",
            "x_percent": "10%", "y_percent": "10%", "width_percent": "10%", "height_percent": "10%"
        }
        """
        if zone.get('align', None) not in Constants.ALLOWED_ZONE_ALIGNMENTS:
            zone['align'] = Constants.DEFAULT_ZONE_ALIGNMENT

        return zone

    @classmethod
    def _item_state_v1_to_v1p5(cls, item):
        """
        Migrates item_state from v1.0 to v1.5

        Changes:
        * Item state is now a dict instead of tuple

        In: ('100px', '120px')
        Out: {'top': '100px', 'left': '120px'}
        """
        if isinstance(item, dict):
            return item
        else:
            return {'top': item[0], 'left': item[1]}

    @classmethod
    def _item_state_v1p5_to_v2(cls, item):
        """
        Migrates item_state from v1.5 to v2.0

        Changes:
        * Item placement attributes switched from absolute (left-top) to relative (x_percent-y_percent) units

        In: {'zone': 'Zone", 'correct': True, 'top': '100px', 'left': '120px'}
        Out: {'zone': 'Zone", 'correct': True, 'top': '100px', 'left': '120px'}
        """
        # Conversion can't be made as parent dimensions are unknown to python - converted in JS
        # Since 2.1 JS this conversion became unnecesary, so it was removed from JS code
        return item

    @classmethod
    def _item_state_v2_to_v2p1(cls, item):
        """
        Migrates item_state from v2.0 to v2.1

        Changes:
        * Removed old "absolute" placement attributes
        * Removed "none" zone alignment, making "x_percent" and "y_percent" attributes obsolete

        In: {'zone': 'Zone", 'correct': True, 'top': '100px', 'left': '120px', 'absolute': true}
        Out: {'zone': 'Zone", 'correct': True}

        In: {'zone': 'Zone", 'correct': True, 'x_percent': '90%', 'y_percent': '20%'}
        Out: {'zone': 'Zone", 'correct': True}
        """
        attributes_to_remove = ['x_percent', 'y_percent', 'left', 'top', 'absolute']
        for attribute in attributes_to_remove:
            del[attribute]

        return item
