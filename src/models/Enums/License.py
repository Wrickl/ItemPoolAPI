import enum


class License(str, enum.Enum):
    CC0 = "CC0"
    CC_BY = "CC_BY"
    CC_BY_SA = "CC_BY_SA"
    CC_BY_ND = "CC_BY_ND"
    CC_BY_NC = "CC_BY_NC"
    CC_BY_NC_SA = "CC_BY_NC_SA"
    CC_BY_NC_ND = "CC_BY_NC_ND"

    ## TODO Für Ausarbeitung: Prüfen ob alle diese Lizenzen wirklich benötigt und sinnvoll sind
