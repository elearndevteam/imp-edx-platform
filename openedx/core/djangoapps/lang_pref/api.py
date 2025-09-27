""" Python API for language and translation management. """

from collections import namedtuple

from django.conf import settings
from django.utils.translation import gettext as _
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.site_configuration.helpers import get_value

# === TVOJ logger (root: edx-platform/imp_logging.py) ===
import imp_logging  # koristi imp_logging.append_log(...)

Language = namedtuple('Language', 'code name')


def header_language_selector_is_enabled():
    """Return true if the header language selector has been enabled via settings or site-specific configuration."""
    setting = get_value('SHOW_HEADER_LANGUAGE_SELECTOR', settings.FEATURES.get('SHOW_HEADER_LANGUAGE_SELECTOR', False))
    deprecated_setting = get_value('SHOW_LANGUAGE_SELECTOR', settings.FEATURES.get('SHOW_LANGUAGE_SELECTOR', False))

    enabled = bool(setting or deprecated_setting)
    imp_logging.append_log(
        f"lang_pref.header_language_selector_is_enabled "
        f"SHOW_HEADER_LANGUAGE_SELECTOR={setting} SHOW_LANGUAGE_SELECTOR(depr)={deprecated_setting} result={enabled}"
    )
    return enabled


def footer_language_selector_is_enabled():
    """Return true if the footer language selector has been enabled via settings or site-specific configuration."""
    enabled = bool(get_value('SHOW_FOOTER_LANGUAGE_SELECTOR', settings.FEATURES.get('SHOW_FOOTER_LANGUAGE_SELECTOR', False)))
    imp_logging.append_log(
        f"lang_pref.footer_language_selector_is_enabled result={enabled}"
    )
    return enabled


def released_languages():
    """Retrieve the list of released languages."""
    try:
        dark_lang_config = DarkLangConfig.current()
    except Exception as exc:
        imp_logging.append_log(
            f"lang_pref.released_languages DarkLangConfig.current ERROR={exc!r} -> fallback to settings.LANGUAGES"
        )
        default_language_code = settings.LANGUAGE_CODE
        codes = sorted({default_language_code, *[c for c, _ in settings.LANGUAGES]})
        result = [Language(c, n) for (c, n) in settings.LANGUAGES if c in codes]
        imp_logging.append_log(
            f"lang_pref.released_languages.fallback codes={codes} count={len(result)}"
        )
        return result

    released_language_codes = list(dark_lang_config.released_languages_list or [])
    default_language_code = settings.LANGUAGE_CODE
    beta_enabled = bool(getattr(dark_lang_config, 'enable_beta_languages', False))

    imp_logging.append_log(
        f"lang_pref.released_languages.initial released={released_language_codes} "
        f"default={default_language_code} beta_enabled={beta_enabled}"
    )

    if default_language_code not in released_language_codes:
        released_language_codes.append(default_language_code)
        imp_logging.append_log(
            f"lang_pref.released_languages.append_default '{default_language_code}'"
        )

    if beta_enabled:
        beta_language_codes = list(dark_lang_config.beta_languages_list or [])
        for code in beta_language_codes:
            if code not in released_language_codes:
                released_language_codes.append(code)
        imp_logging.append_log(
            f"lang_pref.released_languages.merge_beta beta={beta_language_codes}"
        )

    released_language_codes.sort()

    result = [
        Language(language_info[0], language_info[1])
        for language_info in settings.LANGUAGES
        if language_info[0] in released_language_codes
    ]

    imp_logging.append_log(
        "lang_pref.released_languages.final "
        f"codes={released_language_codes} resolved={[f'{l.code}:{l.name}' for l in result]} "
        f"count={len(result)}"
    )
    return result


def all_languages():
    """Retrieve the list of all languages, translated and sorted."""
    languages = [(lang[0], _(lang[1])) for lang in settings.ALL_LANGUAGES]  # lint-amnesty, pylint: disable=translation-of-non-string
    sorted_languages = sorted(languages, key=lambda lang: lang[1])
    imp_logging.append_log(
        f"lang_pref.all_languages input_count={len(settings.ALL_LANGUAGES)} output_count={len(sorted_languages)}"
    )
    return sorted_languages


def get_closest_released_language(target_language_code):
    """
    Return the closest fully-supported language code for target, or None.
    """
    langs = released_languages()
    match = None

    for language in langs:
        if language.code == target_language_code:
            match = language.code
            break
        elif (match is None) and (language.code[:2] == target_language_code[:2]):
            match = language.code

    imp_logging.append_log(
        f"lang_pref.get_closest_released_language target={target_language_code} "
        f"match={match} candidates={[l.code for l in langs]}"
    )
    return match
