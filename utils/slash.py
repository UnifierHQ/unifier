import nextcord

class SlashHelper:
    def __init__(self, language):
        self.language = language

    def option(self, name, *args, **kwargs):
        cogname, cmdname, optionname = name.split('.')
        localizations = self.language.slash_options(cogname+'.'+cmdname)
        if not localizations:
            return nextcord.SlashOption(
                *args,
                name=optionname,
                **kwargs
            )

        base = localizations.pop(self.language.get_locale())

        names = {}
        descriptions = {}

        for locale in localizations.keys():
            try:
                names.update({locale: localizations[locale][optionname]['name']})
                descriptions.update({locale: localizations[locale][optionname]['description']})
            except KeyError:
                pass

        return nextcord.SlashOption(
            *args,
            name=optionname,
            description=base[optionname]['description'],
            name_localizations=names,
            description_localizations=descriptions,
            **kwargs
        )
