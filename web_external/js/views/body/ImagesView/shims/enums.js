// TODO: there's probably a better way to import these...

window.ENUMS = {};

window.ENUMS.DEFAULT_INTERPRETATIONS = {
    'undefined': 'categorical',
    'null': 'categorical',
    boolean: 'categorical',
    integer: 'ordinal',
    number: 'ordinal',
    date: 'categorical',
    string: 'categorical',
    object: 'categorical'
};

window.ENUMS.ATTRIBUTE_GENERALITY = [
    'object',
    'string',
    'number',
    'integer'
];

window.ENUMS.FILTER_STATES = {
    NO_FILTERS: 0,
    FILTERED: 1,
    EXCLUDED: 2
};

window.ENUMS.BIN_STATES = {
    INCLUDED: 0,
    EXCLUDED: 1,
    PARTIAL: 2
};

// TODO: It should be trivial to borrow code from Resonant Laboratory to
// autodetect this (requires an additional server endpoint)
window.ENUMS.SCHEMA = {
    'folderId': {
        'coerceToType': 'string',
        'humanName': 'Study'
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
    }
};
