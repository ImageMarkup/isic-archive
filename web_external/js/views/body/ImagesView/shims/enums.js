// TODO: there's probably a better way to import these...

isic.ENUMS = {};

isic.ENUMS.DEFAULT_INTERPRETATIONS = {
    'undefined': 'categorical',
    'null': 'categorical',
    boolean: 'categorical',
    integer: 'ordinal',
    number: 'ordinal',
    date: 'categorical',
    string: 'categorical',
    object: 'categorical'
};

isic.ENUMS.ATTRIBUTE_GENERALITY = [
    'object',
    'string',
    'number',
    'integer'
];

isic.ENUMS.FILTER_STATES = {
    NO_FILTERS: 0,
    FILTERED: 1,
    EXCLUDED: 2
};

isic.ENUMS.BIN_STATES = {
    INCLUDED: 0,
    EXCLUDED: 1,
    PARTIAL: 2
};

// TODO: It should be trivial to borrow code from Resonant Laboratory to
// autodetect this (requires an additional server endpoint)
isic.ENUMS.SCHEMA = {
    'folderId': {
        'coerceToType': 'string',
        'humanName': 'Dataset'
    },
    'meta.clinical.benign_malignant': {
        'coerceToType': 'string',
        'humanName': 'Benign / Malignant'
    },
    'meta.clinical.sex': {
        'coerceToType': 'string',
        'humanName': 'Sex'
    },
    'meta.clinical.age': {
        'coerceToType': 'number',
        'interpretation': 'ordinal',
        'humanName': 'Age',
        'lowBound': 0,
        'highBound': 100,
        'numBins': 10
    },
    'meta.clinical.clin_size_long_diam_mm': {
        'coerceToType': 'number',
        'interpretation': 'ordinal',
        'humanName': 'Clinical Size - Longest Diameter (mm)',
        'lowBound': 0,
        'highBound': 100,
        'numBins': 10
    }
};
