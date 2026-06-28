import enum


class Status(str, enum.Enum):
    DRAFT = "Draft"
    REVIEW = "Review"
    APPROVED = "Approved"
    PRODUCTIV = "Productiv"
    RETIRED = "Retired"
    ## Todo Ausarbeitung/UI: Ist eine Beschreibung der  Status nötig?