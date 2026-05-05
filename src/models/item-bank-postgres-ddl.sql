CREATE TYPE purpose_enum AS ENUM ('STIMULUS', 'SOLUTION');

CREATE TYPE license_enum AS ENUM (
    'CC0',
    'CC_BY',
    'CC_BY_SA',
    'CC_BY_ND',
    'CC_BY_NC',
    'CC_BY_NC_SA',
    'CC_BY_NC_ND'
);

CREATE TYPE item_collection_order_enum AS ENUM ('LINEAR', 'ARBITRARY');


CREATE TABLE Author (
    author_id BIGINT PRIMARY KEY,
    descriptor VARCHAR,
    mail VARCHAR
);

CREATE TABLE License (
    license_id BIGINT PRIMARY KEY,
    license license_enum
);

CREATE TABLE Item_Type (
    item_type_id BIGINT PRIMARY KEY,
    item_type_name VARCHAR,
    description VARCHAR
);

CREATE TABLE Item_Content_Type (
    item_content_type_id BIGINT PRIMARY KEY,
    item_content_type_name VARCHAR,
    description VARCHAR
);


CREATE TABLE Tag (
    tag_id BIGINT PRIMARY KEY,
    parent_tag_id BIGINT,
    tag VARCHAR,
    description VARCHAR,
    CONSTRAINT fk_tag_parent
        FOREIGN KEY (parent_tag_id)
        REFERENCES Tag(tag_id)
);

CREATE TABLE Item_Representation_Template (
    item_template_id BIGINT PRIMARY KEY,
    template JSONB
);

CREATE TABLE Item (
    item_id BIGINT PRIMARY KEY,
    author_id BIGINT NOT NULL,
    license_id BIGINT NOT NULL,
    item_type_id BIGINT NOT NULL,
    item_template_id BIGINT,
    root_item_id BIGINT,

    CONSTRAINT fk_item_author
        FOREIGN KEY (author_id)
        REFERENCES Author(author_id),

    CONSTRAINT fk_item_license
        FOREIGN KEY (license_id)
        REFERENCES License(license_id),

    CONSTRAINT fk_item_type
        FOREIGN KEY (item_type_id)
        REFERENCES Item_Type(item_type_id),

    CONSTRAINT fk_item_template
        FOREIGN KEY (item_template_id)
        REFERENCES Item_Representation_Template(item_template_id),

    CONSTRAINT fk_item_root
        FOREIGN KEY (root_item_id)
        REFERENCES Item(item_id)
);

CREATE TABLE Item_Content (
    item_content_id BIGINT PRIMARY KEY,
    license_id BIGINT,
    item_content_type_id BIGINT,
    author_id BIGINT,
    json_serialized_content JSONB,
    blob_serialized_content BYTEA,

    CONSTRAINT fk_content_license
        FOREIGN KEY (license_id)
        REFERENCES License(license_id),

    CONSTRAINT fk_content_type
        FOREIGN KEY (item_content_type_id)
        REFERENCES Item_Content_Type(item_content_type_id),

    CONSTRAINT fk_content_author
        FOREIGN KEY (author_id)
        REFERENCES Author(author_id)
);


CREATE TABLE Item_Contents (
    item_content_id BIGINT,
    item_id BIGINT,
    purpose purpose_enum,

    PRIMARY KEY (item_content_id, item_id),

    CONSTRAINT fk_item_contents_content
        FOREIGN KEY (item_content_id)
        REFERENCES Item_Content(item_content_id),

    CONSTRAINT fk_item_contents_item
        FOREIGN KEY (item_id)
        REFERENCES Item(item_id)
);


CREATE TABLE Item_Tags (
    item_id BIGINT,
    tag_id BIGINT,

    PRIMARY KEY (item_id, tag_id),

    FOREIGN KEY (item_id) REFERENCES Item(item_id),
    FOREIGN KEY (tag_id) REFERENCES Tag(tag_id)
);

CREATE TABLE Item_Content_Tags (
    item_content_id BIGINT,
    tag_id BIGINT,

    PRIMARY KEY (item_content_id, tag_id),

    FOREIGN KEY (item_content_id) REFERENCES Item_Content(item_content_id),
    FOREIGN KEY (tag_id) REFERENCES Tag(tag_id)
);

CREATE TABLE Modifier (
    modifier_id BIGINT PRIMARY KEY,
    description VARCHAR,
    modifier VARCHAR
);

CREATE TABLE Item_Modifier (
    item_id BIGINT,
    modifier_id BIGINT,

    PRIMARY KEY (item_id, modifier_id),

    FOREIGN KEY (item_id) REFERENCES Item(item_id),
    FOREIGN KEY (modifier_id) REFERENCES Modifier(modifier_id)
);


CREATE TABLE Validator (
    validator_id BIGINT PRIMARY KEY,
    description VARCHAR,
    validator VARCHAR
);

CREATE TABLE Item_Validator (
    validator_id BIGINT,
    item_id BIGINT,

    PRIMARY KEY (validator_id, item_id),

    FOREIGN KEY (validator_id) REFERENCES Validator(validator_id),
    FOREIGN KEY (item_id) REFERENCES Item(item_id)
);

CREATE TABLE Item_Content_Types (
    item_type_id BIGINT,
    item_content_type_id BIGINT,

    PRIMARY KEY (item_type_id, item_content_type_id),

    FOREIGN KEY (item_type_id)
        REFERENCES Item_Type(item_type_id),

    FOREIGN KEY (item_content_type_id)
        REFERENCES Item_Content_Type(item_content_type_id)
);


CREATE TABLE Item_Collection (
    item_collection_id BIGINT PRIMARY KEY,
    parent_item_id BIGINT,
    order_type item_collection_order_enum,

    FOREIGN KEY (parent_item_id)
        REFERENCES Item(item_id)
);


CREATE TABLE Item_Collection_Sub_Item (
    item_collection_id BIGINT,
    subitem_id BIGINT,
    position INT,

    PRIMARY KEY (item_collection_id, subitem_id),

    FOREIGN KEY (item_collection_id)
        REFERENCES Item_Collection(item_collection_id),

    FOREIGN KEY (subitem_id)
        REFERENCES Item(item_id)
);