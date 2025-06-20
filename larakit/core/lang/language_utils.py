from larakit.core.lang.language import Language


class LanguageUtils:
    @staticmethod
    def parse_chinese_script(language: Language) -> str:
        if not isinstance(language, Language):
            raise TypeError("Expected an instance of Language")
        if language.code() != 'zh':
            raise ValueError("Language must be Chinese (zh) to parse script")

        if language.script and language.script in ('Hans', 'Hant'):
            return language.code_script()

        return 'zh-Hans' if language.region is None or language.region in ('CN', 'SG') else 'zh-Hant'
