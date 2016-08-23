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
        'coerceToType': 'string'
    },
    'meta.acquisition.pixelsX': {
        'coerceToType': 'integer'
    },
    'meta.acquisition.pixelsY': {
        'coerceToType': 'integer'
    },
    'meta.clinical.benign_malignant': {
        'coerceToType': 'string'
    },
    'meta.clinical.sex': {
        'coerceToType': 'string'
    },
    'meta.clinical.age': {
        'coerceToType': 'number',
        'lowBound': 0,
        'highBound': 100
    }
};
